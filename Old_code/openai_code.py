import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk
from threading import Thread

from just_playback import Playback


CONFIG_FILE = "../config.ini"
BASE_PATH = Path(__file__).parent.absolute()
CONFIG = {}


def read_config(config_file):
    """Read the configuration from the file."""
    config = {}
    with open(config_file, 'r') as file:
        for line in file:
            if line.strip() and not line.startswith('#'):
                key, value = line.split('=')
                config[key.strip()] = value.strip()
    return config


def save_config(config_file, config):
    """Save the configuration to the file."""
    with open(config_file, 'w') as file:
        for key, value in config.items():
            file.write(f"{key}={value}\n")


class DeltaTemplate(string.Template):
    delimiter = "%"


def strf_delta(time_delta, fmt):
    d = {
        "D": time_delta.days,
        "H": time_delta.seconds // 3600,
        "M": (time_delta.seconds // 60) % 60,
        "S": time_delta.seconds % 60
    }
    t = DeltaTemplate(fmt)
    return t.substitute(**d)


class EventTimer(tk.Frame):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.parent = parent
        self.config = config

        self.fmt = "%H:%M:%S"
        self.color = "steelblue4"

        self.sound_path = BASE_PATH / self.config['AppSettings']['sound_path']
        self.start_event_sound = self.sound_path / self.config['AppSettings']['starting_sound']
        self.warning_sound = self.sound_path / self.config['AppSettings']['warning_sound']
        self.end_event_sound = self.sound_path / self.config['AppSettings']['ending_sound']

        self.event_duration = int(self.config['AppSettings']['event_duration'])
        self.warning_time = int(self.config['AppSettings']['warning_time'])

        self.timer_running = False
        self.time_now = None
        self.start_time = None
        self.finish_time = None
        self.alarm_id = None

        self.pack()

        self.create_widgets()
        self.set_timer_display()

    def create_widgets(self):
        my_notebook = ttk.Notebook(self)
        my_notebook.pack()

        self.app_frame = ttk.Frame(my_notebook, width=800, height=500)
        self.config_frame = ttk.Frame(my_notebook, width=800, height=300)

        self.sound_frame = ttk.Frame(self.app_frame, width=700, height=100)
        self.time_frame = ttk.Frame(self.app_frame, width=700, height=300)

        # Sound Settings
        self.start_sound_label = ttk.Label(
            self.sound_frame, text="Starting Sound:", font=("Arial", 12))
        self.start_sound_label.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)

        self.start_sound_entry = ttk.Entry(
            self.sound_frame, width=50)
        self.start_sound_entry.insert(
            tk.END, self.start_event_sound)
        self.start_sound_entry.grid(row=0, column=1, padx=10, pady=10)

        self.start_sound_button = ttk.Button(
            self.sound_frame, text="Browse", command=self.browse_start_sound)
        self.start_sound_button.grid(row=0, column=2, padx=10, pady=10)

        self.warning_sound_label = ttk.Label(
            self.sound_frame, text="Warning Sound:", font=("Arial", 12))
        self.warning_sound_label.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)

        self.warning_sound_entry = ttk.Entry(
            self.sound_frame, width=50)
        self.warning_sound_entry.insert(
            tk.END, self.warning_sound)
        self.warning_sound_entry.grid(row=1, column=1, padx=10, pady=10)

        self.warning_sound_button = ttk.Button(
            self.sound_frame, text="Browse", command=self.browse_warning_sound)
        self.warning_sound_button.grid(row=1, column=2, padx=10, pady=10)

        self.end_sound_label = ttk.Label(
            self.sound_frame, text="Ending Sound:", font=("Arial", 12))
        self.end_sound_label.grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)

        self.end_sound_entry = ttk.Entry(
            self.sound_frame, width=50)
        self.end_sound_entry.insert(
            tk.END, self.end_event_sound)
        self.end_sound_entry.grid(row=2, column=1, padx=10, pady=10)

        self.end_sound_button = ttk.Button(
            self.sound_frame, text="Browse", command=self.browse_end_sound)
        self.end_sound_button.grid(row=2, column=2, padx=10, pady=10)

        self.sound_frame.pack()

        # Timer Settings
        self.timer_frame = ttk.Frame(self.time_frame, width=700, height=100)

        self.timer_label = ttk.Label(
            self.timer_frame, text="Event Duration (seconds):", font=("Arial", 12))
        self.timer_label.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)

        self.timer_entry = ttk.Entry(
            self.timer_frame, width=10)
        self.timer_entry.insert(
            tk.END, self.event_duration)
        self.timer_entry.grid(row=0, column=1, padx=10, pady=10)

        self.timer_frame.pack()

        self.warning_frame = ttk.Frame(self.time_frame, width=700, height=100)

        self.warning_label = ttk.Label(
            self.warning_frame, text="Warning Time (seconds):", font=("Arial", 12))
        self.warning_label.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)

        self.warning_entry = ttk.Entry(
            self.warning_frame, width=10)
        self.warning_entry.insert(
            tk.END, self.warning_time)
        self.warning_entry.grid(row=0, column=1, padx=10, pady=10)

        self.warning_frame.pack()

        self.time_frame.pack()

        self.save_button = ttk.Button(
            self.config_frame, text="Save Settings", command=self.save_settings)
        self.save_button.pack(side=tk.RIGHT, padx=10, pady=10)

        self.reset_button = ttk.Button(
            self.config_frame, text="Reset Settings", command=self.reset_settings)
        self.reset_button.pack(side=tk.RIGHT, padx=10, pady=10)

        my_notebook.add(self.app_frame, text="Application")
        my_notebook.add(self.config_frame, text="Settings")

    def browse_start_sound(self):
        filename = filedialog.askopenfilename(
            initialdir=self.sound_path,
            title="Select Starting Sound",
            filetypes=(("WAV files", "*.wav"), ("MP3 files", "*.mp3"), ("All files", "*.*")))
        self.start_sound_entry.delete(0, tk.END)
        self.start_sound_entry.insert(tk.END, filename)

    def browse_warning_sound(self):
        filename = filedialog.askopenfilename(
            initialdir=self.sound_path,
            title="Select Warning Sound",
            filetypes=(("WAV files", "*.wav"), ("MP3 files", "*.mp3"), ("All files", "*.*")))
        self.warning_sound_entry.delete(0, tk.END)
        self.warning_sound_entry.insert(tk.END, filename)

    def browse_end_sound(self):
        filename = filedialog.askopenfilename(
            initialdir=self.sound_path,
            title="Select Ending Sound",
            filetypes=(("WAV files", "*.wav"), ("MP3 files", "*.mp3"), ("All files", "*.*")))
        self.end_sound_entry.delete(0, tk.END)
        self.end_sound_entry.insert(tk.END, filename)

    def set_timer_display(self):
        time_text = "00:00:00"
        self.timer_label = ttk.Label(self.app_frame, text=time_text,
                                     font=("Helvetica", 80), foreground=self.color)
        self.timer_label.pack(pady=20)

    def start_timer(self):
        self.time_now = datetime.datetime.now()
        self.start_time = self.time_now + datetime.timedelta(seconds=self.warning_time)
        self.finish_time = self.start_time + datetime.timedelta(seconds=self.event_duration)

        self.timer_running = True
        self.alarm_id = self.after(1000, self.update_timer)

    def stop_timer(self):
        self.timer_running = False
        if self.alarm_id is not None:
            self.after_cancel(self.alarm_id)
            self.alarm_id = None

    def update_timer(self):
        if self.timer_running:
            self.time_now = datetime.datetime.now()

            if self.time_now < self.start_time:
                self.timer_label.configure(foreground=self.color)
                self.timer_label.configure(text=strf_delta(
                    self.start_time - self.time_now, self.fmt))
            elif self.start_time <= self.time_now <= self.finish_time:
                self.timer_label.configure(foreground="dark green")
                self.timer_label.configure(text=strf_delta(
                    self.finish_time - self.time_now, self.fmt))
            else:
                self.timer_label.configure(foreground="red")
                self.timer_label.configure(text="00:00:00")
                self.play_sound(self.end_event_sound)
                self.timer_running = False

            if self.start_time - self.time_now <= datetime.timedelta(seconds=self.warning_time):
                self.play_sound(self.warning_sound)

            self.alarm_id = self.after(1000, self.update_timer)

    def play_sound(self, sound_path):
        playback_thread = Thread(target=Playback.play_sound, args=(sound_path,))
        playback_thread.start()

    def save_settings(self):
        self.config['AppSettings']['starting_sound'] = self.start_sound_entry.get()
        self.config['AppSettings']['warning_sound'] = self.warning_sound_entry.get()
        self.config['AppSettings']['ending_sound'] = self.end_sound_entry.get()
        self.config['AppSettings']['event_duration'] = self.timer_entry.get()
        self.config['AppSettings']['warning_time'] = self.warning_entry.get()

        save_config(CONFIG_FILE, self.config)

        self.start_event_sound = self.start_sound_entry.get()
        self.warning_sound = self.warning_sound_entry.get()
        self.end_event_sound = self.end_sound_entry.get()
        self.event_duration = int(self.timer_entry.get())
        self.warning_time = int(self.warning_entry.get())

        self.stop_timer()
        self.start_timer()

    def reset_settings(self):
        self.config = read_config(CONFIG_FILE)

        self.start_sound_entry.delete(0, tk.END)
        self.start_sound_entry.insert(tk.END, self.config['AppSettings']['starting_sound'])

        self.warning_sound_entry.delete(0, tk.END)
        self.warning_sound_entry.insert(tk.END, self.config['AppSettings']['warning_sound'])

        self.end_sound_entry.delete(0, tk.END)
        self.end_sound_entry.insert(tk.END, self.config['AppSettings']['ending_sound'])

        self.timer_entry.delete(0, tk.END)
        self.timer_entry.insert(tk.END, self.config['AppSettings']['event_duration'])

        self.warning_entry.delete(0, tk.END)
        self.warning_entry.insert(tk.END, self.config['AppSettings']['warning_time'])

        self.start_event_sound = self.config['AppSettings']['starting_sound']
        self.warning_sound = self.config['AppSettings']['warning_sound']
        self.end_event_sound = self.config['AppSettings']['ending_sound']
        self.event_duration = int(self.config['AppSettings']['event_duration'])
        self.warning_time = int(self.config['AppSettings']['warning_time'])

        self.stop_timer()
        self.start_timer()


if __name__ == "__main__":
    CONFIG = read_config(CONFIG_FILE)

    root = tk.Tk()
    root.title("Event Timer")
    root.geometry("800x500")
    root.resizable(False, False)

    timer_app = EventTimer(root, CONFIG)
    timer_app.start_timer()

    root.mainloop()
