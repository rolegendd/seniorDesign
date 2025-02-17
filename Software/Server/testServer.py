#!/usr/bin/env python3

import socket 

def start_server():

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    host = "100.81.26.99"

    port = 9999

    server_socket.bind((host, port))

    server_socket.listen(5)

    print("Server started and listening for clients. . . ")

    while True:

        client_socket, addr = server_socket.accept()

        data = client_socket.recv(1024).decode('utf-8')

        print(f"Received data: {data}")

        client_socket.close()

start_server()
