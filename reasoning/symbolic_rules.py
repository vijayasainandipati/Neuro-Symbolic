"""
Layer 5 & 6 - Symbolic Rules Engine.
Deterministic first-order logic rules for Emergency Information Intelligence.
Guarantees transparent, verifiable decision-making without neural hallucinations.
"""

from typing import Optional, Tuple, Dict, Any
from utils.schemas import SourceType, StanceType, VerificationStatus, EvidenceMatch


class SymbolicRuleEngine:
    """
    Evaluates grounded evidence and source tiers through deterministic logic rules.
    """

    RULES_CATALOG = {
        "RULE_1_OFFICIAL_SUPPORTED": {
            "name": "Official Authority Confirmation",
            "description": "Source is sovereign disaster authority and claim is directly grounded in official emergency guidelines.",
            "status": VerificationStatus.SUPPORTED,
            "badge": "🟢 SUPPORTED"
        },
        "RULE_2_COMMUNITY_CORROBORATED": {
            "name": "Non-Official Direct Corroboration",
            "description": "Community/media alert is corroborated by official guidance records.",
            "status": VerificationStatus.SUPPORTED,
            "badge": "🟢 SUPPORTED"
        },
        "RULE_3_OFFICIAL_CONFLICT": {
            "name": "Authoritative Contradiction (Rumor/Misinformation)",
            "description": "Non-official message explicitly contradicts active official bulletins and verified facts.",
            "status": VerificationStatus.CONFLICTING,
            "badge": "🟠 CONFLICTING"
        },
        "RULE_4_UNVERIFIED_UNSUPPORTED": {
            "name": "Absence of Grounded Evidence",
            "description": "No authoritative disaster documentation or credible field corroboration found for this claim.",
            "status": VerificationStatus.UNSUPPORTED,
            "badge": "🔴 UNSUPPORTED"
        },
        "RULE_5_TEMPORAL_SUPERSEDED": {
            "name": "Temporal Staleness / Superseded Alert",
            "description": "Older situation report contradicted by a newer authoritative command bulletin.",
            "status": VerificationStatus.STALE,
            "badge": "⚠️ STALE"
        }
    }

    def evaluate(
        self,
        source_type: SourceType,
        source_weight: float,
        best_evidence: Optional[EvidenceMatch],
        is_stale: bool = False,
        stale_reason: Optional[str] = None
    ) -> Tuple[VerificationStatus, str, str, float, str]:
        """
        Executes first-order symbolic logic rules over the extracted parameters.
        Returns: (status, rule_id, rule_desc, confidence, explanation)
        """

        # Rule 5: Check Staleness first
        if is_stale:
            rule_id = "RULE_5_TEMPORAL_SUPERSEDED"
            rule_info = self.RULES_CATALOG[rule_id]
            explanation = (
                f"Flagged as STALE. {stale_reason or 'This alert was issued prior to a newer official advisory.'} "
                f"Ground conditions have been officially updated."
            )
            return VerificationStatus.STALE, rule_id, rule_info["description"], 0.94, explanation

        # Rule 4: No credible evidence or stance is UNKNOWN
        if best_evidence is None or best_evidence.stance == StanceType.UNKNOWN or best_evidence.relevance_score < 0.25:
            rule_id = "RULE_4_UNVERIFIED_UNSUPPORTED"
            rule_info = self.RULES_CATALOG[rule_id]
            explanation = (
                "Flagged as UNSUPPORTED. No matching official records or verified disaster advisories corroborate this claim. "
                "Citizens should treat this message with caution until formally verified."
            )
            return VerificationStatus.UNSUPPORTED, rule_id, rule_info["description"], 0.88, explanation

        # Rule 3: Official Contradiction (Rumor)
        if best_evidence.stance == StanceType.CONTRADICTS:
            if source_type != SourceType.OFFICIAL:
                rule_id = "RULE_3_OFFICIAL_CONFLICT"
                rule_info = self.RULES_CATALOG[rule_id]
                explanation = (
                    f"Flagged as CONFLICTING (RUMOR). Official document '{best_evidence.doc_title}' contradicts "
                    f"this assertion: \"{best_evidence.excerpt}\". Official emergency guidance supersedes public posts."
                )
                return VerificationStatus.CONFLICTING, rule_id, rule_info["description"], 0.96, explanation

        # Rule 1: Official Source + Grounded
        if source_type == SourceType.OFFICIAL:
            rule_id = "RULE_1_OFFICIAL_SUPPORTED"
            rule_info = self.RULES_CATALOG[rule_id]
            explanation = (
                f"Verified as SUPPORTED. Issued by sovereign disaster authority and grounded in official advisory "
                f"'{best_evidence.doc_title}'."
            )
            return VerificationStatus.SUPPORTED, rule_id, rule_info["description"], 0.99, explanation

        # Rule 2: Non-official corroborated
        if best_evidence.stance == StanceType.SUPPORTS:
            rule_id = "RULE_2_COMMUNITY_CORROBORATED"
            rule_info = self.RULES_CATALOG[rule_id]
            explanation = (
                f"Verified as SUPPORTED. Public/community report is corroborated by official document "
                f"'{best_evidence.doc_title}': \"{best_evidence.excerpt}\"."
            )
            return VerificationStatus.SUPPORTED, rule_id, rule_info["description"], 0.89, explanation

        # Default fallback
        rule_id = "RULE_4_UNVERIFIED_UNSUPPORTED"
        rule_info = self.RULES_CATALOG[rule_id]
        explanation = "Flagged as UNSUPPORTED. Stance could not be verified against official databases."
        return VerificationStatus.UNSUPPORTED, rule_id, rule_info["description"], 0.80, explanation


symbolic_rules = SymbolicRuleEngine()
