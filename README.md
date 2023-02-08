# surf_comp_timer
Application was written to run as the countdown timer for a surf competition.

The app is written in python 3 and tkinter.

App dependencies are listed in the "requirements.txt" file ... there is only one dependency - "just_playback" which will need to be installed.

The app starts an "event-start" sound file when the "Start" button is pressed and plays a "warning" sound when the time reaches the warning time and plays a "ending" sound to signify the end of the event.

Initial app configuration settings are stored in "config.ini" file. Mechansim to change some of these settings are provided within the app. All parameters can be changed by editing the "config.ini" file.

The app supports all types of sound files but they must be saved under the 'audio' folder.
