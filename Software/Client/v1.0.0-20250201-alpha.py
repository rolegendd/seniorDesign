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


# Lines 46-48 imports the librarys used within the code so far.

import serial
import binascii
import time


    
# For the next portion of code I had to refer the the documentation for pySerial and the YANZEO SR681
# The documentation stated that the baudrate, parity, stopbits, and bytesize were all user choice configurations
# recommend suggestion were:
# Parity = NONE 
# Baudrate = 9600
# Stopbits = 1 
# Bytesize = 8

# The follow lines of code is utilizing the pySerial library to implement the configurations,
# by defult the pySerial library sets the parity,stopbits,bytesize to he suggested for the scanners
# but I decided to still declare them within the code.
# I am also testing this on Ubuntu 24.04.

ser = serial.Serial(
    port='/dev/ttyACM0',                                                                    ## Opens serial port
    baudrate=115200,                                                                        ## Sets baudrate 
    parity=serial.PARITY_NONE,                                                              ## Sets parity
    stopbits=serial.STOPBITS_ONE,                                                           ## Sets stopbit
    bytesize=serial.EIGHTBITS,                                                              ## Sets bytesize
    timeout=1                                                                               ## Declares timeout 
)

print("Listening for RFID scans...")

# Line 77 Declares an the variable 'buffer' as a empyt byte string.

buffer = b""                                                                                ## Buffer to store Data
expectedLength = 22                                                                         ## Expected full RFID tag length in bytes


# The follow line of code is to declare a starting position for the buffer to restart every scan 
# from previous test if not giving a start marker the new scan detect if deceted was the same RFID card 
# would logical shift the next detection by 2 bytes:

# First scan:  E2606XXXXXXX
# Second scan: XXE2606XXXXXXXX
# Third scan:  XXXXE2606XXXXXXXX

startMarker = b'\xe2'                                                                       ## This assumes that 'E2' marks the start of the RFID ID number I want.

try:
    while True:
        data = ser.read(1)  # Read one byte at a time

            # The follow lines of code will take in the data read from the serail port and append it to the buffer bit by bit and keep the lasts
            # 22 bits.
            # Example :
            #   Buffer: [] 
            # After reading 3 bytes of data 
            #   Buffer: [b1, b2, b3]
            # After 22 bytes of Data
            #   Buffer: [b1, b2, b3, . . . , b22]
            # After exceeding expectedLength 
            #   Buffer: [b2, b3, b4, . . . , b23]

        if data:
            buffer += data                                                                  ## Append byte to buffer
            
            # Follow code keeps the last 22 bytes of data read.
            if len(buffer) > expectedLength:
                buffer = buffer[-expectedLength:]  
            
            
            hexData = binascii.hexlify(buffer).decode('utf-8').upper()                      ## Uses the binascii library to convert the dat to HEX and also uppercase the letters

            # The following checks of the expected RFID data is detected in the buffer 
            # can be a flaw in the code because if TAG ID change and does start with 'E260'
            # code is DOA.

            

            
            if "E280" in hexData:                                                           ## 'E280' marks the start of the RFID Hex ID for the cards being tested.
                startIndex = hexData.find("E280")                                           ## Find the start position
                if startIndex + 24 <= len(hexData):  
                    extracted_data = hexData[startIndex:startIndex + 24]                    ## Extract full 24-char ID
                    
                    print(f"Card Detected: {extracted_data}")

                    buffer = b""                                                            ## Reset and Clear buffer for the next scan

        time.sleep(0.01)                                                                    ## Small delay to prevent excessive CPU usage

except KeyboardInterrupt:
    print("\nExiting...")
    ser.close()

