import socket
from bs4 import BeautifulSoup
import re
import os
import json

HOST = '127.0.0.1'
PORT = 8080

simple_endpoints = ['/', '/home', '/about_us', '/contacts']
product_endpoints = ['/products', '/product']


def create_directory_if_not_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def send_request_and_get_response(endpoint):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    request = f'GET {endpoint} HTTP/1.1\nHost: {HOST}:{PORT}'
    client_socket.send(request.encode('utf-8'))

    response = client_socket.recv(4096).decode('utf-8')
    header, body = response.split('\n', 1)
    print(f'Response status: {header}')
    client_socket.close()

    return body


def process_simple_endpoints():
    for ep in simple_endpoints:
        body = send_request_and_get_response(ep)

        ep_filename = re.sub(r'/', r'page_', ep)
        filename = f'contents/{ep_filename}.html'

        if not os.path.exists(filename):
            option = 'w'
        else:
            option = 'a'

        with open(filename, option) as f:
            f.write(body)


def parse_product_details(product_url):
    response = send_request_and_get_response(product_url)
    detail_parser = BeautifulSoup(response, 'html.parser')

    product_info = {}
    for detail in detail_parser.find_all('p'):
        key_value = detail.contents[0].split(r':')
        product_info[key_value[0].strip()] = key_value[1].strip()

    return product_info


def process_product_endpoints():
    product_list_endpoint = product_endpoints[0]
    product_list_response = send_request_and_get_response(product_list_endpoint)
    list_parser = BeautifulSoup(product_list_response, 'html.parser')

    list_of_products = []
    for product_link in list_parser.find_all('a'):
        product_route = product_link['href']
        product_info = parse_product_details(product_route)
        list_of_products.append(product_info)

    option = 'w' if not os.path.exists('contents/products.json') else 'x'
    with open('contents/products.json', option) as prods:
        prods.write(json.dumps(list_of_products, indent=4))


if __name__ == '__main__':
    try:
        create_directory_if_not_exists('contents')
        process_simple_endpoints()
        process_product_endpoints()
    except KeyboardInterrupt:
        pass
