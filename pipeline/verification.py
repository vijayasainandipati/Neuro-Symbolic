"""
Layer 5 & 6 - Pipeline Verification Orchestrator.
Processes raw alerts or clustered events through neuro-symbolic verification and audit logging.
"""

from typing import List, Dict, Any, Tuple
from utils.schemas import Alert, AlertCluster, VerificationResult
from reasoning.verification_engine import verification_engine
from reasoning.audit_logger import audit_logger
from models.llm_extractor import llm_extractor


class VerificationPipeline:
    def __init__(self):
        self.engine = verification_engine
        self.logger = audit_logger

    def verify_alerts(self, alerts: List[Alert], clusters: List[AlertCluster]) -> List[VerificationResult]:
        """Runs neuro-symbolic verification on all alerts across clusters."""
        results: List[VerificationResult] = []

        # Map alert ID to cluster ID
        alert_to_cluster = {}
        for c in clusters:
            for a in c.alerts:
                alert_to_cluster[a.id] = c.cluster_id

        for alert in alerts:
            claim = llm_extractor.extract_from_text(alert.id, alert.text)
            cid = alert_to_cluster.get(alert.id, "EVENT-00")
            verif = self.engine.verify_claim(alert, claim, cluster_id=cid, all_alerts=alerts)
            results.append(verif)

        # Log audit trail
        self.logger.log_verification_batch(results)
        return results


verification_pipeline = VerificationPipeline()
