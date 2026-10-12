"""
main.py
FastAPI application for DukaanSathi - Multilingual Local Shop Chatbot.
"""

import os
import hashlib
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, status, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

import data_manager
import sarvam_client

# Load environment configuration
load_dotenv()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
AUTH_SECRET_SALT = "dukaansathi_secure_session_salt"

app = FastAPI(
    title="DukaanSathi - Multilingual Shop Assistant",
    description="Multilingual customer support chatbot for local shops powered by Sarvam AI",
    version="1.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def generate_admin_token() -> str:
    """Generate a reproducible session token from the admin password."""
    return hashlib.sha256(f"{ADMIN_PASSWORD}_{AUTH_SECRET_SALT}".encode()).hexdigest()


def verify_admin(auth_header: Optional[str] = Header(None, alias="Authorization"),
                 x_admin_password: Optional[str] = Header(None, alias="x-admin-password")):
    """Verify admin identity via Bearer token or direct password header."""
    expected_token = generate_admin_token()

    # Check Bearer token
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        if token == expected_token:
            return True

    # Check direct password header
    if x_admin_password and x_admin_password == ADMIN_PASSWORD:
        return True

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Invalid admin credentials."
    )


# Pydantic Request Models
class ChatRequest(BaseModel):
    message: str
    language_code: Optional[str] = "hi-IN"
    input_type: Optional[str] = "text"


class TTSRequest(BaseModel):
    text: str
    language_code: Optional[str] = "hi-IN"


class AdminLoginRequest(BaseModel):
    password: str


# ---------------- Frontend Routes ----------------

@app.get("/", response_class=HTMLResponse)
async def serve_customer_page():
    """Serve the customer chat interface."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return HTMLResponse("<h1>DukaanSathi Customer Chat Interface</h1><p>index.html not found</p>")


@app.get("/admin", response_class=HTMLResponse)
async def serve_admin_page():
    """Serve the shop owner admin management interface."""
    admin_file = os.path.join(STATIC_DIR, "admin.html")
    if os.path.exists(admin_file):
        return FileResponse(admin_file)
    return HTMLResponse("<h1>DukaanSathi Admin Panel</h1><p>admin.html not found</p>")


# ---------------- Public API Routes ----------------

@app.get("/api/shop-info")
async def get_shop_info():
    """Retrieve public shop info for the chat header & contact links."""
    data = data_manager.load_shop_data()
    shop_info = data.get("shop_info", {})
    return {
        "name": shop_info.get("name", "Local Store"),
        "owner_name": shop_info.get("owner_name", ""),
        "phone": shop_info.get("phone", ""),
        "whatsapp": shop_info.get("whatsapp", ""),
        "address": shop_info.get("address", ""),
        "timings": shop_info.get("timings", "")
    }


@app.get("/api/languages")
async def get_languages():
    """Retrieve list of supported Indian languages for customer selection."""
    return {
        "languages": [
            {"code": code, "name": name}
            for code, name in sarvam_client.SUPPORTED_LANGUAGES.items()
        ]
    }


@app.post("/api/chat")
async def handle_chat(req: ChatRequest):
    """
    Handle customer text questions.
    Queries the Sarvam Chat Model grounded strictly on shop_data.json.
    """
    query = req.message.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # Build shop knowledge context
    shop_context = data_manager.build_shop_context_string()
    target_lang_name = sarvam_client.SUPPORTED_LANGUAGES.get(req.language_code, None)

    try:
        reply, contact_needed = await sarvam_client.chat_completion(
            user_message=query,
            shop_context=shop_context,
            target_language_name=target_lang_name
        )
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    # Log query and reply
    data_manager.log_conversation(
        question=query,
        answer=reply,
        language=req.language_code or "auto",
        input_type=req.input_type or "text",
        contact_owner_suggested=contact_needed
    )

    shop_data = data_manager.load_shop_data().get("shop_info", {})

    return {
        "reply": reply,
        "contact_owner": contact_needed,
        "language_code": req.language_code,
        "shop_contact": {
            "phone": shop_data.get("phone", ""),
            "whatsapp": shop_data.get("whatsapp", "")
        }
    }


@app.post("/api/speech-to-text")
async def handle_speech_to_text(
    file: UploadFile = File(...),
    language_code: Optional[str] = Form("hi-IN")
):
    """
    Accept recorded voice audio and transcribe it using Sarvam Saaras.
    """
    try:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Uploaded audio file is empty.")

        filename = file.filename or "recording.webm"
        content_type = file.content_type or "audio/webm"

        result = await sarvam_client.speech_to_text(
            audio_bytes=audio_bytes,
            filename=filename,
            content_type=content_type,
            language_code=language_code
        )
        return result
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT processing failed: {str(e)}")


@app.post("/api/text-to-speech")
async def handle_text_to_speech(req: TTSRequest):
    """
    Generate audio speech for a chatbot response using Sarvam Bulbul.
    Returns base64 encoded audio string.
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    try:
        audio_base64 = await sarvam_client.text_to_speech(
            text=req.text,
            language_code=req.language_code or "hi-IN"
        )
        return {
            "audio_base64": audio_base64,
            "mime_type": "audio/wav"
        }
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS processing failed: {str(e)}")


# ---------------- Admin API Routes ----------------

@app.post("/api/admin/login")
async def admin_login(req: AdminLoginRequest):
    """Validate admin password and return session token."""
    if req.password == ADMIN_PASSWORD:
        token = generate_admin_token()
        return {"success": True, "token": token}
    else:
        raise HTTPException(status_code=401, detail="Incorrect admin password.")


@app.get("/api/admin/shop-data")
async def get_admin_shop_data(request: Request):
    """Fetch complete shop_data.json for editing in admin dashboard."""
    auth_header = request.headers.get("Authorization")
    x_admin_pw = request.headers.get("x-admin-password")
    verify_admin(auth_header, x_admin_pw)

    data = data_manager.load_shop_data()
    return data


@app.post("/api/admin/shop-data")
async def update_admin_shop_data(payload: Dict[str, Any], request: Request):
    """Update shop_data.json from admin dashboard."""
    auth_header = request.headers.get("Authorization")
    x_admin_pw = request.headers.get("x-admin-password")
    verify_admin(auth_header, x_admin_pw)

    # Basic schema check
    if "shop_info" not in payload or "products" not in payload:
        raise HTTPException(status_code=400, detail="Invalid shop data structure. 'shop_info' and 'products' required.")

    success = data_manager.save_shop_data(payload)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save shop data to disk.")

    return {"success": True, "message": "Shop data updated successfully."}


@app.get("/api/admin/conversations")
async def get_admin_conversations(request: Request):
    """Retrieve logged customer conversations for the shop owner."""
    auth_header = request.headers.get("Authorization")
    x_admin_pw = request.headers.get("x-admin-password")
    verify_admin(auth_header, x_admin_pw)

    conversations = data_manager.get_conversations()
    return {"conversations": conversations}
