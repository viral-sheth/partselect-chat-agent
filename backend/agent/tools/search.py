from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Product
from db.chroma_client import get_products_collection, embed


async def search_products(
    query: str,
    category: str,
    brand: Optional[str],
    db: AsyncSession,
) -> dict:
    collection = get_products_collection()

    where_filter = {}
    if category != "any":
        where_filter["category"] = category
    if brand:
        where_filter["brand"] = {"$eq": brand.lower()}

    embeddings = embed([query])
    results = collection.query(
        query_embeddings=embeddings,
        n_results=5,
        where=where_filter if where_filter else None,
        include=["metadatas", "distances"],
    )

    part_numbers = []
    if results and results.get("metadatas") and results["metadatas"][0]:
        part_numbers = [m["part_number"] for m in results["metadatas"][0]]

    if not part_numbers:
        return {"products": [], "total": 0}

    stmt = select(Product).where(Product.part_number.in_(part_numbers))
    db_results = await db.execute(stmt)
    products = db_results.scalars().all()

    product_map = {p.part_number: p for p in products}
    ordered = [product_map[pn] for pn in part_numbers if pn in product_map]

    return {
        "products": [
            {
                "part_number": p.part_number,
                "name": p.name,
                "price": p.price,
                "image_url": p.image_url,
                "product_url": p.product_url,
                "in_stock": p.in_stock,
                "brand": p.brand,
                "category": p.category,
                "description": p.description[:300] if p.description else None,
            }
            for p in ordered
        ],
        "total": len(ordered),
    }
