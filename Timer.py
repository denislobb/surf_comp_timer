#!/usr/bin/env python3

import datetime
import tkinter
from pathlib import Path
from threading import Thread
from tkinter import Tk, Button, Label, Entry, Frame, filedialog, ttk
from tkmacosx import Button

from just_playback import Playback

import helper


CONFIG_FILE = "config.ini"
config = helper.read_config(CONFIG_FILE)


def strf_delta(tdelta: int) -> str:
    days = tdelta // (86400)
    hrs = tdelta // 3600
    mins = (tdelta // 60) % 60
    secs = tdelta % 60
    return f'{days:02}:{hrs:02}:{mins:02}:{secs:02}' if days else f'{hrs:02}:{mins:02}:{secs:02}'


class EventTimer(Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack()

        self.fmt = "%H:%M:%S"
        self.color = "steelblue4"

        self._sound_path = str(app.base_path / config['AppSettings']['sound_path'])
        # Get sound files
        self._start_event_sound = str(Path(self._sound_path, config["AppSettings"]["starting_sound"]))
        self._warning_sound = str(Path(self._sound_path, config["AppSettings"]["warning_sound"]))
        self._end_event_sound = str(Path(self._sound_path, config["AppSettings"]["ending_sound"]))

        # Get event_timings.
        self._event_duration = int(config['AppSettings']['event_duration'])
        self._warning_time = int(config['AppSettings']['warning_time'])
        # Initialise variables
        self.time_now = None
        self.start_time = None
        self.finish_time = None
        self._alarm_id = None
        self.timer_running = False

        # Create application Notebook
        my_notebook = ttk.Notebook(self)
        my_notebook.pack()

        # Create application frames
        # Create frame for main application.
        self.my_frame1 = Frame(my_notebook, width=800, height=500, padx=10)
        self.my_frame1.pack(fill="both", expand=1)

        # Create frame to manage configuration options.
        self.my_frame2 = Frame(my_notebook, width=800, height=300)
        self.my_frame2.pack(fill="both", expand=1)

        # create sub frame for "play-sound" buttons
        self.sound_frame = Frame(self.my_frame1, width=700, height=100)
        self.sound_frame.grid(row=4, column=0, columnspan=4)

        # create sub frame to display times
        self.time_frame = Frame(
            self.my_frame1, width=600, height=100,
            highlightbackground="silver", highlightthickness=1,
            relief="ridge", padx=10)
        self.time_frame.grid(row=5, column=0, columnspan=3, pady=10)

        my_notebook.add(self.my_frame1, text="Timer")
        my_notebook.add(self.my_frame2, text="Settings")

        # Create Labels
        # Start-time label.
        self.start_time_label = Label(self.time_frame, font=('Helvetica', 10))
        self.start_time_label.grid(row=0, column=0, padx=40, pady=10)

        # Finish-time (= start_time + duration) label.
        self.finish_time_label = Label(self.time_frame, font=('Helvetica', 10))
        self.finish_time_label.grid(row=0, column=1, padx=40, pady=10)

        # Current-time label
        self.time_now_label = Label(self.time_frame, font=('Helvetica', 10))
        self.time_now_label.grid(row=0, column=2, padx=40, pady=10)

        # Remaining-time label ... text to be created later.
        self.remaining_time_label = Label(self.my_frame1, font=('Helvetica', 80), fg=self.color)
        self.remaining_time_label.grid(row=1, column=0, columnspan=4, pady=20)

        self.create_buttons()
        self.create_config_widgets()
        self.set_timer_display()

    def create_buttons(self):
        """Method to create the App buttons and display remaining event-time"""
        # Add Start-button
        start_button = Button(
            self.my_frame1,
            text="Start Timer", font=("Helvetica", 16), bg="Lime", fg="Black",
            command=self.start_timer)
        start_button.grid(row=0, column=0, padx=20, pady=20)

        # Add Stop-button
        stop_button = Button(
            self.my_frame1,
            text="Stop Timer", font=("Helvetica", 16), bg="red", fg="white",
            command=self.stop_timer)
        stop_button.grid(row=0, column=1, padx=20, pady=20, ipadx=20)

        # Add Reset-button
        reset_button = Button(
            self.my_frame1,
            text="Reset Timer", font=("Helvetica", 16), bg="Orange", fg="Black",
            command=self.reset_timer)
        reset_button.grid(row=0, column=2, padx=20, pady=20, ipadx=20)

        # Create "Play-sounds" buttons
        sounds={"start": {"sound_track": self._start_event_sound,
                          "button_text": "Play\nStart-sound"},
                "warning": {"sound_track": self._warning_sound,
                            "button_text": "Play\nWarning-sound"},
                "ending": {"sound_track": self._end_event_sound,
                           "button_text": "Play\nFinish-sound"}
                }

        column = 0

        for v in sounds.values():
            sound_track = v.get("sound_track")
            button_text = v.get("button_text")
            play_sound_button = Button(
                self.sound_frame,
                text=button_text, font=("Helvetica", 10),
                command=lambda track=sound_track: self.play_audio_thread(track))
            play_sound_button.grid(row=0, column=column, padx=5, pady=10)
            column += 1

            # Stop-sound button
        stop_sound_button = Button(
            self.sound_frame,
            text="Stop\nAudio", font=("Helvetica", 10), bg="Orange",
            command=self.stop_audio)
        stop_sound_button.grid(row=0, column=3, padx=5, pady=10, ipadx=20)

        # Quit-button
        quit_button = Button(
            self.sound_frame,
            text="Quit", font=("Helvetica", 16), bg="red", fg="white",
            command=self.master.quit)
        quit_button.grid(row=0, column=4, padx=15, pady=10, ipadx=20)

    def start_timer(self):
        """ Start the timer from the 'Start-button """
        self.timer_running = True
        self.set_timer_display()
        self.countdown(self._event_duration)
        self.play_audio_thread(self._start_event_sound)

    def set_timer_display(self):
        """ Start the timer from the 'Start-button """
        # Set text for 'start-time' label.
        self.start_time = datetime.datetime.now()
        self.start_time_label.configure(text=f"Start-time: {self.start_time.strftime(self.fmt)}")
        # Set text for 'finish-time' label.
        self.finish_time = self.start_time + datetime.timedelta(seconds=self._event_duration)
        self.finish_time_label.configure(text=f"Finish-time: {self.finish_time.strftime(self.fmt)}")
        # Set text for 'remaining-time' and 'current-time' labels
        self.update_timer()

    def update_timer(self) -> int:
        """Method to display the passed time to the App screen"""
        # Update 'current-time' label.
        self.time_now = datetime.datetime.now()
        self.time_now_label.configure(text=f"Current-time: {self.time_now.strftime(self.fmt)}")
        # Update the 'remaining-time' label.
        remaining_time = self.get_remaining_time()
        time_format = strf_delta(remaining_time)
        self.remaining_time_label.configure(text=time_format)

        return remaining_time

    def get_remaining_time(self) -> int:
        if self.timer_running:
            return (self.finish_time - datetime.datetime.now()).seconds
        else:
            return self._event_duration

    def countdown(self, remaining_time_in_seconds: int):
        """Method that does the actual event countdown"""
        if self.timer_running:
            if remaining_time_in_seconds == self._warning_time:
                self.play_audio_thread(self._warning_sound)
                self.remaining_time_label.configure(fg="red")
                self._alarm_id = self.master.after(1000, self.countdown, self.update_timer())
            elif remaining_time_in_seconds == 0:
                self.play_audio_thread(self._end_event_sound)
                self.remaining_time_label.configure(text="00:00:00")
                # Stop timer
                self.timer_running = False
            else:
                self._alarm_id = self.master.after(1000, self.countdown, self.update_timer())

    def stop_timer(self):
        """ Stop the timer via the Stop-button """
        self.timer_running = False
        self.stop_audio()

    def reset_timer(self):
        """Reset the Timer via the Reset-button. """
        self.timer_running = False
        self.remaining_time_label.configure(fg=self.color)
        self.set_timer_display()

    @staticmethod
    def play_audio_thread(sound_track):
        """Method to Play the selected audio sound_track in separate thread to avoid timing issues"""
        playback.load_file(sound_track)
        playback.loop_at_end(False)

        thread1 = Thread(target=playback.play())
        thread1.start()

    @staticmethod
    def stop_audio():
        """Method to stop playing the audio"""
        if playback.active:
            playback.stop()

    def create_config_widgets(self):
        """Method to create the configuration widgets"""
        # ## CHANGE EVENT DURATION - default = 1200 secs (20 min * 60).
        grid_row = 2
        config_field = 'event_duration'
        button_text = "Change Event-duration (secs)"
        widget_name = "self.event_duration"
        self.change_timings(grid_row, config_field, button_text, widget_name)

        # # ## CHANGE WARNING TIME - default = 300 secs (5 min * 60).
        grid_row = 3
        config_field = 'warning_time'
        button_text = "Change Warning-time (secs)"
        widget_name = "self.warning_time"
        self.change_timings(grid_row, config_field, button_text, widget_name)

        # ## CHANGE START-EVENT SOUND FILE.
        grid_row = 4
        config_field = "starting_sound"
        button_text = "Change 'Start-event' Sound File"
        widget_name = "self.start_sound_label"
        self.change_sound_files(grid_row, config_field, button_text, widget_name)

        # ## CHANGE WARNING SOUND FILE.
        grid_row = 5
        config_field = "warning_sound"
        button_text = "Change 'Warning' Sound File"
        widget_name = "self.warning_sound_label"
        self.change_sound_files(grid_row, config_field, button_text, widget_name)

        # ## CHANGE END-OF-EVENT SOUND FILE.
        grid_row = 6
        config_field = "ending_sound"
        button_text = "Change 'End-of-event' Sound File"
        widget_name = "self.ending_sound_label"
        self.change_sound_files(grid_row, config_field, button_text, widget_name)

    def change_timings(self, grid_row, config_field, button_text, widget_name):
        """Method to change the event-duration and warning-time"""
        # change event timings
        # Display current setting
        widget_name = Entry(self.my_frame2, width=30)
        widget_name.grid(row=grid_row, column=1, padx=5, pady=5)
        widget_name.insert(0, f"{config['AppSettings'][config_field]}")

        time_button = Button(self.my_frame2,
                             text=button_text, width=300, anchor=tkinter.W,
                             command=lambda arg1=grid_row, arg2=config_field, arg3=widget_name:
                             self.change_duration(arg1, arg2, arg3))
        time_button.grid(row=grid_row, column=0, padx=5, pady=5)


    def change_duration(self, grid_row, config_field, widget_name):
        """Method to save changes to config.ini and display updated values"""
        duration = widget_name.get()
        # Update configuration file
        helper.save_config(CONFIG_FILE, config, "AppSettings", config_field, duration)
        # Display changed value
        widget_name = Label(
            self.my_frame2,
            text=f"Value changed to {config['AppSettings'][config_field]}",
            anchor="w", width=30)
        widget_name.grid(row=grid_row, column=2, padx=5, pady=5)
        # reset timings in self
        self._event_duration = int(config['AppSettings']['event_duration'])
        self._warning_time = int(config['AppSettings']['warning_time'])
        # Set timer display
        self.update_timer()

    def change_sound_files(self, grid_row, config_field, button_text, widget_name):
        """Method to change the "sound" files"""

        # Display current setting
        widget_name = Entry(self.my_frame2, width=30)
        widget_name.grid(row=grid_row, column=1, padx=5, pady=5)
        widget_name.insert(0, f"{config['AppSettings'][config_field]}")

        change_sound_button = Button(self.my_frame2, text=button_text, width=300, anchor="w",
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
        helper.save_config(CONFIG_FILE, config, 'AppSettings', config_field, field)
        # refresh sound files in self
        self._start_event_sound = str(Path(self._sound_path, config["AppSettings"]["starting_sound"]))
        self._warning_sound = str(Path(self._sound_path, config["AppSettings"]["warning_sound"]))
        self._end_event_sound = str(Path(self._sound_path, config["AppSettings"]["ending_sound"]))
        # refresh screens
        self.display_current_sound_file(config_field, widget)

    def display_current_sound_file(self, config_field, widget):
        """Method to display the selected sound files"""
        widget.delete(0, "end")
        widget.insert(0, f"{config['AppSettings'][config_field]}")


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
