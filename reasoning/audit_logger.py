"""
Layer 6 - Audit Logger.
Maintains full explainability audit trails for all verification steps.
Logs decision traces into audit_log.json.
"""

import json
import os
from typing import List, Dict, Any
from datetime import datetime
from utils.schemas import VerificationResult


class AuditLogger:
    def __init__(self, log_path: str = "audit_log.json"):
        self.log_path = log_path

    def log_verification_batch(self, results: List[VerificationResult]):
        entries = []
        for r in results:
            entry = {
                "trace_id": f"TRC-{r.claim_id}-{int(datetime.utcnow().timestamp())}",
                "timestamp": r.timestamp,
                "claim_id": r.claim_id,
                "cluster_id": r.cluster_id,
                "claim_text": r.claim_text,
                "source": {
                    "name": r.source_name,
                    "type": r.source_type.value if hasattr(r.source_type, "value") else str(r.source_type),
                    "priority_weight": r.source_priority_weight
                },
                "official_evidence": {
                    "doc_title": r.official_evidence.doc_title if r.official_evidence else "None",
                    "excerpt": r.official_evidence.excerpt if r.official_evidence else "No relevant document found",
                    "relevance_score": r.official_evidence.relevance_score if r.official_evidence else 0.0,
                    "stance": r.official_evidence.stance.value if r.official_evidence and hasattr(r.official_evidence.stance, "value") else "UNKNOWN"
                } if r.official_evidence else None,
                "neuro_symbolic_reasoning": {
                    "rule_triggered": r.rule_triggered,
                    "rule_description": r.rule_description,
                    "final_status": r.status.value if hasattr(r.status, "value") else str(r.status),
                    "confidence": r.confidence,
                    "explanation": r.explanation
                },
                "recommended_action": r.recommended_action
            }
            entries.append(entry)

        existing = []
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, list):
                        existing = loaded
                    else:
                        existing = []
            except Exception:
                existing = []

        existing.extend(entries)
        # Keep last 200 entries
        existing = existing[-200:]

        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        if not os.path.exists(self.log_path):
            return []
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                logs = json.load(f)
                if isinstance(logs, list):
                    return logs[-limit:]
                return []
        except Exception:
            return []


audit_logger = AuditLogger()
