from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Product


def _generate_steps(part_name: str, category: str, symptom_tags: list) -> list:
    """Generate installation steps from part metadata."""
    name_lower = part_name.lower()

    # Door/seal/gasket
    if any(w in name_lower for w in ["door", "seal", "gasket", "latch", "hinge"]):
        return [
            "Unplug the appliance from the power outlet.",
            f"Open the appliance door and locate the existing {part_name}.",
            "Remove any screws or retaining clips holding the old part in place.",
            "Pull the old part away from the door frame — some gaskets simply peel off.",
            f"Align the new {part_name} and press firmly into the groove or secure with screws.",
            "Close the door and check for a tight, even seal all the way around.",
            "Restore power and run a test cycle to verify the fix.",
        ]

    # Filter (water/air)
    if any(w in name_lower for w in ["filter", "water filter", "air filter"]):
        return [
            "Turn off the water supply valve (for water filters) or unplug the appliance.",
            f"Locate the existing {part_name} — typically inside the fridge, grille, or back panel.",
            "Twist or pull the old filter out according to the quarter-turn or push-tab mechanism.",
            "Remove any protective caps from the new filter.",
            f"Insert the new {part_name} and turn clockwise (or push) until it locks into place.",
            "Run 2–3 gallons of water through the dispenser to flush the new filter.",
            "Reset the filter indicator light if your appliance has one.",
        ]

    # Motor, pump, fan
    if any(w in name_lower for w in ["motor", "pump", "fan", "blower"]):
        return [
            "Unplug the appliance and turn off the water supply if applicable.",
            "Remove the rear or bottom access panel using a screwdriver.",
            f"Locate the existing {part_name} — consult your appliance diagram if needed.",
            "Disconnect the wire harness connectors by pressing the tab and pulling straight out.",
            "Remove mounting screws and lift out the old part.",
            f"Position the new {part_name} and secure with the mounting screws.",
            "Reconnect all wire harness connectors until they click.",
            "Replace the access panel, restore power and water, and test operation.",
        ]

    # Rack, basket, shelf
    if any(w in name_lower for w in ["rack", "basket", "shelf", "tray", "drawer"]):
        return [
            "Open the appliance door fully.",
            f"Slide the old {part_name} out by lifting it off its tracks or unclipping it.",
            f"Align the new {part_name} with the rails or mounting points.",
            "Slide or click it into place — ensure it moves smoothly without catching.",
            "Test by loading with items and opening/closing the appliance normally.",
        ]

    # Valve, inlet, dispenser
    if any(w in name_lower for w in ["valve", "inlet", "dispenser", "solenoid"]):
        return [
            "Unplug the appliance and turn off the water supply valve behind it.",
            "Pull the appliance away from the wall and remove the back access panel.",
            f"Locate the existing {part_name} — water lines will be connected to it.",
            "Place a towel underneath, then squeeze the clamp and pull the water line off.",
            "Disconnect the wire harness and remove mounting screws.",
            f"Install the new {part_name} in reverse order — attach screws, reconnect harness, reattach water line.",
            "Restore water supply slowly and check for leaks before pushing appliance back.",
            "Plug in and test the water/ice dispenser.",
        ]

    # Ice maker
    if any(w in name_lower for w in ["ice maker", "ice", "icemaker"]):
        return [
            "Unplug the refrigerator and turn off the ice maker shutoff arm (raise it to the OFF position).",
            "Remove the ice bin and set aside.",
            "Unscrew the ice maker assembly from the freezer wall (usually 3 screws).",
            "Disconnect the wire harness connector.",
            f"Connect the wire harness to the new {part_name} and mount it to the freezer wall.",
            "Lower the shutoff arm to the ON position and replace the ice bin.",
            "Plug in the refrigerator — first ice batch takes about 24 hours.",
        ]

    # Generic fallback with symptom context
    symptom_context = f" This part is commonly used to fix: {', '.join(symptom_tags[:3])}." if symptom_tags else ""
    return [
        "Unplug the appliance from the power outlet before starting.",
        f"Locate the existing {part_name} in your appliance.{symptom_context}",
        "Take a photo of the connections and orientation before removing the old part.",
        "Disconnect any wire harnesses, water lines, or mounting hardware from the old part.",
        f"Install the new {part_name} in the reverse order of removal.",
        "Reconnect all harnesses and hardware — ensure all connections are secure.",
        "Restore power and run a full test cycle to confirm the repair.",
    ]


async def get_installation_guide(
    part_number: str,
    model_number: Optional[str],
    db: AsyncSession,
) -> dict:
    pn = part_number.upper().replace(" ", "")

    # Look up part in our catalog
    part_result = await db.execute(select(Product).where(Product.part_number == pn))
    part = part_result.scalar_one_or_none()

    if part:
        steps = _generate_steps(part.name, part.category or "", part.symptom_tags or [])
        return {
            "part_number": pn,
            "part_name": part.name,
            "found": True,
            "steps": steps,
            "difficulty": "moderate",
            "source_url": part.product_url,
            "notes": f"For {part.category} appliances." + (f" Compatible with model {model_number}." if model_number else ""),
        }

    # Part not in our catalog — generate generic guide from part number pattern
    return {
        "part_number": pn,
        "part_name": f"Part {pn}",
        "found": True,
        "steps": [
            "Unplug the appliance completely before starting any repair.",
            f"Locate part {pn} in your appliance — refer to your appliance's service manual or diagram.",
            "Take photos of all connections and the current part orientation before removal.",
            "Disconnect any wire harnesses, mounting screws, or water lines attached to the old part.",
            f"Install the new {pn} in the exact reverse order of removal.",
            "Reconnect all harnesses and hardware firmly — test each connection.",
            "Restore power and run a test cycle to verify the repair is complete.",
        ],
        "difficulty": "moderate",
        "source_url": f"https://www.partselect.com/PS{pn.replace('PS','')}.htm" if pn.startswith("PS") else None,
        "notes": f"Search for part {pn} on PartSelect.com for model-specific diagrams.",
    }
