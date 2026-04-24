# ⚖️ T&C Analyzer — Chrome Extension

Instantly analyze any Terms & Conditions in your browser.
Paste text (or click "Grab page") → get a risk score, TL;DR, and red flags.

## Install (Developer Mode)

1. Open Chrome → go to `chrome://extensions/`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked**
4. Select this folder (`tc-extension/`)
5. The ⚖️ icon appears in your toolbar

## Setup

1. Click the ⚖️ icon → go to **Settings** tab
2. Enter your **free Groq API key** (get one at https://console.groq.com)
3. Click **Save Settings**

## Usage

**Option A — Paste text:**
1. Copy any T&C text from a website
2. Open the extension → paste into the text area
3. Click **Analyze**

**Option B — Grab from page:**
1. Navigate to any T&C page
2. Open the extension
3. Click **📋 Grab page** to auto-fill the text
4. Click **Analyze**

## What You Get

- **Risk Score** (1–10) with color-coded bar
- **Verdict** (User-Friendly / Moderate / High / Very Concerning)
- **TL;DR** — plain English summary
- **Clause chips** — color-coded: 🔴 high / 🟡 medium / 🟢 low
- **Red Flags** — specific concerns to watch out for

## File Structure

```
tc-extension/
├── manifest.json    ← Chrome extension config (Manifest V3)
├── popup.html       ← Extension popup UI
├── popup.css        ← Styling
├── popup.js         ← Logic, API calls, rendering
├── icons/           ← Extension icons
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
└── README.md
```

## Supported Providers

| Provider | Cost | Setup |
|---|---|---|
| Groq (Llama 3.3 70B) | 🆓 Free | console.groq.com |
| OpenAI (GPT-4o-mini) | 💳 ~$0.001/analysis | platform.openai.com |
