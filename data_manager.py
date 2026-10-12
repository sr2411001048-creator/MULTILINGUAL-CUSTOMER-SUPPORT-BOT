"""
data_manager.py
Handles reading and writing to shop_data.json and logging interactions to conversations.json.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List

SHOP_DATA_FILE = os.path.join(os.path.dirname(__file__), "shop_data.json")
CONVERSATIONS_FILE = os.path.join(os.path.dirname(__file__), "conversations.json")


def load_shop_data() -> Dict[str, Any]:
    """Load the shop data from shop_data.json safely."""
    if not os.path.exists(SHOP_DATA_FILE):
        return {
            "shop_info": {},
            "products": [],
            "faqs": []
        }
    try:
        with open(SHOP_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading shop_data.json: {e}")
        return {"shop_info": {}, "products": [], "faqs": []}


def save_shop_data(data: Dict[str, Any]) -> bool:
    """Save updated shop data to shop_data.json."""
    try:
        with open(SHOP_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving shop_data.json: {e}")
        return False


def get_conversations() -> List[Dict[str, Any]]:
    """Retrieve all logged conversations."""
    if not os.path.exists(CONVERSATIONS_FILE):
        return []
    try:
        with open(CONVERSATIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error reading conversations.json: {e}")
        return []


def log_conversation(
    question: str,
    answer: str,
    language: str,
    input_type: str = "text",
    contact_owner_suggested: bool = False
) -> bool:
    """
    Log a customer query and the chatbot answer to conversations.json.
    """
    try:
        conversations = get_conversations()
        entry = {
            "id": len(conversations) + 1,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "question": question,
            "answer": answer,
            "language": language,
            "input_type": input_type,
            "contact_owner_suggested": contact_owner_suggested
        }
        conversations.append(entry)

        with open(CONVERSATIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(conversations, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error logging conversation: {e}")
        return False


def build_shop_context_string() -> str:
    """
    Format shop data into a structured textual context for the LLM system prompt.
    """
    data = load_shop_data()
    shop_info = data.get("shop_info", {})
    products = data.get("products", [])
    faqs = data.get("faqs", [])

    lines = []
    lines.append(f"SHOP NAME: {shop_info.get('name', 'Local Shop')}")
    lines.append(f"OWNER NAME: {shop_info.get('owner_name', '')}")
    lines.append(f"PHONE: {shop_info.get('phone', '')}")
    lines.append(f"WHATSAPP: {shop_info.get('whatsapp', '')}")
    lines.append(f"ADDRESS: {shop_info.get('address', '')}")
    if shop_info.get('landmark'):
        lines.append(f"LANDMARK: {shop_info.get('landmark')}")
    lines.append(f"TIMINGS: {shop_info.get('timings', '')}")
    lines.append(f"PAYMENT METHODS: {shop_info.get('payment_methods', '')}")
    lines.append(f"DELIVERY INFO: {shop_info.get('delivery_info', '')}")

    lines.append("\nAVAILABLE PRODUCTS & PRICES:")
    if products:
        for p in products:
            stock_str = "In Stock" if p.get("in_stock", True) else "Out of Stock"
            lines.append(f"- {p.get('name')} ({p.get('category', 'General')}): ₹{p.get('price')} / {p.get('unit', 'unit')} [{stock_str}]")
    else:
        lines.append("No products listed.")

    lines.append("\nFREQUENTLY ASKED QUESTIONS (FAQs):")
    if faqs:
        for faq in faqs:
            lines.append(f"Q: {faq.get('question')}")
            lines.append(f"A: {faq.get('answer')}")
    else:
        lines.append("No FAQs listed.")

    return "\n".join(lines)
