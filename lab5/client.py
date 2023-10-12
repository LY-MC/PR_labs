import os
import socket
import threading
import json


def establish_client_connection(host, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    print(f"Connected to {host}:{port}")
    return client_socket


def receive_and_print_messages(client_socket):
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            message = json.loads(data)
            process_received_message(message)

        except Exception as e:
            print(f"Error receiving messages: {e}")
            break


def process_received_message(message):
    message_type = message.get("type")
    payload = message.get("payload")

    if message_type == "connect_ack":
        connect_message = payload.get("message")
        print(f"Server: {connect_message}")
    elif message_type == "message":
        sender = payload.get("sender")
        room = payload.get("room")
        text = payload.get("text")
        print(f"{sender} in '{room}': {text}")
    elif message_type == "notification":
        notification_message = payload.get("message")
        print(f"Notification: {notification_message}")
    else:
        print("Unknown message type")


def send_upload_command(client_socket, room):
    file_path = input("Enter the path to the file you want to upload: ")
    upload_command = {
        "type": "upload",
        "payload": {
            "name": "User",
            "room": room,
            "file_name": os.path.basename(file_path),
            "file_size": os.path.getsize(file_path)
        }
    }
    client_socket.send(json.dumps(upload_command).encode('utf-8'))


def send_download_command(client_socket, room):
    file_name = input("Enter the name of the file you want to download: ")
    download_command = {
        "type": "download",
        "payload": {
            "name": "User",
            "room": room,
            "file_name": file_name
        }
    }
    client_socket.send(json.dumps(download_command).encode('utf-8'))


def send_user_message(client_socket, room):
    while True:
        message = input("Enter a message (or 'exit' to quit, 'upload' to upload a file, 'download' to download a file): ")

        if message.lower() == 'exit':
            break
        elif message.lower() == 'upload':
            send_upload_command(client_socket, room)
        elif message.lower() == 'download':
            send_download_command(client_socket, room)
        else:
            message_data = {
                "type": "message",
                "payload": {
                    "sender": "User",
                    "room": room,
                    "text": message
                }
            }
            client_socket.send(json.dumps(message_data).encode('utf-8'))


if __name__ == "__main__":
    HOST = '127.0.0.1'
    PORT = 12345

    client_socket = establish_client_connection(HOST, PORT)
    room = input("Enter a room:")

    receive_thread = threading.Thread(target=receive_and_print_messages, args=(client_socket,))
    receive_thread.daemon = True
    receive_thread.start()

    send_user_message(client_socket, room)