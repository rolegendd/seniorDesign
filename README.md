Welcome to the My senior design project a Senior Design from the University of Louisiana at Lafayette. This system automates student bus attendance using RFID scanning, GPS tracking, and secure client-server communication to improve student safety and operational efficiency for school transportation.



📌 Project Overview
SmartBus is designed to:

Automatically detect when students board or leave the bus using RFID cards

Capture real-time GPS data

Log and transmit this data securely to a centralized server

Allow schools to track student activity, by time and location

Provide a foundation for future parent and admin access portals

⚙️ Features
✅ RFID Scanning via serial-based reader (Yanzeo SR681)

🌍 GPS Tracking over UART

🔗 Persistent TCP Client-Server Communication

🗃️ MySQL Database Integration

📁 Automatic Daily Logging

🔒 Secure Networking with Tailscale VPN

⏱️ Debounce Logic to Prevent Duplicate Reads

HARDWARE SYSYEM

1) Client-side (on the bus)
   
Raspberry Pi (2)

Runs the Python client

Waveshare 4G HAT (SIM7600G)

Plugs onto the Pi’s 40-pin header

Requires a SIM card and a 4G LTE antenna

Provides cellular Internet for your socket connection

Yanzeo SR681 RFID Scanner

USB → /dev/ttyACM0

GPS Receiver Module (e.g. u-blox G70xx)

USB → /dev/ttyACM1

RFID Cards/Tags

Power Supply for Pi (5 V, 2–3 A)

2) Network Infrastructure
   
4G Cellular Network via the SIM7600G (no onboard Wi-Fi/Ethernet needed)

4) Server-side (school office)
   
DELL Optilex 3010(Linux Server/Workstation)

MySQL Database Server

Terminal or Monitor for the curses UI

Static IP or VPN so your Pi can always reach 100.81.26.99:9999

4) Miscellaneous
   
USB cables and power cables

Cellular and GPS antennas

Enclosure/mounting hardware

📦 Project Structure

BusClient/

├── Client/                # Raspberry Pi client-side code

│   └── v3.0.0-20250324-alpha.py

├── Server/                # Python server for data handling and logging

│   └── v2.0.0-20250417-alpha.py

├── Database/              # MySQL schema and utility scripts

├── Docs/                  # Design documents and setup instructions

└── README.md              # This file


👨‍💻 Authors

Roland Simmons

Madison Lee

Kenrick Williams
