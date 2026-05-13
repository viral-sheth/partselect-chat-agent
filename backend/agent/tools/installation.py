from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Product
from db.chroma_client import get_guides_collection, embed


async def get_installation_guide(
    part_number: str,
    model_number: Optional[str],
    db: AsyncSession,
) -> dict:
    pn = part_number.upper().replace(" ", "")
    collection = get_guides_collection()

    query = f"installation guide for part {pn}"
    if model_number:
        query += f" model {model_number}"

    embeddings = embed([query])

    try:
        results = collection.query(
            query_embeddings=embeddings,
            n_results=3,
            include=["documents", "metadatas"],
        )

        if results and results.get("documents") and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            combined_text = "\n\n".join(docs)

            return {
                "part_number": pn,
                "found": True,
                "guide_text": combined_text,
                "source_url": metas[0].get("source_url") if metas else None,
                "difficulty": metas[0].get("difficulty", "moderate") if metas else "moderate",
            }
    except Exception:
        pass

    # Fallback: return generic guidance from product description
    part_result = await db.execute(select(Product).where(Product.part_number == pn))
    part = part_result.scalar_one_or_none()

    if part:
        return {
            "part_number": pn,
            "found": False,
            "guide_text": (
                f"Specific installation guide for {pn} ({part.name}) is not available yet. "
                f"General steps: 1. Unplug the appliance. 2. Locate the part to be replaced. "
                f"3. Remove the old part carefully. 4. Install {part.name} in reverse order. "
                f"5. Restore power and test. For model-specific instructions, visit: {part.product_url}"
            ),
            "source_url": part.product_url,
            "difficulty": "moderate",
        }

    return {
        "part_number": pn,
        "found": False,
        "guide_text": f"Installation guide for part {pn} is not available. Please visit partselect.com for assistance.",
        "source_url": None,
        "difficulty": "unknown",
    }
