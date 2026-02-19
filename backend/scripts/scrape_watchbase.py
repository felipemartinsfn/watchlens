"""
Scrapes watch specs and images from watchbase.com.
Produces: scripts/watchbase_catalog.json

Run: python scripts/scrape_watchbase.py

Strategy:
  1. Discover model URLs for each brand/collection (already done via discover step)
  2. For each model page, parse the info-table specs + cdn.watchbase.com images
  3. Save structured JSON ready for seed_from_watchbase.py
"""
import sys, os, re, time, json, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import urllib.request
from html.parser import HTMLParser

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
}

# Brands to scrape — maps watchbase slug → canonical brand name
BRANDS = {
    "rolex":               "Rolex",
    "omega":               "Omega",
    "patek-philippe":      "Patek Philippe",
    "audemars-piguet":     "Audemars Piguet",
    "tudor":               "Tudor",
    "seiko":               "Seiko",
    "grand-seiko":         "Grand Seiko",
    "iwc":                 "IWC Schaffhausen",
    "cartier":             "Cartier",
    "tag-heuer":           "TAG Heuer",
    "longines":            "Longines",
    "breitling":           "Breitling",
    "panerai":             "Panerai",
    "jaeger-lecoultre":    "Jaeger-LeCoultre",
    "a-lange-sohne":       "A. Lange & Söhne",
    "nomos-glashutte":     "Nomos Glashütte",
    "vacheron-constantin": "Vacheron Constantin",
    "zenith":              "Zenith",
    "hublot":              "Hublot",
}

# Max models per brand to scrape (to avoid too long runs)
MAX_MODELS_PER_BRAND = 30
# Max collections to discover per brand
MAX_COLLECTIONS_PER_BRAND = 20
# Max refs to pick per collection
MAX_REFS_PER_COLLECTION = 3


# ─── HTML Parsers ──────────────────────────────────────────────────────────────

class CollectionLinkParser(HTMLParser):
    """Extracts collection links from a brand page."""
    def __init__(self, brand_slug):
        super().__init__()
        self.brand_slug = brand_slug
        self.collections = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            d = dict(attrs)
            href = d.get("href", "")
            prefix = f"https://watchbase.com/{self.brand_slug}/"
            if href.startswith(prefix):
                # collection: exactly one more path segment
                path = href[len(prefix):].strip("/")
                if path and "/" not in path and path not in self.collections:
                    self.collections.append(href)


class ModelLinkParser(HTMLParser):
    """Extracts model reference links from a collection page."""
    def __init__(self, collection_url):
        super().__init__()
        self.collection_url = collection_url.rstrip("/")
        self.refs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            d = dict(attrs)
            href = d.get("href", "")
            prefix = self.collection_url + "/"
            if href.startswith(prefix):
                path = href[len(prefix):].strip("/")
                if path and "/" not in path and href not in self.refs:
                    self.refs.append(href)


class WatchPageParser(HTMLParser):
    """Parses a watchbase watch page for specs and images."""
    def __init__(self):
        super().__init__()
        self.images = []
        self.specs = {}
        self._in_th = False
        self._in_td = False
        self._current_key = None
        self._buf = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "img":
            src = d.get("src", "")
            if "cdn.watchbase.com/watch" in src and "/lg/" in src:
                if src not in self.images:
                    self.images.append(src)
        if tag == "th":
            self._in_th = True
            self._buf = []
        if tag == "td":
            self._in_td = True
            self._buf = []

    def handle_endtag(self, tag):
        if tag == "th" and self._in_th:
            self._in_th = False
            self._current_key = " ".join(self._buf).strip().rstrip(":").strip()
            self._buf = []
        if tag == "td" and self._in_td:
            self._in_td = False
            val = " ".join(self._buf).strip()
            if self._current_key and val:
                self.specs[self._current_key] = val
            self._buf = []

    def handle_data(self, data):
        if self._in_th or self._in_td:
            stripped = data.strip()
            if stripped:
                self._buf.append(stripped)


# ─── Helpers ───────────────────────────────────────────────────────────────────

def fetch(url, retries=2):
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as r:
                raw = r.read()
                # Handle gzip
                try:
                    import gzip
                    if r.info().get("Content-Encoding") == "gzip":
                        raw = gzip.decompress(raw)
                except Exception:
                    pass
                return raw.decode("utf-8", errors="ignore"), r.url
        except Exception as e:
            if attempt < retries:
                time.sleep(1.5)
            else:
                return None, str(e)


def discover_collections(brand_slug):
    url = f"https://watchbase.com/{brand_slug}"
    html, _ = fetch(url)
    if not html:
        return []
    parser = CollectionLinkParser(brand_slug)
    parser.feed(html)
    return parser.collections[:MAX_COLLECTIONS_PER_BRAND]


def discover_refs(collection_url):
    html, _ = fetch(collection_url)
    if not html:
        return []
    parser = ModelLinkParser(collection_url)
    parser.feed(html)
    return parser.refs[:MAX_REFS_PER_COLLECTION]


def parse_watch_page(url):
    html, final_url = fetch(url)
    if not html:
        return None

    parser = WatchPageParser()
    parser.feed(html)

    if not parser.images and not parser.specs:
        return None

    # Pick best image: prefer .png over .jpg
    images_png = [i for i in parser.images if i.endswith(".png")]
    images_jpg = [i for i in parser.images if i.endswith(".jpg")]
    ordered = images_png + images_jpg + parser.images
    primary = ordered[0] if ordered else None

    return {
        "source_url": final_url,
        "specs": parser.specs,
        "primary_image": primary,
        "all_images": parser.images[:5],
    }


def extract_slug_from_url(url):
    """Convert watchbase URL to our app slug: brand-collection-reference"""
    parts = url.rstrip("/").split("/")
    # https://watchbase.com/{brand}/{collection}/{reference}
    if len(parts) >= 6:
        brand = parts[3]
        collection = parts[4]
        ref = parts[5]
        return f"{brand}-{collection}-{ref}".lower()
    return url.split("/")[-1]


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    out_path = os.path.join(os.path.dirname(__file__), "watchbase_catalog.json")

    # Load existing progress if any
    if os.path.exists(out_path):
        with open(out_path) as f:
            catalog = json.load(f)
        print(f"📂 Resuming — {len(catalog)} watches already scraped")
    else:
        catalog = {}

    total_scraped = 0

    for brand_slug, brand_name in BRANDS.items():
        brand_count = sum(1 for k in catalog if k.startswith(brand_slug + "-"))
        if brand_count >= MAX_MODELS_PER_BRAND:
            print(f"⏭️  {brand_name}: already have {brand_count} models, skipping")
            continue

        print(f"\n🏭 {brand_name} ({brand_slug})")
        collections = discover_collections(brand_slug)
        print(f"   Found {len(collections)} collections")
        time.sleep(0.5)

        brand_scraped = brand_count
        for coll_url in collections:
            if brand_scraped >= MAX_MODELS_PER_BRAND:
                break

            coll_name = coll_url.rstrip("/").split("/")[-1]
            refs = discover_refs(coll_url)
            time.sleep(0.4)

            for ref_url in refs:
                if brand_scraped >= MAX_MODELS_PER_BRAND:
                    break

                slug = extract_slug_from_url(ref_url)
                if slug in catalog:
                    brand_scraped += 1
                    continue

                print(f"   📦 {coll_name}/{ref_url.split('/')[-1]}")
                data = parse_watch_page(ref_url)
                time.sleep(random.uniform(0.6, 1.2))

                if data and (data["primary_image"] or data["specs"]):
                    catalog[slug] = {
                        "brand_slug": brand_slug,
                        "brand_name": brand_name,
                        "collection_slug": coll_name,
                        "source_url": data["source_url"],
                        "specs": data["specs"],
                        "primary_image": data["primary_image"],
                        "all_images": data["all_images"],
                    }
                    brand_scraped += 1
                    total_scraped += 1
                    print(f"      ✅ specs={len(data['specs'])} img={'yes' if data['primary_image'] else 'NO'}")

                    # Save progress every 10 watches
                    if total_scraped % 10 == 0:
                        with open(out_path, "w") as f:
                            json.dump(catalog, f, indent=2, ensure_ascii=False)
                        print(f"      💾 Saved {len(catalog)} total")
                else:
                    print(f"      ⚠️  No data found")

        print(f"   → {brand_scraped} models for {brand_name}")

    # Final save
    with open(out_path, "w") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    print(f"\n\n{'='*60}")
    print(f"✅ DONE — {len(catalog)} watches scraped")
    print(f"💾 Saved to {out_path}")

    # Show sample
    sample = list(catalog.items())[:3]
    for slug, data in sample:
        print(f"\n  {slug}:")
        print(f"    image: {data['primary_image']}")
        print(f"    specs: {list(data['specs'].items())[:5]}")


if __name__ == "__main__":
    main()
