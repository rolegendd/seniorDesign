#!/usr/bin/env python3

# -----------------------------------------------------------------------------
# Project: Automated School Bus 
# Author(s): Madison Lee, Kenrick Williams, Roland Simmons 
# Institution: UNIVERSITY OF LOUISIANA AT LAFAYETTE 
# Course: Senior Design (EECE 460)
# Instructor: Dr. Paul Darby 
# Date: February 1, 2025
#
# Description:
# This software interfaces with a Yanzeo SR681 RFID scanner to detect and 
# process RFID card data for an access control system. It reads serial data 
# from the scanner, extracts relevant RFID tag information, and logs detections.
#
# Dependencies:
# - Python 3.x
# - pyserial library (`pip install pyserial`)
# - binascii library 
# - time library
# 
# License:
# MIT License (see below)
#
# Copyright (c) 2025 Madison Lee, Kenrick Williams, Roland Simmons 
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE, AND NONINFRINGEMENT.
# -----------------------------------------------------------------------------


# Lines below imports the librarys used within the code so far.

import serial
import binascii
import time
import socket 
import select
import threading

# Def to read the GPS data from the receiver 
def read_gps_data(gpsReceiver):
    # Reads GPS data and extracts time, latitude & longitude from GPGGA sentences.
    # The follow line resets the input to get the accurate data like live 
    gpsReceiver.reset_input_buffer()
    while True: 

        data = gpsReceiver.readline().decode('utf-8', errors='ignore').strip()

        if data.startswith('$GPGGA'):  # $GPGGA contains time & position information
           return parse_gpgga(data)

# Def to parse through the raw GPS data 
def parse_gpgga(data):

    # Parses GPGGA sentence and prints time, latitude & longitude.
    
    parts = data.split(',')
    if len(parts) >= 6 and parts[1] and parts[2] and parts[4]:
        try:
            # Extract and format time (HH:MM:SS UTC) from the raw GPS data from the receiver 
            
            # Example: "074353.00" → HHMMSS.ss

            raw_time = parts[1]
            hours = raw_time[:2]
            minutes = raw_time[2:4]
            seconds = raw_time[4:6]
            formatted_time = f"{hours}:{minutes}:{seconds} UTC"

            # Extract and convert latitude & longitude to decimal format
            latitude = float(parts[2][:2]) + float(parts[2][2:]) / 60.0
            longitude = float(parts[4][:3]) + float(parts[4][3:]) / 60.0

            if parts[3] == 'S': latitude = -latitude
            if parts[5] == 'W': longitude = -longitude

            return f"{formatted_time} | {latitude}, {longitude}"

        except ValueError:
            return None

    return None 


def read_rfid( scanner, startMarker = b'\xe2', expectedLength = 12):
# Following line Declares an the variable 'buffer' as a empyt byte string.
    buffer = b""                                                                                ## Buffer to store Data

# The follow line of code is to declare a starting position for the buffer to restart every scan 
# from previous test if not giving a start marker the new scan detect if deceted was the same RFID card 
# would logical shift the next detection by 2 bytes:

# First scan:  E2606XXXXXXX
# Second scan: XXE2606XXXXXXXX
# Third scan:  XXXXE2606XXXXXXXX 
 


    try:
        while True:
            data = scanner.read(1)  # Read one byte at a time

            # The follow lines of code will take in the data read from the serail port and append it to the buffer bit by bit and keep the lasts
            # 22 bits.
            # Example :
            #  Buffer: [] 
            # After reading 3 bytes of data 
            #   Buffer: [b1, b2, b3]
            # After 22 bytes of Data
            #   Buffer: [b1, b2, b3, . . . , b22]
            # After exceeding expectedLength 
            #   Buffer: [b2, b3, b4, . . . , b23]
            

            if data:
                buffer += data                                                                  ## Append byte to buffer
            
            # Follow code keeps the last 22 bytes of data read.
                if len(buffer) > 100:
                    buffer = buffer[-expectedLength:]  
            
            # Locating the start marker 
            startIndex = buffer.find(startMarker)

            if startIndex != -1 and len(buffer[startIndex:]) >= expectedLength:

                tagBytes = buffer[startIndex:startIndex + expectedLength]
                extractedData = binascii.hexlify(tagBytes).decode('utf-8').upper()                      ## Uses the binascii library to convert the dat to HEX and also uppercase the letters

            # The following checks of the expected RFID data is detected in the buffer 
            # can be a flaw in the code because if TAG ID change and does start with 'E260'
            # code is DOA.
            

                if extractedData.startswith("E280"):
                    return extractedData


            
          #      if "E280" in hexData:                                                           ## 'E280' marks the start of the RFID Hex ID for the cards being tested.
          #          startIndex = hexData.find("E280")                                           ## Find the start position
          #          if startIndex + 24 <= len(hexData):  
          #              extracted_data = hexData[startIndex:startIndex + 24]                    ## Extract full 24-char ID
                    
                        #print(f"Card Detected: {extracted_data}")
                        #print(f"Sending {extracted_data} to the Server")
    except Exception as e:

        print(f"[RFID Read Error] {e}")

        return None 



# Def for client 

def start_client(scanner, gpsReceiver):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = "100.81.26.99"
    port = 9999

    try:
        client_socket.connect((host, port))

        # Send HELLO BUS ID
        bus_id = "Fish"
        client_socket.sendall(f"HELLO BUS:{bus_id}\n".encode('utf-8'))

        recent_tags = {}
        tagState = {}
        cooldown = 5
        stop_event = threading.Event()

        print("Connected to server...")


        # --- Background thread for scanning ---
        def scan_loop():
            while not stop_event.is_set():
                try:
                    rfid_data = read_rfid(scanner)
                    gps_data = read_gps_data(gpsReceiver)
                    now = time.time()

                    if rfid_data and gps_data:
                        last_seen = recent_tags.get(rfid_data, 0)
                        if (now - last_seen) > cooldown:
                            current_state = tag_state.get(rfid_data, "offboard")
                            new_state = "onboard" if current_state == "offboard" else "offboard"

                            tag_state[rfid_data] = new_state
                            recent_tags[rfid_data] = now

                            transmission = f"RFID:{rfid_data} | STATUS:{new_state.upper()} | GPS: {gps_data}"
                            client_socket.sendall((transmission + "\n").encode('utf-8'))
                            print(f"📡 Sent: {transmission}")
                except Exception as e:
                    print(f"[Scanner Error] {e}")

                time.sleep(0.01)


        # Start scanning in a background thread
        threading.Thread(target=scan_loop, daemon=True).start()



        # --- Main loop: handle server commands ---
        while True:
            readable, _, _ = select.select([client_socket], [], [], 0.1)
            if readable:
                server_command = client_socket.recv(1024).decode('utf-8').strip()
                print(f"[CLIENT DEBUG] Received command: {server_command}")

                if server_command == "PING":
                    try:
                        gps_data = read_gps_data(gpsReceiver)
                        timestamp = time.strftime("%H:%M:%S")
                        response = f"PONG | {timestamp} | {gps_data}"
                        client_socket.sendall((response + "\n").encode('utf-8'))
                        print(f"✅ Responded to PING: {response}")
                    except Exception as e:
                        print(f"[PING ERROR] {e}")

                elif server_command == "GET_LOCATION":
                    try:
                        gps_data = read_gps_data(gpsReceiver)
                        response = f"LOCATION: {gps_data}"
                        client_socket.sendall((response + "\n").encode('utf-8'))
                        print(f"📍 Sent location: {response}")
                    except Exception as e:
                        print(f"[GET_LOCATION ERROR] {e}")


    except KeyboardInterrupt:
        print("\nExiting...")
        scanner.close()
        gpsReceiver.close()
        client_socket.close()



### Main ###


if __name__ == "__main__":

# For the next portion of code I had to refer the the documentation for pySerial and the YANZEO SR681
# The documentation stated that the baudrate, parity, stopbits, and bytesize were all user choice configurations
# recommend suggestion were:
#    Parity = NONE 
#    Baudrate = 9600
#   Stopbits = 1 
#   Bytesize = 8

# The follow lines of code is utilizing the pySerial library to implement the configurations,
# Serial connection for the RFID attenna 

    scanner = serial.Serial(
        port='/dev/ttyACM0',                                                                    ## Opens serial port
        baudrate=115200,                                                                        ## Sets baudrate 
        parity=serial.PARITY_NONE,                                                              ## Sets parity
        stopbits=serial.STOPBITS_ONE,                                                           ## Sets stopbit
        bytesize=serial.EIGHTBITS,                                                              ## Sets bytesize
        timeout=1                                                                               ## Declares timeout 
        )
    # Serial connection for the GPS receiver 
    gpsReceiver = serial.Serial('/dev/ttyACM1', 115200)
    gpsReceiver.flushInput()

    print("Listening for RFID scans...")


 
# by defult the pySerial library sets the parity,stopbits,bytesize to he suggested for the scanners
# but I decided to still declare them within the code.
# I am also testing this on Ubuntu 24.04.

    while True: 
        start_client(scanner, gpsReceiver)
        time.sleep(3)


