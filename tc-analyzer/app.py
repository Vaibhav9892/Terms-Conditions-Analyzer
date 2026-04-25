"""
app.py  —  T&C Analyzer  |  RAG + Multi-Agent Pipeline
"""
import json
import time
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="T&C Analyzer | AI Risk Agent",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)
#CSS markdown because it looks aesthetic using bootstrap templates
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.score-card {
    background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3e 100%);
    border-radius: 16px; padding: 32px; text-align: center;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3); margin-bottom: 1rem;
}
.score-number { font-size: 72px; font-weight: 700; line-height: 1; margin: 8px 0; }
.score-label  { font-size: 14px; color: #a0a0b0; letter-spacing: 0.1em; text-transform: uppercase; }
.score-badge  { display: inline-block; padding: 4px 16px; border-radius: 999px; font-size: 13px; font-weight: 600; margin-top: 12px; }
.clause-excerpt {
    font-family: 'JetBrains Mono', monospace; font-size: 12px;
    background: #0f0f1a; border-left: 3px solid #6366f1;
    padding: 8px 12px; border-radius: 4px; margin: 8px 0;
    color: #c4c4d4; white-space: pre-wrap; word-break: break-word;
}
.risk-pill { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; letter-spacing: 0.05em; }
.risk-high   { background: #450a0a; color: #fca5a5; }
.risk-medium { background: #451a03; color: #fcd34d; }
.risk-low    { background: #052e16; color: #86efac; }
.risk-none   { background: #1e293b; color: #64748b; }
.tldr-banner { background: linear-gradient(90deg,#1e3a5f,#1a2f4a); border-left: 4px solid #3b82f6; border-radius: 8px; padding: 16px 20px; margin-bottom: 16px; font-size: 15px; line-height: 1.7; color: #e2e8f0; }
.red-flag { background: #1c0a0a; border: 1px solid #7f1d1d; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px; font-size: 14px; color: #fca5a5; }
.verdict-banner { border-radius: 8px; padding: 14px 18px; font-weight: 600; font-size: 15px; text-align: center; margin: 12px 0; }
.metric-row { display: flex; gap: 16px; flex-wrap: wrap; margin: 12px 0; }
.metric-box { flex: 1; min-width: 120px; background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 10px; padding: 14px; text-align: center; }
.metric-val { font-size: 28px; font-weight: 700; color: #93c5fd; }
.metric-lbl { font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 2px; }
.section-header { font-size: 13px; font-weight: 600; color: #6366f1; text-transform: uppercase; letter-spacing: 0.1em; border-bottom: 1px solid #2a2a4a; padding-bottom: 8px; margin: 20px 0 12px; }
.provider-badge { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; }
.free-badge { background: #052e16; color: #86efac; border: 1px solid #166534; }
.paid-badge { background: #1c1a03; color: #fcd34d; border: 1px solid #92400e; }
.local-badge{ background: #1e1a2e; color: #c4b5fd; border: 1px solid #6d28d9; }
</style>
""", unsafe_allow_html=True)

#Risk Constants
RISK_ICONS = {"high": "🔴", "medium": "🟡", "low": "🟢", "none": "⚪"}
CLAUSE_LABELS = {
    "data_sharing": "Data Sharing", "auto_renewal": "Auto-Renewal",
    "arbitration": "Arbitration / Disputes", "liability_limitation": "Liability Limitation",
    "privacy": "Privacy Policy", "termination": "Termination Rights",
    "payment_terms": "Payment Terms", "intellectual_property": "Intellectual Property",
}
VERDICT_STYLES = {
    "User-Friendly":    ("background:#052e16;color:#86efac;border:1px solid #166534;", "✅"),
    "Moderate Concern": ("background:#451a03;color:#fcd34d;border:1px solid #92400e;", "⚠️"),
    "High Concern":     ("background:#450a0a;color:#fca5a5;border:1px solid #991b1b;", "🚨"),
    "Very Concerning":  ("background:#3b0764;color:#e879f9;border:1px solid #7e22ce;", "🛑"),
}
PROVIDER_INFO = {
    "groq":    {"label": "Groq (FREE)",         "badge": "free",  "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"], "key_label": "Groq API Key", "key_placeholder": "gsk_..."},
    "gemini":  {"label": "Google Gemini (FREE)", "badge": "free",  "models": ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"], "key_label": "Gemini API Key", "key_placeholder": "AIza..."},
    "openai":  {"label": "OpenAI (Paid)",        "badge": "paid",  "models": ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"], "key_label": "OpenAI API Key", "key_placeholder": "sk-..."},
    "ollama":  {"label": "Ollama (Local FREE)",  "badge": "local", "models": ["llama3.2", "llama3.1", "mistral", "gemma2"], "key_label": None, "key_placeholder": None},
}

def risk_pill(level):
    cls = f"risk-{level.lower()}" if level.lower() in ("high","medium","low") else "risk-none"
    return f'<span class="risk-pill {cls}">{RISK_ICONS.get(level.lower(),"⚪")} {level.upper()}</span>'

def score_color(s):
    return "#22c55e" if s<=3 else "#f59e0b" if s<=5 else "#ef4444" if s<=7.5 else "#a855f7"

def build_llm(provider, api_key, model, temperature):
    if provider == "groq":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model, temperature=temperature,
            openai_api_key=api_key,
            openai_api_base="https://api.groq.com/openai/v1",
        )
    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model, temperature=temperature, google_api_key=api_key,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model, temperature=temperature, openai_api_key=api_key)
    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, temperature=temperature)
    else:
        raise ValueError(f"Unknown provider: {provider}")

with st.sidebar:
    st.markdown("### ⚖️ T&C Analyzer")
    st.markdown("*RAG + Multi-Agent Risk Assessment*")
    st.divider()

    st.markdown("**🔌 LLM Provider**")
    provider = st.selectbox(
        "Provider", list(PROVIDER_INFO.keys()),
        format_func=lambda k: PROVIDER_INFO[k]["label"],
        label_visibility="collapsed",
    )
    info = PROVIDER_INFO[provider]
    badge_cls = f"{info['badge']}-badge"
    st.markdown(f'<span class="provider-badge {badge_cls}">{info["label"]}</span>', unsafe_allow_html=True)

    api_key = ""
    if provider != "ollama":
        api_key = st.text_input(
            info["key_label"],
            type="password",
            placeholder=info["key_placeholder"],
        )
        if provider == "groq":
            st.markdown("<small style='color:#64748b'>Free key → <a href='https://console.groq.com' target='_blank' style='color:#6366f1'>console.groq.com</a></small>", unsafe_allow_html=True)
        elif provider == "gemini":
            st.markdown("<small style='color:#64748b'>Free key → <a href='https://aistudio.google.com' target='_blank' style='color:#6366f1'>aistudio.google.com</a></small>", unsafe_allow_html=True)
    else:
        st.info("Make sure Ollama is running locally: `ollama serve`")

    model_name = st.selectbox("Model", info["models"])

    st.divider()
    with st.expander("⚙️ Advanced Settings", expanded=False):
        temperature  = st.slider("Temperature", 0.0, 1.0, 0.1, 0.05)
        chunk_size   = st.slider("Chunk Size", 400, 2000, 1000, 100)
        chunk_overlap= st.slider("Chunk Overlap", 50, 400, 200, 50)
        top_k        = st.slider("RAG Top-K", 3, 10, 5)
        embed_choice = st.selectbox("Embeddings", ["huggingface (free, local)", "openai (paid)"])
        embed_provider = "huggingface" if "huggingface" in embed_choice else "openai"
        show_eval    = st.checkbox("Show Evaluation Tab", value=True)

    st.divider()
    st.markdown("""
**Pipeline**
```
PDF/Text → Chunks → FAISS
              ↓ RAG
    Agent 1: Extract Clauses
    Agent 2: Analyze Risk
    Agent 3: Summarize
              ↓
     Risk Score + Report
```
    """)
    st.markdown(f"<small style='color:#64748b'>Embeddings: {'🆓 HuggingFace' if embed_provider=='huggingface' else '💳 OpenAI'}</small>", unsafe_allow_html=True)

st.markdown("## ⚖️ Terms & Conditions Analyzer")
st.markdown("Upload any T&C → plain-English summary, extracted clauses, and a 1–10 risk score.")

tab_upload, tab_results, tab_eval, tab_about = st.tabs(
    ["📄 Upload & Analyze", "📊 Results", "🔬 Evaluation", "📘 About"])

# TAB 1 — UPLOAD 
with tab_upload:
    col_left, col_right = st.columns([1.1, 1], gap="large")

    with col_left:
        st.markdown('<div class="section-header">Input Document</div>', unsafe_allow_html=True)
        input_mode = st.radio("mode", ["📎 Upload PDF", "✏️ Paste Text"], horizontal=True, label_visibility="collapsed")

        doc_text, doc_source, uploaded = "", "document", None

        if input_mode == "📎 Upload PDF":
            uploaded = st.file_uploader("PDF", type=["pdf"], label_visibility="collapsed")
            if uploaded:
                doc_source = uploaded.name
                st.success(f"✅ {uploaded.name} ({uploaded.size:,} bytes)")
        else:
            sample = """TERMS OF SERVICE

1. Data Collection and Sharing
We collect personal information including your name, email, location, and browsing behavior.
We may share your data with third-party advertising partners and data brokers.
By using our service, you consent to this data sharing.

2. Auto-Renewal
Your subscription will automatically renew each month. We will charge your payment method
without further notice. No refunds will be issued for partial periods.

3. Arbitration
ALL DISPUTES SHALL BE RESOLVED BY BINDING ARBITRATION. YOU WAIVE YOUR RIGHT TO A JURY TRIAL
AND TO PARTICIPATE IN CLASS ACTION LAWSUITS. Arbitration shall take place in Delaware.

4. Limitation of Liability
TO THE MAXIMUM EXTENT PERMITTED BY LAW, OUR TOTAL LIABILITY SHALL NOT EXCEED $50.
We are not liable for any indirect, incidental, or consequential damages.

5. Intellectual Property
All content you post on our platform becomes our property. We may use, modify,
and monetize your content without additional compensation to you.

6. Termination
We may terminate your account at any time, for any reason, without notice.
"""
            doc_text = st.text_area("Paste T&C", value=sample, height=300, label_visibility="collapsed")
            if doc_text:
                doc_source = "pasted_text"
                st.info(f"📝 {len(doc_text.split()):,} words")

    with col_right:
        st.markdown('<div class="section-header">Pipeline</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style='background:#0f172a;border:1px solid #1e293b;border-radius:10px;padding:16px;font-size:13px;color:#94a3b8;line-height:2.1'>
        <b style='color:#c4c4d4'>1.</b> Load document (PDF / text)<br>
        <b style='color:#c4c4d4'>2.</b> Chunk into semantic segments<br>
        <b style='color:#c4c4d4'>3.</b> Build FAISS index <span style='color:#64748b'>({'🆓 HuggingFace' if embed_provider=='huggingface' else '💳 OpenAI'} embeddings)</span><br>
        <b style='color:#c4c4d4'>4.</b> RAG retrieval per clause type<br>
        <b style='color:#c4c4d4'>5.</b> 🤖 Agent 1 — Extract clauses<br>
        <b style='color:#c4c4d4'>6.</b> ⚠️ Agent 2 — Analyze risk<br>
        <b style='color:#c4c4d4'>7.</b> 📝 Agent 3 — Summarize<br>
        <b style='color:#c4c4d4'>8.</b> 📊 Weighted risk score (1–10)
        </div>
        """, unsafe_allow_html=True)
        st.markdown("")

        provider_ready = (provider == "ollama") or bool(api_key)
        doc_ready = bool(doc_text) or (uploaded is not None)
        embed_ready = (embed_provider == "huggingface") or bool(api_key)

        if not provider_ready:
            st.warning(f"⬅️ Enter your {info['key_label']} to continue.")
        if not doc_ready:
            st.info("Paste text or upload a PDF to get started.")

        run_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True,
                            disabled=not (provider_ready and doc_ready and embed_ready))

    if run_btn and provider_ready and doc_ready:
        from src.document_processor import DocumentProcessor
        from src.vector_store import VectorStore
        from src.agents import ClauseExtractorAgent, RiskAnalyzerAgent, SummarizerAgent
        from src.risk_scorer import RiskScorer
        from src.evaluator import evaluate

        pb = st.progress(0)
        status = st.empty()
        try:
            # Step 1: Load & chunk
            status.markdown("**⏳ Step 1/5 — Loading document…**")
            processor = DocumentProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            if input_mode == "📎 Upload PDF":
                chunks, full_text = processor.process(uploaded.read(), uploaded.name, "pdf")
            else:
                chunks, full_text = processor.process(doc_text, "pasted_text", "text")
            pb.progress(15)

            # Step 2: Vector store
            openai_key_for_embed = api_key if (provider == "openai" and embed_provider == "openai") else ""
            status.markdown(f"**⏳ Step 2/5 — Building FAISS index ({embed_provider} embeddings)…**")
            if embed_provider == "huggingface":
                status.markdown("**⏳ Step 2/5 — Loading HuggingFace model (first run downloads ~90MB)…**")
            vs = VectorStore(provider=embed_provider, api_key=openai_key_for_embed)
            vs.build(chunks)
            pb.progress(30)

            # Step 3: LLM + agents
            status.markdown(f"**⏳ Step 3/5 — Initializing {info['label']} agents…**")
            llm = build_llm(provider, api_key, model_name, temperature)
            extractor  = ClauseExtractorAgent(llm)
            risk_agent = RiskAnalyzerAgent(llm)
            summarizer = SummarizerAgent(llm)
            scorer     = RiskScorer()
            pb.progress(42)

            # Step 4: Agent 1: Extract
            status.markdown("**⏳ Step 4/5 — Agent 1: Extracting clauses via RAG…**")
            extract_context = "\n\n---\n\n".join(
                vs.get_context(q, k=top_k) for q in [
                    "data sharing third party personal information privacy",
                    "auto renewal subscription payment terms refund",
                    "arbitration dispute resolution class action waiver",
                    "liability limitation indemnification warranty",
                    "termination account suspension intellectual property",
                ])
            clauses = extractor.extract(extract_context)
            pb.progress(62)

            # Step 5: Agent 2 + 3
            status.markdown("**⏳ Step 5/5 — Agent 2 & 3: Risk + Summary…**")
            risk_context    = vs.get_context("user rights data privacy liability risk harm consumer", k=top_k)
            risk_analysis   = risk_agent.analyze(clauses, risk_context)
            summary_context = vs.get_context("agreement terms conditions user obligations rights", k=top_k)
            summary         = summarizer.summarize(summary_context, risk_analysis)
            score_result    = scorer.compute(clauses, risk_analysis)

            from src.evaluator import baseline_summarize
            baseline     = baseline_summarize(full_text)
            eval_metrics = evaluate(summary, clauses, risk_analysis, score_result, full_text)
            pb.progress(100)
            status.success(f"✅ Done! Powered by **{info['label']}** · Switch to the Results tab.")
            time.sleep(1); status.empty(); pb.empty()

            st.session_state["results"] = {
                "clauses": clauses, "risk_analysis": risk_analysis,
                "summary": summary, "score": score_result,
                "eval": eval_metrics, "baseline": baseline,
                "chunk_count": len(chunks), "word_count": len(full_text.split()),
                "provider": info["label"], "model": model_name,
                "raw_summary": summary.get("_raw",""),
                "parse_error": summary.get("_parse_error", False),
            }

        except Exception as e:
            pb.empty(); status.error(f"❌ {e}")
            with st.expander("Traceback"):
                import traceback; st.code(traceback.format_exc())

with tab_results:
    if "results" not in st.session_state:
        st.info("👈 Run an analysis first."); st.stop()

    r = st.session_state["results"]
    score, summary, clauses = r["score"], r["summary"], r["clauses"]

    # Show debug warning if JSON parsing failed | I made it on a mac so it can sometimes fail on windows. sorry
    if r.get("parse_error"):
        with st.expander("⚠️ JSON Parse Warning — click to see raw LLM output", expanded=True):
            st.warning("The LLM returned a response that could not be fully parsed as JSON. The TL;DR below shows the raw output. This usually means the model added extra prose around the JSON — try switching to a different model (e.g. llama-3.3-70b-versatile or gpt-4o-mini).")
            st.code(r.get("raw_summary", ""), language="text")

    col_score, col_meta = st.columns([1, 2], gap="large")
    with col_score:
        s = score["overall_score"]; col_s = score_color(s)
        st.markdown(f"""
        <div class="score-card">
            <div class="score-label">Overall Risk Score</div>
            <div class="score-number" style="color:{col_s}">{s}</div>
            <div style="color:#64748b;font-size:13px">out of 10</div>
            <span class="score-badge" style="background:{col_s}22;color:{col_s};border:1px solid {col_s}66">{score['category']}</span>
        </div>""", unsafe_allow_html=True)
        st.markdown(f"<center><small style='color:#64748b'>via {r['provider']} · {r['model']}</small></center>", unsafe_allow_html=True)

    with col_meta:
        st.markdown('<div class="section-header">Document Snapshot</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="metric-row">
          <div class="metric-box"><div class="metric-val">{r['word_count']:,}</div><div class="metric-lbl">Words</div></div>
          <div class="metric-box"><div class="metric-val">{r['chunk_count']}</div><div class="metric-lbl">Chunks</div></div>
          <div class="metric-box"><div class="metric-val">{score['clause_count']}</div><div class="metric-lbl">Clauses</div></div>
          <div class="metric-box"><div class="metric-val">{len(score['high_risk_clauses'])}</div><div class="metric-lbl">High Risk</div></div>
        </div>""", unsafe_allow_html=True)
        verdict = summary.get("overall_verdict","")
        if verdict in VERDICT_STYLES:
            vstyle, vicon = VERDICT_STYLES[verdict]
            st.markdown(f'<div class="verdict-banner" style="{vstyle}">{vicon} {verdict}</div>', unsafe_allow_html=True)
        reason = summary.get("verdict_reason","")
        if reason: st.markdown(f"<small style='color:#94a3b8'>{reason}</small>", unsafe_allow_html=True)

    st.divider()
    tldr = summary.get("tldr","")
    if tldr:
        st.markdown('<div class="section-header">TL;DR</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="tldr-banner">💬 {tldr}</div>', unsafe_allow_html=True)

    col_r, col_o = st.columns(2, gap="medium")
    with col_r:
        st.markdown('<div class="section-header">✅ Your Rights</div>', unsafe_allow_html=True)
        for item in summary.get("key_rights",[]): st.markdown(f"• {item}")
    with col_o:
        st.markdown('<div class="section-header">📋 Your Obligations</div>', unsafe_allow_html=True)
        for item in summary.get("key_obligations",[]): st.markdown(f"• {item}")

    red_flags = summary.get("red_flags",[])
    if red_flags:
        st.markdown('<div class="section-header">🚨 Red Flags</div>', unsafe_allow_html=True)
        for flag in red_flags: st.markdown(f'<div class="red-flag">⚠️ {flag}</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="section-header">Clause-by-Clause Breakdown</div>', unsafe_allow_html=True)
    order = {"high":0,"medium":1,"low":2}
    found = {k:v for k,v in score["breakdown"].items() if v.get("found")}
    for ctype, data in sorted(found.items(), key=lambda x: order.get(x[1].get("risk_level","low"),3)):
        label = CLAUSE_LABELS.get(ctype, ctype.replace("_"," ").title())
        level = data.get("risk_level","none")
        icon  = RISK_ICONS.get(level,"⚪")
        with st.expander(f"{icon} {label}  —  {level.upper()}", expanded=(level=="high")):
            st.markdown(risk_pill(level), unsafe_allow_html=True)
            for ex in data.get("excerpts",[])[:2]:
                st.markdown(f'<div class="clause-excerpt">{ex}</div>', unsafe_allow_html=True)
            if data.get("risk_reason"): st.markdown(f"**Why it's risky:** {data['risk_reason']}")
            if data.get("user_impact"):  st.markdown(f"**Impact on you:** {data['user_impact']}")
            elif data.get("notes"):      st.markdown(f"_{data['notes']}_")

    missing = [k for k,v in score["breakdown"].items() if not v.get("found")]
    if missing:
        with st.expander(f"⚪ {len(missing)} clauses not found"):
            for ct in missing: st.markdown(f"- {CLAUSE_LABELS.get(ct, ct)}")

    st.divider()
    report = {"overall_score": score["overall_score"], "category": score["category"],
              "verdict": summary.get("overall_verdict",""), "tldr": summary.get("tldr",""),
              "key_rights": summary.get("key_rights",[]), "key_obligations": summary.get("key_obligations",[]),
              "red_flags": summary.get("red_flags",[]), "provider": r["provider"], "model": r["model"]}
    c1,c2 = st.columns(2)
    c1.download_button("⬇️ JSON Report", json.dumps(report,indent=2), "tc_report.json", "application/json", use_container_width=True)
    md = f"# T&C Analysis\n**Score:** {score['overall_score']}/10 — {score['category']}\n\n## TL;DR\n{summary.get('tldr','')}\n\n## Red Flags\n" + "\n".join(f"- {f}" for f in summary.get("red_flags",[]))
    c2.download_button("⬇️ Markdown Report", md, "tc_report.md", "text/markdown", use_container_width=True)


with tab_eval:
    if "results" not in st.session_state: st.info("Run an analysis first."); st.stop()
    if not show_eval: st.info("Enable 'Show Evaluation Tab' in sidebar."); st.stop()
    r  = st.session_state["results"]
    ev = r["eval"]
    st.markdown("### 🔬 RAG vs. Naive Baseline Evaluation")
    st.markdown("The **full RAG output** (extracted clauses + risk analysis + summary) is compared against a naive baseline (first 150 words of the raw document).")

    st.markdown("#### 📌 Clause Detection  *(RAG-only advantage — baseline detects 0)*")
    cd1, cd2, cd3, cd4 = st.columns(4)
    cd1.metric("Clauses Detected",  f"{ev['clauses_detected']} / {ev['clauses_total']}")
    cd2.metric("Detection Rate",    f"{ev['clause_detection_rate']*100:.0f}%", delta=f"+{ev['clause_detection_rate']*100:.0f}% vs baseline")
    cd3.metric("High-Risk Flagged", str(ev['high_risk_found']))
    cd4.metric("Baseline Detects",  "0",  delta="-100%", delta_color="off")
    if ev.get("detected_clauses"):
        st.markdown("**Detected:** " + " · ".join(f"`{c.replace('_',' ')}`" for c in ev["detected_clauses"]))

    st.divider()
    st.markdown("#### 📖 Key-Term Coverage  *(legal terms found in full output)*")
    c1, c2, c3 = st.columns(3)
    c1.metric("RAG Full Output",    f"{ev['rag_key_term_coverage']*100:.1f}%", delta=f"+{ev['coverage_improvement']*100:.1f}%")
    c2.metric("Baseline (150 words)", f"{ev['baseline_key_term_coverage']*100:.1f}%")
    c3.metric("Improvement",        f"{ev['coverage_improvement_pct']:.1f}%")
    st.caption("Terms: data, privacy, arbitration, liability, renewal, consent, personal information, intellectual property, warranty, jurisdiction, and more.")

    st.divider()
    st.markdown("#### 💬 Readability  *(shorter avg sentence = more readable)*")
    c4, c5, c6 = st.columns(3)
    c4.metric("RAG Avg Sentence",      f"{ev['rag_avg_sentence_length']:.1f} words")
    c5.metric("Baseline Avg Sentence", f"{ev['baseline_avg_sentence_length']:.1f} words")
    c6.metric("Compression Ratio",     f"{ev['compression_ratio']:.3f}")

    st.divider()
    st.markdown("#### Naive Baseline (raw first 150 words)")
    st.markdown(f'<div style="background:#1e293b;border-radius:8px;padding:14px;font-size:13px;color:#94a3b8;line-height:1.7">{ev.get("baseline_text", r.get("baseline",""))}</div>', unsafe_allow_html=True)
    st.markdown("#### RAG TL;DR (plain-English — for users, not metrics)")
    st.markdown(f'<div class="tldr-banner">💬 {ev.get("rag_tldr") or r["summary"].get("tldr","")}</div>', unsafe_allow_html=True)
    st.info("💡 **Note:** The TL;DR is intentionally jargon-free, so measuring it alone gives a misleadingly low score. The metrics above measure the *full RAG output* including extracted clauses and risk reasons.")


with tab_about:
    st.markdown("""
## About

RAG + Multi-Agent pipeline for T&C risk analysis. Supports free and paid LLM providers.

### Supported Providers

| Provider | Cost | Model Examples | Get Key |
|---|---|---|---|
| **Groq** | 🆓 Free | Llama 3.3 70B, Mixtral 8x7B | console.groq.com |
| **Google Gemini** | 🆓 Free tier | Gemini 2.0 Flash, 1.5 Pro | aistudio.google.com |
| **Ollama** | 🆓 Local | Llama3.2, Mistral, Gemma2 | ollama.com |
| **OpenAI** | 💳 Paid | GPT-4o-mini, GPT-4o | platform.openai.com |

### Embeddings
- **HuggingFace `all-MiniLM-L6-v2`** (default) — free, runs locally, 90MB download on first use
- **OpenAI `text-embedding-3-small`** — paid, better quality

### Architecture
```
User Input (PDF / Text)
    ↓
DocumentProcessor   → pdfplumber + RecursiveCharacterTextSplitter
    ↓
VectorStore         → HuggingFace/OpenAI embeddings → FAISS index
    ↓ RAG (Top-K retrieval)
Agent 1: ClauseExtractorAgent   → 8 clause types, verbatim excerpts
Agent 2: RiskAnalyzerAgent      → low/medium/high per clause
Agent 3: SummarizerAgent        → TL;DR, rights, red flags, verdict
    ↓
RiskScorer                      → weighted 1–10 score
    ↓
Streamlit UI                    → results + JSON/MD export
```

### Risk Score Formula
Score = Σ(wᵢ · rᵢ) / Σwᵢ  where rᵢ ∈ {2, 5, 9} for low/medium/high risk.
Data sharing and privacy carry weight 2.0 · Arbitration 1.8 · Liability/Auto-renewal 1.5
    """)
