"""
Ingest scraped part data into SQLite (via SQLAlchemy) and ChromaDB.

Usage:
    python scraper/ingest.py --file scraper/data/refrigerator_parts.json
    python scraper/ingest.py --file scraper/data/dishwasher_parts.json
"""
import asyncio
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from db.models import Base, Product, ModelCompatibility
from db.chroma_client import get_products_collection, embed
from config import get_settings

settings = get_settings()


async def ingest_to_sqlite(parts: list[dict], engine):
    AsyncSession = async_sessionmaker(engine, expire_on_commit=False)

    async with AsyncSession() as session:
        for part in parts:
            # Upsert product
            existing = await session.get(Product, part["id"])
            if existing is None:
                product = Product(
                    id=part["id"],
                    part_number=part["part_number"],
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

            # Model compatibility rows
            for model_num in part.get("model_numbers", []):
                if model_num and len(model_num) > 3:
                    compat = ModelCompatibility(
                        part_number=part["part_number"],
                        model_number=model_num.upper(),
                    )
                    session.merge(compat)

        await session.commit()
        print(f"Saved {len(parts)} products to SQLite")


def ingest_to_chroma(parts: list[dict]):
    collection = get_products_collection()

    # Build documents to embed
    ids = []
    texts = []
    metadatas = []

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

    # Embed in batches of 50
    batch_size = 50
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i+batch_size]
        batch_texts = texts[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]

        embeddings = embed(batch_texts)
        collection.upsert(
            ids=batch_ids,
            embeddings=embeddings,
            documents=batch_texts,
            metadatas=batch_metas,
        )
        print(f"  Embedded batch {i//batch_size + 1} ({len(batch_ids)} parts)")

    print(f"Upserted {len(ids)} parts to ChromaDB")


async def main(file_path: str):
    data_file = Path(file_path)
    if not data_file.exists():
        print(f"File not found: {file_path}")
        return

    with open(data_file) as f:
        parts = json.load(f)

    print(f"Loading {len(parts)} parts from {file_path}")

    engine = create_async_engine(settings.database_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await ingest_to_sqlite(parts, engine)
    await engine.dispose()

    ingest_to_chroma(parts)
    print("Ingestion complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Path to scraped JSON file")
    args = parser.parse_args()
    asyncio.run(main(args.file))
