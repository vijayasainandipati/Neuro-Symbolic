"""
Layer 5 & 6 - Neuro-Symbolic Verification Engine.
Fuses neural extraction, vector evidence retrieval, freshness checks, and symbolic rules.
Generates comprehensive explainability audit records.
"""

from typing import List, Optional, Dict, Any
from utils.schemas import (
    Alert, ExtractedClaim, AlertCluster, VerificationResult,
    VerificationStatus, EvidenceMatch, SourceType
)
from pipeline.source_classifier import SourceClassifier
from pipeline.retrieval import RAGRetrievalEngine, rag_engine
from pipeline.freshness import FreshnessAnalyzer
from reasoning.symbolic_rules import SymbolicRuleEngine, symbolic_rules


class NeuroSymbolicVerificationEngine:
    def __init__(
        self,
        retriever: Optional[RAGRetrievalEngine] = None,
        rules: Optional[SymbolicRuleEngine] = None
    ):
        self.retriever = retriever or rag_engine
        self.rules = rules or symbolic_rules
        self.classifier = SourceClassifier()
        self.freshness = FreshnessAnalyzer()

    def verify_claim(
        self,
        alert: Alert,
        claim: ExtractedClaim,
        cluster_id: str = "EVENT-00",
        all_alerts: Optional[List[Alert]] = None
    ) -> VerificationResult:
        all_alerts = all_alerts or []

        # 1. Source Classification & Priority
        src_type, src_weight, _ = self.classifier.classify_source(alert.source, alert.source_type)

        # 2. RAG Evidence Retrieval
        evidence_matches = self.retriever.retrieve_evidence(
            claim_text=claim.claim,
            event_type=claim.event_type,
            location=claim.location,
            top_k=3
        )
        best_evidence: Optional[EvidenceMatch] = evidence_matches[0] if evidence_matches else None

        # 3. Freshness & Staleness Analysis
        contradicting = (best_evidence is not None and best_evidence.stance.value == "CONTRADICTS")
        is_stale, stale_reason = self.freshness.check_staleness(alert, all_alerts, contradicting)

        # 4. Symbolic Rule Evaluation
        status, rule_id, rule_desc, confidence, explanation = self.rules.evaluate(
            source_type=src_type,
            source_weight=src_weight,
            best_evidence=best_evidence,
            is_stale=is_stale,
            stale_reason=stale_reason
        )

        return VerificationResult(
            claim_id=claim.alert_id,
            cluster_id=cluster_id,
            event_type=claim.event_type,
            location=claim.location,
            claim_text=claim.claim,
            source_name=alert.source,
            source_type=src_type,
            source_priority_weight=src_weight,
            status=status,
            rule_triggered=rule_id,
            rule_description=rule_desc,
            confidence=confidence,
            official_evidence=best_evidence,
            all_evidence=evidence_matches,
            explanation=explanation,
            recommended_action=claim.action,
            timestamp=alert.timestamp
        )

    def verify_cluster(
        self,
        cluster: AlertCluster,
        all_alerts: Optional[List[Alert]] = None
    ) -> List[VerificationResult]:
        results = []
        if not cluster.representative_claim and cluster.alerts:
            from models.llm_extractor import llm_extractor
            cluster.representative_claim = llm_extractor.extract_from_text(
                cluster.alerts[0].id, cluster.alerts[0].text
            )

        for alert in cluster.alerts:
            from models.llm_extractor import llm_extractor
            claim = llm_extractor.extract_from_text(alert.id, alert.text)
            verif = self.verify_claim(alert, claim, cluster.cluster_id, all_alerts)
            results.append(verif)

        return results


verification_engine = NeuroSymbolicVerificationEngine()
