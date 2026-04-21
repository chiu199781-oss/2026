import requests
from bs4 import BeautifulSoup

url = "https://2026-rust.vercel.app/"
Data = requests.get(url)
Data.encoding = "utf-8"
#print(Data.text)
sp = BeautifulSoup(Data.text, "html.parser")
result=sp.select("#pic")

for item in result:
	print(item)
	print(item.get("src"))
	print()
