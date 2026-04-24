"""
agents.py — Multi-agent pipeline
Compatible with LangChain v0.2+ | Robust JSON parsing for all providers
"""
import json
import re
from typing import Dict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# ─── Robust JSON extractor ────────────────────────────────────────────────────
def _parse_json(raw: str) -> Dict:
    """
    Multi-strategy JSON extraction — handles all LLM output styles:
    1. Plain JSON
    2. ```json ... ``` fenced blocks
    3. ``` ... ``` fenced blocks
    4. JSON object found anywhere in the text via regex
    """
    raw = raw.strip()

    # Strategy 1: direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Strategy 2: strip ```json ... ``` or ``` ... ``` fences
    fenced = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.IGNORECASE)
    fenced = re.sub(r'\s*```$', '', fenced).strip()
    try:
        return json.loads(fenced)
    except json.JSONDecodeError:
        pass

    # Strategy 3: find first {...} block in the text (handles extra prose before/after)
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Strategy 4: find last {...} block (sometimes LLMs add preamble)
    matches = list(re.finditer(r'\{.*?\}', raw, re.DOTALL))
    if matches:
        try:
            return json.loads(matches[-1].group())
        except json.JSONDecodeError:
            pass

    # All strategies failed — return raw for debugging
    return {"_raw": raw, "_parse_error": True}


def _parse_failed(result: Dict) -> bool:
    return "_parse_error" in result or "_raw" in result


# ─────────────────────────────────────────────────────────────────────────────
class ClauseExtractorAgent:
    CLAUSE_TYPES = [
        "data_sharing", "auto_renewal", "arbitration",
        "liability_limitation", "privacy", "termination",
        "payment_terms", "intellectual_property",
    ]

    SYSTEM = """You are a legal analyst extracting clauses from Terms & Conditions.
Respond with ONLY a JSON object — no prose, no explanation, no markdown."""

    HUMAN = """Analyze this T&C text and extract clauses for these categories:
{clause_types}

TEXT:
{context}

Return ONLY a JSON object. For each clause type use this exact structure:
{{
  "data_sharing": {{
    "found": true,
    "excerpts": ["verbatim quote from text..."],
    "notes": "one sentence explanation"
  }},
  "auto_renewal": {{
    "found": false,
    "excerpts": [],
    "notes": "not found in document"
  }}
}}

Include ALL 8 clause types. Set found=false for missing ones. JSON ONLY:"""

    def __init__(self, llm):
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM),
            ("human", self.HUMAN),
        ])
        self.chain = prompt | llm | StrOutputParser()

    def extract(self, context: str) -> Dict:
        raw = self.chain.invoke({
            "context": context,
            "clause_types": ", ".join(self.CLAUSE_TYPES),
        })
        result = _parse_json(raw)
        if _parse_failed(result):
            # Build fallback structure so pipeline continues
            fallback = {}
            for ct in self.CLAUSE_TYPES:
                fallback[ct] = {"found": False, "excerpts": [], "notes": "parse error"}
            fallback["_raw"] = raw
            return fallback
        return result


# ─────────────────────────────────────────────────────────────────────────────
class RiskAnalyzerAgent:
    SYSTEM = """You are a consumer-rights expert assessing risk in Terms & Conditions.
Respond with ONLY a JSON object — no prose, no explanation, no markdown."""

    HUMAN = """Analyze risk for these found clauses:
{clauses}

Supporting context:
{context}

Return ONLY a JSON object. For each clause type include:
{{
  "data_sharing": {{
    "risk_level": "high",
    "risk_reason": "why this harms the user",
    "user_impact": "plain English effect on the average person"
  }}
}}

Only include clause types that were found. JSON ONLY:"""

    def __init__(self, llm):
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM),
            ("human", self.HUMAN),
        ])
        self.chain = prompt | llm | StrOutputParser()

    def analyze(self, clauses: Dict, context: str) -> Dict:
        found = {k: v for k, v in clauses.items()
                 if isinstance(v, dict) and v.get("found") and not k.startswith("_")}
        if not found:
            return {}
        raw = self.chain.invoke({
            "clauses": json.dumps(found, indent=2),
            "context": context,
        })
        result = _parse_json(raw)
        if _parse_failed(result):
            return {"_raw": raw}
        return result


# ─────────────────────────────────────────────────────────────────────────────
class SummarizerAgent:
    SYSTEM = """You are a consumer advocate explaining legal documents in plain English.
Respond with ONLY a JSON object — no prose, no explanation, no markdown."""

    HUMAN = """Summarize this Terms & Conditions for a regular user.

Document context:
{context}

Risk findings:
{risk_analysis}

Return ONLY this exact JSON structure (fill in the values):
{{
  "tldr": "2-3 sentence plain English summary of what the user is agreeing to",
  "key_rights": [
    "right 1",
    "right 2",
    "right 3"
  ],
  "key_obligations": [
    "obligation 1",
    "obligation 2",
    "obligation 3"
  ],
  "red_flags": [
    "concerning clause 1",
    "concerning clause 2"
  ],
  "overall_verdict": "High Concern",
  "verdict_reason": "one sentence reason for the verdict"
}}

overall_verdict must be exactly one of: "User-Friendly" | "Moderate Concern" | "High Concern" | "Very Concerning"
JSON ONLY:"""

    def __init__(self, llm):
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM),
            ("human", self.HUMAN),
        ])
        self.chain = prompt | llm | StrOutputParser()

    def summarize(self, context: str, risk_analysis: Dict) -> Dict:
        raw = self.chain.invoke({
            "context": context,
            "risk_analysis": json.dumps(risk_analysis, indent=2),
        })
        result = _parse_json(raw)
        if _parse_failed(result):
            # Return the raw text as tldr so the UI still shows something
            return {
                "tldr": raw[:500] if raw else "Summary generation failed — see raw output below.",
                "key_rights": [],
                "key_obligations": [],
                "red_flags": ["⚠️ JSON parsing failed — raw LLM output shown in TL;DR above."],
                "overall_verdict": "Moderate Concern",
                "verdict_reason": "Could not parse structured output.",
                "_raw": raw,
                "_parse_error": True,
            }
        return result
