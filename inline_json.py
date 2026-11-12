"""Scrape a JavaScript-rendered page without a browser: read the data from the page's script.

https://quotes.toscrape.com/js/ shows no quotes to tools that do not run
JavaScript. The quotes are still in the HTML, inside <script>var data = [...];</script>,
and the page's JavaScript only draws them. Extract that JSON and parse it.

    pip install -r requirements.txt
    python inline_json.py
"""
import json
import os
import random
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

START = "https://quotes.toscrape.com/js/"


def proxies() -> dict:
    """Optional residential proxy: set FUSION_USER and FUSION_PASS to use one sticky IP for the run."""
    user, password = os.environ.get("FUSION_USER"), os.environ.get("FUSION_PASS")
    if not (user and password):
        return {}
    country = os.environ.get("FUSION_COUNTRY", "us")
    session_user = f"{user}-country-{country}-sessid-{random.randint(1000000, 9999999)}-sessTime-1800s"
    proxy = f"http://{session_user}:{password}@resi.fusionproxy.net:12286"
    return {"http": proxy, "https": proxy}


def extract_data(html: str) -> list:
    """Find 'var data = [...];' in an inline script and parse the array as JSON."""
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", src=False):
        m = re.search(r"var\s+data\s*=\s*(\[.*?\]);", script.string or "", re.S)
        if m:
            return json.loads(m.group(1))
    return []


def main() -> None:
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
    session.proxies.update(proxies())

    # what a plain HTML parser sees: no quote elements in the markup
    first = session.get(START, timeout=30).text
    print("quote elements in the raw HTML:", len(BeautifulSoup(first, "html.parser").select("div.quote")))

    quotes, url, page = [], START, 1
    while url:
        html = session.get(url, timeout=30).text
        data = extract_data(html)
        quotes += [{"text": q["text"], "author": q["author"]["name"], "tags": q["tags"]} for q in data]
        print(f"page {page}: {len(data)} quotes from the inline script")
        nxt = BeautifulSoup(html, "html.parser").select_one("li.next a")
        url = urljoin(url, nxt["href"]) if nxt else None
        page += 1

    with open("quotes.json", "w", encoding="utf-8") as f:
        json.dump(quotes, f, indent=2, ensure_ascii=False)
    print(f"saved {len(quotes)} quotes to quotes.json")


if __name__ == "__main__":
    main()
