import socket
import threading
import json
import os

MEDIA_FOLDER = 'server_media'

if not os.path.exists(MEDIA_FOLDER):
    os.mkdir(MEDIA_FOLDER)


def create_server_socket(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen()
    print(f"Server is listening on {host}:{port}")
    return server_socket


def create_room_directory(message):
    payload = message.get("payload")
    room = payload.get("room")
    room_path = os.path.join(MEDIA_FOLDER, room)
    if not os.path.exists(room_path):
        os.mkdir(room_path)


def handle_client_connection(client_socket, client_address, clients, rooms):
    print(f"Accepted connection from {client_address}")

    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            message = json.loads(data)
            handle_message(message, client_socket, rooms)

        except Exception as e:
            print(f"Error handling client: {e}")
            break

    for room_name, room_clients in rooms.items():
        if client_socket in room_clients:
            room_clients.remove(client_socket)

    clients.remove(client_socket)
    client_socket.close()


def handle_message(message, client_socket, rooms):
    message_type = message.get("type")
    payload = message.get("payload")
    create_room_directory(message)
    if message_type == "connect":
        name = payload.get("name")
        room = payload.get("room")
        print(f"{name} has joined the room '{room}'")

        if room not in rooms:
            rooms[room] = []

        rooms[room].append(client_socket)

        response = {
            "type": "connect_ack",
            "payload": {
                "message": "Connected to the room."
            }
        }
        client_socket.send(json.dumps(response).encode('utf-8'))
    elif message_type == "message":
        sender = payload.get("sender")
        room = payload.get("room")
        text = payload.get("text")
        print(f"Received from {sender} in '{room}': {text}")

        if room in rooms:
            for client in rooms[room]:
                if client != client_socket:
                    client.send(json.dumps(message).encode('utf-8'))
    elif message_type == "upload":
        handle_upload_command(message, client_socket, rooms)

    elif message_type == "download":
        handle_download_command(message, client_socket, rooms)

    else:
        print("Unknown message type")


def server_broadcast(sender, clients, message):
    for client in clients:
        if client != sender:
            client.send(message)


def handle_upload_command(message, client_socket, rooms):
    payload = message.get("payload")
    name = payload.get("name")
    room = payload.get("room")
    file_name = payload.get("file_name")

    file_path = os.path.join(MEDIA_FOLDER, room, file_name)

    if os.path.exists(file_path):
        notification_message = {
            "type": "notification",
            "payload": {
                "message": f"{name} tried to upload a file, but the file already exists: {file_name}"
            }
        }
    else:
        file_size = payload.get("file_size")

        with open(file_path, 'wb') as file:
            received_size = 0
            while received_size < file_size:
                data = client_socket.recv(1024)
                if not data:
                    break
                file.write(data)
                received_size += len(data)

        print(f"{name} uploaded the {file_name} file")
        notification_message = {
            "type": "notification",
            "payload": {
                "message": f"{name} uploaded the file: {file_name}"
            }
        }
        server_broadcast(client_socket, rooms[room], json.dumps(notification_message).encode('utf-8'))




def handle_download_command(message, client_socket, rooms):
    payload = message.get("payload")
    room = payload.get("room")
    file_name = payload.get("file_name")

    file_path = os.path.join(MEDIA_FOLDER, room, file_name)

    if os.path.exists(file_path):

        stream_message = {
            "type": "download-ack",
            "payload": {
                "file_name": file_name,
            }
        }
        client_socket.send(json.dumps(stream_message).encode('utf-8'))

        with open(file_path, 'rb') as file:
            while True:
                data = file.read(1024)
                if not data:
                    break
                client_socket.send(data)
    else:
        notification_message = {
            "type": "notification",
            "payload": {
                "message": f"The file {file_name} does not exist."
            }
        }
        client_socket.send(json.dumps(notification_message).encode('utf-8'))


if __name__ == "__main__":
    HOST = '127.0.0.1'
    PORT = 12345

    server_socket = create_server_socket(HOST, PORT)
    clients = []
    rooms = {}

    while True:
        client_socket, client_address = server_socket.accept()
        clients.append(client_socket)
        client_thread = threading.Thread(target=handle_client_connection,
                                         args=(client_socket, client_address, clients, rooms))
        client_thread.start()
