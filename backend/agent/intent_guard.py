from groq import AsyncGroq
from config import get_settings

settings = get_settings()

ALLOWED_INTENTS = {
    "product", "compatibility", "installation",
    "troubleshooting", "order", "cart", "greeting", "continuation"
}

# Short messages that are always conversational continuations — never off-topic
CONTINUATION_PHRASES = {
    "yes", "no", "ok", "okay", "sure", "please", "thanks", "thank you",
    "yep", "nope", "yeah", "nah", "add it", "add to cart", "show me",
    "show the products", "show products", "go ahead", "do it", "sounds good",
    "what else", "anything else", "that's all", "perfect", "great", "got it",
    "correct", "right", "exactly", "maybe", "not sure", "i don't know",
}

GUARD_PROMPT = """You are classifying whether a user message is relevant to an appliance parts assistant.
The assistant helps with: refrigerator parts, dishwasher parts, appliance repair, part compatibility,
installation instructions, cart, and orders.

Classify the message as ONE of:
- product: searching for parts or products
- compatibility: checking if a part works with a model
- installation: asking how to install a part
- troubleshooting: appliance not working, diagnosing problems
- order: asking about an existing order
- cart: adding/viewing cart items
- greeting: hello, hi, general polite opener
- continuation: short reply continuing a conversation (yes, no, sure, show me, add it, etc.)
- off_topic: clearly unrelated (cooking recipes, weather, sports, general tech help, etc.)

When in doubt, choose the closest appliance-related category rather than off_topic.
Respond with ONLY the category word, nothing else."""

_client = None


def get_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=settings.groq_api_key)
    return _client


async def classify_intent(message: str, history: list = None) -> str:
    normalized = message.strip().lower().rstrip("!.,?")

    # Bypass LLM for known continuation phrases
    if normalized in CONTINUATION_PHRASES:
        return "continuation"

    # Bypass LLM for very short messages (≤3 words) when there's prior history
    words = normalized.split()
    if len(words) <= 3 and history:
        return "continuation"

    client = get_client()
    messages = [{"role": "system", "content": GUARD_PROMPT}]

    # Add last 2 turns of history as context so the guard can judge continuations
    if history:
        for turn in history[-4:]:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if isinstance(content, str) and content:
                messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": message})

    response = await client.chat.completions.create(
        model=settings.groq_model,
        max_tokens=10,
        messages=messages,
    )
    intent = response.choices[0].message.content.strip().lower()
    return intent if intent in ALLOWED_INTENTS else "off_topic"


OFF_TOPIC_RESPONSE = (
    "I can only help with refrigerator and dishwasher parts and repairs. "
    "Is there something I can help you find?"
)
