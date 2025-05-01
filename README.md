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


📦 Project Structure

SmartBus/
├── Client/                # Raspberry Pi client-side code
│   └── rfid_gps_sender.py
├── Server/                # Python server for data handling and logging
│   └── main_server.py
├── Database/              # MySQL schema and utility scripts
├── Docs/                  # Design documents and setup instructions
└── README.md              # This file


👨‍💻 Authors

Roland Simmons

Madison Lee

Kenrick Williams
