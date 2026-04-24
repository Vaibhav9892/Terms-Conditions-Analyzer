// popup.js — T&C Analyzer Extension
// Calls Groq (or OpenAI/Gemini) API directly from the extension

const PROVIDERS = {
  groq: {
    label: "Groq (Free)",
    url: "https://api.groq.com/openai/v1/chat/completions",
    models: ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
    keyPlaceholder: "gsk_...",
    keyLink: "https://console.groq.com",
    keyLinkText: "console.groq.com",
  },
  openai: {
    label: "OpenAI (Paid)",
    url: "https://api.openai.com/v1/chat/completions",
    models: ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
    keyPlaceholder: "sk-...",
    keyLink: "https://platform.openai.com/api-keys",
    keyLinkText: "platform.openai.com",
  },
};

const MAX_CHARS = 12000; // ~3000 tokens — enough for any T&C

// ── Prompt ────────────────────────────────────────────────────────────────────
function buildPrompt(text) {
  return `You are a consumer-rights expert analyzing Terms & Conditions.
Analyze the following T&C text and respond with ONLY a valid JSON object — no prose, no markdown fences.

T&C TEXT:
${text.slice(0, MAX_CHARS)}

Return this exact JSON structure:
{
  "risk_score": <number 1-10, where 10 is most risky>,
  "verdict": <exactly one of: "User-Friendly" | "Moderate Concern" | "High Concern" | "Very Concerning">,
  "tldr": "<2-3 plain English sentences — what is the user really agreeing to?>",
  "red_flags": ["<flag 1>", "<flag 2>", "<flag 3>"],
  "clauses": {
    "data_sharing":         {"found": <bool>, "risk": "<none|low|medium|high>", "summary": "<1 sentence or empty>"},
    "auto_renewal":         {"found": <bool>, "risk": "<none|low|medium|high>", "summary": "<1 sentence or empty>"},
    "arbitration":          {"found": <bool>, "risk": "<none|low|medium|high>", "summary": "<1 sentence or empty>"},
    "liability_limitation": {"found": <bool>, "risk": "<none|low|medium|high>", "summary": "<1 sentence or empty>"},
    "privacy":              {"found": <bool>, "risk": "<none|low|medium|high>", "summary": "<1 sentence or empty>"},
    "termination":          {"found": <bool>, "risk": "<none|low|medium|high>", "summary": "<1 sentence or empty>"}
  }
}

JSON ONLY — no text before or after:`;
}

// ── JSON extraction (multi-strategy) ─────────────────────────────────────────
function extractJSON(raw) {
  // 1. Direct
  try { return JSON.parse(raw.trim()); } catch {}
  // 2. Strip fences
  const stripped = raw.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/,'').trim();
  try { return JSON.parse(stripped); } catch {}
  // 3. Find first {...}
  const m = raw.match(/\{[\s\S]*\}/);
  if (m) { try { return JSON.parse(m[0]); } catch {} }
  return null;
}

// ── API call ──────────────────────────────────────────────────────────────────
async function callLLM(text, settings) {
  const provider = PROVIDERS[settings.provider] || PROVIDERS.groq;
  const response = await fetch(provider.url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${settings.apiKey}`,
    },
    body: JSON.stringify({
      model: settings.model,
      messages: [{ role: "user", content: buildPrompt(text) }],
      temperature: 0.1,
      max_tokens: 1500,
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err?.error?.message || `HTTP ${response.status}`);
  }

  const data = await response.json();
  const raw = data.choices?.[0]?.message?.content || "";
  const parsed = extractJSON(raw);
  if (!parsed) throw new Error("Could not parse LLM response as JSON. Try again or switch model.");
  return parsed;
}

// ── UI helpers ────────────────────────────────────────────────────────────────
function scoreColor(s) {
  if (s <= 3) return "#3fb950";
  if (s <= 5) return "#d29922";
  if (s <= 7.5) return "#f85149";
  return "#bc8cff";
}

function verdictStyle(v) {
  const map = {
    "User-Friendly":    { bg: "#052e16", color: "#86efac", border: "#166534" },
    "Moderate Concern": { bg: "#451a03", color: "#fcd34d", border: "#92400e" },
    "High Concern":     { bg: "#450a0a", color: "#fca5a5", border: "#991b1b" },
    "Very Concerning":  { bg: "#3b0764", color: "#e879f9", border: "#7e22ce" },
  };
  return map[v] || map["Moderate Concern"];
}

const CLAUSE_LABELS = {
  data_sharing:         "Data Sharing",
  auto_renewal:         "Auto-Renewal",
  arbitration:          "Arbitration",
  liability_limitation: "Liability Cap",
  privacy:              "Privacy",
  termination:          "Termination",
};
const RISK_ICONS = { high: "🔴", medium: "🟡", low: "🟢", none: "⚪" };

function renderResults(result) {
  const score   = Math.min(10, Math.max(1, Number(result.risk_score) || 5));
  const verdict = result.verdict || "Moderate Concern";
  const tldr    = result.tldr || "Analysis complete.";
  const flags   = Array.isArray(result.red_flags) ? result.red_flags : [];
  const clauses = result.clauses || {};
  const vs      = verdictStyle(verdict);
  const col     = scoreColor(score);

  document.getElementById("results").innerHTML = `
    <div class="results">

      <!-- Score -->
      <div class="score-bar-wrap">
        <div class="score-top">
          <div>
            <span class="score-num" style="color:${col}">${score.toFixed(1)}</span>
            <span class="score-denom"> / 10</span>
          </div>
          <span class="verdict-pill" style="background:${vs.bg};color:${vs.color};border:1px solid ${vs.border}">
            ${verdict}
          </span>
        </div>
        <div class="score-bar-bg">
          <div class="score-bar-fill" style="width:${score*10}%;background:${col}"></div>
        </div>
      </div>

      <!-- TL;DR -->
      <div class="section-title">TL;DR</div>
      <div class="tldr-box">💬 ${tldr}</div>

      <!-- Clauses -->
      <div class="section-title">Detected Clauses</div>
      <div class="clause-grid">
        ${Object.entries(clauses).map(([key, val]) => {
          const risk = val?.risk || "none";
          const found = val?.found;
          if (!found) return `<span class="clause-chip chip-none" title="Not found">${CLAUSE_LABELS[key] || key}</span>`;
          const chipClass = `chip-${risk}`;
          const icon = RISK_ICONS[risk] || "⚪";
          const tip = val.summary || "";
          return `<span class="clause-chip ${chipClass}" title="${tip}">${icon} ${CLAUSE_LABELS[key] || key}</span>`;
        }).join("")}
      </div>

      <!-- Red Flags -->
      ${flags.length > 0 ? `
      <div class="section-title">🚨 Red Flags</div>
      <div class="flag-list">
        ${flags.map(f => `
          <div class="flag-item">
            <span class="flag-icon">⚠️</span>
            <span>${f}</span>
          </div>`).join("")}
      </div>` : ""}

    </div>
  `;
}

function showLoading(msg = "Analyzing with AI…") {
  document.getElementById("results").innerHTML = `
    <div class="loading">
      <div class="spinner"></div>
      <div class="loading-text">${msg}</div>
    </div>`;
}

function showError(msg) {
  document.getElementById("results").innerHTML = `<div class="error-box">❌ ${msg}</div>`;
}

function showEmpty() {
  document.getElementById("results").innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">⚖️</div>
      <div class="empty-text">Paste any Terms & Conditions text above<br>and click <b>Analyze</b> to get a risk assessment.</div>
    </div>`;
}

// ── Settings persistence ──────────────────────────────────────────────────────
function loadSettings(cb) {
  chrome.storage.local.get(["apiKey","provider","model"], cb);
}
function saveSettings(settings, cb) {
  chrome.storage.local.set(settings, cb);
}

function populateModels(provider) {
  const sel = document.getElementById("modelSel");
  const models = PROVIDERS[provider]?.models || [];
  sel.innerHTML = models.map(m => `<option value="${m}">${m}</option>`).join("");
}

function updateKeyInfo(provider) {
  const p = PROVIDERS[provider];
  document.getElementById("apiKeyInput").placeholder = p?.keyPlaceholder || "API key...";
  document.getElementById("keyInfoLink").href = p?.keyLink || "#";
  document.getElementById("keyInfoLink").textContent = p?.keyLinkText || "";
}

// ── Main ──────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const textarea    = document.getElementById("tcText");
  const analyzeBtn  = document.getElementById("analyzeBtn");
  const grabBtn     = document.getElementById("grabBtn");
  const wordCount   = document.getElementById("wordCount");

  // Tabs
  document.querySelectorAll(".tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
      tab.classList.add("active");
      document.getElementById(tab.dataset.view).classList.add("active");
    });
  });

  // Word count
  textarea.addEventListener("input", () => {
    const words = textarea.value.trim().split(/\s+/).filter(Boolean).length;
    const chars = textarea.value.length;
    wordCount.textContent = `${words.toLocaleString()} words · ${chars.toLocaleString()} chars`;

    const warn = document.getElementById("charWarn");
    if (chars > MAX_CHARS) {
      warn.style.display = "block";
      warn.textContent = `⚠️ Text truncated to ${MAX_CHARS.toLocaleString()} chars for analysis (first ${MAX_CHARS.toLocaleString()} chars used).`;
    } else {
      warn.style.display = "none";
    }
  });

  // Grab text from active tab
  grabBtn.addEventListener("click", async () => {
    grabBtn.disabled = true;
    grabBtn.textContent = "Grabbing…";
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => document.body.innerText,
      });
      const text = results?.[0]?.result || "";
      textarea.value = text.slice(0, 20000);
      textarea.dispatchEvent(new Event("input"));
    } catch (e) {
      console.error(e);
    }
    grabBtn.disabled = false;
    grabBtn.textContent = "📋 Grab page";
  });

  // Load saved settings
  loadSettings(({ apiKey = "", provider = "groq", model = "" }) => {
    document.getElementById("apiKeyInput").value = apiKey;
    document.getElementById("providerSel").value = provider;
    populateModels(provider);
    updateKeyInfo(provider);
    if (model) document.getElementById("modelSel").value = model;
  });

  // Provider change
  document.getElementById("providerSel").addEventListener("change", e => {
    populateModels(e.target.value);
    updateKeyInfo(e.target.value);
  });

  // Save settings
  document.getElementById("saveSettingsBtn").addEventListener("click", () => {
    const settings = {
      apiKey:   document.getElementById("apiKeyInput").value.trim(),
      provider: document.getElementById("providerSel").value,
      model:    document.getElementById("modelSel").value,
    };
    saveSettings(settings, () => {
      const msg = document.getElementById("saveMsg");
      msg.style.display = "block";
      setTimeout(() => { msg.style.display = "none"; }, 2000);
    });
  });

  // Analyze
  showEmpty();

  analyzeBtn.addEventListener("click", async () => {
    const text = textarea.value.trim();
    if (!text) return;

    const settings = await new Promise(resolve => loadSettings(resolve));
    if (!settings.apiKey) {
      // Switch to settings tab
      document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
      document.querySelector('[data-view="settingsView"]').classList.add("active");
      document.getElementById("settingsView").classList.add("active");
      document.getElementById("apiKeyInput").focus();
      document.getElementById("results").innerHTML = "";
      return;
    }

    analyzeBtn.disabled = true;
    analyzeBtn.textContent = "Analyzing…";
    showLoading(`Analyzing with ${settings.model || "AI"}…`);

    try {
      const result = await callLLM(text, settings);
      renderResults(result);
    } catch (e) {
      showError(e.message || "Unknown error. Check your API key and try again.");
    } finally {
      analyzeBtn.disabled = false;
      analyzeBtn.textContent = "🔍 Analyze";
    }
  });
});
