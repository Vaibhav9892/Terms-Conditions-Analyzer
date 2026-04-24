"""
evaluator.py
Evaluation: compare full RAG output vs naive baseline.

Three metrics:
  1. Key-term coverage  — legal terms found in output text
  2. Clause detection   — how many of 8 clause types were identified (RAG only)
  3. Readability        — avg sentence length (shorter = more readable)
"""
import re
from typing import Dict, List


# Terms that should appear in a thorough T&C analysis output
TC_KEY_TERMS = [
    # High-frequency legal concepts (likely in any T&C)
    "data", "privacy", "terminate", "liability",
    "subscription", "renewal", "agreement", "rights", "consent",
    # Mid-frequency — appear in many T&Cs
    "arbitration", "third party", "personal information",
    "intellectual property", "payment", "refund",
    # Lower-frequency — bonus coverage
    "warranty", "indemnif", "jurisdiction", "governing",
]

ALL_CLAUSE_TYPES = [
    "data_sharing", "auto_renewal", "arbitration",
    "liability_limitation", "privacy", "termination",
    "payment_terms", "intellectual_property",
]


def baseline_summarize(text: str, max_words: int = 150) -> str:
    """Naive baseline: first N words of the document."""
    words = text.split()
    return " ".join(words[:max_words]) + ("..." if len(words) > max_words else "")


def key_term_coverage(text: str, terms: List[str] = TC_KEY_TERMS) -> float:
    """Fraction of key terms present in text (case-insensitive, substring match)."""
    t = text.lower()
    covered = sum(1 for term in terms if term.lower() in t)
    return round(covered / len(terms), 3) if terms else 0.0


def clause_detection_score(score_result: Dict) -> Dict:
    """
    Measures how many clause types were detected by the RAG system.
    Baseline always scores 0 here (it extracts nothing).
    """
    found = score_result.get("found_clauses", [])
    return {
        "clauses_detected":   len(found),
        "clauses_total":      len(ALL_CLAUSE_TYPES),
        "detection_rate":     round(len(found) / len(ALL_CLAUSE_TYPES), 3),
        "high_risk_found":    len(score_result.get("high_risk_clauses", [])),
        "detected_list":      found,
    }


def avg_sentence_length(text: str) -> float:
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    if not sentences:
        return 0.0
    return round(sum(len(s.split()) for s in sentences) / len(sentences), 1)


def build_full_rag_text(summary: Dict, clauses: Dict, risk_analysis: Dict) -> str:
    """
    Combine ALL RAG output into one string for evaluation.
    Includes: TL;DR, rights, obligations, red flags, clause excerpts, risk reasons.
    This is what we actually measure — NOT just the TL;DR alone.
    """
    parts = []

    # Summary fields
    for field in ("tldr", "overall_verdict", "verdict_reason"):
        val = summary.get(field, "")
        if val:
            parts.append(str(val))

    for field in ("key_rights", "key_obligations", "red_flags"):
        for item in summary.get(field, []):
            parts.append(str(item))

    # Clause excerpts
    for ctype, cdata in clauses.items():
        if isinstance(cdata, dict) and cdata.get("found"):
            parts.append(cdata.get("notes", ""))
            for ex in cdata.get("excerpts", []):
                parts.append(ex)

    # Risk analysis
    for rtype, rdata in risk_analysis.items():
        if isinstance(rdata, dict):
            parts.append(rdata.get("risk_reason", ""))
            parts.append(rdata.get("user_impact", ""))

    return " ".join(p for p in parts if p)


def evaluate(
    summary: Dict,
    clauses: Dict,
    risk_analysis: Dict,
    score_result: Dict,
    original_text: str,
) -> Dict:
    """
    Full evaluation of RAG output vs naive baseline.
    Pass the raw dicts — we build the full text internally.
    """
    rag_full_text = build_full_rag_text(summary, clauses, risk_analysis)
    baseline_text = baseline_summarize(original_text)

    rag_cov  = key_term_coverage(rag_full_text)
    base_cov = key_term_coverage(baseline_text)
    clause_d = clause_detection_score(score_result)

    return {
        # Coverage
        "rag_key_term_coverage":        rag_cov,
        "baseline_key_term_coverage":   base_cov,
        "coverage_improvement":         round(rag_cov - base_cov, 3),
        "coverage_improvement_pct":     round((rag_cov - base_cov) / max(base_cov, 0.001) * 100, 1),
        # Clause detection (RAG-only metric — baseline always 0)
        "clauses_detected":             clause_d["clauses_detected"],
        "clauses_total":                clause_d["clauses_total"],
        "clause_detection_rate":        clause_d["detection_rate"],
        "high_risk_found":              clause_d["high_risk_found"],
        "detected_clauses":             clause_d["detected_list"],
        # Readability
        "rag_avg_sentence_length":      avg_sentence_length(rag_full_text),
        "baseline_avg_sentence_length": avg_sentence_length(baseline_text),
        # Word counts
        "rag_word_count":               len(rag_full_text.split()),
        "baseline_word_count":          len(baseline_text.split()),
        "original_word_count":          len(original_text.split()),
        "compression_ratio":            round(len(rag_full_text.split()) / max(len(original_text.split()), 1), 4),
        # For display
        "baseline_text":                baseline_text,
        "rag_tldr":                     summary.get("tldr", ""),
    }
