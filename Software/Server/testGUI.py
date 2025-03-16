#!/usr/bin/env python3 
import pyfiglet
from colorama import Fore, Style, init
import sys
import tty
import termios

# Function to wait for a key press (Linux)
def wait_for_key():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        sys.stdin.read(1)  # Read a single key press
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

# Initialize color support
init(autoreset=True)

# Generate ASCII art title
title = pyfiglet.figlet_format("WOPR Systems", font="slant")
print(Fore.RED + title)

# Function to print a boxed message
def print_boxed_message(message):
    lines = message.split("\n")
    width = max(len(line) for line in lines) + 4
    print("+" + "-" * width + "+")
    for line in lines:
        print(f"| {line.ljust(width - 2)} |")
    print("+" + "-" * width + "+")

# Message to display
message = """This is an interactive experience developed by Cappy
and highly inspired by the movie Wargames from 1983.
I definitely recommend you watch it before playing.
It is a unique and creative movie. It is also a good
idea to watch the movie because there are a lot of
references and easter eggs for the movie. So you might
not understand or find them all.

Either way, I hope you enjoy the experience!"""

print_boxed_message(message)

# Pause before continuing
print("\n" + Fore.YELLOW + "Press any key to continue...")
wait_for_key()  # Wait for user input


