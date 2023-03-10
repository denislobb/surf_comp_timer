import time
from pathlib import Path
from threading import Thread
from tkinter import *
from tkinter import filedialog
from tkinter import ttk
import datetime

from just_playback import Playback
from string import Template

import helper

config = helper.read_config()


class DeltaTemplate(Template):
    delimiter = "%"


def strfdelta(tdelta, fmt):
    d = {"D": tdelta.days}
    d["H"], rem = divmod(tdelta.seconds, 3600)
    d["M"], d["S"] = divmod(rem, 60)
    t = DeltaTemplate(fmt)
    return t.substitute(**d)


class EventTimer(Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack()

        self.config_file = "config.ini"
        self._sound_path = str(app.base_path / config['AppSettings']['sound_path'])
        self.get_sound_files()

        self.set_event_timings()

        self.start_time = datetime.datetime.now()
        self.finish_time = self.start_time + datetime.timedelta(seconds=self._event_duration)

        self._alarm_id = None
        self._paused = False

        self.color = "steelblue4"

        self.createTabs()
        self.createWidgets()
        self.createConfigWidgets()

    def get_sound_files(self):
        """Method to read sound files defined in config.ini."""
        self._start_event_sound = str(Path(self._sound_path, config["AppSettings"]["starting_sound"]))
        self._warning_sound = str(Path(self._sound_path, config["AppSettings"]["warning_sound"]))
        self._end_event_sound = str(Path(self._sound_path, config["AppSettings"]["ending_sound"]))

    def set_event_timings(self):
        """Method to read app timings from config.ini file"""
        self._event_duration = int(config['AppSettings']['event_duration'])
        self._warningtime = int(config['AppSettings']['warning_time'])

    def createTabs(self):
        """Method to create the App and Config Tabs"""
        # Create Tabs
        my_notebook = ttk.Notebook(self)
        my_notebook.pack()

        self.my_frame1 = Frame(my_notebook, width=800, height=500, padx=10)
        self.my_frame2 = Frame(my_notebook, width=800, height=300)

        self.my_frame1.pack(fill="both", expand=1)
        self.my_frame2.pack(fill="both", expand=1)

        # create sub frame for "play-sound" buttons
        self.sound_frame = Frame(self.my_frame1, width=700, height=100)
        self.sound_frame.grid(row=4, column=0, columnspan=4)

        # create sub frame to display times
        self.time_frame = Frame(self.my_frame1, width=600, height=100,
                                highlightbackground="silver", highlightthickness=1,
                                relief="ridge", padx=10)
        self.time_frame.grid(row=5, column=0, columnspan=3, pady=10)

        my_notebook.add(self.my_frame1, text="App")
        my_notebook.add(self.my_frame2, text="Config")

    def createWidgets(self):
        """Method to create the App buttons and display remaining event-time"""
        # Add start button
        startButton = Button(self.my_frame1, text="Start Timer", font=("Helvetica", 16),
                             command=self.startTime)
        startButton.grid(row=0, column=0, padx=20, pady=20)

        # Add Stop button
        stopButton = Button(self.my_frame1, text="Stop/Pause Timer", font=("Helvetica", 16),
                            command=self.stopTime)
        stopButton.grid(row=0, column=1, padx=20, pady=20, ipadx=20)

        # Add Reset button
        resetButton = Button(self.my_frame1, text="Reset Timer", font=("Helvetica", 16),
                             command=self.resetTime)
        resetButton.grid(row=0, column=2, padx=20, pady=20, ipadx=20)

        # Create "Play Sound" buttons
        sounds = {"start"  : {"track"      : self._start_event_sound,
                              "button_text": "Play\nStart-sound"},
                  "warning": {"track"      : self._warning_sound,
                              "button_text": "Play\nWarning-sound"},
                  "ending" : {"track"      : self._end_event_sound,
                              "button_text": "Play\nFinish-sound"}
                  }

        column = 0
        for v in sounds.values():
            track = v.get("track")
            button_text = v.get("button_text")
            playSoundButton = Button(self.sound_frame, text=button_text, font=("Helvetica", 10),
                                     command=lambda track=track: self.play_audio_thread(track))
            playSoundButton.grid(row=0, column=column, padx=5, pady=10)
            column += 1

        # Stop sound button
        stopSoundButton = Button(self.sound_frame, text="Stop\nAudio",
                                 font=("Helvetica", 10), bg="indianred1",
                                 command=self.stop_audio)
        stopSoundButton.grid(row=0, column=3, padx=5, pady=10, ipadx=20)

        # Quit button
        quit_button = Button(self.sound_frame, text="Quit", font=("Helvetica", 16),
                             bg="red3", fg="white",
                             command=self.master.quit)
        quit_button.grid(row=0, column=4, padx=15, pady=10, ipadx=20)

        # Display timer  - row=1
        event_duration = int(config['AppSettings']['event_duration'])  # in seconds
        self.display_timer(event_duration)

    def display_timer(self, remaining_time):
        """Method to display the passed time to the App screen"""

        # display event start time
        start_time = self.start_time
        str_start_time = self.start_time.strftime('%H:%M:%S')
        start_time_label = Label(self.time_frame, text="Event start-time: " + str_start_time,
                                 font=('Helvetica', 10))
        start_time_label.grid(row=0, column=0, padx= 40, pady=10)

        # display schedule event finish time = start_time + event_duration
        finish_time = self.finish_time
        str_finish_time = finish_time.strftime('%H:%M:%S')
        finish_time_label = Label(self.time_frame, text="Scheduled finish-time: " + str_finish_time,
                                  font=('Helvetica', 10))
        finish_time_label.grid(row=0, column=1, padx= 40, pady=10)

        # display current time
        time_now = datetime.datetime.now()
        str_time_now = time_now.strftime('%H:%M:%S')
        time_now_label = Label(self.time_frame, text="Event current-time: " + str_time_now,
                               font=('Helvetica', 10))
        time_now_label.grid(row=0, column=2, padx= 40, pady=10)

        # display time remaining in the event
        remaining_time_variable = StringVar()
        # time_remaining = (finish_time - time_now + datetime.timedelta(seconds=1)).seconds
        if self._event_duration >= 3600:
            hrs, rem = divmod(remaining_time, 3600)
            mins, secs = divmod(rem, 60)
            time_format = f"{hrs:02d}:{mins:02d}:{secs:02d}"
        else:
            mins, secs = divmod(remaining_time, 60)
            time_format = f"{mins:02d}:{secs:02d}"

        remaining_time_variable.set(time_format)
        time_remaining_label = Label(self.my_frame1, textvariable=remaining_time_variable,
                                     font=('Helvetica', 80), fg=self.color)
        time_remaining_label.grid(row=1, column=0, columnspan=4, pady=20)

        return

    def startTime(self):
        """ Resume """
        self._paused = False
        if self._alarm_id is None:
            self.countdown(self._event_duration)
            self.play_audio_thread(self._start_event_sound)

    def stopTime(self):
        """ Pause """
        if self._alarm_id is not None:
            self._paused = True
            self.stop_audio()

    def resetTime(self):
        """Restore to last countdown value. """

        self.start_time = datetime.datetime.now()
        self.finish_time = self.start_time + datetime.timedelta(seconds=self._event_duration)
        self.color = "steelblue4"

        if self._alarm_id is not None:
            self.master.after_cancel(self._alarm_id)
            self._alarm_id = None
            self._paused = False
            self.display_timer((self.finish_time - self.start_time).seconds)

    def countdown(self, timeInSeconds, start=True):
        """Method that does the actual event countdown"""
        if start:
            self._event_duration = timeInSeconds
            self.start_time = datetime.datetime.now()
            self.finish_time = self.start_time + datetime.timedelta(seconds=self._event_duration)

        if self._paused:
            self._alarm_id = self.master.after(1000, self.countdown, timeInSeconds, False)

        else:   # not paused
            self.display_timer(timeInSeconds)

            if timeInSeconds == self._warningtime:
                self.play_audio_thread(self._warning_sound)
                self.color = "red"
            elif timeInSeconds == 0:
                self.play_audio_thread(self._end_event_sound)
                self._paused = True

            self.time_remaining = (self.finish_time - datetime.datetime.now()).seconds
            self._alarm_id = self.master.after(1000, self.countdown, self.time_remaining, False)

    def play_audio_thread(self, track):
        """Method to Play the selected audio track in separate thread to avoid timing issues"""
        playback.load_file(track)
        playback.loop_at_end(False)

        thread1 = Thread(target=playback.play())
        thread1.start()

    def stop_audio(self):
        """Method to stop playing the audio"""
        if playback.active:
            playback.stop()

    def createConfigWidgets(self):
        """Method to create the configuration widgets"""
        # ## CHANGE EVENT DURATION - default = 1200 secs (20 min * 60).
        grid_row = 2
        config_field = 'event_duration'
        button_text = "Change Event Duration (secs)"
        widget_name = "self.event_duration"
        self.change_timings(grid_row, config_field, button_text, widget_name)

        # # ## CHANGE WARNING TIME - default = 300 secs (5 min * 60).
        grid_row = 3
        config_field = 'warning_time'
        button_text = "Change Warning Time (secs)"
        widget_name = "self.warningtime"
        self.change_timings(grid_row, config_field, button_text, widget_name)

        # ## CHANGE START-EVENT SOUND FILE.
        grid_row = 4
        config_field = "starting_sound"
        button_text = "Change 'Start-event' Sound File"
        widget_name = "self.start_soundlabel"
        self.change_sound_files(grid_row, config_field, button_text, widget_name)

        # ## CHANGE WARNING SOUND FILE.
        grid_row = 5
        config_field = "warning_sound"
        button_text = "Change 'Warning' Sound File"
        widget_name = "self.warning_soundlabel"
        self.change_sound_files(grid_row, config_field, button_text, widget_name)

        # ## CHANGE END-OF-EVENT SOUND FILE.
        grid_row = 6
        config_field = "ending_sound"
        button_text = "Change 'End-of-event' Sound File"
        widget_name = "self.ending_soundlabel"
        self.change_sound_files(grid_row, config_field, button_text, widget_name)

    def change_timings(self, grid_row, config_field, button_text, widget_name):
        """Method to change the event-duration and warning-time"""
        # change event timings
        # Display current setting
        widget_name = Entry(self.my_frame2, width=30)
        widget_name.grid(row=grid_row, column=1, padx=5, pady=5)
        widget_name.insert(0, f"{config['AppSettings'][config_field]}")

        time_button = Button(self.my_frame2, text=button_text, width=30, anchor="w",
                             command=lambda arg1=grid_row, arg2=config_field, arg3=widget_name:
                             self.change_duration(arg1, arg2, arg3))
        time_button.grid(row=grid_row, column=0, padx=5, pady=5)

        return

    def change_duration(self, grid_row, config_field, widget_name):
        """Method to save changes to config.ini and display updated values"""
        duration = widget_name.get()
        # Update configuration file
        helper.save_config("config.ini", config, "AppSettings", config_field, duration)
        # Display changed value
        widget_name = Label(self.my_frame2, text=f"Value changed to {config['AppSettings'][config_field]}",
                            anchor="w", width=30)
        widget_name.grid(row=grid_row, column=2, padx=5, pady=5)
        # reset timings in self
        self.set_event_timings()
        # Set timer display
        self.display_timer(int(config['AppSettings']['event_duration']))
        return

    def change_sound_files(self, grid_row, config_field, button_text, widget_name):
        """Method to change the "sound" files"""

        # Display current setting
        widget_name = Entry(self.my_frame2, width=30)
        widget_name.grid(row=grid_row, column=1, padx=5, pady=5)
        widget_name.insert(0, f"{config['AppSettings'][config_field]}")

        change_sound_button = Button(self.my_frame2, text=button_text, width=30, anchor="w",
                                     command=lambda arg1=config_field, widget=widget_name:
                                     self.get_new_sound_file(arg1, widget)
                                     )
        change_sound_button.grid(row=grid_row, column=0, padx=5, pady=5)

    def get_new_sound_file(self, config_field, widget):
        """Method to select and save the selected sound file"""
        filename = filedialog.askopenfilename(
                initialdir=str(self._sound_path),
                title="Select Sound File",
                filetypes=(("Sound Files", "*.mp3"), ("All Files", "*.*"),)
        )

        field = str(Path(filename).name)
        # update config file
        helper.save_config("config.ini", config, 'AppSettings', config_field, field)
        # refresh sound files in self
        self.get_sound_files()
        # refresh screens
        self.display_current_sound_file(config_field, widget)
        return

    def display_current_sound_file(self, config_field, widget):
        """Method to display the selected sound files"""
        widget.delete(0, "end")
        widget.insert(0, f"{config['AppSettings'][config_field]}")

    def quit(self):
        """Method to Quit the application."""
        self._interrupt = True


class App(Tk):
    def __init__(self):
        super(App, self).__init__()

        self.base_path = Path(__file__).parent.absolute()
        self.title(config['AppSettings']["app_title"])
        self.geometry(config['AppSettings']["app_geometry"])
        self.iconbitmap(str(self.base_path / config['AppSettings']["app_iconbitmap"]))


if __name__ == "__main__":
    playback = Playback()

    app = App()
    EventTimer(app)
    app.mainloop()

