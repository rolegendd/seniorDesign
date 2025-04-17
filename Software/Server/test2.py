#!/usr/bin/env python3

import curses
import threading
import queue
import socket
import pymysql
import time
import os
from datetime import datetime

# ------------------ GLOBAL QUEUE FOR LOGS ------------------ #
server_logs = queue.Queue()

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
    """Add a student via curses input."""
    curses.echo()
    stdscr.addstr("\nEnter student's name: ")
    name = stdscr.getstr().decode('utf-8')

    stdscr.addstr("Enter student's RFID: ")
    rfid = stdscr.getstr().decode('utf-8')

    stdscr.addstr("Enter student's Bus ID: ")
    bus = stdscr.getstr().decode('utf-8')
    curses.noecho()

    conn = connect()
    cursor = conn.cursor()
    try:
        insert_sql = "INSERT INTO students (name, rfid_tag, Bus_ID) VALUES (%s, %s, %s)"
        cursor.execute(insert_sql, (name, rfid, bus))
        conn.commit()
        stdscr.addstr("\n✅ Student added successfully.\n")
        stdscr.refresh()
        stdscr.getch()
    except Exception as e:
        stdscr.addstr(f"\n❌ Error adding student: {e}\n")
        stdscr.refresh()
        stdscr.getch()
    finally:
        cursor.close()
        conn.close()

def delete_student(stdscr):
    """Delete a student by name via curses input."""
    curses.echo()
    stdscr.addstr("\nEnter the name of the student to delete: ")
    name = stdscr.getstr().decode('utf-8')
    curses.noecho()

    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM students WHERE name = %s", (name,))
        results = cursor.fetchall()

        if not results:
            stdscr.addstr("\n❌ No student found with that name.\n")
            stdscr.addstr("Press any key to continue...\n")
            stdscr.getch()
            return

        stdscr.addstr("\nFound the following student(s):\n")
        for i, student in enumerate(results, 1):
            stdscr.addstr(f"{i}. Name: {student[1]}, RFID Tag: {student[2]}, Bus ID: {student[3]}\n")

        stdscr.addstr("\nDelete all students with this name? (y/n): ")
        curses.echo()
        confirm = stdscr.getstr().decode('utf-8').strip().lower()
        curses.noecho()

        if confirm == 'y':
            cursor.execute("DELETE FROM students WHERE name = %s", (name,))
            conn.commit()
            stdscr.addstr("\n🗑️ Student(s) deleted successfully.\n")
        else:
            stdscr.addstr("\n❎ Deletion cancelled.\n")
    except Exception as e:
        stdscr.addstr(f"\n❌ Error deleting student: {e}\n")
    finally:
        cursor.close()
        conn.close()
    stdscr.addstr("Press any key to continue...\n")
    stdscr.getch()

# --------------- HELPER: Get student name from RFID --------------- #
def get_student_name(rfid):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM students WHERE rfid_tag = %s", (rfid,))  # Fixed column name
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

# --------------- LOG ATTENDANCE --------------- #
def log_attendance(name, status, gps):
    """Log attendance to a daily text file in logs/."""
    today_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")
    if not os.path.exists("logs"):
        os.makedirs("logs")
    filename = f"logs/{today_str}_attendance.txt"
    with open(filename, "a") as f:
        line = f"{time_str} | Name: {name}, Status: {status}, GPS: {gps}\n"
        f.write(line)

# --------------- SERVER & HANDLER --------------- #
DEBOUNCE_SECONDS = 5
rfid_timestamps = {}  # RFID -> last time processed

def handle_client(client_socket, addr):
    server_logs.put(f"🔌 Connected to {addr}")

    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8', errors='ignore').strip()
            if not data:
                server_logs.put(f"❗ Client {addr} disconnected.")
                break

            server_logs.put(f"📥 Received from {addr}: {data}")

            parts = data.split(" | ")
            if len(parts) != 4:
                server_logs.put(f"⚠️ Expected 4 parts but got {len(parts)}. Data: {data}")
                continue

            try:
                rfid_str = parts[0].replace("RFID:", "").strip()
                status_str = parts[1].replace("STATUS:", "").strip()
                gps_time_str = parts[2].replace("GPS:", "").strip()
                coords_str = parts[3].strip()

                # Debounce
                now = time.time()
                last_seen = rfid_timestamps.get(rfid_str, 0)
                if (now - last_seen) < DEBOUNCE_SECONDS:
                    server_logs.put(f"⏳ Debounce: ignoring repeated RFID {rfid_str}")
                    continue
                rfid_timestamps[rfid_str] = now

                # Look up student
                name = get_student_name(rfid_str)
                if not name:
                    server_logs.put(f"❌ Unknown RFID: {rfid_str}")
                    continue

                combined_gps = f"{gps_time_str} | {coords_str}"
                log_attendance(name, status_str.upper(), combined_gps)
                server_logs.put(f"📝 Logged: {name} - {status_str.upper()} - {combined_gps}")

            except Exception as e:
                server_logs.put(f"⚠️ Parse error: {e}")

    except Exception as e:
        server_logs.put(f"⚠️ Client error with {addr}: {e}")
    finally:
        client_socket.close()
        server_logs.put(f"🔴 Disconnected from {addr}")

def start_server_thread():
    """Run the server in a background thread."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    host = "100.81.26.99"
    port = 9999
    server_socket.bind((host, port))
    server_socket.listen(5)
    server_logs.put(f"🟢 Server listening on {host}:{port}")  # This message is critical

    while True:
        client_socket, addr = server_socket.accept()
        t = threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True)
        t.start()

# --------------- CURSES UI --------------- #
def student_db_menu(menu_win):
    """Menu for student DB (curses)."""
    while True:
        menu_win.clear()
        menu_win.addstr("=== STUDENT MANAGEMENT MENU ===\n", curses.A_BOLD)
        menu_win.addstr("1. Add Student\n")
        menu_win.addstr("2. Delete Student by Name\n")
        menu_win.addstr("3. Return to Main Menu\n")
        menu_win.addstr("\nSelect an option: ")
        menu_win.refresh()

        curses.echo()
        choice = menu_win.getstr().decode('utf-8').strip()
        curses.noecho()

        if choice == "1":
            add_student(menu_win)
        elif choice == "2":
            delete_student(menu_win)
        elif choice == "3":
            break
        else:
            menu_win.addstr("\n❌ Invalid choice. Press any key.\n")
            menu_win.getch()

def curses_main(stdscr):
    curses.curs_set(0)  # Hide cursor
    height, width = stdscr.getmaxyx()
    log_height = height // 2
    menu_height = height - log_height

    # Windows for logs + menu
    log_win = curses.newwin(log_height, width, 0, 0)
    menu_win = curses.newwin(menu_height, width, log_height, 0)
    
    # Enable keypad input
    menu_win.keypad(True)
    curses.noecho()
    curses.cbreak()

    while True:
        # 1) Draw log window
        log_win.erase()
        log_win.addstr("=== SERVER LOGS ===\n", curses.A_BOLD)
        
        lines = []
        while not server_logs.empty():
            lines.append(server_logs.get())
        
        lines = lines[-(log_height-2):]
        for line in lines:
            log_win.addstr(f"{line}\n")
        log_win.noutrefresh()

        # 2) Draw menu window
        menu_win.erase()
        menu_win.addstr("=== SCHOOL BUS SERVER MENU ===\n", curses.A_BOLD)
        menu_win.addstr("1. Manage Students (DB)\n")
        menu_win.addstr("2. Exit\n")
        menu_win.addstr("Select an option: ")
        menu_win.noutrefresh()
        
        # Update screen once per loop
        curses.doupdate()

        # 3) Handle input with timeout
        try:
            c = menu_win.getch()
            if c == -1:
                continue  # No input available
                
            if c == ord('1'):
                student_db_menu(menu_win)
            elif c == ord('2'):
                menu_win.addstr("\n👋 Exiting...\n")
                menu_win.refresh()
                time.sleep(1)
                break
            else:
                menu_win.addstr("\n❌ Invalid choice. Press any key...\n")
                menu_win.refresh()
                menu_win.getch()
        except KeyboardInterrupt:
            break

    curses.endwin()


def main():
    # Start server in background
    server_thread = threading.Thread(target=start_server_thread, daemon=True)
    server_thread.start()

    # Start curses UI in main thread
    curses.wrapper(curses_main)

if __name__ == "__main__":
    main()
