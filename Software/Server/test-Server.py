#!/usr/bin/env python3

import socket
import sys

def start_server():
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

start_server()

