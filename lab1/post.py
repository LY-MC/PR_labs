import requests


url = "http://127.0.0.1:5000/hello"

data = {
    "key1": "value1",
    "key2": "value2"
}

response = requests.post(url, json=data)

if response.status_code == 200:
    print("Request was successful")
    print("Response:")
    print(response.text)
else:
    print("Request failed with status code:", response.status_code)
