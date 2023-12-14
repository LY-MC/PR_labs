import multiprocessing
import os
import pika
import re
import requests
from bs4 import BeautifulSoup
import sqlite3

db_path = 'details.db'

def create_table():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        create_table_query = '''
            CREATE TABLE IF NOT EXISTS details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link_title TEXT,
                url TEXT,
                characteristics TEXT,
                additional TEXT,
                price TEXT,
                address TEXT,
                phone TEXT
            );
        '''

        cursor.execute(create_table_query)
        conn.commit()
        conn.close()


def extractDetails(url):
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'lxml')

        details = {
            'Link Title': soup.title.string.strip() if soup.title else '',
            'url': url,
            'Characteristics': {},
            'Additional': [],
            'Price': '',
            'Address': '',
            'Phone': ''
        }

        keys_all = soup.find_all('span', class_='adPage__content__features__key')
        values_all = soup.find_all('span', class_='adPage__content__features__value')

        keys = [key.get_text(strip=True) for key in keys_all]

        for key_elem, value_elem in zip(keys_all, values_all):
            key = key_elem.get_text(strip=True)
            value = value_elem.get_text(strip=True)
            value = value if value is not None else 'N/A'

            details['Characteristics'][key] = value

        details['Additional'] = [key for key in keys if key not in details['Characteristics']]

        prices_all = soup.find_all('span', class_='adPage__content__price-feature__prices__price__value')
        currencies_all = soup.find_all('span', class_='adPage__content__price-feature__prices__price__currency')

        prices = [price.get_text(strip=True) for price in prices_all]
        currencies = [currency.get_text(strip=True) for currency in currencies_all]

        details['Price'] = ' '.join([f'{price}{currency}' for price, currency in zip(prices, currencies)])

        address_all = soup.find_all('span', class_='adPage__aside__address-feature__text')
        details['Address'] = address_all[0].get_text(strip=True)

        links = soup.find_all('a', href=True)
        for link in links:
            if re.match(r"tel:", link['href']):
                details['Phone'] = link['href'][4:]
                break

        return details


def consume_url_from_queue(url):
    details = extractDetails(url)
    process_id = os.getpid()

    print(f"Consumer {process_id} processed URL: {url}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    insert_query = '''
            INSERT INTO details (link_title, url, characteristics, additional, price, address, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?);
    '''

    cursor.execute(insert_query, (
            details['Link Title'],
            details['url'],
            str(details['Characteristics']),
            str(details['Additional']),
            details['Price'],
            details['Address'],
            details['Phone']
        ))

    conn.commit()
    conn.close()


def main():
    create_table()

    queue_name = 'product_urls_queue'
    num_consumers = 20
    pool = multiprocessing.Pool(num_consumers)

    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)

    def callback(ch, method, properties, body):
        url = body.decode('utf-8')
        pool.apply_async(consume_url_from_queue, args=(url,))

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    channel.start_consuming()

    connection.close()


if __name__ == '__main__':
    main()
