/**
 * admin.js - Shop Owner Admin Dashboard Controller
 * Manages shop details, product inventory, FAQs, and customer query logs.
 */

let currentShopData = {
  shop_info: {},
  products: [],
  faqs: []
};

const toast = document.getElementById("toast");
const loginSection = document.getElementById("loginSection");
const dashboardSection = document.getElementById("dashboardSection");
const loginForm = document.getElementById("loginForm");
const adminPasswordInput = document.getElementById("adminPasswordInput");
const loginError = document.getElementById("loginError");
const logoutBtn = document.getElementById("logoutBtn");

document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  setupAuth();
});

function showToast(message) {
  toast.innerText = message;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, 3500);
}

// ---------------- Authentication ----------------

function setupAuth() {
  const token = sessionStorage.getItem("admin_token");
  if (token) {
    verifyAndLoadData(token);
  } else {
    showLogin();
  }

  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    loginError.style.display = "none";
    const password = adminPasswordInput.value.trim();

    try {
      const res = await fetch("/api/admin/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password })
      });

      if (!res.ok) {
        loginError.innerText = "Incorrect admin password. Please try again.";
        loginError.style.display = "block";
        return;
      }

      const data = await res.json();
      sessionStorage.setItem("admin_token", data.token);
      showDashboard();
      await loadShopData();
      showToast("Logged in successfully!");
    } catch (err) {
      loginError.innerText = "Connection failed. Please check if the server is running.";
      loginError.style.display = "block";
    }
  });

  logoutBtn.addEventListener("click", () => {
    sessionStorage.removeItem("admin_token");
    showLogin();
    showToast("Logged out.");
  });
}

function showLogin() {
  loginSection.style.display = "block";
  dashboardSection.style.display = "none";
  logoutBtn.style.display = "none";
}

function showDashboard() {
  loginSection.style.display = "none";
  dashboardSection.style.display = "block";
  logoutBtn.style.display = "inline-block";
}

async function verifyAndLoadData(token) {
  try {
    const res = await fetch("/api/admin/shop-data", {
      headers: { "Authorization": `Bearer ${token}` }
    });

    if (res.ok) {
      showDashboard();
      await loadShopData();
    } else {
      sessionStorage.removeItem("admin_token");
      showLogin();
    }
  } catch (err) {
    showLogin();
  }
}

function getAuthHeaders() {
  const token = sessionStorage.getItem("admin_token") || "";
  return {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  };
}

// ---------------- Tabs ----------------

function setupTabs() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));

      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      document.getElementById(targetId).classList.add("active");

      if (targetId === "tab-conversations") {
        fetchConversations();
      }
    });
  });
}

// ---------------- Data Loading & Populating ----------------

async function loadShopData() {
  try {
    const res = await fetch("/api/admin/shop-data", {
      headers: getAuthHeaders()
    });

    if (!res.ok) {
      showToast("Failed to load shop data.");
      return;
    }

    currentShopData = await res.json();
    populateShopDetails(currentShopData.shop_info || {});
    renderProducts(currentShopData.products || []);
    renderFaqs(currentShopData.faqs || []);
  } catch (err) {
    showToast("Error connecting to server.");
  }
}

function populateShopDetails(info) {
  document.getElementById("shopNameInput").value = info.name || "";
  document.getElementById("ownerNameInput").value = info.owner_name || "";
  document.getElementById("shopPhoneInput").value = info.phone || "";
  document.getElementById("shopWhatsappInput").value = info.whatsapp || "";
  document.getElementById("shopAddressInput").value = info.address || "";
  document.getElementById("shopLandmarkInput").value = info.landmark || "";
  document.getElementById("shopTimingsInput").value = info.timings || "";
  document.getElementById("shopPaymentInput").value = info.payment_methods || "";
  document.getElementById("shopDeliveryInput").value = info.delivery_info || "";
}

// ---------------- Products Management ----------------

function renderProducts(products) {
  const tbody = document.getElementById("productsTableBody");
  tbody.innerHTML = "";

  if (!products || products.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color: #9ca3af; padding: 20px;">No products listed yet. Click '+ Add Product' to create one.</td></tr>`;
    return;
  }

  products.forEach((p, index) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>
        <input type="text" class="form-control" value="${escapeAttr(p.name)}" 
               onchange="updateProductField(${index}, 'name', this.value)" style="min-width: 160px;">
      </td>
      <td>
        <input type="text" class="form-control" value="${escapeAttr(p.category || 'General')}" 
               onchange="updateProductField(${index}, 'category', this.value)" style="width: 120px;">
      </td>
      <td>
        <input type="number" class="form-control" value="${p.price}" min="0" step="1" 
               onchange="updateProductField(${index}, 'price', Number(this.value))" style="width: 80px;">
      </td>
      <td>
        <input type="text" class="form-control" value="${escapeAttr(p.unit || '1 kg')}" 
               onchange="updateProductField(${index}, 'unit', this.value)" style="width: 90px;">
      </td>
      <td>
        <label style="display:flex; align-items:center; gap: 4px; cursor: pointer; font-size: 13px;">
          <input type="checkbox" ${p.in_stock ? "checked" : ""} 
                 onchange="updateProductField(${index}, 'in_stock', this.checked)">
          <span>${p.in_stock ? "In Stock" : "Out of Stock"}</span>
        </label>
      </td>
      <td>
        <button type="button" class="btn-danger" onclick="deleteProduct(${index})">Delete</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function updateProductField(index, field, value) {
  if (currentShopData.products && currentShopData.products[index]) {
    currentShopData.products[index][field] = value;
  }
}

function openAddProductModal() {
  const name = prompt("Enter Product Name (e.g. Parle-G Biscuits):");
  if (!name || !name.trim()) return;

  const priceStr = prompt("Enter Price in ₹ (e.g. 20):", "20");
  const price = priceStr ? parseFloat(priceStr) || 0 : 0;

  const unit = prompt("Enter Unit / Quantity (e.g. 250 g, 1 Litre, 1 kg):", "1 pc") || "1 unit";
  const category = prompt("Enter Category (e.g. Snacks, Dairy, Staples):", "General") || "General";

  const newProduct = {
    id: Date.now(),
    name: name.trim(),
    category: category.trim(),
    price: price,
    unit: unit.trim(),
    in_stock: true
  };

  currentShopData.products.unshift(newProduct);
  renderProducts(currentShopData.products);
  showToast("Product added! Remember to click 'Save Products'.");
}

function deleteProduct(index) {
  if (confirm(`Are you sure you want to delete '${currentShopData.products[index].name}'?`)) {
    currentShopData.products.splice(index, 1);
    renderProducts(currentShopData.products);
    showToast("Product removed.");
  }
}

// ---------------- FAQs Management ----------------

function renderFaqs(faqs) {
  const container = document.getElementById("faqsListContainer");
  container.innerHTML = "";

  if (!faqs || faqs.length === 0) {
    container.innerHTML = `<p style="text-align: center; color: #9ca3af; padding: 20px;">No FAQs added yet. Click '+ Add FAQ' to add common questions.</p>`;
    return;
  }

  faqs.forEach((faq, index) => {
    const card = document.createElement("div");
    card.className = "admin-card";
    card.style.marginBottom = "12px";
    card.style.backgroundColor = "#fafafa";
    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px;">
        <div style="flex: 1;">
          <div class="form-group" style="margin-bottom: 8px;">
            <label class="form-label">Question</label>
            <input type="text" class="form-control" value="${escapeAttr(faq.question)}" 
                   onchange="updateFaqField(${index}, 'question', this.value)">
          </div>
          <div class="form-group" style="margin-bottom: 0;">
            <label class="form-label">Answer</label>
            <textarea class="form-control" rows="2" 
                      onchange="updateFaqField(${index}, 'answer', this.value)">${escapeHtml(faq.answer)}</textarea>
          </div>
        </div>
        <button type="button" class="btn-danger" style="margin-top: 24px;" onclick="deleteFaq(${index})">Delete</button>
      </div>
    `;
    container.appendChild(card);
  });
}

function updateFaqField(index, field, value) {
  if (currentShopData.faqs && currentShopData.faqs[index]) {
    currentShopData.faqs[index][field] = value;
  }
}

function openAddFaqModal() {
  const question = prompt("Enter FAQ Question (e.g. Do you accept credit/khata?):");
  if (!question || !question.trim()) return;

  const answer = prompt("Enter FAQ Answer:", "") || "";

  currentShopData.faqs.unshift({
    question: question.trim(),
    answer: answer.trim()
  });

  renderFaqs(currentShopData.faqs);
  showToast("FAQ added! Click 'Save FAQs'.");
}

function deleteFaq(index) {
  if (confirm("Delete this FAQ?")) {
    currentShopData.faqs.splice(index, 1);
    renderFaqs(currentShopData.faqs);
    showToast("FAQ removed.");
  }
}

// ---------------- Save All Shop Data ----------------

async function saveAllShopData() {
  // Collect shop info from form inputs
  currentShopData.shop_info = {
    name: document.getElementById("shopNameInput").value.trim(),
    owner_name: document.getElementById("ownerNameInput").value.trim(),
    phone: document.getElementById("shopPhoneInput").value.trim(),
    whatsapp: document.getElementById("shopWhatsappInput").value.trim(),
    address: document.getElementById("shopAddressInput").value.trim(),
    landmark: document.getElementById("shopLandmarkInput").value.trim(),
    timings: document.getElementById("shopTimingsInput").value.trim(),
    payment_methods: document.getElementById("shopPaymentInput").value.trim(),
    delivery_info: document.getElementById("shopDeliveryInput").value.trim()
  };

  try {
    const res = await fetch("/api/admin/shop-data", {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(currentShopData)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Failed to save data" }));
      showToast(`Error: ${err.detail}`);
      return;
    }

    showToast("✅ All shop data saved to shop_data.json!");
  } catch (err) {
    showToast("Network error saving shop data.");
  }
}

// ---------------- Customer Conversations Viewer ----------------

async function fetchConversations() {
  const container = document.getElementById("conversationsContainer");
  container.innerHTML = `<p style="text-align: center; color: var(--text-muted);">Refreshing conversations...</p>`;

  try {
    const res = await fetch("/api/admin/conversations", {
      headers: getAuthHeaders()
    });

    if (!res.ok) {
      container.innerHTML = `<p style="color: #ef4444;">Failed to fetch conversations log.</p>`;
      return;
    }

    const data = await res.json();
    const list = data.conversations || [];

    if (list.length === 0) {
      container.innerHTML = `<p style="text-align: center; color: var(--text-muted); padding: 24px;">No customer inquiries recorded yet. Questions asked on the chat page will appear here.</p>`;
      return;
    }

    // Show newest first
    const reversed = [...list].reverse();
    container.innerHTML = "";

    reversed.forEach((conv) => {
      const item = document.createElement("div");
      item.className = "conversation-card";

      const badgeType = conv.input_type === "voice" 
        ? `<span class="badge" style="background:#e0e7ff; color:#3730a3;">🎙️ Voice</span>` 
        : `<span class="badge" style="background:#f1f5f9; color:#475569;">⌨️ Text</span>`;

      const contactBadge = conv.contact_owner_suggested 
        ? `<span class="badge badge-danger">Contact Owner Triggered</span>` 
        : "";

      item.innerHTML = `
        <div class="conv-header">
          <div>
            <span>🕒 ${conv.timestamp || "Recent"}</span> &nbsp;|&nbsp;
            <span>🌐 ${conv.language || "Unknown"}</span>
          </div>
          <div style="display:flex; gap: 4px;">
            ${badgeType}
            ${contactBadge}
          </div>
        </div>
        <div class="conv-q">Customer: "${escapeHtml(conv.question)}"</div>
        <div class="conv-a">DukaanSathi: ${escapeHtml(conv.answer)}</div>
      `;
      container.appendChild(item);
    });

  } catch (err) {
    container.innerHTML = `<p style="color: #ef4444;">Connection error fetching conversations.</p>`;
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

function escapeAttr(text) {
  if (!text) return "";
  return String(text).replace(/"/g, "&quot;");
}
