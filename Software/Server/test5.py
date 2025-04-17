#!/usr/bin/env python3

import curses
import threading
import queue
import socket
import pymysql
import time
import os
from datetime import datetime
from wcwidth import wcswidth  # For accurate emoji and wide character rendering

# ------------------ GLOBAL VARIABLES ------------------ #
server_logs = queue.Queue()
LOG_HISTORY = []
MAX_LOG_LINES = 25
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

# --------------- DATABASE FUNCTIONS --------------- #
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

def add_student(stdscr):
    """Add a student with robust feedback"""
    while True:
        try:
            stdscr.clear()
            curses.echo()
            
            # Input with clear labels
            stdscr.addstr(1, 2, "ADD NEW STUDENT", curses.A_BOLD)
            stdscr.addstr(3, 2, "Name: ")
            name = stdscr.getstr().decode('utf-8')
            if not name:
                raise ValueError("Name cannot be empty")
            
            stdscr.addstr(4, 2, "RFID: ")
            rfid = stdscr.getstr().decode('utf-8')
            if not rfid:
                raise ValueError("RFID cannot be empty")
            
            stdscr.addstr(5, 2, "Bus ID: ")
            bus = stdscr.getstr().decode('utf-8')
            
            curses.noecho()
            
            # Database operation
            conn = None
            try:
                conn = connect()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO students (name, rfid_tag, Bus_ID) VALUES (%s, %s, %s)",
                    (name, rfid, bus)
                )
                conn.commit()
                
                # SUCCESS DISPLAY
                stdscr.clear()
                stdscr.addstr(1, 2, "✅ STUDENT ADDED", curses.A_BOLD)
                stdscr.addstr(3, 2, f"Name: {name}")
                stdscr.addstr(4, 2, f"RFID: {rfid}")
                stdscr.addstr(5, 2, f"Bus: {bus}")
                stdscr.addstr(7, 2, "Press any key to continue...")
                stdscr.refresh()
                
                # Log to server after successful display
                server_logs.put(f"✅ Added student: {name} (RFID: {rfid}, Bus: {bus})")
                stdscr.getch()
                return
                
            except pymysql.err.IntegrityError as e:
                stdscr.clear()
                if "rfid_tag" in str(e):
                    msg = f"RFID {rfid} already exists!"
                else:
                    msg = "Database error: " + str(e)
                stdscr.addstr(1, 2, "❌ ERROR", curses.A_BOLD)
                stdscr.addstr(3, 2, msg)
                stdscr.addstr(5, 2, "Press any key to try again...")
                server_logs.put(f"❌ Failed to add student: {msg}")
                stdscr.refresh()
                stdscr.getch()
                continue
                
            except Exception as e:
                stdscr.clear()
                stdscr.addstr(1, 2, "❌ DATABASE ERROR", curses.A_BOLD)
                stdscr.addstr(3, 2, f"Error: {str(e)}")
                stdscr.addstr(5, 2, "Press any key to continue...")
                server_logs.put(f"❌ Error adding student: {e}")
                stdscr.refresh()
                stdscr.getch()
                return
                
            finally:
                if conn:
                    conn.close()
                    
        except ValueError as e:
            stdscr.clear()
            stdscr.addstr(1, 2, "❌ INPUT ERROR", curses.A_BOLD)
            stdscr.addstr(3, 2, str(e))
            stdscr.addstr(5, 2, "Press any key to try again...")
            stdscr.refresh()
            stdscr.getch()
            continue
            
        except curses.error:
            stdscr.clear()
            stdscr.addstr(0, 0, "⚠️ Terminal too small! Resize and try again.")
            stdscr.refresh()
            stdscr.getch()
            return
def delete_student(stdscr):
    """Delete a student by name with validation"""
    while True:
        stdscr.clear()
        curses.echo()
        try:
            stdscr.addstr("\nEnter the name of the student to delete: ")
            name = stdscr.getstr().decode('utf-8')
            if not name:
                raise ValueError("Name cannot be empty")
            
            curses.noecho()
            
            conn = connect()
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT * FROM students WHERE name = %s", (name,))
                results = cursor.fetchall()
                
                if not results:
                    server_logs.put(f"❌ No student found: {name}")
                    stdscr.addstr("\nNo student found with that name.\nPress any key...")
                    stdscr.getch()
                    return
                    
                stdscr.clear()
                stdscr.addstr("\nFound the following student(s):\n")
                for student in results:
                    stdscr.addstr(f"- Name: {student[1]}, RFID: {student[2]}, Bus: {student[3]}\n")
                
                stdscr.addstr("\nDelete these students? (y/n): ")
                stdscr.refresh()
                confirm = stdscr.getch()
                
                if confirm == ord('y'):
                    cursor.execute("DELETE FROM students WHERE name = %s", (name,))
                    conn.commit()
                    server_logs.put(f"🗑️ Deleted student: {name}")
                    stdscr.addstr("\n\nStudent(s) deleted! Press any key...")
                    stdscr.getch()
                else:
                    stdscr.addstr("\n\nDeletion cancelled. Press any key...")
                    stdscr.getch()
                return
            except Exception as e:
                server_logs.put(f"❌ Error deleting student: {e}")
                stdscr.addstr(f"\n\nError: {e}\nPress any key...")
                stdscr.getch()
                return
            finally:
                cursor.close()
                conn.close()
                
        except ValueError as e:
            curses.noecho()
            stdscr.addstr(f"\n\nError: {e}\nPress any key...")
            stdscr.getch()
            continue
        except curses.error:
            stdscr.clear()
            stdscr.addstr(0, 0, "Screen too small! Resize terminal.")
            stdscr.refresh()
            stdscr.getch()
            return


def safe_truncate(s, max_width):
    truncated = ""
    total = 0
    for ch in s:
        ch_width = wcswidth(ch)
        if ch_width < 0:
            continue  # skip unprintable chars
        if total + ch_width > max_width:
            break
        truncated += ch
        total += ch_width
    return truncated











# --------------- CURSES UI --------------- #
def curses_main(stdscr):
    # Minimum required screen dimensions
    MIN_HEIGHT = 24
    MIN_WIDTH = 100  # Increased minimum width for wider menu
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    
    while True:  # Outer loop for screen size handling
        # Get current screen dimensions
        height, width = stdscr.getmaxyx()
        
        # Check if screen is too small
        if height < MIN_HEIGHT or width < MIN_WIDTH:
            stdscr.clear()
            stdscr.addstr(0, 0, "⚠️ Screen Too Small ⚠️", curses.A_BOLD | curses.A_BLINK)
            stdscr.addstr(2, 0, f"Current: {width}x{height}", curses.A_BOLD)
            stdscr.addstr(3, 0, f"Required: At least {MIN_WIDTH}x{MIN_HEIGHT}")
            stdscr.addstr(5, 0, "Please resize your terminal window")
            stdscr.addstr(7, 0, "Press R to refresh or Q to quit")
            stdscr.refresh()
            
            while True:
                c = stdscr.getch()
                if c == ord('r') or c == ord('R'):
                    break  # Retry with new size
                elif c == ord('q') or c == ord('Q'):
                    return  # Quit program
            continue
        
        # Screen is large enough - initialize UI
        curses.curs_set(0)
        curses.noecho()
        curses.cbreak()
        
        # Calculate window sizes for side-by-side layout
        menu_width = 40  # Wider menu panel (was 30)
        log_width = width - menu_width - 1  # Remainder for logs
        global MAX_LOG_LINES
        MAX_LOG_LINES = height - 4  # Adjust for borders
        
        # Create windows
        menu_win = curses.newwin(height-1, menu_width, 0, 0)  # Left panel
        log_win = curses.newwin(height-1, log_width, 0, menu_width+1)  # Right panel
        border_win = curses.newwin(height-1, 1, 0, menu_width)  # Separator
        
        # Draw vertical separator line
        border_win.vline(0, 0, curses.ACS_VLINE, height-1)
        border_win.refresh()
        
        menu_win.keypad(True)
        log_win.timeout(100)  # Non-blocking log updates

        # Main application loop
        while True:
            # Check for screen resize
            new_height, new_width = stdscr.getmaxyx()
            if new_height != height or new_width != width:
                break  # Will recreate windows with new size
            
            try:
                # Draw MENU in left panel (wider)
                menu_win.erase()
                menu_win.box()
                menu_win.addstr(1, 1, " SCHOOL BUS SERVER MENU ", curses.A_BOLD | curses.A_STANDOUT)
                menu_win.addstr(3, 2, "1. Add New Student")
                menu_win.addstr(4, 2, "2. Delete Existing Student")
                menu_win.addstr(5, 2, "3. Exit Program")
                menu_win.addstr(height-3, 2, "Select option (1-3): _")
                menu_win.refresh()

                # Update LOGS in right panel
                log_win.erase()
                log_win.box()
                log_win.addstr(1, 1, " SERVER ACTIVITY LOGS ", curses.A_BOLD)
                
                # Process new logs
                while not server_logs.empty():
                    new_log = server_logs.get()
                    LOG_HISTORY.append(new_log)
                    if len(LOG_HISTORY) > MAX_LOG_LINES:
                        LOG_HISTORY.pop(0)
                
                # Display logs with truncation
               
                for i, line in enumerate(LOG_HISTORY[-MAX_LOG_LINES:], 3):
                    try:
                        log_line = safe_truncate(line, log_width - 4)
                        if "✅" in line or "🟢" in line:
                            log_win.addstr(i, 2, log_line, curses.color_pair(1))
                        elif "❌" in line or "🔴" in line:
                            log_win.addstr(i, 2, log_line, curses.color_pair(2))
                        else:
                            log_win.addstr(i, 2, log_line)
                    except curses.error:
                        pass
                
                log_win.noutrefresh()
                curses.doupdate()

                # Non-blocking input with timeout
                menu_win.timeout(100)
                c = menu_win.getch()
                
                if c != -1:  # Only process if key was pressed
                    if c == ord('1'):
                        menu_win.timeout(-1)  # Switch to blocking for data entry
                        add_student(menu_win)
                    elif c == ord('2'):
                        menu_win.timeout(-1)
                        delete_student(menu_win)
                    elif c == ord('3'):
                        return
            
            except curses.error as e:
                if str(e) == "addwstr() returned ERR":
                    menu_win.refresh()
                    log_win.refresh()
                else:
                    break

    
def main():
    server_thread = threading.Thread(target=start_server_thread, daemon=True)
    server_thread.start()
    curses.wrapper(curses_main)

if __name__ == "__main__":
    main()
