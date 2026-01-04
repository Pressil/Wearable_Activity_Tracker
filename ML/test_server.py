import requests
import random
import json

url = 'http://127.0.0.1:5000/readings'

fake_data = []
for _ in range(50):
    reading = {
        'ax': random.uniform(0.5, 1.5), 
        'ay': random.uniform(-0.5, 0.5),
        'az': random.uniform(0.0, 1.0),
        'gx': 0.1, 'gy': 0.1, 'gz': 0.1
    }
    fake_data.append(reading)

payload = {'readings': fake_data}

print("Sending 50 fake readings to server...")
response = requests.post(url, json=payload)
print("Server Response:", response.json())