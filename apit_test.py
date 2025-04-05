import requests

response = requests.get("http://127.0.0.1:7860")
print(response.text)
