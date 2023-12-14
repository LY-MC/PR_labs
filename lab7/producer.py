import requests
from bs4 import BeautifulSoup
import re
import pika


def scan(url, urls, max_num_pages):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'lxml')
            soup.prettify()
            links = soup.find_all('a', href=True)
            links_counter = 0
            for link in links:
                if re.match(r"/r[ou]/[0-9]+", link['href']) and 'https://999.md/' + link['href'] not in urls:
                    urls.append('https://999.md/' + link.get('href'))
                    links_counter += 1

        page = re.split('page=', url)
        if len(page) == 1:
            new_page = 1
            newurl = page[0] + '&page=' + str(new_page + 1)
        else:
            new_page = int(page[1])
            newurl = page[0] + 'page=' + str(new_page + 1)

        if links_counter != 0:
            if max_num_pages is None:
                scan(newurl, urls, None)
            elif new_page < max_num_pages:
                scan(newurl, urls, max_num_pages - 1)

        else:
            print(f"Failed to retrieve the web page. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the request: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def produce_url_to_queue(url, queue_name):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue=queue_name)

    channel.basic_publish(exchange='', routing_key=queue_name, body=url)

    connection.close()


if __name__ == '__main__':
    queue_name = 'product_urls_queue'
    urls = []

    scan('https://999.md/ru/list/real-estate/apartments-and-rooms?applied=1&o_30_241=894&eo=12900&eo=12912&eo=12885&eo=13859&ef=32&ef=33&o_33_1=776', urls, 3)
    for url in urls:
        produce_url_to_queue(url, queue_name)
