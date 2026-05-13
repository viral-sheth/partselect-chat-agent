"""
PartSelect part scraper using Playwright.
Scrapes Refrigerator and Dishwasher parts and saves to SQLite + ChromaDB.

Usage:
    python scraper/scrape_parts.py --category refrigerator --max-parts 200
    python scraper/scrape_parts.py --category dishwasher --max-parts 200
"""
import asyncio
import argparse
import json
import re
import sys
import os
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

BASE_URL = "https://www.partselect.com"
CATEGORY_URLS = {
    "refrigerator": f"{BASE_URL}/Refrigerator-Parts.htm",
    "dishwasher": f"{BASE_URL}/Dishwasher-Parts.htm",
}


def normalize_part_number(text: str) -> str:
    match = re.search(r"PS\d+", text, re.IGNORECASE)
    return match.group(0).upper() if match else ""


def parse_price(text: str) -> float | None:
    match = re.search(r"\$?([\d,]+\.?\d*)", text.replace(",", ""))
    return float(match.group(1)) if match else None


async def scrape_part_page(page, url: str, category: str) -> dict | None:
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(1)
        html = await page.content()
        soup = BeautifulSoup(html, "lxml")

        # Part number
        pn_el = soup.find("span", {"itemprop": "productID"}) or soup.find(
            "span", class_=re.compile(r"part.?number", re.I)
        )
        part_number = ""
        if pn_el:
            part_number = normalize_part_number(pn_el.get_text())

        if not part_number:
            # Try from URL
            match = re.search(r"PS(\d+)", url, re.I)
            part_number = f"PS{match.group(1)}" if match else ""

        if not part_number:
            return None

        # Name
        name_el = soup.find("h1", {"itemprop": "name"}) or soup.find("h1")
        name = name_el.get_text(strip=True) if name_el else "Unknown Part"

        # Description
        desc_el = soup.find("div", {"itemprop": "description"}) or soup.find(
            "div", class_=re.compile(r"description", re.I)
        )
        description = desc_el.get_text(strip=True)[:1000] if desc_el else ""

        # Price
        price_el = soup.find("span", {"itemprop": "price"}) or soup.find(
            "span", class_=re.compile(r"price", re.I)
        )
        price = None
        if price_el:
            price = parse_price(price_el.get("content", "") or price_el.get_text())

        # Image
        img_el = soup.find("img", {"itemprop": "image"}) or soup.find(
            "img", class_=re.compile(r"product.?image", re.I)
        )
        image_url = img_el.get("src", "") if img_el else ""
        if image_url and not image_url.startswith("http"):
            image_url = BASE_URL + image_url

        # Brand
        brand_el = soup.find("span", {"itemprop": "brand"}) or soup.find(
            "a", class_=re.compile(r"brand", re.I)
        )
        brand = brand_el.get_text(strip=True).lower() if brand_el else ""

        # Compatible models
        model_section = soup.find(
            "div", class_=re.compile(r"compatible|fits.?model", re.I)
        ) or soup.find("section", class_=re.compile(r"model", re.I))

        model_numbers = []
        if model_section:
            model_links = model_section.find_all("a", href=re.compile(r"model", re.I))
            for link in model_links[:100]:
                text = link.get_text(strip=True)
                if text and len(text) > 3:
                    model_numbers.append(text.upper())

        # Symptom tags (fixes X, Y, Z)
        symptom_tags = []
        fixes_section = soup.find(
            "div", class_=re.compile(r"symptom|fixes|repair", re.I)
        )
        if fixes_section:
            tags = fixes_section.find_all(["li", "span", "a"])
            for tag in tags[:10]:
                text = tag.get_text(strip=True)
                if text and len(text) > 5:
                    symptom_tags.append(text.lower())

        in_stock_el = soup.find("span", {"itemprop": "availability"})
        in_stock = True
        if in_stock_el:
            in_stock = "InStock" in in_stock_el.get("content", "InStock")

        return {
            "id": str(uuid.uuid4()),
            "part_number": part_number,
            "name": name,
            "description": description,
            "category": category,
            "brand": brand,
            "price": price,
            "in_stock": in_stock,
            "image_url": image_url,
            "product_url": url,
            "symptom_tags": symptom_tags,
            "model_numbers": model_numbers,
        }

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


async def get_part_urls(page, category: str, max_parts: int) -> list[str]:
    url = CATEGORY_URLS[category]
    urls = []

    print(f"Crawling {url}...")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)

        # Scroll to load more
        for _ in range(3):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)

        html = await page.content()
        soup = BeautifulSoup(html, "lxml")

        # Find part links — PartSelect URLs contain PS{number}
        links = soup.find_all("a", href=re.compile(r"/PS\d+", re.I))
        for link in links:
            href = link.get("href", "")
            if href and ".htm" in href:
                full_url = BASE_URL + href if href.startswith("/") else href
                if full_url not in urls:
                    urls.append(full_url)
                    if len(urls) >= max_parts:
                        break

    except Exception as e:
        print(f"Error getting URLs: {e}")

    print(f"Found {len(urls)} part URLs")
    return urls


async def main(category: str, max_parts: int):
    output_dir = Path(__file__).parent / "data"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"{category}_parts.json"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        part_urls = await get_part_urls(page, category, max_parts)

        parts = []
        for i, url in enumerate(part_urls):
            print(f"[{i+1}/{len(part_urls)}] Scraping {url}")
            part = await scrape_part_page(page, url, category)
            if part:
                parts.append(part)
                print(f"  ✓ {part['part_number']} — {part['name'][:60]}")
            await asyncio.sleep(1.2)  # polite delay

        await browser.close()

    with open(output_file, "w") as f:
        json.dump(parts, f, indent=2)

    print(f"\nSaved {len(parts)} parts to {output_file}")
    return parts


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", choices=["refrigerator", "dishwasher"], required=True)
    parser.add_argument("--max-parts", type=int, default=100)
    args = parser.parse_args()
    asyncio.run(main(args.category, args.max_parts))
