import requests
from urllib.parse import quote

API_KEY = "AIzaSyCeUOYRKg4S-sHuWumFAC4yTCcCH31hCQg"
CX = "c5b310058b63c4868"

query = "dell laptop harga Indonesia"
url = (
    "https://www.googleapis.com/customsearch/v1?key="
    + API_KEY
    + "&cx="
    + CX
    + "&q="
    + quote(query)
    + "&num=5&hl=id"
)

print("Testing with CX:", CX)
r = requests.get(url, timeout=15)
print("Status:", r.status_code)

if r.status_code == 200:
    data = r.json()
    items = data.get("items", [])
    print("Results:", len(items))
    for item in items[:3]:
        print("-", item.get("title", "")[:60])
        print("  URL:", item.get("link", "")[:60])
else:
    print("Error:", r.text[:200])
