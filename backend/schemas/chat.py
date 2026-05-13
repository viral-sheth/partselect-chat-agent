from typing import Optional, List, Any
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ChatResponse(BaseModel):
    session_id: str
    message: str


class ProductResult(BaseModel):
    part_number: str
    name: str
    price: Optional[float]
    image_url: Optional[str]
    product_url: Optional[str]
    in_stock: bool
    brand: Optional[str]
    category: str
    description: Optional[str]


class CompatibilityResult(BaseModel):
    part_number: str
    model_number: str
    is_compatible: bool
    notes: str
    alternative_parts: List[str] = []


class InstallationGuide(BaseModel):
    part_number: str
    steps: List[str]
    difficulty: str
    tools_required: List[str]
    source_url: Optional[str]


class TroubleshootingResult(BaseModel):
    symptom: str
    likely_causes: List[str]
    recommended_parts: List[ProductResult]
    repair_tips: List[str]


class CartItem(BaseModel):
    part_number: str
    name: str
    price: Optional[float]
    quantity: int
    image_url: Optional[str]


class CartResult(BaseModel):
    success: bool
    message: str
    items: List[CartItem] = []
    subtotal: float = 0.0
    item_count: int = 0


class OrderStatus(BaseModel):
    order_number: str
    status: str
    estimated_delivery: Optional[str]
    tracking_url: Optional[str]
    items: List[dict] = []
