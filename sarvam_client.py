"""
sarvam_client.py
Client for interacting with Sarvam AI REST APIs:
- Speech-to-Text (Saaras)
- Chat / LLM (Sarvam-105b)
- Text-to-Speech (Bulbul)
"""

import os
import re
import httpx
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SARVAM_BASE_URL = "https://api.sarvam.ai"

# Supported Indian language codes mapped to common display names
SUPPORTED_LANGUAGES = {
    "hi-IN": "Hindi (हिंदी)",
    "bn-IN": "Bengali (বাংলা)",
    "ta-IN": "Tamil (தமிழ்)",
    "te-IN": "Telugu (తెలుగు)",
    "mr-IN": "Marathi (मराठी)",
    "gu-IN": "Gujarati (ગુજરાતી)",
    "kn-IN": "Kannada (ಕನ್ನಡ)",
    "ml-IN": "Malayalam (മലയാളം)",
    "pa-IN": "Punjabi (ਪੰਜਾਬੀ)",
    "od-IN": "Odia (ଓଡ଼ିଆ)",
    "en-IN": "English"
}

# Voice speakers supported by Sarvam Bulbul
DEFAULT_SPEAKER = "shubh_enhi_ads"


def get_api_key() -> str:
    """Retrieve Sarvam API key from environment, ensuring it is set."""
    key = os.getenv("SARVAM_API_KEY", "").strip()
    return key


def validate_api_key(key: str) -> bool:
    """Check if the API key is set and not the placeholder."""
    return bool(key and key != "your_sarvam_api_key_here")


async def speech_to_text(
    audio_bytes: bytes,
    filename: str = "audio.wav",
    content_type: str = "audio/wav",
    language_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transcribe speech using Sarvam Saaras model.
    Endpoint: POST https://api.sarvam.ai/speech-to-text
    """
    api_key = get_api_key()
    if not validate_api_key(api_key):
        raise ValueError("SARVAM_API_KEY is not configured or is a placeholder in .env")

    if not audio_bytes or len(audio_bytes) < 100:
        raise ValueError("Audio recording is empty or too short. Please speak clearly.")

    headers = {
        "api-subscription-key": api_key
    }

    data: Dict[str, Any] = {
        "model": "saaras:v4"
    }
    if language_code and language_code != "auto":
        data["language_code"] = language_code

    files = {
        "file": (filename, audio_bytes, content_type)
    }

    url = f"{SARVAM_BASE_URL}/speech-to-text"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, headers=headers, data=data, files=files)
        except httpx.TimeoutException:
            raise RuntimeError("Sarvam Speech-to-Text request timed out. Please try again.")
        except httpx.RequestError as e:
            raise RuntimeError(f"Network error connecting to Sarvam STT: {str(e)}")

        if response.status_code == 401 or response.status_code == 403:
            raise PermissionError("Invalid Sarvam API key. Please check your SARVAM_API_KEY in .env.")
        elif response.status_code == 429:
            raise RuntimeError("Sarvam API rate limit exceeded. Please wait a moment and try again.")
        elif response.is_error:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get("error", {}).get("message", response.text)
            except Exception:
                pass
            raise RuntimeError(f"Sarvam STT failed ({response.status_code}): {error_detail}")

        result = response.json()
        return {
            "transcript": result.get("transcript", "").strip(),
            "language_code": result.get("language_code", language_code or "hi-IN")
        }


async def chat_completion(
    user_message: str,
    shop_context: str,
    target_language_name: Optional[str] = None
) -> Tuple[str, bool]:
    """
    Generate an answer using Sarvam Chat Model (sarvam-105b).
    Endpoint: POST https://api.sarvam.ai/v1/chat/completions
    Returns: (reply_text, contact_owner_needed)
    """
    api_key = get_api_key()
    if not validate_api_key(api_key):
        raise ValueError("SARVAM_API_KEY is not configured or is a placeholder in .env")

    if not user_message or not user_message.strip():
        raise ValueError("Question cannot be empty.")

    system_prompt = f"""You are 'DukaanSathi' (दुकान साथी), a helpful, friendly, and honest multilingual AI shop assistant for a local neighborhood shop.

Here is the EXACT information about our shop:
=== SHOP DATA START ===
{shop_context}
=== SHOP DATA END ===

RULES:
1. REPLY LANGUAGE: Reply in the same language the customer used.
2. TONE: Be polite, short, and simple (customers are regular shoppers).
3. ABSOLUTE ACCURACY: Answer ONLY using facts from the SHOP DATA. Never invent prices, products, or timings.
4. TAG INSTRUCTION:
- If the customer's question IS answered by the SHOP DATA: Answer clearly and directly. Do NOT output '[CONTACT_OWNER]'.
- If the requested product, price, or policy is NOT in the SHOP DATA: Politely say you do not have it or are not sure, and append '[CONTACT_OWNER]' at the very end.
"""

    if target_language_name and target_language_name != "English":
        system_prompt += f"\nCustomer preferred language: {target_language_name}."

    headers = {
        "api-subscription-key": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "model": "sarvam-105b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message.strip()}
        ],
        "temperature": 0.1,
        "reasoning_effort": None
    }

    url = f"{SARVAM_BASE_URL}/v1/chat/completions"

    async with httpx.AsyncClient(timeout=45.0) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException:
            raise RuntimeError("Sarvam Chat LLM request timed out. Please try again.")
        except httpx.RequestError as e:
            raise RuntimeError(f"Network error connecting to Sarvam Chat: {str(e)}")

        if response.status_code == 401 or response.status_code == 403:
            raise PermissionError("Invalid Sarvam API key. Please check your SARVAM_API_KEY in .env.")
        elif response.status_code == 429:
            raise RuntimeError("Sarvam API rate limit exceeded. Please wait a moment and try again.")
        elif response.is_error:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get("error", {}).get("message", response.text)
            except Exception:
                pass
            raise RuntimeError(f"Sarvam Chat failed ({response.status_code}): {error_detail}")

        res_data = response.json()
        reply_content = res_data["choices"][0]["message"]["content"].strip()

        # Check if the model signalled that contact with owner is recommended
        contact_owner_needed = False
        if "[CONTACT_OWNER]" in reply_content:
            contact_owner_needed = True
            reply_content = reply_content.replace("[CONTACT_OWNER]", "").strip()

        # Fallback check: if reply mentions not being sure or contact owner
        keywords = ["not sure", "पता नहीं", "माहित नाही", "தெரியவில்லை", "తెలియదు", "contact owner", "दुकानदार से संपर्क", "call owner"]
        if any(kw in reply_content.lower() for kw in keywords):
            contact_owner_needed = True

        return reply_content, contact_owner_needed


async def text_to_speech(
    text: str,
    language_code: str = "hi-IN",
    speaker: str = DEFAULT_SPEAKER
) -> str:
    """
    Convert text to speech using Sarvam Bulbul model.
    Endpoint: POST https://api.sarvam.ai/text-to-speech
    Returns: Base64-encoded audio string
    """
    api_key = get_api_key()
    if not validate_api_key(api_key):
        raise ValueError("SARVAM_API_KEY is not configured or is a placeholder in .env")

    clean_text = text.strip()
    if not clean_text:
        raise ValueError("Text for audio generation cannot be empty.")

    # Bulbul has a 2500 character limit
    if len(clean_text) > 2000:
        clean_text = clean_text[:2000] + "..."

    # Ensure valid language code or fallback to Hindi/English
    if language_code not in SUPPORTED_LANGUAGES and language_code != "auto":
        language_code = "hi-IN"
    elif language_code == "auto":
        language_code = "hi-IN"

    headers = {
        "api-subscription-key": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "text": clean_text,
        "language_code": language_code,
        "model": "bulbul:v4-flash",
        "speaker": speaker,
        "pace": 1.0
    }

    url = f"{SARVAM_BASE_URL}/text-to-speech"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
        except httpx.TimeoutException:
            raise RuntimeError("Sarvam Text-to-Speech request timed out.")
        except httpx.RequestError as e:
            raise RuntimeError(f"Network error connecting to Sarvam TTS: {str(e)}")

        if response.status_code == 401 or response.status_code == 403:
            raise PermissionError("Invalid Sarvam API key. Please check your SARVAM_API_KEY in .env.")
        elif response.status_code == 429:
            raise RuntimeError("Sarvam API rate limit exceeded.")
        elif response.is_error:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get("error", {}).get("message", response.text)
            except Exception:
                pass
            raise RuntimeError(f"Sarvam TTS failed ({response.status_code}): {error_detail}")

        data = response.json()
        audios = data.get("audios", [])
        if not audios or not audios[0]:
            raise RuntimeError("Sarvam TTS returned an empty audio stream.")

        return audios[0]
