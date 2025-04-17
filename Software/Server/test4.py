#!/usr/bin/env python3

import curses
import threading
import queue
import socket
import pymysql
import time
import os
from datetime import datetime

# ------------------ GLOBAL VARIABLES ------------------ #
server_logs = queue.Queue()
LOG_HISTORY = []
MAX_LOG_LINES = 100
DEBOUNCE_SECONDS = 5
rfid_timestamps = {}

# --------------- MYSQL CONNECTION --------------- #
def connect():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="tigapups2/",
        database="SchoolDB"
    )

# --------------- DATABASE FUNCTIONS --------------- #
def add_student(stdscr):
    """Add a student via curses input"""
    stdscr.clear()
    curses.echo()
    fields = ["name", "RFID", "Bus ID"]
    values = []
    
    for field in fields:
        stdscr.addstr(f"Enter student's {field}: ")
        stdscr.refresh()
        values.append(stdscr.getstr().decode('utf-8'))
    
    curses.noecho()
    
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO students (name, rfid_tag, Bus_ID) VALUES (%s, %s, %s)",
            (values[0], values[1], values[2])
        )
        conn.commit()
        server_logs.put(f"✅ Added student: {values[0]}")
    except Exception as e:
        server_logs.put(f"❌ Error adding student: {e}")
    finally:
        cursor.close()
        conn.close()
    
    stdscr.getch()  # Wait for key press

def delete_student(stdscr):
    """Delete a student by name"""
    stdscr.clear()
    curses.echo()
    stdscr.addstr("Enter student name to delete: ")
    name = stdscr.getstr().decode('utf-8')
    curses.noecho()
    
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM students WHERE name = %s", (name,))
        results = cursor.fetchall()
        
        if not results:
            server_logs.put(f"❌ No student found: {name}")
            return
            
        stdscr.clear()
        for student in results:
            stdscr.addstr(f"Found: {student[1]} (RFID: {student[2]}, Bus: {student[3]})\n")
        
        stdscr.addstr("\nDelete this student? (y/n): ")
        stdscr.refresh()
        confirm = stdscr.getch()
        
        if confirm == ord('y'):
            cursor.execute("DELETE FROM students WHERE name = %s", (name,))
            conn.commit()
            server_logs.put(f"🗑️ Deleted student: {name}")
    except Exception as e:
        server_logs.put(f"❌ Error deleting student: {e}")
    finally:
        cursor.close()
        conn.close()
    
    stdscr.getch()  # Wait for key press

def get_student_name(rfid):
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM students WHERE rfid_tag = %s", (rfid,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        cursor.close()
        conn.close()

def log_attendance(name, status, gps):
    today = datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists("logs"):
        os.makedirs("logs")
    with open(f"logs/{today}_attendance.txt", "a") as f:
        f.write(f"{datetime.now().strftime('%H:%M:%S')} | {name} | {status} | {gps}\n")

# --------------- SERVER FUNCTIONS --------------- #
def handle_client(client_socket, addr):
    server_logs.put(f"🔌 Connected to {addr}")
    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8', errors='ignore').strip()
            if not data:
                server_logs.put(f"❗ Client {addr} disconnected.")
                break

            server_logs.put(f"📥 Received: {data}")

            parts = data.split(" | ")
            if len(parts) == 4:
                try:
                    rfid = parts[0].replace("RFID:", "").strip()
                    status = parts[1].replace("STATUS:", "").strip()
                    gps_time = parts[2].replace("GPS:", "").strip()
                    coords = parts[3].strip()

                    # Debounce check
                    now = time.time()
                    if (now - rfid_timestamps.get(rfid, 0)) < DEBOUNCE_SECONDS:
                        continue
                    rfid_timestamps[rfid] = now

                    # Process data
                    name = get_student_name(rfid)
                    if name:
                        log_attendance(name, status, f"{gps_time} | {coords}")
                        server_logs.put(f"📝 Logged: {name} - {status}")
                except Exception as e:
                    server_logs.put(f"⚠️ Error processing: {e}")

    except Exception as e:
        server_logs.put(f"⚠️ Client error: {e}")
    finally:
        client_socket.close()
        server_logs.put(f"🔴 Disconnected: {addr}")

def start_server_thread():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("100.81.26.99", 9999))
    server_socket.listen(5)
    server_logs.put("🟢 Server listening on 100.81.26.99:9999")

    while True:
        client_socket, addr = server_socket.accept()
        t = threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True)
        t.start()

# --------------- CURSES UI --------------- #
def curses_main(stdscr):
    curses.curs_set(0)
    curses.noecho()
    curses.cbreak()
    
    height, width = stdscr.getmaxyx()
    global MAX_LOG_LINES
    MAX_LOG_LINES = height - 6

    log_win = curses.newwin(height-4, width, 0, 0)
    menu_win = curses.newwin(4, width, height-4, 0)
    menu_win.keypad(True)
    menu_win.timeout(100)

    while True:
        # Update log display
        log_win.erase()
        log_win.addstr(0, 0, "=== SERVER LOGS ===", curses.A_BOLD)
        
        # Process new logs
        while not server_logs.empty():
            new_log = server_logs.get()
            LOG_HISTORY.append(new_log)
            if len(LOG_HISTORY) > MAX_LOG_LINES:
                LOG_HISTORY.pop(0)
        
        # Display logs
        for i, line in enumerate(LOG_HISTORY[-MAX_LOG_LINES:], 1):
            try:
                log_win.addstr(i, 0, line)
            except curses.error:
                pass
        
        log_win.noutrefresh()

        # Menu handling
        menu_win.erase()
        menu_win.addstr(0, 0, "=== MENU ===", curses.A_BOLD)
        menu_win.addstr(1, 0, "1. Add Student | 2. Delete Student | 3. Exit")
        menu_win.addstr(2, 0, "Select option: ")
        menu_win.noutrefresh()

        c = menu_win.getch()
        if c == ord('1'):
            add_student(menu_win)
        elif c == ord('2'):
            delete_student(menu_win)
        elif c == ord('3'):
            break

        curses.doupdate()

    curses.endwin()

def main():
    server_thread = threading.Thread(target=start_server_thread, daemon=True)
    server_thread.start()
    curses.wrapper(curses_main)

if __name__ == "__main__":
    main()
