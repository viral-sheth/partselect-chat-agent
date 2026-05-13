"""
Seed the database with curated PartSelect parts data.
Populates both SQLite and ChromaDB.

Usage:
    python scraper/seed.py
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, delete
from db.models import Base, Product, ModelCompatibility
from db.chroma_client import get_products_collection, embed
from config import get_settings

settings = get_settings()
DATA_FILE = Path(__file__).parent / "seed_data.json"


async def ingest_sqlite(parts: list, engine):
    AsyncSession = async_sessionmaker(engine, expire_on_commit=False)
    async with AsyncSession() as session:
        # Clear existing compatibility rows and re-insert cleanly
        await session.execute(delete(ModelCompatibility))
        await session.commit()

        prod_inserted = 0
        compat_inserted = 0

        for part in parts:
            # Upsert product
            existing = await session.get(Product, part["id"])
            if not existing:
                product = Product(
                    id=part["id"],
                    part_number=part["part_number"],
                    manufacturer_part_number=part.get("manufacturer_part_number"),
                    name=part["name"],
                    description=part.get("description"),
                    category=part["category"],
                    brand=part.get("brand"),
                    price=part.get("price"),
                    in_stock=part.get("in_stock", True),
                    image_url=part.get("image_url"),
                    product_url=part.get("product_url"),
                    symptom_tags=part.get("symptom_tags", []),
                )
                session.add(product)
                prod_inserted += 1

            # Always insert compatibility rows
            for model_num in part.get("model_numbers", []):
                if model_num:
                    session.add(ModelCompatibility(
                        part_number=part["part_number"],
                        model_number=model_num.upper(),
                    ))
                    compat_inserted += 1

        await session.commit()
        print(f"SQLite: {prod_inserted} new products, {compat_inserted} compatibility rows")


def ingest_chroma(parts: list):
    collection = get_products_collection()

    ids, texts, metadatas = [], [], []
    for part in parts:
        text = f"{part['name']}. {part.get('description', '')}. "
        if part.get("symptom_tags"):
            text += "Fixes: " + ", ".join(part["symptom_tags"]) + ". "
        if part.get("brand"):
            text += f"Brand: {part['brand']}."

        ids.append(part["part_number"])
        texts.append(text[:1000])
        metadatas.append({
            "part_number": part["part_number"],
            "category": part["category"],
            "brand": part.get("brand", ""),
            "in_stock": str(part.get("in_stock", True)),
            "price": str(part.get("price", "")),
        })

    if not ids:
        return

    batch_size = 32
    for i in range(0, len(ids), batch_size):
        b_ids = ids[i:i+batch_size]
        b_texts = texts[i:i+batch_size]
        b_metas = metadatas[i:i+batch_size]
        embeddings = embed(b_texts)
        collection.upsert(ids=b_ids, embeddings=embeddings, documents=b_texts, metadatas=b_metas)
        print(f"ChromaDB: embedded batch {i//batch_size + 1} ({len(b_ids)} parts)")

    print(f"ChromaDB: upserted {len(ids)} parts total")


async def main():
    print(f"Loading seed data from {DATA_FILE}")
    with open(DATA_FILE) as f:
        parts = json.load(f)

    refrigerator = sum(1 for p in parts if p["category"] == "refrigerator")
    dishwasher = sum(1 for p in parts if p["category"] == "dishwasher")
    print(f"Found {len(parts)} parts ({refrigerator} refrigerator, {dishwasher} dishwasher)")

    engine = create_async_engine(settings.database_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("\n--- SQLite ---")
    await ingest_sqlite(parts, engine)
    await engine.dispose()

    print("\n--- ChromaDB ---")
    ingest_chroma(parts)

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
