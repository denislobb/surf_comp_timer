#!/usr/bin/env python3
import datetime
from pathlib import Path
from threading import Thread
import configparser

from tkinter import *
from tkinter import ttk, Button, Label, Frame, filedialog

from just_playback import Playback
from tkmacosx import Button

import logging

logger = logging.getLogger()
file_handler = logging.FileHandler('logs.log')
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s',
                              datefmt='%Y-%m-%d %I:%M:%S'
                              )
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def read_config(config_file):
    config_obj = configparser.ConfigParser()
    # with open('config.ini', 'r') as file:
    #     config = file.read()
    config_obj.read(config_file)
    return config_obj


def save_config(config_file, config_obj):
    with open(config_file, "w") as file_obj:
        config_obj.write(file_obj)
    return


CONFIG_FILE = "config.ini"
SOUND_PATH = Path(__file__).parent / 'audio'
config = read_config(CONFIG_FILE)


def strf_delta(tdelta: int) -> str:
    days = tdelta // 86400
    hrs = tdelta // 3600
    mins = (tdelta // 60) % 60
    secs = tdelta % 60
    return f'{days:02}:{hrs:02}:{mins:02}:{secs:02}' if hrs else f'{mins:02}:{secs:02}'


class EventTimer(Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack()

        self.fmt = "%H:%M:%S"
        self.color = "steelblue4"

        # SOUND_PATH = BASE_PATH / config['AppSettings']['sound_path']
        self.start_event_sound = str(SOUND_PATH / config["AppSettings"]["starting_sound"])
        self.warning_sound = str(SOUND_PATH / config["AppSettings"]["warning_sound"])
        self.end_event_sound = str(SOUND_PATH / config["AppSettings"]["ending_sound"])
        # Get event_timings.
        self.event_duration = int(config['AppSettings']['event_duration'])
        self.warning_time = int(config['AppSettings']['warning_time'])
        # Initialise variables
        self.timer_running = False
        self.time_now = None
        self.start_time = None
        self.finish_time = None
        self.warning_start_time = None
        self.alarm_id = None

        self.pack()

        # Create application Notebook
        self.app_notebook = ttk.Notebook(self)
        self.app_notebook.pack()

        self.create_widgets()
        # self.create_buttons()
        self.create_settings_widgets()

        self.set_timer_display()

    def create_widgets(self):
        # Create frame for main application.
        self.app_frame = ttk.Frame(self.app_notebook, padding=(10))
        self.app_frame.pack(fill="both", expand=1)
        # create sub frame for "play-sound" buttons
        self.sound_frame = ttk.Frame(self.app_frame, padding=(5))
        self.sound_frame.grid(row=4, column=0, columnspan=4)

        # create sub frame to display times
        self.time_frame = Frame(self.app_frame,
                                highlightbackground="silver", highlightthickness=1,
                                relief="ridge", padx=10)
        self.time_frame.grid(row=5, column=0, columnspan=3, pady=10)
        self.app_notebook.add(self.app_frame, text="Timer")

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
        self.remaining_time_label = Label(self.app_frame, font=('Helvetica', 80), fg=self.color)
        self.remaining_time_label.grid(row=1, column=0, columnspan=4, pady=20)

        # Add Start-button
        start_button = Button(self.app_frame,
                              text="Start Timer", font=("Helvetica", 16), bg="Lime", fg="Black",
                              command=self.start_timer)
        start_button.grid(row=0, column=0, padx=20, pady=20)
        # Add Stop-button
        stop_button = Button(self.app_frame,
                             text="Stop Timer", font=("Helvetica", 16), bg="red", fg="white",
                             command=self.stop_timer)
        stop_button.grid(row=0, column=1, padx=20, pady=20, ipadx=20)
        # Add Reset-button
        reset_button = Button(self.app_frame,
                              text="Reset Timer", font=("Helvetica", 16), bg="Orange", fg="Black",
                              command=self.reset_timer)
        reset_button.grid(row=0, column=2, padx=20, pady=20, ipadx=20)

        # Create "Play-sounds" buttons
        self.create_play_audio_buttons()

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

    def create_play_audio_buttons(self):
        sounds = {"start": {"sound_track": self.start_event_sound,
                            "button_text": "Play\nStart-sound"},
                  "warning": {"sound_track": self.warning_sound,
                              "button_text": "Play\nWarning-sound"},
                  "ending": {"sound_track": self.end_event_sound,
                             "button_text": "Play\nFinish-sound"}
                  }

        column = 0

        for v in sounds.values():
            sound_track = v.get("sound_track")
            button_text = v.get("button_text")
            play_audio_thread_button = Button(
                self.sound_frame,
                text=button_text, font=("Helvetica", 10),
                command=lambda track=sound_track: self.play_audio_thread(track))
            play_audio_thread_button.grid(row=0, column=column, padx=5, pady=10)
            column += 1

    def create_settings_widgets(self):
        # Create frame to manage configuration options.
        self.settings_frame = ttk.Frame(self.app_notebook, width=800, height=300, padding=(10))
        self.settings_frame.pack(fill="both", expand=1)
        self.app_notebook.add(self.settings_frame, text="Settings")

        self.sound_settings_frame = ttk.Frame(self.settings_frame, width=700, height=100)
        self.timer_settings_frame = ttk.Frame(self.settings_frame, width=700, height=300)

        # Sound Settings
        self.start_sound_label = ttk.Label(
            self.sound_settings_frame, text="Starting Sound:", font=("Arial", 12))
        self.start_sound_label.grid(row=0, column=0, padx=10, pady=10, sticky=W)

        self.start_sound_entry = ttk.Entry(
            self.sound_settings_frame, width=50)
        self.start_sound_entry.insert(
            END, self.start_event_sound)
        self.start_sound_entry.grid(row=0, column=1, padx=10, pady=10)

        self.start_sound_button = ttk.Button(
            self.sound_settings_frame, text="Browse", command=self.browse_start_sound)
        self.start_sound_button.grid(row=0, column=2, padx=10, pady=10)

        self.warning_sound_label = ttk.Label(
            self.sound_settings_frame, text="Warning Sound:", font=("Arial", 12))
        self.warning_sound_label.grid(row=1, column=0, padx=10, pady=10, sticky=W)

        self.warning_sound_entry = ttk.Entry(
            self.sound_settings_frame, width=50)
        self.warning_sound_entry.insert(
            END, self.warning_sound)
        self.warning_sound_entry.grid(row=1, column=1, padx=10, pady=10)

        self.warning_sound_button = ttk.Button(
            self.sound_settings_frame, text="Browse", command=self.browse_warning_sound)
        self.warning_sound_button.grid(row=1, column=2, padx=10, pady=10)

        self.end_sound_label = ttk.Label(
            self.sound_settings_frame, text="Ending Sound:", font=("Arial", 12))
        self.end_sound_label.grid(row=2, column=0, padx=10, pady=10, sticky=W)

        self.end_sound_entry = ttk.Entry(
            self.sound_settings_frame, width=50)
        self.end_sound_entry.insert(
            END, self.end_event_sound)
        self.end_sound_entry.grid(row=2, column=1, padx=10, pady=10)

        self.end_sound_button = ttk.Button(
            self.sound_settings_frame, text="Browse", command=self.browse_end_sound)
        self.end_sound_button.grid(row=2, column=2, padx=10, pady=10)

        self.sound_settings_frame.pack()

        # Timer Settings
        # Event duration setting
        self.event_duration_label = ttk.Label(
            self.timer_settings_frame, text="Event Duration (seconds):", font=("Arial", 12))
        self.event_duration_label.grid(row=0, column=0, padx=10, pady=10, sticky=W)

        self.timer_entry = ttk.Entry(
            self.timer_settings_frame, width=10)
        self.timer_entry.insert(
            END, str(self.event_duration))
        self.timer_entry.grid(row=0, column=1, padx=10, pady=10)

        # Warning time setting
        self.warning_label = ttk.Label(
            self.timer_settings_frame, text="Warning Time (seconds):", font=("Arial", 12))
        self.warning_label.grid(row=1, column=0, padx=10, pady=10, sticky=W)

        self.warning_entry = ttk.Entry(
            self.timer_settings_frame, width=10)
        self.warning_entry.insert(
            END, str(self.warning_time))
        self.warning_entry.grid(row=1, column=1, padx=10, pady=10)

        self.timer_settings_frame.pack()

        self.save_button = ttk.Button(
            self.settings_frame, text="Save Settings", command=self.save_settings)
        self.save_button.pack(side=RIGHT, padx=10, pady=10)

        self.reset_button = ttk.Button(
            self.settings_frame, text="Reset Settings", command=self.reset_settings)
        self.reset_button.pack(side=RIGHT, padx=10, pady=10)

    def browse_start_sound(self):
        filename = filedialog.askopenfilename(
            initialdir=SOUND_PATH,
            title="Select Starting Sound",
            filetypes=(("MP3 files", "*.mp3"), ("WAV files", "*.wav"), ("All files", "*.*")))
        self.start_sound_entry.delete(0, END)
        self.start_sound_entry.insert(END, filename)

    def browse_warning_sound(self):
        filename = filedialog.askopenfilename(
            initialdir=SOUND_PATH,
            title="Select Warning Sound",
            filetypes=(("MP3 files", "*.mp3"), ("WAV files", "*.wav"), ("All files", "*.*")))
        self.warning_sound_entry.delete(0, END)
        self.warning_sound_entry.insert(END, filename)

    def browse_end_sound(self):
        filename = filedialog.askopenfilename(
            initialdir=SOUND_PATH,
            title="Select Ending Sound",
            filetypes=(("MP3 files", "*.mp3"), ("WAV files", "*.wav"), ("All files", "*.*")))
        self.end_sound_entry.delete(0, END)
        self.end_sound_entry.insert(END, filename)


    def set_timer_display(self):
        self.time_now = datetime.datetime.now()
        self.start_time = self.time_now
        self.finish_time = self.start_time + datetime.timedelta(seconds=self.event_duration)
        self.warning_start_time = self.finish_time - datetime.timedelta(seconds=self.event_duration)

        self.start_time_label.configure(text=f"Start-time: {self.start_time.strftime(self.fmt)}")
        self.finish_time_label.configure(text=f"Finish-time: {self.finish_time.strftime(self.fmt)}")
        self.time_now_label.configure(text=f"Time-now: {self.time_now.strftime(self.fmt)}")

        time_text = strf_delta(self.event_duration)
        self.remaining_time_label.configure(text=time_text)

    def start_timer(self):
        self.time_now = datetime.datetime.now()
        self.start_time = self.time_now
        self.finish_time = self.start_time + datetime.timedelta(seconds=self.event_duration)
        self.warning_start_time = self.finish_time - datetime.timedelta(seconds=self.warning_time)

        self.start_time_label.configure(text=f"Start-time: {self.start_time.strftime(self.fmt)}")
        self.finish_time_label.configure(text=f"Finish-time: {self.finish_time.strftime(self.fmt)}")
        self.time_now_label.configure(text=f"Time-now: {self.time_now.strftime(self.fmt)}")
        self.timer_running = True
        self.remaining_time_label.configure(foreground="dark green")
        self.play_audio_thread(self.start_event_sound)
        self.alarm_id = self.after(1000, self.update_timer)

    def stop_timer(self):
        self.timer_running = False
        if self.alarm_id is not None:
            self.after_cancel(self.alarm_id)
            self.alarm_id = None

    def update_timer(self):
        if self.timer_running:
            self.time_now = datetime.datetime.now()
            self.time_now_label.configure(text=f"Time-now: {self.time_now.strftime(self.fmt)}")
            remaining_time_in_seconds = (self.finish_time - self.time_now).seconds + 1

            if self.start_time <= self.time_now < self.warning_start_time:
                self.remaining_time_label.configure(text=strf_delta(remaining_time_in_seconds))
                self.alarm_id = self.after(1000, self.update_timer)

            elif self.warning_start_time <= self.time_now <= self.finish_time:
                self.remaining_time_label.configure(foreground="red")
                self.remaining_time_label.configure(text=strf_delta(remaining_time_in_seconds))
                if remaining_time_in_seconds == self.warning_time:
                    self.play_audio_thread(self.warning_sound)
                self.alarm_id = self.after(1000, self.update_timer)

            else:
                logger.info(
                    f'Event_duration: {self.event_duration} secs, '
                    f'Started: {self.start_time.strftime(self.fmt)}, '
                    f'Planned_finish: {self.finish_time.strftime(self.fmt)}, '
                    f'Finished: {self.time_now.strftime(self.fmt)}, '
                    f'Time_error: {(self.time_now - self.finish_time).seconds}')

                self.remaining_time_label.configure(text="Event Finished")
                self.play_audio_thread(self.end_event_sound)
                self.timer_running = False
                if remaining_time_in_seconds == 0:
                    self.play_audio_thread(self.end_event_sound)

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

    def save_settings(self):
        config['AppSettings']['starting_sound'] = Path(self.start_sound_entry.get()).name
        config['AppSettings']['warning_sound'] = Path(self.warning_sound_entry.get()).name
        config['AppSettings']['ending_sound'] = Path(self.end_sound_entry.get()).name
        config['AppSettings']['event_duration'] = self.timer_entry.get()
        config['AppSettings']['warning_time'] = self.warning_entry.get()

        save_config(CONFIG_FILE, config)

        self.start_event_sound = self.start_sound_entry.get()
        self.warning_sound = str(SOUND_PATH / Path(self.warning_sound_entry.get()).name)
        self.end_event_sound = str(SOUND_PATH / Path(self.end_sound_entry.get()).name)
        self.event_duration = int(self.timer_entry.get())
        self.warning_time = int(self.warning_entry.get())

        self.create_play_audio_buttons()

    def reset_settings(self):
        self.config = read_config(CONFIG_FILE)

        self.start_sound_entry.delete(0, END)
        self.start_sound_entry.insert(END, config['AppSettings']['starting_sound'])

        self.warning_sound_entry.delete(0, END)
        self.warning_sound_entry.insert(END, config['AppSettings']['warning_sound'])

        self.end_sound_entry.delete(0, END)
        self.end_sound_entry.insert(END, config['AppSettings']['ending_sound'])

        self.timer_entry.delete(0, END)
        self.timer_entry.insert(END, config['AppSettings']['event_duration'])

        self.warning_entry.delete(0, END)
        self.warning_entry.insert(END, config['AppSettings']['warning_time'])

        self.start_event_sound = str(SOUND_PATH / config['AppSettings']['starting_sound'])
        self.warning_sound = str(SOUND_PATH / config['AppSettings']['warning_sound'])
        self.end_event_sound = str(SOUND_PATH / config['AppSettings']['ending_sound'])
        self.event_duration = int(config['AppSettings']['event_duration'])
        self.warning_time = int(config['AppSettings']['warning_time'])


class App(Tk):
    def __init__(self):
        super(App, self).__init__()
        self.base_path = Path(__file__).cwd()
        self.title(config['AppSettings']['app_title'])
        self.geometry(config['AppSettings']['app_geometry'])
        self.iconbitmap(str(self.base_path / config['AppSettings']["app_iconbitmap"]))


# if __name__ == "__main__":
logger.setLevel(logging.INFO)
playback = Playback()
app = App()
EventTimer(app)
app.mainloop()
