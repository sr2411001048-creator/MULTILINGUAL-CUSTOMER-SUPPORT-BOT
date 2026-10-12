/**
 * chat.js - Customer Support Chat Controller for DukaanSathi
 * Supports Text + Voice (Sarvam STT) + Speech Playback (Sarvam Bulbul TTS)
 */

let shopData = {
  name: "DukaanSathi",
  phone: "+919876543210",
  whatsapp: "+919876543210",
  timings: "Open 7:00 AM - 10:00 PM",
  address: ""
};

// Audio recording variables
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let currentPlayingBtn = null;

const chatMessages = document.getElementById("chatMessages");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");
const micBtn = document.getElementById("micBtn");
const languageSelect = document.getElementById("languageSelect");
const recordingOverlay = document.getElementById("recordingOverlay");
const stopRecordBtn = document.getElementById("stopRecordBtn");
const audioPlayer = document.getElementById("audioPlayer");
const toast = document.getElementById("toast");

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  fetchShopInfo();
  setupEventListeners();
});

function showToast(message) {
  toast.innerText = message;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, 3500);
}

// Fetch shop info to populate header and contact buttons
async function fetchShopInfo() {
  try {
    const res = await fetch("/api/shop-info");
    if (res.ok) {
      const data = await res.json();
      shopData = { ...shopData, ...data };
      if (data.name) document.getElementById("shopName").innerText = data.name;
      if (data.timings) document.getElementById("shopTimings").innerText = `⏰ ${data.timings}`;
      if (data.address) document.getElementById("shopAddress").innerText = `📍 ${data.address}`;
    }
  } catch (err) {
    console.warn("Could not load shop info:", err);
  }
}

function setupEventListeners() {
  // Send on Enter key
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendText();
    }
  });

  sendBtn.addEventListener("click", handleSendText);

  // Mic button for voice input
  micBtn.addEventListener("click", toggleVoiceRecording);
  stopRecordBtn.addEventListener("click", stopVoiceRecording);

  // Quick chips
  document.querySelectorAll(".chip-btn").forEach((chip) => {
    chip.addEventListener("click", () => {
      const q = chip.getAttribute("data-query");
      if (q) {
        chatInput.value = q;
        handleSendText();
      }
    });
  });

  // Audio player end handler
  audioPlayer.addEventListener("ended", () => {
    if (currentPlayingBtn) {
      currentPlayingBtn.classList.remove("playing");
      currentPlayingBtn.innerHTML = "🔊 Listen";
      currentPlayingBtn = null;
    }
  });

  audioPlayer.addEventListener("error", () => {
    if (currentPlayingBtn) {
      currentPlayingBtn.classList.remove("playing");
      currentPlayingBtn.innerHTML = "🔊 Listen";
      currentPlayingBtn = null;
    }
    showToast("Audio playback error.");
  });
}

function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ---------------- Text Messaging ----------------

async function handleSendText() {
  const query = chatInput.value.trim();
  if (!query) return;

  chatInput.value = "";
  chatInput.focus();

  // Append user bubble
  appendUserMessage(query, false);

  // Query LLM backend
  await processQuery(query, "text");
}

function appendUserMessage(text, isVoice = false) {
  const row = document.createElement("div");
  row.className = "message-row user";
  
  const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  const icon = isVoice ? "🎙️ " : "";

  row.innerHTML = `
    <div class="bubble">
      <p>${escapeHtml(text)} ${icon}</p>
      <div class="message-time">${timeStr}</div>
    </div>
  `;
  chatMessages.appendChild(row);
  scrollToBottom();
}

function appendTypingIndicator(message = "Thinking...") {
  const row = document.createElement("div");
  row.className = "message-row bot typing-row";
  row.id = "typingRow";
  row.innerHTML = `
    <div class="typing-indicator">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <span style="font-size: 12px; color: #64748b; margin-left: 6px;">${message}</span>
    </div>
  `;
  chatMessages.appendChild(row);
  scrollToBottom();
}

function removeTypingIndicator() {
  const indicator = document.getElementById("typingRow");
  if (indicator) indicator.remove();
}

async function processQuery(query, inputType = "text") {
  appendTypingIndicator("Consulting shop data...");
  const langCode = languageSelect.value;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: query,
        language_code: langCode,
        input_type: inputType
      })
    });

    removeTypingIndicator();

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Network error" }));
      appendBotMessage(
        `⚠️ Error: ${err.detail || "Unable to get an answer right now. Please try again."}`,
        false,
        query
      );
      return;
    }

    const data = await res.json();
    appendBotMessage(data.reply, data.contact_owner, query);

  } catch (err) {
    removeTypingIndicator();
    appendBotMessage("⚠️ Could not connect to the server. Please check your connection.", false, query);
  }
}

function appendBotMessage(replyText, contactOwner = false, userQuery = "") {
  const row = document.createElement("div");
  row.className = "message-row bot";

  const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  let contactHtml = "";
  if (contactOwner) {
    const phone = shopData.phone || "+919876543210";
    const rawWa = (shopData.whatsapp || phone).replace(/[^0-9]/g, "");
    const waText = encodeURIComponent(`Namaste, I had a question about: "${userQuery}"`);
    const waLink = `https://wa.me/${rawWa}?text=${waText}`;

    contactHtml = `
      <div class="contact-owner-box">
        <p>💡 For custom orders or stock updates, contact the shop owner directly:</p>
        <div class="contact-buttons-row">
          <a href="tel:${phone}" class="contact-action-btn call-btn">
            📞 Call Owner
          </a>
          <a href="${waLink}" target="_blank" rel="noopener noreferrer" class="contact-action-btn wa-btn">
            💬 WhatsApp
          </a>
        </div>
      </div>
    `;
  }

  const encodedReply = encodeURIComponent(replyText);

  row.innerHTML = `
    <div class="bubble">
      <p class="bot-text">${escapeHtml(replyText).replace(/\n/g, "<br>")}</p>
      ${contactHtml}
      <div class="bubble-actions">
        <button class="listen-btn" data-reply="${encodedReply}" onclick="handleListenClick(this)">
          🔊 Listen
        </button>
      </div>
      <div class="message-time">${timeStr}</div>
    </div>
  `;

  chatMessages.appendChild(row);
  scrollToBottom();
}

// ---------------- Text-to-Speech (Bulbul) ----------------

async function handleListenClick(btn) {
  // If already playing this audio, toggle pause
  if (currentPlayingBtn === btn && !audioPlayer.paused) {
    audioPlayer.pause();
    btn.classList.remove("playing");
    btn.innerHTML = "🔊 Listen";
    currentPlayingBtn = null;
    return;
  }

  // Reset previously playing button
  if (currentPlayingBtn) {
    currentPlayingBtn.classList.remove("playing");
    currentPlayingBtn.innerHTML = "🔊 Listen";
  }

  const encodedText = btn.getAttribute("data-reply");
  const rawText = decodeURIComponent(encodedText);
  const langCode = languageSelect.value;

  btn.classList.add("playing");
  btn.innerHTML = "⏳ Generating audio...";
  currentPlayingBtn = btn;

  try {
    const res = await fetch("/api/text-to-speech", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: rawText,
        language_code: langCode
      })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "TTS generation failed" }));
      showToast(err.detail || "Unable to play audio.");
      btn.classList.remove("playing");
      btn.innerHTML = "🔊 Listen";
      currentPlayingBtn = null;
      return;
    }

    const data = await res.json();
    if (!data.audio_base64) {
      showToast("No audio received from Sarvam TTS.");
      btn.classList.remove("playing");
      btn.innerHTML = "🔊 Listen";
      currentPlayingBtn = null;
      return;
    }

    // Play base64 audio
    audioPlayer.src = `data:audio/wav;base64,${data.audio_base64}`;
    audioPlayer.play();
    btn.innerHTML = "⏹️ Stop Audio";

  } catch (err) {
    showToast("Error connecting to audio service.");
    btn.classList.remove("playing");
    btn.innerHTML = "🔊 Listen";
    currentPlayingBtn = null;
  }
}

// ---------------- Voice Recording & Sarvam STT ----------------

async function toggleVoiceRecording() {
  if (isRecording) {
    stopVoiceRecording();
  } else {
    await startVoiceRecording();
  }
}

async function startVoiceRecording() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showToast("Voice recording is not supported on this browser.");
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];

    // Choose best supported mimeType
    let mimeType = "audio/webm";
    if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
      mimeType = "audio/webm;codecs=opus";
    } else if (MediaRecorder.isTypeSupported("audio/mp4")) {
      mimeType = "audio/mp4";
    } else if (MediaRecorder.isTypeSupported("audio/ogg")) {
      mimeType = "audio/ogg";
    }

    mediaRecorder = new MediaRecorder(stream, { mimeType });

    mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        audioChunks.push(event.data);
      }
    };

    mediaRecorder.onstop = async () => {
      // Stop all tracks to release microphone
      stream.getTracks().forEach((track) => track.stop());
      const audioBlob = new Blob(audioChunks, { type: mimeType });
      await sendVoiceToSTT(audioBlob, mimeType);
    };

    mediaRecorder.start();
    isRecording = true;
    recordingOverlay.classList.add("active");
    micBtn.style.background = "#fee2e2";
    micBtn.style.color = "#dc2626";

  } catch (err) {
    console.error("Microphone access error:", err);
    showToast("Microphone permission denied. Please allow microphone access.");
  }
}

function stopVoiceRecording() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    isRecording = false;
    recordingOverlay.classList.remove("active");
    micBtn.style.background = "";
    micBtn.style.color = "";
  }
}

async function sendVoiceToSTT(audioBlob, mimeType) {
  if (audioBlob.size < 500) {
    showToast("Voice recording was too short. Please try again.");
    return;
  }

  appendTypingIndicator("Transcribing your voice (Sarvam Saaras)...");

  const formData = new FormData();
  const extension = mimeType.includes("mp4") ? "mp4" : mimeType.includes("ogg") ? "ogg" : "webm";
  formData.append("file", audioBlob, `voice_query.${extension}`);
  formData.append("language_code", languageSelect.value);

  try {
    const res = await fetch("/api/speech-to-text", {
      method: "POST",
      body: formData
    });

    removeTypingIndicator();

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "STT processing error" }));
      showToast(err.detail || "Could not transcribe audio. Please try typing.");
      return;
    }

    const data = await res.json();
    const transcript = (data.transcript || "").trim();

    if (!transcript) {
      showToast("Could not recognize any speech. Please try speaking again.");
      return;
    }

    // Display the transcribed text as customer query
    appendUserMessage(transcript, true);

    // If Sarvam STT detected language, update dropdown
    if (data.language_code && languageSelect.querySelector(`option[value="${data.language_code}"]`)) {
      languageSelect.value = data.language_code;
    }

    // Now send to LLM
    await processQuery(transcript, "voice");

  } catch (err) {
    removeTypingIndicator();
    showToast("Failed to send audio to server.");
  }
}

function escapeHtml(text) {
  if (!text) return "";
  const map = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  };
  return text.replace(/[&<>"']/g, (m) => map[m]);
}
