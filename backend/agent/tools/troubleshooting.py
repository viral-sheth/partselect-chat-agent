from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Product
from db.chroma_client import get_products_collection, embed


async def get_troubleshooting(
    symptom: str,
    appliance_type: str,
    brand: Optional[str],
    db: AsyncSession,
) -> dict:
    collection = get_products_collection()

    query = f"{appliance_type} {symptom}"
    if brand:
        query = f"{brand} {query}"

    where_filter = {"category": appliance_type}

    embeddings = embed([query])

    part_numbers = []
    try:
        results = collection.query(
            query_embeddings=embeddings,
            n_results=5,
            where=where_filter,
            include=["metadatas", "distances"],
        )
        if results and results.get("metadatas") and results["metadatas"][0]:
            part_numbers = [m["part_number"] for m in results["metadatas"][0]]
    except Exception:
        pass

    recommended_parts = []
    if part_numbers:
        stmt = select(Product).where(Product.part_number.in_(part_numbers))
        db_results = await db.execute(stmt)
        products = db_results.scalars().all()
        recommended_parts = [
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
            for p in products
        ]

    causes_map = {
        "ice maker": [
            "Faulty ice maker assembly",
            "Clogged water inlet valve",
            "Defective water filter",
            "Ice maker shut-off arm in off position",
        ],
        "not cooling": [
            "Dirty condenser coils",
            "Faulty evaporator fan motor",
            "Defective compressor start relay",
            "Refrigerant leak",
        ],
        "leaking": [
            "Clogged defrost drain",
            "Faulty door gasket/seal",
            "Cracked drain pan",
            "Water inlet valve leak",
        ],
        "not draining": [
            "Clogged drain hose",
            "Faulty drain pump",
            "Blocked drain filter",
            "Garbage disposal knockout not removed",
        ],
        "not cleaning": [
            "Clogged spray arms",
            "Faulty wash pump",
            "Low water temperature",
            "Blocked filter assembly",
        ],
        "noisy": [
            "Worn wash arm bearing",
            "Faulty circulation pump",
            "Foreign object in pump",
            "Loose spray arm",
        ],
    }

    likely_causes = ["Component wear or failure", "Blocked or clogged parts"]
    for keyword, causes in causes_map.items():
        if keyword in symptom.lower():
            likely_causes = causes
            break

    tips_map = {
        "ice maker": [
            "Check that the ice maker power switch is turned ON",
            "Verify the freezer temperature is set to 0°F (-18°C)",
            "Replace water filter if it hasn't been changed in 6 months",
            "Check for kinked water supply line",
        ],
        "not cooling": [
            "Clean condenser coils (usually located at back or bottom of fridge)",
            "Ensure proper ventilation around the refrigerator",
            "Check door seals for tears or gaps",
            "Verify thermostat settings",
        ],
        "not draining": [
            "Check and clean the dishwasher filter",
            "Inspect the drain hose for kinks or clogs",
            "Run garbage disposal before starting dishwasher",
            "Check drain pump for obstructions",
        ],
    }

    repair_tips = ["Unplug appliance before any repair", "Document the disassembly with photos"]
    for keyword, tips in tips_map.items():
        if keyword in symptom.lower():
            repair_tips = tips
            break

    return {
        "symptom": symptom,
        "appliance_type": appliance_type,
        "likely_causes": likely_causes,
        "recommended_parts": recommended_parts,
        "repair_tips": repair_tips,
    }
