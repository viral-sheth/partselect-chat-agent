import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from .search import search_products
from .compatibility import check_compatibility
from .installation import get_installation_guide
from .troubleshooting import get_troubleshooting
from .cart import add_to_cart, get_cart
from .orders import get_order_status


async def execute_tool(
    tool_name: str,
    tool_input: dict,
    db: AsyncSession,
    session_id: str,
) -> dict:
    """Dispatch a tool call to the correct implementation."""
    if tool_name == "search_products":
        brand = tool_input.get("brand") or None  # treat empty string as None
        return await search_products(
            query=tool_input["query"],
            category=tool_input.get("category", "any"),
            brand=brand,
            db=db,
        )
    elif tool_name == "check_compatibility":
        return await check_compatibility(
            part_number=tool_input["part_number"],
            model_number=tool_input["model_number"],
            db=db,
        )
    elif tool_name == "get_installation_guide":
        return await get_installation_guide(
            part_number=tool_input["part_number"],
            model_number=tool_input.get("model_number"),
            db=db,
        )
    elif tool_name == "get_troubleshooting":
        return await get_troubleshooting(
            symptom=tool_input["symptom"],
            appliance_type=tool_input["appliance_type"],
            brand=tool_input.get("brand"),
            db=db,
        )
    elif tool_name == "add_to_cart":
        raw_qty = tool_input.get("quantity", 1)
        return await add_to_cart(
            part_number=tool_input["part_number"],
            quantity=int(raw_qty) if raw_qty is not None else 1,
            session_id=session_id,
            db=db,
        )
    elif tool_name == "get_cart":
        return await get_cart(
            session_id=tool_input.get("session_id", session_id),
            db=db,
        )
    elif tool_name == "get_order_status":
        return await get_order_status(
            order_number=tool_input["order_number"],
            email=tool_input["email"],
            db=db,
        )
    else:
        return {"error": f"Unknown tool: {tool_name}"}
