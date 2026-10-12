"""
test_app.py
Verification test script for DukaanSathi.
Tests all endpoints, authentication, data persistence, and error handling.
"""

import sys
import json
from fastapi.testclient import TestClient

import main
import data_manager

client = TestClient(main.app)

def run_tests():
    print("=== Testing DukaanSathi MVP Endpoints ===")
    
    # 1. Customer Chat Page
    r = client.get("/")
    assert r.status_code == 200, f"Expected 200 for /, got {r.status_code}"
    assert "DukaanSathi" in r.text
    print("[PASS] GET / (Customer page)")

    # 2. Admin Page
    r = client.get("/admin")
    assert r.status_code == 200, f"Expected 200 for /admin, got {r.status_code}"
    assert "Admin" in r.text
    print("[PASS] GET /admin (Admin page)")

    # 3. Shop Info API
    r = client.get("/api/shop-info")
    assert r.status_code == 200
    info = r.json()
    assert "name" in info and "timings" in info
    print(f"[PASS] GET /api/shop-info (Store: {info['name']})")

    # 4. Languages API
    r = client.get("/api/languages")
    assert r.status_code == 200
    langs = r.json().get("languages", [])
    assert len(langs) >= 10
    print(f"[PASS] GET /api/languages ({len(langs)} Indian languages available)")

    # 5. Admin Authentication
    r = client.post("/api/admin/login", json={"password": "wrongpassword"})
    assert r.status_code == 401
    print("[PASS] Admin rejection on wrong password")

    r = client.post("/api/admin/login", json={"password": main.ADMIN_PASSWORD})
    assert r.status_code == 200
    token = r.json().get("token")
    assert token is not None
    print("[PASS] Admin login on correct password")

    # 6. Admin Shop Data Read & Write
    headers = {"Authorization": f"Bearer {token}"}
    r = client.get("/api/admin/shop-data", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "shop_info" in data and "products" in data
    print(f"[PASS] GET /api/admin/shop-data ({len(data['products'])} products loaded)")

    # Test update
    data["shop_info"]["landmark"] = "Opposite Civil Hospital, Near Hanuman Mandir (Verified)"
    r = client.post("/api/admin/shop-data", json=data, headers=headers)
    assert r.status_code == 200
    print("[PASS] POST /api/admin/shop-data (Save updated shop details)")

    # 7. Conversations Log Read
    r = client.get("/api/admin/conversations", headers=headers)
    assert r.status_code == 200
    print("[PASS] GET /api/admin/conversations")

    # 8. Validation on Empty Inputs
    r = client.post("/api/chat", json={"message": "   "})
    assert r.status_code == 400
    print("[PASS] POST /api/chat empty input rejection")

    r = client.post("/api/text-to-speech", json={"text": "   "})
    assert r.status_code == 400
    print("[PASS] POST /api/text-to-speech empty text rejection")

    # 9. Test conversation logging directly
    success = data_manager.log_conversation(
        question="Dukaan kab khulti hai?",
        answer="Dukaan subah 7:00 baje se raat 10:00 baje tak khuli rehti hai.",
        language="hi-IN",
        input_type="text",
        contact_owner_suggested=False
    )
    assert success is True
    convs = data_manager.get_conversations()
    assert len(convs) >= 1
    assert convs[-1]["question"] == "Dukaan kab khulti hai?"
    print("[PASS] Conversation logging & persistence")

    # 10. Check shop context generation
    ctx = data_manager.build_shop_context_string()
    assert "AVAILABLE PRODUCTS" in ctx
    print("[PASS] Context builder for LLM system prompt")

    print("\nALL 10 TEST SUITES PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
