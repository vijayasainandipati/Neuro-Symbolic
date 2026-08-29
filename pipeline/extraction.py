"""
Layer 3 - Information Extraction Stage.
Coordinates LLM / structured entity extraction for alerts and alert clusters.
"""

from typing import List, Dict
from utils.schemas import Alert, ExtractedClaim, AlertCluster
from models.llm_extractor import llm_extractor


class ExtractionPipeline:
    def __init__(self):
        self.extractor = llm_extractor

    def extract_alert_claim(self, alert: Alert) -> ExtractedClaim:
        return self.extractor.extract_from_text(alert.id, alert.text)

    def extract_batch(self, alerts: List[Alert]) -> List[ExtractedClaim]:
        return [self.extract_alert_claim(a) for a in alerts]

    def enrich_cluster(self, cluster: AlertCluster) -> AlertCluster:
        """Ensures the cluster has a high-fidelity representative claim and unified metadata."""
        if not cluster.representative_claim:
            if cluster.alerts:
                cluster.representative_claim = self.extract_alert_claim(cluster.alerts[0])
        return cluster
