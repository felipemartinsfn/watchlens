"""
Fetches watch image URLs from watchbase.com (cdn.watchbase.com).
Run: python scripts/fetch_watchbase_images.py
"""
import sys, os, time, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import urllib.request
from html.parser import HTMLParser

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Map: our slug → list of watchbase URLs to try (first that works wins)
WATCHBASE_CANDIDATES = {
    # ── ROLEX ──
    "submariner-date-126610ln": [
        "https://watchbase.com/rolex/submariner/126610ln-0001",
        "https://watchbase.com/rolex/submariner-date/126610ln-0001",
    ],
    "submariner-date-116610ln": [
        "https://watchbase.com/rolex/submariner/116610ln-0001",
    ],
    "datejust-126300": [
        "https://watchbase.com/rolex/datejust/126300-0001",
        "https://watchbase.com/rolex/datejust-ii/126300-0001",
        "https://watchbase.com/rolex/datejust/126300-0005",
    ],
    "gmt-master-ii-pepsi-126710blro": [
        "https://watchbase.com/rolex/gmt-master-ii/126710blro-0003",
        "https://watchbase.com/rolex/gmt-master-ii/126710blro-0001",
    ],
    "daytona-116500ln": [
        "https://watchbase.com/rolex/daytona/116500ln-0001",
        "https://watchbase.com/rolex/cosmograph-daytona/116500ln-0001",
    ],
    "explorer-ii-214270": [
        "https://watchbase.com/rolex/explorer-ii/214270-0001",
        "https://watchbase.com/rolex/explorer/214270-0001",
    ],
    # ── OMEGA ──
    "speedmaster-moonwatch-310-30-42-50-01-001": [
        "https://watchbase.com/omega/speedmaster/310-30-42-50-01-001",
        "https://watchbase.com/omega/speedmaster-moonwatch/310-30-42-50-01-001",
    ],
    "seamaster-300m-210-30-42-20-01-001": [
        "https://watchbase.com/omega/seamaster/210-30-42-20-01-001",
        "https://watchbase.com/omega/seamaster-300m/210-30-42-20-01-001",
    ],
    "constellation-131-10-39-20-02-001": [
        "https://watchbase.com/omega/constellation/131-10-39-20-02-001",
    ],
    # ── PATEK ──
    "nautilus-5711-1a": [
        "https://watchbase.com/patek-philippe/nautilus/5711-1a-010",
        "https://watchbase.com/patek-philippe/nautilus/5711-1a-001",
    ],
    "calatrava-5196g": [
        "https://watchbase.com/patek-philippe/calatrava/5196g-001",
        "https://watchbase.com/patek-philippe/calatrava/5196g-010",
    ],
    # ── AP ──
    "royal-oak-jumbo-15202st": [
        "https://watchbase.com/audemars-piguet/royal-oak/15202st-oo-1240st-01",
        "https://watchbase.com/audemars-piguet/royal-oak/15202st-oo-0944st-01",
    ],
    "royal-oak-offshore-26400so": [
        "https://watchbase.com/audemars-piguet/royal-oak-offshore/26400so-oo-a002ca-01",
        "https://watchbase.com/audemars-piguet/royal-oak-offshore/26400so-oo-002ca-01",
    ],
    # ── IWC ──
    "pilot-mark-xx-iw328201": [
        "https://watchbase.com/iwc/pilots-watch/iw328201",
        "https://watchbase.com/iwc/pilot/iw328201",
    ],
    "portugieser-iw500705": [
        "https://watchbase.com/iwc/portugieser/iw500705",
        "https://watchbase.com/iwc/portugieser/iw5007-05",
    ],
    # ── TUDOR ──
    "black-bay-58-m79030n": [
        "https://watchbase.com/tudor/black-bay/m79030n-0001",
        "https://watchbase.com/tudor/black-bay-58/m79030n-0001",
    ],
    "pelagos-fxd-m25717n": [
        "https://watchbase.com/tudor/pelagos/m25717n-0001",
        "https://watchbase.com/tudor/pelagos-fxd/m25717n-0001",
    ],
    # ── SEIKO ──
    "prospex-spb317j1": [
        "https://watchbase.com/seiko/prospex/spb317j1",
        "https://watchbase.com/seiko/prospex/spb317",
    ],
    "5-sports-srpd51k1": [
        "https://watchbase.com/seiko/5-sports/srpd51k1",
        "https://watchbase.com/seiko/5-sports/srpd51",
    ],
    # ── GRAND SEIKO ──
    "heritage-sbgw231": [
        "https://watchbase.com/grand-seiko/heritage/sbgw231",
        "https://watchbase.com/grand-seiko/heritage-collection/sbgw231",
    ],
    # ── CARTIER ──
    "tank-must-wsta0041": [
        "https://watchbase.com/cartier/tank/wsta0041",
        "https://watchbase.com/cartier/tank-must/wsta0041",
    ],
    "santos-wssa0018": [
        "https://watchbase.com/cartier/santos/wssa0018",
        "https://watchbase.com/cartier/santos-de-cartier/wssa0018",
    ],
    # ── TAG HEUER ──
    "carrera-cbn2a1b-ba0643": [
        "https://watchbase.com/tag-heuer/carrera/cbn2a1b-ba0643",
        "https://watchbase.com/tag-heuer/carrera/cbn2a1bba0643",
    ],
    # ── LONGINES ──
    "hydroconquest-l3-781-4-96-6": [
        "https://watchbase.com/longines/hydroconquest/l3-781-4-96-6",
        "https://watchbase.com/longines/hydroconquest/l37814966",
    ],
    # ── NOMOS ──
    "tangente-139": [
        "https://watchbase.com/nomos/tangente/139",
        "https://watchbase.com/nomos-glashuette/tangente/139",
    ],
    # ── PANERAI ──
    "luminor-pam01392": [
        "https://watchbase.com/panerai/luminor/pam01392",
        "https://watchbase.com/panerai/luminor-base/pam01392",
        "https://watchbase.com/panerai/luminor-base-logo/pam01392",
    ],
    # ── A. LANGE ──
    "lange-1-191-032": [
        "https://watchbase.com/a-lange-sohne/lange-1/191-032",
        "https://watchbase.com/a-lange-sohne/lange-1/191032",
    ],
    # ── BREITLING ──
    "navitimer-b01-ab0138241g1p1": [
        "https://watchbase.com/breitling/navitimer/ab0138241g1p1",
        "https://watchbase.com/breitling/navitimer-b01/ab0138241g1p1",
    ],
    # ── JLC ──
    "reverso-q3858522": [
        "https://watchbase.com/jaeger-lecoultre/reverso/q3858522",
        "https://watchbase.com/jaeger-lecoultre/reverso-classic/q3858522",
    ],
}


class ImgParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.final_url = None

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            attrs_dict = dict(attrs)
            src = attrs_dict.get("src", "")
            if "cdn.watchbase.com/watch" in src:
                self.images.append(src)


def fetch_page(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as r:
            final_url = r.url
            html = r.read().decode("utf-8", errors="ignore")
            return html, final_url
    except Exception as e:
        return None, str(e)


def get_images_for_slug(slug, candidates):
    for url in candidates:
        print(f"    Trying: {url}")
        html, final_url = fetch_page(url)
        if not html:
            print(f"    ❌ Failed: {final_url}")
            time.sleep(0.5)
            continue

        parser = ImgParser()
        parser.feed(html)

        if parser.images:
            # Prefer lg (large) PNG, then md JPG
            lg = [i for i in parser.images if "/lg/" in i and i.endswith(".png")]
            md = [i for i in parser.images if "/md/" in i]
            all_imgs = lg + md + parser.images
            primary = all_imgs[0] if all_imgs else None
            thumb = md[0] if md else primary

            # Upgrade thumb to lg if possible
            if thumb and "/md/" in thumb:
                thumb_lg = thumb.replace("/md/", "/lg/").replace(".jpg", ".png")
                if thumb_lg in parser.images:
                    thumb = thumb_lg

            print(f"    ✅ Found {len(parser.images)} images → {primary}")
            return {
                "primary": primary,
                "thumb": thumb or primary,
                "extras": [i for i in parser.images if i != primary][:2],
                "source_url": final_url,
            }
        else:
            print(f"    ⚠️  Page loaded but no watchbase CDN images found")
            time.sleep(0.5)

    return None


def main():
    results = {}
    not_found = []

    print(f"🔍 Fetching images from watchbase.com for {len(WATCHBASE_CANDIDATES)} watches...\n")

    for slug, candidates in WATCHBASE_CANDIDATES.items():
        print(f"📦 {slug}")
        imgs = get_images_for_slug(slug, candidates)
        if imgs:
            results[slug] = imgs
        else:
            not_found.append(slug)
            print(f"  ❌ NOT FOUND")
        time.sleep(1.2)  # polite delay

    print(f"\n\n{'='*60}")
    print(f"✅ Found: {len(results)}/{len(WATCHBASE_CANDIDATES)}")
    if not_found:
        print(f"❌ Not found: {not_found}")

    # Save results
    out_path = os.path.join(os.path.dirname(__file__), "watchbase_images.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Saved to {out_path}")

    # Print Python dict for copy-paste into enrich script
    print("\n\n# ── PYTHON DICT ─────────────────────────────────────")
    print("IMAGE_MAP = {")
    for slug, imgs in results.items():
        print(f'    "{slug}": {{')
        print(f'        "primary": "{imgs["primary"]}",')
        print(f'        "thumb":   "{imgs["thumb"]}",')
        extras_str = ", ".join(f'"{e}"' for e in imgs.get("extras", []))
        print(f'        "extras": [{extras_str}],')
        print(f'    }},')
    print("}")


if __name__ == "__main__":
    main()
