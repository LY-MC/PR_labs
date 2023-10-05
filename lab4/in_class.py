import json
import re
import socket

HOST = '127.0.0.1'
PORT = 8080

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_socket.bind((HOST, PORT))

server_socket.listen()
print(f"Server is listening on {HOST}:{PORT}")

client_socket, client_address = server_socket.accept()
print(client_address)


def load_page(page_name):
    with open(f'resources/{page_name}.html', 'r') as page:
        return page.read()


def listening(products):
    request_data = client_socket.recv(1024).decode('utf-8')
    print(f"Received Request:\n{request_data}")

    request_lines = request_data.split('\n')
    request_line = request_lines[0].strip().split()
    path = request_line[1]
    status_code = 200

    if path == '/':
        response_content = 'Welcome page'
    elif path in ('/home', '/about_us', '/contacts'):
        response_content = load_page(path[1:])
    elif path == '/products':
        response_content = 'List of products<br>'
        for product in products:
            response_content += f"<a href='/product/{product['id']}'> Product {product['name']} </a><br>"
    elif re.match(r"/product/[0-9]+", path):
        id = int(re.split(r"/", path)[2])
        check = 0
        p = {}
        for product in products:
            if int(product['id']) == id:
                p = product
                check += 1
                break

        if check != 0:
            response_content = f"""<p> ID : {p['id']} </p><br>""" + \
                               f"""<p> Name : {p['name']} </p><br>""" + \
                               f"""<p> Author : {p['author']} </p><br>""" + \
                               f"""<p> Price : {p['price']} </p><br>""" + \
                               f"""<p> Description : {p['description']} </p><br>"""
        else:
            response_content = '404 Product Not Found'
        status_code = 404
    else:
        response_content = '404 Not Found'
        status_code = 404

    response = f'HTTP/1.1 {status_code} OK\nContent-Type: text/html\n\n{response_content}'
    client_socket.send(response.encode('utf-8'))
    client_socket.close()


if __name__ == '__main__':
    with open('resources/products.json', 'r') as product:
        products = json.load(product)

    while True:
        client_socket, client_address = server_socket.accept()
        try:
            listening(products)
        except KeyboardInterrupt:
            pass
