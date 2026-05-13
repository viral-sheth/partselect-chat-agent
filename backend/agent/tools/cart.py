from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from db.models import CartSession, Product


async def add_to_cart(
    part_number: str,
    quantity: int,
    session_id: str,
    db: AsyncSession,
) -> dict:
    pn = part_number.upper().replace(" ", "")

    # Fetch product details
    result = await db.execute(select(Product).where(Product.part_number == pn))
    product = result.scalar_one_or_none()

    if not product:
        return {
            "success": False,
            "message": f"Part {pn} not found in catalog.",
            "items": [],
            "subtotal": 0.0,
            "item_count": 0,
        }

    # Get or create cart
    cart_result = await db.execute(
        select(CartSession).where(CartSession.session_id == session_id)
    )
    cart = cart_result.scalar_one_or_none()

    if cart is None:
        cart = CartSession(session_id=session_id, items=[], updated_at=datetime.utcnow())
        db.add(cart)

    items = list(cart.items or [])

    # Check if already in cart
    existing = next((item for item in items if item["part_number"] == pn), None)
    if existing:
        existing["quantity"] += quantity
    else:
        items.append({
            "part_number": pn,
            "name": product.name,
            "price": product.price,
            "quantity": quantity,
            "image_url": product.image_url,
        })

    cart.items = items
    cart.updated_at = datetime.utcnow()
    await db.commit()

    subtotal = sum((i["price"] or 0) * i["quantity"] for i in items)

    return {
        "success": True,
        "message": f"Added {product.name} (x{quantity}) to your cart.",
        "items": items,
        "subtotal": round(subtotal, 2),
        "item_count": sum(i["quantity"] for i in items),
    }


async def get_cart(session_id: str, db: AsyncSession) -> dict:
    result = await db.execute(
        select(CartSession).where(CartSession.session_id == session_id)
    )
    cart = result.scalar_one_or_none()

    if not cart or not cart.items:
        return {
            "success": True,
            "message": "Your cart is empty.",
            "items": [],
            "subtotal": 0.0,
            "item_count": 0,
        }

    subtotal = sum((i["price"] or 0) * i["quantity"] for i in cart.items)

    return {
        "success": True,
        "message": f"You have {len(cart.items)} item(s) in your cart.",
        "items": cart.items,
        "subtotal": round(subtotal, 2),
        "item_count": sum(i["quantity"] for i in cart.items),
    }
