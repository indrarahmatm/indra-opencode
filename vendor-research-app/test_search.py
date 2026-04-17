import requests
from bs4 import BeautifulSoup

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

url = "https://www.google.com/search?q=dell+laptop+terbaru&tbm=shop&hl=id"
r = requests.get(url, headers=headers, timeout=15)
soup = BeautifulSoup(r.text, "html.parser")

divs = soup.select("div.sh-np7sh")
print("Shopping results found:", len(divs))

for d in divs[:5]:
    t = d.select_one("div.e4HiGM")
    if t:
        print("- " + t.get_text()[:60])
    p = d.select_one("div.kvSW7Y")
    if p:
        print("  Price:", p.get_text()[:40])
