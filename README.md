# Terms-Conditions-Analyzer
# ⚖️ T&C Analyzer — RAG + Multi-Agent Risk Assessment

An AI agent that reads Terms & Conditions documents, extracts key clauses,
assesses consumer risk, and generates a plain-English summary.

## Architecture

```
PDF / Text
    ↓
DocumentProcessor  (pdfplumber, chunking)
    ↓
VectorStore        (OpenAI embeddings → FAISS index)
    ↓ RAG retrieval
Agent 1: ClauseExtractorAgent  →  8 clause types + excerpts
Agent 2: RiskAnalyzerAgent     →  low/medium/high per clause
Agent 3: SummarizerAgent       →  TL;DR, rights, red flags, verdict
    ↓
RiskScorer         →  weighted 1–10 score
    ↓
Streamlit UI       →  results + JSON/MD export
```

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/Vaibhav9892/Terms-Conditions-Analyzer
cd tc-analyzer

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API key

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 3. Run

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Project Structure

```
tc-analyzer/
├── app.py                      # Streamlit web UI (main entry point)
├── config.py                   # Centralized config / env vars
├── requirements.txt
├── .env.example                # Copy to .env
├── architecture.html           # Visual architecture diagram
├── README.md
└── src/
    ├── __init__.py
    ├── document_processor.py   # PDF/text loading + chunking
    ├── vector_store.py         # FAISS vector DB wrapper
    ├── agents.py               # 3 LangChain agents
    ├── risk_scorer.py          # Weighted risk score (1–10)
    └── evaluator.py            # Baseline comparison metrics
```

## Key Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| LLM | GPT-4o-mini | Best cost/quality for structured extraction |
| Embeddings | text-embedding-3-small | Fast + cheap, 1536-dim |
| Vector DB | FAISS (in-memory) | No setup needed, great for prototyping |
| Framework | LangChain | Abstracts prompts, chains, retrievers |
| UI | Streamlit | Fastest path to demo-ready interface |
| Evaluation | Key-term coverage | Simple, interpretable, no reference needed |

## Evaluation

The system compares against a **naive baseline** (first 150 words):

| Metric | Baseline | RAG System |
|---|---|---|
| Key-term coverage | ~15–25% | ~60–80% |
| Avg sentence length | Long (raw legal text) | Short (plain English) |
| Clause detection | None | 8 structured types |

## Extending This Project

- **Better evaluation**: Add ROUGE-L with human-written reference summaries
- **Multi-document**: Compare T&C across multiple companies
- **Privacy audit**: Flag GDPR/CCPA violations specifically
- **Fine-tuning**: Fine-tune on T&C datasets (ToS;DR dataset)
- **Better vector DB**: Replace FAISS with Pinecone/Chroma for persistence



# Chrome Extension

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
| Groq (Llama 3.3 70B) |  Free | console.groq.com |
| OpenAI (GPT-4o-mini) |  ~$0.001/analysis | platform.openai.com |
