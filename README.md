# DukaanSathi (दुकान साथी) 🏪
**Multilingual AI Customer Support Chatbot for Local Indian Shops**

DukaanSathi is an AI-powered assistant designed specifically for neighborhood stores (Kirana, medical stores, tailors, salons, etc.). Customers can ask questions by **voice or text** in their preferred Indian language (Hindi, Bengali, Tamil, Telugu, Marathi, Gujarati, etc.) and receive immediate answers in the same language.

Store owners can effortlessly update inventory, timings, and policies via a password-protected admin dashboard without touching a database.

---

## 🌟 Key Features

1. **Multilingual Voice & Text Support**:
   - Customers can tap the microphone 🎙️ to ask in their native language or type normally.
   - Powered by **Sarvam AI Saaras** Speech-to-Text (`saaras:v4`).
2. **Accurate & Grounded Store Responses**:
   - Answers are strictly generated from `shop_data.json` using **Sarvam AI Chat Model** (`sarvam-105b`).
   - The assistant never invents prices, offers, or non-existent stock.
3. **Voice Audio Replies (Text-to-Speech)**:
   - Each answer includes a **"🔊 Listen"** button powered by **Sarvam AI Bulbul** (`bulbul:v4-flash`), reading the answer aloud in the customer's language.
4. **"Contact Shop Owner" Fallback**:
   - If a requested item or policy is missing or uncertain, DukaanSathi politely states that and renders one-tap **"Call Shop Owner" (`tel:`)** and **"WhatsApp Shop Owner"** buttons.
5. **Shop Owner Admin Dashboard (`/admin`)**:
   - Protected by `ADMIN_PASSWORD` from `.env`.
   - Edit store name, timings, address, delivery rules, payment options, product catalog with prices, and FAQs.
6. **Customer Inquiries Log (`conversations.json`)**:
   - Logs every customer interaction (question, answer, language, voice/text, and timestamp) so owners can discover high-demand products and recurring questions.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, HTTPX
- **Frontend**: HTML5, Vanilla JavaScript, CSS3 (Mobile-responsive UI)
- **AI Provider**: [Sarvam AI APIs](https://docs.sarvam.ai)
  - STT: `POST https://api.sarvam.ai/speech-to-text` (`saaras:v4`)
  - Chat/LLM: `POST https://api.sarvam.ai/v1/chat/completions` (`sarvam-105b`)
  - TTS: `POST https://api.sarvam.ai/text-to-speech` (`bulbul:v4-flash`)
- **Data Storage**: Local JSON files (`shop_data.json`, `conversations.json`)

---

## 🚀 Quickstart & Setup Guide

### 1. Clone or Open Project Directory
```bash
cd "c:\Users\TOPPERS\OneDrive\Desktop\SARVAM PROJECT"
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure `.env`
Copy `.env.example` to `.env` (or edit existing `.env`):
```env
# Get your API key from https://dashboard.sarvam.ai/
SARVAM_API_KEY=your_actual_sarvam_api_key_here

# Password for /admin dashboard
ADMIN_PASSWORD=admin123
```

### 4. Run the Application
```bash
uvicorn main:app --reload
```
The server will start at: `http://127.0.0.1:8000`

---

## 📱 Usage

### 💬 Customer Chat Interface
Open `http://127.0.0.1:8000/` in your browser:
- Select your preferred Indian language from the top-right dropdown (e.g., Hindi, Bengali, Tamil, etc.).
- Type a query like: *"आशीर्वाद आटा का क्या भाव है?"* or *"Do you deliver to home?"*.
- Or click the **🎙️ Mic button**, grant microphone access, and speak your query.
- Click **"🔊 Listen"** on any response to hear it read aloud.
- If asking for something not in the store, observe the direct **"Call Owner"** and **"WhatsApp"** action buttons.

### ⚙️ Shop Owner Admin Dashboard
Open `http://127.0.0.1:8000/admin`:
1. Enter the password configured in `.env` (default: `admin123`).
2. Update shop hours, contact details, products, prices, or FAQs.
3. Click **"Save"** to persist changes directly to `shop_data.json`.
4. Navigate to the **"💬 Customer Questions"** tab to see what customers have asked.

---

## 📂 Project Directory Structure

```text
SARVAM PROJECT/
├── .env                  # Environment configuration (API key and Admin password)
├── .env.example          # Template configuration
├── requirements.txt      # Python dependencies
├── shop_data.json        # Fictional Kirana store data (timing, products, FAQs)
├── conversations.json    # Customer inquiry logs
├── main.py               # FastAPI application & REST endpoints
├── sarvam_client.py      # Sarvam AI API client (Saaras, Sarvam-105b, Bulbul)
├── data_manager.py       # JSON storage and prompt context builder
├── static/
│   ├── index.html        # Customer chat UI
│   ├── admin.html        # Shop owner dashboard UI
│   ├── css/
│   │   └── style.css     # Clean responsive design
│   └── js/
│       ├── chat.js       # Customer chat controller (voice/text/audio)
│       └── admin.js      # Admin dashboard controller
└── README.md             # Documentation & running instructions
```

---

## 🛡️ Error Handling
- **Bad or Missing Audio**: Returns informative prompt to speak clearly.
- **Invalid API Key**: Detects unconfigured or invalid Sarvam keys and guides the user.
- **Rate Limits & Network Timeouts**: Handles 429 status codes and network interruptions cleanly.
- **Safety**: API keys are strictly accessed via environment variables and never exposed to the client.
