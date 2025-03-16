#!/usr/bin/python3
# -*- coding:utf-8 -*-

import serial
import time

# Open the serial port to the GPS module
ser = serial.Serial('/dev/ttyACM1', 115200)
ser.flushInput()

def read_gps_data():
    """Reads GPS data and extracts time, latitude & longitude from GPGGA sentences."""
    data = ser.readline().decode('utf-8', errors='ignore').strip()

    if data.startswith('$GPGGA'):  # $GPGGA contains time & position information
        parse_gpgga(data)

def parse_gpgga(data):
    """Parses GPGGA sentence and prints time, latitude & longitude."""
    parts = data.split(',')
    if len(parts) >= 6 and parts[1] and parts[2] and parts[4]:  # Ensure fields are not empty
        try:
            # Extract and format time (HH:MM:SS UTC)
            raw_time = parts[1]  # Example: "074353.00" → HHMMSS.ss
            hours = raw_time[:2]
            minutes = raw_time[2:4]
            seconds = raw_time[4:6]
            formatted_time = f"{hours}:{minutes}:{seconds} UTC"

            # Extract and convert latitude & longitude to decimal format
            latitude = float(parts[2][:2]) + float(parts[2][2:]) / 60.0
            longitude = float(parts[4][:3]) + float(parts[4][3:]) / 60.0

            if parts[3] == 'S': latitude = -latitude
            if parts[5] == 'W': longitude = -longitude

            print(f"{formatted_time} | {latitude}, {longitude}")

        except ValueError:
            pass  # Ignore invalid data

# Continuously read and parse GPS data
while True:
    read_gps_data()

