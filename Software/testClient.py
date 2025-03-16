#!/usr/bin/env python3
import socket 
import time 
import random 


def start_client():

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    host = "100.81.26.99"

    port = 9999

    message = str(random.randrange(3333, 4444))
    message = "RF-" + message 

    client_socket.connect((host, port))


    print(f"Sending {message} to the Server")

    client_socket.send(message.encode('utf-8'))

    client_socket.close()

while True:
    #for step in range(10):
    start_client()
    time.sleep(5)


    
