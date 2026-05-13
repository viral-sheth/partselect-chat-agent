from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Order


async def get_order_status(
    order_number: str,
    email: str,
    db: AsyncSession,
) -> dict:
    result = await db.execute(
        select(Order).where(
            Order.order_number == order_number.upper(),
            Order.email == email.lower(),
        )
    )
    order = result.scalar_one_or_none()

    if not order:
        return {
            "found": False,
            "message": (
                f"No order found with order number {order_number} and that email address. "
                "Please double-check your order number and the email used at checkout."
            ),
        }

    return {
        "found": True,
        "order_number": order.order_number,
        "status": order.status,
        "estimated_delivery": order.estimated_delivery,
        "tracking_url": order.tracking_url,
        "items": order.items or [],
        "total": order.total,
    }
