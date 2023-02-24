# surf_comp_timer
This is a countdown timer app developed for running a surfing competition.

The app is written in python 3 and tkinter.

Dependencies: "just_playback" - included in "requirements.txt". 

The app:  
 . Plays an "event-start" sound file once the "Start" button is pressed, it then  
 . Plays a "event-warning" sound file when the time reaches the warning time, and  
 . Plays an "event-ending" sound file once the countdown reaches zero time remaining to signify the end of the event.

Configuration settings are stored in the "config.ini" file. All parameters can be changed by editing the "config.ini" file. The app provides a mechanism to change a subset of these settings. 

The app supports all types of sound files, but they must be saved within the 'audio' folder.
