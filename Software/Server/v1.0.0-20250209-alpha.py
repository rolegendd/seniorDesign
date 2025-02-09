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
# This software is dedicate to the server within the Automated bus system. The code will open a port and listen for data from the clients 
# in this case is the system that are on the bus. I will receieve the RFID # and qurry the database to see if the tag is within the database
# if it is the server will then log the card detected and notify who need to be notified. 
#
# Dependencies:
# - Python 3.x 
# - socket(library) 
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


import socket 

def startServer():

    serverSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

    host = socket.gethostbyname(socket.gethostname())

    port = 9999

    serverSocket.bind((host, port))

    serverSocket.listen(5)

    print("Server started and listing for connections. . .")
    #print(host)

    while True:

        clientSocket, addr = serverSocket.accept()

        print(f"Got a connection from {addr}")


        data = clientSocket.recv(1024).decode('utf-8')

        print(f"Recieved data: {data}")

        clientSocket.close()

startServer()
