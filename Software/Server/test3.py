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
    """Non-blocking student addition"""
    stdscr.timeout(100)  # Non-blocking mode
    inputs = ["", "", ""]  # name, rfid, bus
    current_field = 0
    field_prompts = [
        "\nEnter student's name: ",
        "Enter student's RFID: ",
        "Enter student's Bus ID: "
    ]

    while True:
        stdscr.clear()
        for i, prompt in enumerate(field_prompts):
            stdscr.addstr(prompt)
            stdscr.addstr(inputs[i] + ("_" if i == current_field else ""))
            stdscr.addstr("\n")

        c = stdscr.getch()
        if c == curses.KEY_ENTER or c == 10 or c == 13:
            if current_field == 2:  # Last field
                break
            current_field += 1
        elif c == curses.KEY_BACKSPACE or c == 127:
            inputs[current_field] = inputs[current_field][:-1]
        elif c >= 32 and c <= 126:  # Printable characters
            inputs[current_field] += chr(c)
        elif c == 27:  # ESC
            return False

    # Save to database
    conn = connect()
    cursor = conn.cursor()
    try:
        insert_sql = "INSERT INTO students (name, rfid_tag, Bus_ID) VALUES (%s, %s, %s)"
        cursor.execute(insert_sql, (inputs[0], inputs[1], inputs[2]))
        conn.commit()
        server_logs.put("✅ Student added successfully")
        return True
    except Exception as e:
        server_logs.put(f"❌ Error adding student: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def delete_student(stdscr):
    """Non-blocking student deletion"""
    stdscr.timeout(100)
    name_input = ""
    confirm = None

    while True:
        stdscr.clear()
        stdscr.addstr("\nEnter student name to delete: ")
        stdscr.addstr(name_input + "_")
        
        c = stdscr.getch()
        if c == curses.KEY_ENTER or c == 10 or c == 13:
            break
        elif c == curses.KEY_BACKSPACE or c == 127:
            name_input = name_input[:-1]
        elif c == 27:  # ESC
            return False
        elif c >= 32 and c <= 126:
            name_input += chr(c)

    # Search and confirm deletion
    conn = connect()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM students WHERE name = %s", (name_input,))
        results = cursor.fetchall()

        if not results:
            server_logs.put("❌ No student found with that name")
            return False

        while True:
            stdscr.clear()
            stdscr.addstr("\nFound student(s):\n")
            for student in results:
                stdscr.addstr(f"- {student[1]} (RFID: {student[2]}, Bus: {student[3]})\n")
            stdscr.addstr("\nDelete all? (y/n): ")
            
            c = stdscr.getch()
            if c == ord('y'):
                cursor.execute("DELETE FROM students WHERE name = %s", (name_input,))
                conn.commit()
                server_logs.put("🗑️ Student(s) deleted successfully")
                return True
            elif c == ord('n'):
                server_logs.put("❎ Deletion cancelled")
                return False

    except Exception as e:
        server_logs.put(f"❌ Error deleting student: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# ... [Keep get_student_name, log_attendance, handle_client functions unchanged] ...

def handle_client(client_socket, addr):
    server_logs.put(f"🔌 Connected to {addr}")
    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8', errors='ignore').strip()
            if not data:
                server_logs.put(f"❗ Client {addr} disconnected.")
                break

            server_logs.put(f"📥 Received from {addr}: {data}")
            
            # Process RFID/GPS data here
            # ...

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
    server_logs.put(f"🟢 Server listening on {host}:{port}")

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
    log_win = curses.newwin(height//2, width, 0, 0)
    menu_win = curses.newwin(height//2, width, height//2, 0)
    
    menu_win.keypad(True)
    menu_win.timeout(100)

    current_menu = "main"
    while True:
        # Update logs continuously
        log_win.erase()
        log_win.addstr("=== SERVER LOGS ===\n", curses.A_BOLD)
        
        lines = []
        while not server_logs.empty():
            lines.append(server_logs.get())
        
        lines = lines[-(height//2-2):]
        for line in lines:
            log_win.addstr(f"{line}\n")
        log_win.noutrefresh()

        # Handle menu navigation
        if current_menu == "main":
            menu_win.erase()
            menu_win.addstr("=== SCHOOL BUS SERVER MENU ===\n", curses.A_BOLD)
            menu_win.addstr("1. Manage Students (DB)\n")
            menu_win.addstr("2. Exit\n")
            menu_win.addstr("Select an option: ")
            menu_win.noutrefresh()

            c = menu_win.getch()
            if c == ord('1'):
                current_menu = "student"
            elif c == ord('2'):
                break

        elif current_menu == "student":
            menu_win.erase()
            menu_win.addstr("=== STUDENT MANAGEMENT MENU ===\n", curses.A_BOLD)
            menu_win.addstr("1. Add Student\n")
            menu_win.addstr("2. Delete Student\n")
            menu_win.addstr("3. Back to Main Menu\n")
            menu_win.addstr("Select an option: ")
            menu_win.noutrefresh()

            c = menu_win.getch()
            if c == ord('1'):
                if add_student(menu_win):
                    current_menu = "main"
            elif c == ord('2'):
                if delete_student(menu_win):
                    current_menu = "main"
            elif c == ord('3'):
                current_menu = "main"

        curses.doupdate()

    curses.endwin()

def main():
    server_thread = threading.Thread(target=start_server_thread, daemon=True)
    server_thread.start()
    curses.wrapper(curses_main)

if __name__ == "__main__":
    main()
