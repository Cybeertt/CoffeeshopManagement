import requests
import json

url = "http://127.0.0.1:8000/quebras/"
headers = {"Content-Type": "application/json"}
data = {
    "loja": "Loja A",
    "produto": "Pão de Deus",
    "quantidade": 1,
    "motivo": "Estragado",
    "data": "2025-12-26T11:00:00"
}

response = requests.post(url, headers=headers, data=json.dumps(data))

print(response.status_code)
print(response.json())