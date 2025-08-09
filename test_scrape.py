import requests

API_KEY = "e401c87a31a45c9ef0f7b709e8af3efa"
url = "http://httpbin.org/headers"  # harmless site for header testing

params = {"api_key": API_KEY, "url": url, "render": "false"}

response = requests.get("http://api.scraperapi.com", params=params)
print(response.text)
