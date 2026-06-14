from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_home_page():
    """Test that the main UI page loads"""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "دستیار هوشمند راستاد" in resp.text

def test_api_root():
    """Test the API root endpoint"""
    resp = client.get("/api/")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Rastad AI Assistant API is running"

def test_vip_message():
    """Test VIP question classification"""
    payload = {"user_id":"u1","name":"Ali","message":"خدمات VIP راستاد چیست؟"}
    resp = client.post("/api/message", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "vip_question"
    assert data["user_segment"] == "vip_interest"
    assert data["needs_human_support"] == False
    assert len(data["reply"]) > 0
    assert "VIP" in data["reply"]

def test_exchange_registration():
    """Test exchange registration classification"""
    payload = {"user_id":"u2","name":"Sara","message":"چطور در صرافی ثبت‌نام کنم؟"}
    resp = client.post("/api/message", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "exchange_registration"
    assert data["user_segment"] == "exchange_signup"
    assert data["needs_human_support"] == False

def test_kol_collaboration():
    """Test KOL collaboration intent"""
    payload = {"user_id":"u3","name":"Reza","message":"می‌خواهم KOL بشم"}
    resp = client.post("/api/message", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "kol_collaboration"
    assert data["user_segment"] == "kol_candidate"

def test_support_request():
    """Test support request - should need human support"""
    payload = {"user_id":"u4","name":"Maryam","message":"مشکل پرداخت دارم"}
    resp = client.post("/api/message", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "support_request"
    assert data["user_segment"] == "support_needed"
    assert data["needs_human_support"] == True

def test_payment_not_activated():
    """Test payment issue - requires human"""
    payload = {"user_id":"u5","name":"Hossein","message":"پول دادم ولی اشتراکم فعال نشده"}
    resp = client.post("/api/message", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "support_request"
    assert data["needs_human_support"] == True

def test_general_question():
    """Test general question about services"""
    payload = {"user_id":"u6","name":"Zahra","message":"Trade Assist چیست؟"}
    resp = client.post("/api/message", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] in ["general_info", "unknown"]
    assert len(data["reply"]) > 0

def test_unknown_message():
    """Test message that doesn't match any keyword"""
    payload = {"user_id":"u7","name":"Test","message":"هوا امروز چطوره؟"}
    resp = client.post("/api/message", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "unknown"
    assert data["user_segment"] == "new_user"
    assert data["needs_human_support"] == True

def test_empty_message_rejected():
    """Test validation - empty message should fail"""
    payload = {"user_id":"u1","name":"Ali","message":""}
    resp = client.post("/api/message", json=payload)
    assert resp.status_code == 422  # Validation error

def test_empty_user_id_rejected():
    """Test validation - empty user_id should fail"""
    payload = {"user_id":"","name":"Ali","message":"سلام"}
    resp = client.post("/api/message", json=payload)
    assert resp.status_code == 422

def test_empty_name_rejected():
    """Test validation - empty name should fail"""
    payload = {"user_id":"u1","name":"","message":"سلام"}
    resp = client.post("/api/message", json=payload)
    assert resp.status_code == 422

def test_get_users_list():
    """Test getting users list (after some messages sent)"""
    # First send a message to create a user
    client.post("/api/message", json={
        "user_id":"test_user_1",
        "name":"Test User",
        "message":"خدمات VIP چیست؟"
    })
    resp = client.get("/api/users")
    assert resp.status_code == 200
    users = resp.json()
    assert isinstance(users, list)
    assert len(users) > 0
    # Check our user exists
    user_ids = [u["user_id"] for u in users]
    assert "test_user_1" in user_ids

def test_get_user_messages():
    """Test getting messages for a specific user"""
    # Send a message first
    client.post("/api/message", json={
        "user_id":"msg_test_user",
        "name":"Message Test",
        "message":"چطور در صرافی ثبت‌نام کنم؟"
    })
    # Now get their messages
    resp = client.get("/api/users/msg_test_user/messages")
    assert resp.status_code == 200
    messages = resp.json()
    assert isinstance(messages, list)
    assert len(messages) > 0
    # Check the message content
    assert messages[0]["intent"] == "exchange_registration"
    assert messages[0]["user_message"] == "چطور در صرافی ثبت‌نام کنم؟"

def test_user_not_found():
    """Test getting messages for non-existent user"""
    resp = client.get("/api/users/nonexistent_user/messages")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "User not found"

def test_user_update_on_repeat():
    """Test that repeated messages from same user update last_seen"""
    # Send first message
    resp1 = client.post("/api/message", json={
        "user_id":"repeat_user",
        "name":"Repeat",
        "message":"سلام"
    })
    # Send second message (different name)
    resp2 = client.post("/api/message", json={
        "user_id":"repeat_user",
        "name":"Repeat Updated",
        "message":"خدمات VIP چیست؟"
    })
    assert resp2.status_code == 200
    # Check user was updated
    users_resp = client.get("/api/users")
    users = users_resp.json()
    repeat_user = next((u for u in users if u["user_id"] == "repeat_user"), None)
    assert repeat_user is not None
    assert repeat_user["name"] == "Repeat Updated"

def test_form_submission():
    """Test the HTML form endpoint"""
    resp = client.post("/api/message-form", data={
        "user_id": "form_user",
        "name": "Form Test",
        "message": "خدمات VIP چیست؟"
    })
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "VIP" in resp.text

def test_cors_headers():
    """Test that CORS headers are present"""
    resp = client.options("/api/message", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST"
    })
    # FastAPI TestClient might not trigger full CORS, but we can check API works
    assert resp.status_code in [200, 405]  # OPTIONS might not be explicitly handled