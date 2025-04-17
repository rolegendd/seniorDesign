#!/usr/bin/env python3

import socket
import threading
import sys
import os
import time
from datetime import datetime
import mysql.connector

# -------------------- MySQL Connection -------------------- #
def connect():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="SchoolDB"
    )

# -------------------- Attendance Logging -------------------- #
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def log_attendance(name, status, gps):
    """Logs an attendance event to a daily text file."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")
    log_filename = os.path.join(LOG_DIR, f"{today_str}_attendance.txt")

    with open(log_filename, "a") as file:
        log_line = f"{time_str} | Name: {name}, Status: {status}, GPS: {gps}\n"
        file.write(log_line)

    print(f"📝 Logged attendance: {log_line.strip()}")

# -------------------- Database Functions -------------------- #
def add_student():
    """Prompts user for student info and adds them to the 'students' table."""
    name = input("Enter student's name: ")
    rfid = input("Enter student's RFID: ")
    bus = input("Enter student's Bus ID: ")

    conn = connect()
    cursor = conn.cursor()
    try:
        insert_sql = "INSERT INTO students (name, rfid, bus) VALUES (%s, %s, %s)"
        cursor.execute(insert_sql, (name, rfid, bus))
        conn.commit()
        print("✅ Student added successfully.")
    except Exception as e:
        print(f"❌ Error adding student: {e}")
    finally:
        cursor.close()
        conn.close()

def delete_student():
    """Deletes a student record by name from the 'students' table."""
    name = input("Enter the name of the student to delete: ")

    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM students WHERE name = %s", (name,))
        results = cursor.fetchall()

        if not results:
            print("❌ No student found with that name.")
            return

        print("\nFound the following student(s):")
        for i, student in enumerate(results, 1):
            print(f"{i}. Name: {student[1]}, RFID: {student[2]}, Bus: {student[3]}")

        confirm = input("\nDelete all students with this name? (y/n): ").strip().lower()
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

# -------------------- Menu System -------------------- #
def student_menu():
    """A submenu for student database management."""
    while True:
        print("\n=== STUDENT MANAGEMENT MENU ===")
        print("1. Add Student")
        print("2. Delete Student by Name")
        print("3. Return to Main Menu")
        choice = input("Choose an option: ")

        if choice == "1":
            add_student()
        elif choice == "2":
            delete_student()
        elif choice == "3":
            break
        else:
            print("❌ Invalid choice. Try again.")

def main_menu():
    """Main menu for the server system."""
    while True:
        print("\n=== SCHOOL BUS SERVER MENU ===")
        print("1. Manage Students (DB)")
        print("2. Exit")
        choice = input("Choose an option: ")

        if choice == "1":
            student_menu()
        elif choice == "2":
            print("👋 Exiting menu interface.")
            break
        else:
            print("❌ Invalid choice. Try again.")

# -------------------- RFID/Bus Server -------------------- #
def get_student_name(rfid):
    """Look up the student name by RFID in the database."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM students WHERE rfid = %s", (rfid,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

def handle_client(client_socket, addr):
    """Handles a single client connection."""
    print(f"🔌 Connected to {addr}")
    # Toggle states: rfid -> "ONBOARD"/"OFFBOARD"
    rfid_states = {}

    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                print(f"❗ Client {addr} disconnected.")
                break

            print(f"📥 Received from {addr}: {data.strip()}")

            # Example data: "RFID:E280695500004011FB55244E | GPS:30.5259,-92.0811"
            if "RFID:" in data and "GPS:" in data:
                try:
                    parts = data.split("|")
                    rfid_part = parts[0].strip()    # "RFID:E2806955..."
                    gps_part = parts[1].strip()     # "GPS:30.5259,-92.0811"

                    rfid = rfid_part.split("RFID:")[1].strip()
                    gps = gps_part.split("GPS:")[1].strip()

                    name = get_student_name(rfid)
                    if name:
                        prev_state = rfid_states.get(rfid, "OFFBOARD")
                        new_state = "ONBOARD" if prev_state == "OFFBOARD" else "OFFBOARD"
                        rfid_states[rfid] = new_state

                        # Log attendance
                        log_attendance(name, new_state, gps)
                    else:
                        print(f"❌ Unknown RFID: {rfid}")
                except Exception as e:
                    print(f"⚠️ Failed to parse data: {e}")

    except Exception as e:
        print(f"⚠️ Client error with {addr}: {e}")
    finally:
        client_socket.close()
        print(f"🔴 Disconnected from {addr}")

def start_server():
    """Starts the TCP server in a blocking loop."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    host = "100.81.26.99"
    port = 9999
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"🟢 Server listening on {host}:{port}")

    try:
        while True:
            client_socket, addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\n🛑 Server shutting down.")
    finally:
        server_socket.close()

# -------------------- Main Entry -------------------- #
def run_system():
    """Launches the server in background and runs the main menu in the foreground."""
    # Start server thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Run the main menu in the main thread
    main_menu()

if __name__ == "__main__":
    run_system()
