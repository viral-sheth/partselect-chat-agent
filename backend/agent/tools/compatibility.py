import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import ModelCompatibility, Product


def normalize_part_number(pn: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "", pn).upper()


def normalize_model_number(mn: str) -> str:
    return re.sub(r"\s+", "", mn).upper()


async def check_compatibility(
    part_number: str,
    model_number: str,
    db: AsyncSession,
) -> dict:
    pn = normalize_part_number(part_number)
    mn = normalize_model_number(model_number)

    # Exact match
    result = await db.execute(
        select(ModelCompatibility).where(
            ModelCompatibility.part_number == pn,
            ModelCompatibility.model_number == mn,
        )
    )
    exact = result.scalar_one_or_none()

    if exact:
        return {
            "part_number": pn,
            "model_number": mn,
            "is_compatible": True,
            "notes": f"Part {pn} is confirmed compatible with model {mn}.",
            "alternative_parts": [],
        }

    # Fuzzy: try prefix match on model number (e.g., WDT780SAEM matches WDT780SAEM1)
    fuzzy_result = await db.execute(
        select(ModelCompatibility).where(
            ModelCompatibility.part_number == pn,
            ModelCompatibility.model_number.like(f"{mn[:8]}%"),
        )
    )
    fuzzy = fuzzy_result.scalars().all()

    if fuzzy:
        close_models = [row.model_number for row in fuzzy[:3]]
        return {
            "part_number": pn,
            "model_number": mn,
            "is_compatible": False,
            "notes": (
                f"Exact match not found for model {mn}, but part {pn} is compatible with "
                f"similar models: {', '.join(close_models)}. "
                "Please verify your full model number."
            ),
            "alternative_parts": [],
        }

    # Check if part exists at all
    part_result = await db.execute(
        select(Product).where(Product.part_number == pn)
    )
    part = part_result.scalar_one_or_none()

    if not part:
        return {
            "part_number": pn,
            "model_number": mn,
            "is_compatible": False,
            "notes": f"Part number {pn} was not found in our catalog.",
            "alternative_parts": [],
        }

    return {
        "part_number": pn,
        "model_number": mn,
        "is_compatible": False,
        "notes": (
            f"Part {pn} does not appear to be compatible with model {mn}. "
            "This part may be designed for a different model series."
        ),
        "alternative_parts": [],
    }
