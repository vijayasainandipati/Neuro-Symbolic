"""
Comprehensive Unit and Integration Tests for NeuroSym Crisis.
Validates all 7 layers of the Neuro-Symbolic Crisis Information Intelligence architecture.
"""

import unittest
import os
import sys

# Add workspace root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.schemas import Alert, SourceType, VerificationStatus, StanceType
from pipeline.ingestion import AlertIngestionPipeline
from pipeline.clustering import EventClusterer
from pipeline.source_classifier import SourceClassifier
from pipeline.retrieval import RAGRetrievalEngine
from pipeline.freshness import FreshnessAnalyzer
from models.llm_extractor import LLMExtractor
from models.embeddings import EmbeddingEngine
from reasoning.symbolic_rules import SymbolicRuleEngine
from reasoning.verification_engine import NeuroSymbolicVerificationEngine
from pipeline.digest import EmergencyDigestGenerator
from utils.metrics import calculate_noise_reduction, calculate_rumor_filter_metrics


class TestNeuroSymCrisis(unittest.TestCase):

    def setUp(self):
        self.ingestion = AlertIngestionPipeline()
        self.clusterer = EventClusterer()
        self.extractor = LLMExtractor()
        self.retriever = RAGRetrievalEngine()
        self.rules = SymbolicRuleEngine()
        self.verifier = NeuroSymbolicVerificationEngine()
        self.digest_gen = EmergencyDigestGenerator()

    def test_layer1_and_2_ingestion_and_cleaning(self):
        alert = self.ingestion.ingest_single(
            text="  URGENT:   Zone A is flooding!   Please evacuate!  ",
            source="District Disaster Authority",
            source_type="official"
        )
        self.assertEqual(alert.source_type, SourceType.OFFICIAL)
        self.assertEqual(alert.text, "URGENT: Zone A is flooding! Please evacuate!")

    def test_layer3_neural_extraction(self):
        claim = self.extractor.extract_from_text(
            "A01",
            "Mandatory evacuation ordered for Zone A before 6:00 PM due to rising water."
        )
        self.assertEqual(claim.location, "Zone A")
        self.assertEqual(claim.event_type, "evacuation")
        self.assertIn("6:00 PM", claim.deadline_time)
        self.assertIn("Evacuate", claim.action)

    def test_layer4_event_clustering(self):
        alerts = [
            Alert(id="T1", text="Flooding reported in Zone A.", source="News", source_type=SourceType.NEWS),
            Alert(id="T2", text="Water levels rising in Zone A.", source="User1", source_type=SourceType.CITIZEN),
            Alert(id="T3", text="Zone A residents asked to evacuate.", source="User2", source_type=SourceType.CITIZEN)
        ]
        clusters = self.clusterer.cluster_alerts(alerts)
        self.assertGreaterEqual(len(clusters), 1)
        # All refer to Zone A
        zone_a_clusters = [c for c in clusters if c.location == "Zone A"]
        self.assertGreaterEqual(len(zone_a_clusters), 1)

    def test_layer5_rag_retrieval_and_stance(self):
        # Contradiction test: Shelter A is closed vs knowledge base (Shelter A is open)
        matches = self.retriever.retrieve_evidence("Shelter A is closed and waterlogged", location="Shelter A", top_k=1)
        self.assertTrue(len(matches) > 0)
        self.assertEqual(matches[0].stance, StanceType.CONTRADICTS)

        # Support test: North River Bridge is closed
        matches_bridge = self.retriever.retrieve_evidence("North River Bridge is strictly closed", location="North River Bridge", top_k=1)
        self.assertTrue(len(matches_bridge) > 0)
        self.assertEqual(matches_bridge[0].stance, StanceType.SUPPORTS)

    def test_layer5_and_6_symbolic_rules_and_conflict_detection(self):
        # False rumor: Shelter A closed from social media -> CONFLICTING
        alert = Alert(id="R1", text="Shelter A is closed", source="WhatsApp Group", source_type=SourceType.SOCIAL_MEDIA)
        claim = self.extractor.extract_from_text(alert.id, alert.text)
        res = self.verifier.verify_claim(alert, claim)
        self.assertEqual(res.status, VerificationStatus.CONFLICTING)
        self.assertEqual(res.rule_triggered, "RULE_3_OFFICIAL_CONFLICT")

        # Unsupported rumor: Alien spaceships -> UNSUPPORTED
        alert_unsupported = Alert(id="R2", text="Alien spaceships cause storm", source="Forum", source_type=SourceType.SOCIAL_MEDIA)
        claim_u = self.extractor.extract_from_text(alert_unsupported.id, alert_unsupported.text)
        res_u = self.verifier.verify_claim(alert_unsupported, claim_u)
        self.assertEqual(res_u.status, VerificationStatus.UNSUPPORTED)
        self.assertEqual(res_u.rule_triggered, "RULE_4_UNVERIFIED_UNSUPPORTED")

    def test_layer7_digest_and_checklist_generation(self):
        alerts = self.ingestion.load_alerts(filter_scenario="Scenario F")
        clusters = self.clusterer.cluster_alerts(alerts)
        results = [self.verifier.verify_claim(a, self.extractor.extract_from_text(a.id, a.text), all_alerts=alerts) for a in alerts]
        digest = self.digest_gen.generate_digest(alerts, clusters, results)

        self.assertIsNotNone(digest.digest_title)
        self.assertGreater(len(digest.items), 0)
        self.assertGreater(len(digest.shareable_checklist), 0)
        self.assertGreater(digest.noise_reduction_percentage, 0)

    def test_noise_reduction_metric(self):
        red = calculate_noise_reduction(80, 23)
        self.assertAlmostEqual(red, 71.25, delta=0.1)


if __name__ == "__main__":
    unittest.main()
