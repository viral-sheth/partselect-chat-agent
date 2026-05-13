"""
PartSelect scraper — model-page strategy.

Strategy:
1. For each target model number, fetch /Models/{model}/Parts/ → get all part URLs
2. For each part URL, scrape: name, price, stock, description, category, brand
3. Compatibility is inferred from which model page each part appeared on
4. Image URLs are constructed from the part URL pattern (no lazy-load needed)

Run:
    cd /Users/viralmanojsheth/Documents/Test
    python3 scraper/scrape_partselect.py
"""
import asyncio
import json
import re
import random
import sys
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

OUTPUT_FILE = Path(__file__).parent / "scraped_parts.json"
BASE_URL = "https://www.partselect.com"

# ── Target models ────────────────────────────────────────────────────────────
# Mix of popular Whirlpool, Maytag, KitchenAid, GE, Frigidaire models.
# Each must exist on PartSelect. We verified WDT780SAEM1 and WRS325SDHZ work.

DISHWASHER_MODELS = [
    "WDT780SAEM1",   # Whirlpool
    "WDT730PAHZ0",   # Whirlpool
    "WDF520PADM7",   # Whirlpool
    "KDTM354DSS4",   # KitchenAid
    "MDB8989SHZ0",   # Maytag
    "WDT750SAHZ0",   # Whirlpool
    "WDTA50SAHZ0",   # Whirlpool
    "GDT695SSJSS0",  # GE
    "FGID2466QF4A",  # Frigidaire
    "WDT970SAHZ0",   # Whirlpool
]

REFRIGERATOR_MODELS = [
    "WRS325SDHZ",    # Whirlpool
    "WRF535SWHZ",    # Whirlpool
    "WRS571CIHZ",    # Whirlpool
    "WRT518SZFM",    # Whirlpool
    "WRX735SDHZ",    # Whirlpool
    "MFI2570FEZ",    # Maytag
    "GSS25GSHSS",    # GE
    "KRFF507HPS",    # KitchenAid
    "WRS311SDHM",    # Whirlpool
    "FFHD2250TS",    # Frigidaire
]

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]

MAX_PARTS_PER_MODEL = 8   # Keep scrape time reasonable; 20 models × 8 = up to 160 parts
MAX_TOTAL_PARTS = 100     # Hard cap


def url_to_image_url(part_url: str):
    """
    Construct CDN image URL from part page URL.
    Pattern: /PS11752778-Whirlpool-WPW10321304-Name.htm
         →   {ps_digits}-1-M-Whirlpool-WPW10321304-Name.jpg
    """
    m = re.search(r"/PS(\d+)-(.+?)\.htm", part_url)
    if not m:
        return None
    digits, rest = m.group(1), m.group(2)
    return f"https://partselectcom-gtcdcddbene3cpes.z01.azurefd.net/{digits}-1-M-{rest}.jpg"


def clean_url(url: str) -> str:
    """Strip query params from part URL."""
    return url.split("?")[0].split("#")[0]


def parse_part_from_url(url: str) -> dict:
    """Extract PS number, brand, mfr part number from URL."""
    m = re.search(r"/PS(\d+)-([^-]+)-([^-]+)-(.+?)\.htm", url)
    if not m:
        return {}
    return {
        "part_number": f"PS{m.group(1)}",
        "brand": m.group(2).lower(),
        "manufacturer_part_number": m.group(3),
    }


def clean_name(title: str) -> str:
    """Remove 'Official', brand prefix, and trailing site name from page title."""
    title = re.sub(r"^\s*Official\s+\w+\s+", "", title)
    title = re.sub(r"\s*[–-]\s*PartSelect.*$", "", title)
    title = re.sub(r"\s*\|\s*PartSelect.*$", "", title)
    return title.strip()


async def get_part_urls_for_model(page, model: str, category: str) -> list[str]:
    """Fetch /Models/{model}/Parts/ and return deduplicated part URLs."""
    url = f"{BASE_URL}/Models/{model}/Parts/"
    try:
        resp = await page.goto(url, wait_until="networkidle", timeout=20000)
        if not resp or resp.status != 200:
            print(f"  [{model}] HTTP {resp.status if resp else 'N/A'} — skipping")
            return []

        # Scroll to load more parts
        for _ in range(3):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(0.8)

        links = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a[href*="/PS"]'))
                .map(a => a.href.split('?')[0].split('#')[0])
                .filter(h => /\\/PS\\d+/.test(h) && h.endsWith('.htm'))
                .filter((v, i, a) => a.indexOf(v) === i);
        }""")

        print(f"  [{model}] {len(links)} parts found")
        return links[:MAX_PARTS_PER_MODEL]

    except PWTimeout:
        print(f"  [{model}] Timeout — skipping")
        return []
    except Exception as e:
        print(f"  [{model}] Error: {e}")
        return []


async def scrape_part(page, url: str, compatible_models: list, category: str):
    """Scrape one part page. Returns dict or None on failure."""
    clean = clean_url(url)
    url_meta = parse_part_from_url(clean)
    if not url_meta.get("part_number"):
        return None

    try:
        await page.goto(clean, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(random.uniform(0.5, 1.2))

        # Scroll to trigger lazy price/stock load
        await page.evaluate("window.scrollTo(0, 500)")
        await asyncio.sleep(0.8)

        data = await page.evaluate("""() => {
            const getText = (sel) => {
                const el = document.querySelector(sel);
                return el ? el.innerText.trim() : null;
            };
            const getAll = (sel) =>
                Array.from(document.querySelectorAll(sel))
                    .map(e => e.innerText.trim())
                    .filter(Boolean);

            // Title / name
            const title = document.title || '';

            // Price — find first "$XX.XX" pattern
            const allText = document.body.innerText;
            const priceMatch = allText.match(/\\$(\\d+\\.\\d{2})/);
            const price = priceMatch ? parseFloat(priceMatch[1]) : null;

            // Stock
            const stockEl = document.querySelector('.js-partAvailability, [class*="availability"]');
            const inStock = stockEl ? stockEl.innerText.includes('In Stock') : true;

            // Description
            const desc = getText('.pd__description, [itemprop="description"]');

            // Symptoms — "This part fixes" section
            const symptoms = getAll(
                '.pd__fix .bold, .pd__fix__list__item, [class*="fix"] .col-6 span'
            ).filter(s => s.length > 5 && s.length < 80);

            // Breadcrumb for category confirmation
            const crumbs = getAll(
                '.breadcrumb__item, [aria-label="breadcrumb"] li, .breadcrumb li'
            );

            // MFR part number — sometimes in subtitle
            const mfrEl = getText('.pd__mpart, .mfr-part-number, [class*="mpart-num"]');

            return { title, price, inStock, desc, symptoms, crumbs, mfrEl };
        }""")

        name = clean_name(data["title"])
        if not name or "Error" in name:
            return None

        # Determine category from breadcrumbs
        crumbs_lower = " ".join(data["crumbs"]).lower()
        if "dishwasher" in crumbs_lower:
            inferred_category = "dishwasher"
        elif "refrigerator" in crumbs_lower or "fridge" in crumbs_lower:
            inferred_category = "refrigerator"
        else:
            inferred_category = category

        return {
            "id": url_meta["part_number"],
            "part_number": url_meta["part_number"],
            "manufacturer_part_number": url_meta.get("manufacturer_part_number"),
            "name": name,
            "description": data["desc"],
            "category": inferred_category,
            "brand": url_meta.get("brand", "").capitalize() or None,
            "price": data["price"],
            "in_stock": data["inStock"],
            "image_url": url_to_image_url(clean),
            "product_url": clean,
            "symptom_tags": data["symptoms"][:6],
            "model_numbers": compatible_models,
        }

    except PWTimeout:
        print(f"    Timeout on {url_meta.get('part_number', '?')}")
        return None
    except Exception as e:
        print(f"    Error on {url_meta.get('part_number', '?')}: {e}")
        return None


async def main():
    # Load existing scraped data so we can resume
    existing: dict[str, dict] = {}
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE) as f:
            for p in json.load(f):
                existing[p["part_number"]] = p
        print(f"Resuming — {len(existing)} parts already scraped")

    # Map: part_number → set of compatible models
    compat_map: dict[str, list[str]] = {
        k: list(v["model_numbers"]) for k, v in existing.items()
    }

    all_parts = dict(existing)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1280, "height": 800},
            locale="en-US",
        )
        await ctx.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        page = await ctx.new_page()

        targets = (
            [(m, "dishwasher") for m in DISHWASHER_MODELS]
            + [(m, "refrigerator") for m in REFRIGERATOR_MODELS]
        )

        # Step 1: collect all part URLs from model pages
        print("\n=== Step 1: Collecting part URLs from model pages ===")
        model_to_urls: dict[str, list[str]] = {}
        for model, category in targets:
            if len(all_parts) >= MAX_TOTAL_PARTS:
                break
            print(f"Scanning {category} model {model}...")
            urls = await get_part_urls_for_model(page, model, category)
            model_to_urls[model] = urls
            await asyncio.sleep(random.uniform(2, 4))

        # Build: url → list of models it appeared on
        url_to_models: dict[str, list[str]] = {}
        for model, urls in model_to_urls.items():
            for url in urls:
                pn_match = re.search(r"/PS(\d+)", url)
                if pn_match:
                    pn = f"PS{pn_match.group(1)}"
                    url_to_models.setdefault(url, [])
                    if model not in url_to_models[url]:
                        url_to_models[url].append(model)

        print(f"\nUnique part URLs to scrape: {len(url_to_models)}")

        # Step 2: scrape each part page
        print("\n=== Step 2: Scraping part pages ===")
        scraped_count = 0
        for url, models in url_to_models.items():
            if len(all_parts) >= MAX_TOTAL_PARTS:
                print(f"Reached {MAX_TOTAL_PARTS} parts — stopping.")
                break

            pn_match = re.search(r"/PS(\d+)", url)
            pn = f"PS{pn_match.group(1)}" if pn_match else None

            # Skip already scraped
            if pn and pn in all_parts:
                # Still merge any new compatible models
                existing_models = set(all_parts[pn]["model_numbers"])
                new_models = existing_models | set(models)
                all_parts[pn]["model_numbers"] = list(new_models)
                continue

            # Determine category from model category map
            cat = "refrigerator"
            for m in models:
                for tgt_model, tgt_cat in targets:
                    if tgt_model == m:
                        cat = tgt_cat
                        break

            print(f"  Scraping {pn} ({cat})...")
            part = await scrape_part(page, url, models, cat)

            if part is not None:
                all_parts[part["part_number"]] = part
                scraped_count += 1
                print(f"    ✓ {part['name'][:60]} | ${part['price']} | {len(part['model_numbers'])} models")

                # Save incrementally
                if scraped_count % 5 == 0:
                    with open(OUTPUT_FILE, "w") as f:
                        json.dump(list(all_parts.values()), f, indent=2)
                    print(f"    → Saved {len(all_parts)} parts to {OUTPUT_FILE}")
            else:
                print(f"    ✗ Failed to scrape")

            await asyncio.sleep(random.uniform(2, 5))

        await browser.close()

    # Final save
    parts_list = list(all_parts.values())
    with open(OUTPUT_FILE, "w") as f:
        json.dump(parts_list, f, indent=2)

    fridge = sum(1 for p in parts_list if p["category"] == "refrigerator")
    dish = sum(1 for p in parts_list if p["category"] == "dishwasher")
    total_compat = sum(len(p["model_numbers"]) for p in parts_list)
    print(f"\n✓ Done: {len(parts_list)} parts ({fridge} refrigerator, {dish} dishwasher)")
    print(f"  Total compatibility rows: {total_compat}")
    print(f"  Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
