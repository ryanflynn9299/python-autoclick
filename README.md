# python-autoclick
A simple, customize-able python CLI program to repeatedly click your screen

# Requires
Python 3\
pynput (pip install pynput)

# How to use
v1(Developer only): clone the repo and run 'python teams.py' from the command line 

# Functions
--end=HH:mmA        : Set the quit time of the program, the clicker will stop at this time. \
--delay=HhMmSsNms   : Set the delay between clicks (defaults to 5m )\
--position          : Interactive mode - will prompt user to click a position on the screen where clicks should be delivered. \
>                      Will return cursor back to orignal position. Note: if chosen location makes the program click off the current      
>                      application, making it 'inactive', the application will remain 'inactive' (this may interrupt typing).
