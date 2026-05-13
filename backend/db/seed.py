"""
Seed the database and ChromaDB from scraped_parts.json.
Only runs if the products table is empty — safe to call on every startup.
"""
import json
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Product, ModelCompatibility
from db.chroma_client import get_products_collection, embed

DATA_FILE = Path(__file__).parent.parent / "data" / "scraped_parts.json"


async def seed_if_empty(db: AsyncSession) -> None:
    # Check if already seeded
    result = await db.execute(select(func.count()).select_from(Product))
    count = result.scalar()
    if count and count > 0:
        print(f"[seed] {count} products already in DB — skipping seed")
        return

    if not DATA_FILE.exists():
        print(f"[seed] {DATA_FILE} not found — skipping seed")
        return

    with open(DATA_FILE) as f:
        parts = json.load(f)

    print(f"[seed] Seeding {len(parts)} parts into SQLite + ChromaDB...")

    products_to_add = []
    compat_rows = []
    chroma_ids = []
    chroma_docs = []
    chroma_metas = []

    for p in parts:
        part_number = p.get("part_number") or p.get("id")
        if not part_number:
            continue

        product = Product(
            id=p.get("id", part_number),
            part_number=part_number,
            manufacturer_part_number=p.get("manufacturer_part_number"),
            name=p.get("name", ""),
            description=p.get("description"),
            category=p.get("category", "refrigerator"),
            brand=p.get("brand"),
            price=p.get("price"),
            in_stock=p.get("in_stock", True),
            image_url=p.get("image_url"),
            product_url=p.get("product_url"),
            symptom_tags=p.get("symptom_tags", []),
            scraped_at=datetime.utcnow(),
        )
        products_to_add.append(product)

        for model_num in p.get("model_numbers", []):
            compat_rows.append(
                ModelCompatibility(
                    part_number=part_number,
                    model_number=model_num,
                )
            )

        # Build ChromaDB document
        tags = " ".join(p.get("symptom_tags", []))
        doc = f"{p.get('name', '')} {p.get('description', '') or ''} {tags}".strip()
        chroma_ids.append(part_number)
        chroma_docs.append(doc)
        chroma_metas.append({
            "part_number": part_number,
            "category": p.get("category", "refrigerator"),
            "brand": (p.get("brand") or "").lower(),
        })

    db.add_all(products_to_add)
    db.add_all(compat_rows)
    await db.commit()
    print(f"[seed] SQLite: {len(products_to_add)} products, {len(compat_rows)} compatibility rows inserted")

    # Seed ChromaDB in batches
    collection = get_products_collection()
    existing = collection.count()
    if existing == 0:
        batch_size = 32
        for start in range(0, len(chroma_ids), batch_size):
            batch_ids = chroma_ids[start:start + batch_size]
            batch_docs = chroma_docs[start:start + batch_size]
            batch_metas = chroma_metas[start:start + batch_size]
            embeddings = embed(batch_docs)
            collection.add(
                ids=batch_ids,
                embeddings=embeddings,
                documents=batch_docs,
                metadatas=batch_metas,
            )
        print(f"[seed] ChromaDB: {len(chroma_ids)} vectors inserted")
    else:
        print(f"[seed] ChromaDB already has {existing} vectors — skipping")
