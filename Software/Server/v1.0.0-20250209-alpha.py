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
import mysql.connector 


# Connect to mySQL def 
def connect():

    return mysql.connector.connect(

        host = "localhost",
        user = "root",
        password = "",
        database = "SchoolDB" 
    )

# Add a student def 
def add_student():

    name = input("Enter student's name: ")
    rfid = input("Enter student's ID: ")
    bus = input("Enter student's Bus: ")

    conn = connect()
    cursor = conn.cursor()
    
    try:

        insert_entry = "INSERT INTO students (name, rfid, bus) VALUES (%s, %s, %s)"
        cursor.execute(insert_entry, (name, rfid, bus))
        conn.commit()
    
        print("✅ Student added successfully.")

    cursor.close()
    conn.close()



def delete_student():
    name = input("Enter the name of the student to delete: ")

    conn = connect()
    cursor = conn.cursor()

    try:
        # Search for students 
        cursor.execute("SELECT * FROM students WHERE name = %s", (name,))
        results = cursor.fetchall()

        if not results:
            print("❌ No student found with that name.")
            return

        print("\nFound the following student(s):")
        for i, student in enumerate(results, 1):
            print(f"{i}. Name: {student[1]}, RFID: {student[2]}, Bus: {student[3]}")

        confirm = input("\nDo you want to delete all students with this name? (y/n): ").strip().lower()
        if confirm == 'y':
            cursor.execute("DELETE FROM students WHERE name = %s", (name,))
            conn.commit()
            print("🗑️ Student(s) deleted successfully.")
        else:
            print("❎ Deletion cancelled.")

    except Exception as e:
        print(f"❌ Error deleting student: {e}")
    finally:
        cursor.close()
        conn.close()




# Server Def 
def startServer():
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    host = "100.81.26.99"
    port = 9999

    server_socket.bind((host, port))
    server_socket.listen(5)  # Allow up to 5 waiting clients

    print("Server started and listening for clients...")

    try:
        while True:
            client_socket, addr = server_socket.accept()  # Accept a new client connection
            print(f"Connected to {addr}")

            try:
                while True:  # Keep receiving multiple messages from the same client
                    data = client_socket.recv(1024).decode('utf-8')

                    if not data:
                        print(f"Client {addr} disconnected.")
                        break  # Exit the inner loop when client disconnects

                    print(f"Received data: {data}")

            except KeyboardInterrupt:
                print("\nShutting down server.")
                server_socket.close()
                sys.exit(0)

            finally:
                client_socket.close()  # Close connection only when the client disconnects

    finally:
        server_socket.close()

    

    startServer()
