"""
risk_scorer.py
Computes a weighted 1-10 risk score from agent outputs.
"""
from typing import Dict, List


class RiskScorer:
    # Higher weight = more impact on final score
    WEIGHTS: Dict[str, float] = {
        "data_sharing":        2.0,
        "privacy":             2.0,
        "arbitration":         1.8,
        "liability_limitation": 1.5,
        "auto_renewal":        1.5,
        "termination":         1.2,
        "payment_terms":       1.0,
        "intellectual_property": 1.0,
    }
    RISK_VALUES = {"low": 2, "medium": 5, "high": 9}
    VERDICT_COLORS = {
        "User-Friendly":    "#22c55e",
        "Moderate Concern": "#f59e0b",
        "High Concern":     "#ef4444",
        "Very Concerning":  "#991b1b",
    }

    def compute(self, clauses: Dict, risk_analysis: Dict) -> Dict:
        breakdown: Dict[str, Dict] = {}
        weighted_sum = 0.0
        total_weight = 0.0

        for clause_type, weight in self.WEIGHTS.items():
            clause_data = clauses.get(clause_type, {})
            risk_data = risk_analysis.get(clause_type, {})

            if isinstance(clause_data, dict) and clause_data.get("found"):
                risk_level = risk_data.get("risk_level", "medium")
                raw_score = self.RISK_VALUES.get(risk_level, 5)
                breakdown[clause_type] = {
                    "found": True,
                    "risk_level": risk_level,
                    "score": raw_score,
                    "weight": weight,
                    "excerpts": clause_data.get("excerpts", []),
                    "notes": clause_data.get("notes", ""),
                    "risk_reason": risk_data.get("risk_reason", ""),
                    "user_impact": risk_data.get("user_impact", ""),
                }
                weighted_sum += raw_score * weight
                total_weight += weight
            else:
                breakdown[clause_type] = {"found": False, "risk_level": "none", "score": 0}

        overall = round(min(10.0, max(1.0, weighted_sum / total_weight)), 1) if total_weight else 1.0

        if overall <= 3:
            category, badge_color = "Low Risk", "#22c55e"
        elif overall <= 5:
            category, badge_color = "Moderate Risk", "#f59e0b"
        elif overall <= 7.5:
            category, badge_color = "High Risk", "#ef4444"
        else:
            category, badge_color = "Very High Risk", "#991b1b"

        high_risk = [k for k, v in breakdown.items() if v.get("risk_level") == "high"]
        found = [k for k, v in breakdown.items() if v.get("found")]

        return {
            "overall_score": overall,
            "category": category,
            "badge_color": badge_color,
            "breakdown": breakdown,
            "high_risk_clauses": high_risk,
            "found_clauses": found,
            "clause_count": len(found),
        }
