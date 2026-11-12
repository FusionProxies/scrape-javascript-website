<p align="center">
  <a href="https://fusionproxy.net/?utm_source=github&utm_medium=scrape-javascript-website">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/FusionProxies/.github/main/assets/logo-on-dark.png">
      <img src="https://raw.githubusercontent.com/FusionProxies/.github/main/assets/logo-on-light.png" alt="Fusion Proxy" height="52">
    </picture>
  </a>
</p>

# How to scrape JavaScript-rendered websites with Python (often without a browser)

You download a page with `requests`, parse it with BeautifulSoup, and the data is not there: the site builds the page with JavaScript. Before you reach for a headless browser, check where the JavaScript gets its data. In most cases the data is already in the HTML or comes from an API you can call directly, and both are 10 to 100 times faster than a browser.

[`inline_json.py`](inline_json.py) scrapes [quotes.toscrape.com/js](https://quotes.toscrape.com/js/), a practice page that renders with JavaScript:

```bash
pip install -r requirements.txt
python inline_json.py
```

```
quote elements in the raw HTML: 0
page 1: 10 quotes from the inline script
page 2: 10 quotes from the inline script
...
saved 100 quotes to quotes.json
```

The parser finds zero quote elements, yet the script gets all 100 quotes without running any JavaScript.

## Work through these in order

### 1. Look at the page source, not the inspector

The browser's element inspector shows the page **after** JavaScript ran. Press **Ctrl+U** (view source) to see what `requests` gets, and search for a value you can see on the page. If it is there, it is usually in one of these places.

### 2. Data in an inline script

```html
<script>
    var data = [{"text": "...", "author": {"name": "Albert Einstein"}}, ...];
</script>
```

Pull it out with a regular expression and parse it as JSON:

```python
for script in soup.find_all("script", src=False):
    m = re.search(r"var\s+data\s*=\s*(\[.*?\]);", script.string or "", re.S)
    if m:
        data = json.loads(m.group(1))
```

The same idea covers the common framework patterns:

| You see in the source | Framework | Read it with |
|---|---|---|
| `<script id="__NEXT_DATA__" type="application/json">` | Next.js | `json.loads(soup.select_one("#__NEXT_DATA__").string)` |
| `window.__NUXT__=` or `<script id="__NUXT_DATA__">` | Nuxt | the JSON script tag, or a regex on `window.__NUXT__` |
| `window.__INITIAL_STATE__ =` / `__APOLLO_STATE__` | many SPAs | regex up to the closing `;</script>` |
| `<script type="application/ld+json">` | any (SEO data) | `json.loads(tag.string)`: names, prices, ratings, availability |

If the inline value is a JavaScript object rather than strict JSON (single quotes, unquoted keys), `json.loads` fails. Try the `chompjs` package, which parses JavaScript object literals.

### 3. Data from an API

Open DevTools, **Network** tab, filter **Fetch/XHR**, reload the page. The request that returns the data is usually obvious (JSON with the values you see). Call it with `requests`, copying the headers the browser sent. The [scrape-infinite-scroll](https://github.com/FusionProxies/scrape-infinite-scroll) guide walks through this step by step.

### 4. Only then: a headless browser

If the data is computed in the browser, or the API needs tokens you cannot reproduce, render the page with Playwright and read the DOM after it loads:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://quotes.toscrape.com/js/")
    page.wait_for_selector("div.quote")
    texts = page.locator("span.text").all_inner_texts()
```

A browser downloads every script, image and font, so it is slower and uses much more proxy traffic. See [playwright-proxy](https://github.com/FusionProxies/playwright-proxy) for proxies in Playwright.

## Proxies

The script uses a residential proxy when `FUSION_USER` and `FUSION_PASS` are set, keeping one IP for the run:

```bash
export FUSION_USER="your_username" FUSION_PASS="your_password"
python inline_json.py
```

## Related

- [scrape-infinite-scroll](https://github.com/FusionProxies/scrape-infinite-scroll): find and call the API behind a page
- [scrape-website-with-login](https://github.com/FusionProxies/scrape-website-with-login): scrape pages behind a login
- [python-web-scraping](https://github.com/FusionProxies/python-web-scraping): the requests + BeautifulSoup basics

[Fusion Proxy residential proxies](https://fusionproxy.net/proxies/residential?utm_source=github&utm_medium=scrape-javascript-website) from $2.95/GB, with a [free trial](https://fusionproxy.net/free-trial?utm_source=github&utm_medium=scrape-javascript-website).

## License

MIT, see [LICENSE](LICENSE).
