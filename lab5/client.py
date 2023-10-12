import os
import socket
import threading
import json
import uuid


def create_client_folder():
    client_id = str(uuid.uuid4())
    folder_path = os.path.join('client_media', client_id)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


def establish_client_connection(host, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    print(f"Connected to {host}:{port}")
    client_media_folder = create_client_folder()
    return client_socket, client_media_folder


def receive_and_print_messages(client_socket, client_media_folder):
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            message = json.loads(data)
            process_received_message(message, client_media_folder)

        except Exception as e:
            print(f"Error receiving messages: {e}")
            break


def process_received_message(message, client_media_folder):
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
    elif message_type == "download-ack":
        handle_download_ack(payload, client_media_folder)
    else:
        print("Unknown message type")


def handle_download_ack(payload, client_media_folder):
    file_name = payload["file_name"]
    print(f"Downloading file: {file_name}")

    download_folder = client_media_folder

    save_path = os.path.join(download_folder, file_name)
    print(f"Saving file to: {save_path}")

    with open(save_path, "wb") as file:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            file.write(data)

    print(f"File '{file_name}' downloaded and saved to '{save_path}'")


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


def send_download_command(client_socket, room, client_media_folder):
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
    download_response = client_socket.recv(1024).decode('utf-8')
    print("suck")
    handle_download_response(download_response, client_socket, client_media_folder)


def handle_download_response(download_response, client_socket, client_media_folder):
    response = json.loads(download_response)

    if response['type'] == 'download-ack':
        file_name = response["payload"]["file_name"]

        download_folder = client_media_folder

        save_path = os.path.join(download_folder, file_name)

        with open(save_path, "wb") as file:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                file.write(data)

        print(f"File '{file_name}' downloaded and saved to '{save_path}'")
    elif response["type"] == "notification":
        message = response["payload"]["message"]
        print(f"Server notification: {message}")
    else:
        print("Unknown message type")


def send_user_message(client_socket, room, client_media_folder):
    while True:
        message = input("Enter a message (or 'exit' to quit, 'upload' to upload a file, 'download' to download a file): ")

        if message.lower() == 'exit':
            break
        elif message.lower() == 'upload':
            send_upload_command(client_socket, room)
        elif message.lower() == 'download':
            send_download_command(client_socket, room, client_media_folder)
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

    client_socket, client_media_folder = establish_client_connection(HOST, PORT)
    room = input("Enter a room:")

    receive_thread = threading.Thread(target=receive_and_print_messages, args=(client_socket,client_media_folder,))
    receive_thread.daemon = True
    receive_thread.start()

    send_user_message(client_socket, room, client_media_folder)
    os.rmdir(client_media_folder)
