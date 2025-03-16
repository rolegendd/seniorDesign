#!/usr/bin/env python3

import socket 
import sys

def start_server():

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)

    host = "100.81.26.99"

    port = 9999

    server_socket.bind((host, port))

    server_socket.listen(5)

    print("Server started and listening for clients. . . ")

    try:

        while True:

            try:

                client_socket, addr = server_socket.accept()

                data = client_socket.recv(1024).decode('utf-8')

                print(f"Received data: {data}")

            except KeyboardInterrupt:

                print("\nShutting down server.")

                server_socket.close()

                sys.exit(0)

    finally:

        server_socket.close()

start_server()
