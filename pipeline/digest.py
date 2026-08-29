"""
Layer 7 - Emergency Digest & Shareable Checklist Generator.
Transforms noisy alerts into a verified, actionable Emergency Intelligence Digest.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.schemas import (
    Alert, AlertCluster, VerificationResult, VerificationStatus,
    EmergencyDigest, EmergencyDigestItem
)
from utils.metrics import calculate_noise_reduction


class EmergencyDigestGenerator:
    def generate_digest(
        self,
        alerts: List[Alert],
        clusters: List[AlertCluster],
        verification_results: List[VerificationResult],
        region_name: str = "Coastal Disaster Zone (Kanyakumari District)"
    ) -> EmergencyDigest:
        """
        Synthesizes verified claims into structured executive digest and action checklist.
        """
        total_alerts = len(alerts)
        total_clusters = len(clusters)
        noise_red = calculate_noise_reduction(total_alerts, total_clusters)

        # Count statuses
        status_counts = {"SUPPORTED": 0, "CONFLICTING": 0, "UNSUPPORTED": 0, "STALE": 0}
        for v in verification_results:
            st = v.status.value if hasattr(v.status, "value") else str(v.status)
            status_counts[st] = status_counts.get(st, 0) + 1

        items: List[EmergencyDigestItem] = []
        checklist: List[str] = []
        warnings: List[str] = []

        # Deduplicate verified items by (location, event_type, status)
        seen_topics = set()

        for v in verification_results:
            topic_key = f"{v.location.lower()}::{v.event_type.lower()}::{v.status.value if hasattr(v.status, 'value') else v.status}"
            if topic_key in seen_topics:
                continue
            seen_topics.add(topic_key)

            st_val = v.status.value if hasattr(v.status, "value") else str(v.status)

            if st_val == "SUPPORTED":
                if "evacuat" in v.event_type.lower() or "flood" in v.event_type.lower() or "cyclone" in v.event_type.lower():
                    priority = 1
                    cat = "EVACUATION & SAFETY"
                    badge = "🟢 SUPPORTED"
                else:
                    priority = 2
                    cat = "OPERATIONAL STATUS"
                    badge = "🟢 SUPPORTED"

                items.append(EmergencyDigestItem(
                    item_id=f"DIG-{v.claim_id}",
                    priority_level=priority,
                    category=cat,
                    title=f"{v.location}: {v.claim_text}",
                    key_action=v.recommended_action,
                    deadline="Follow active timeline",
                    status_badge=badge,
                    source_note=f"Verified via {v.source_name}",
                    why_flagged_summary=v.explanation,
                    verification_detail=v
                ))

                if "evacuat" in v.recommended_action.lower() or "avoid" in v.recommended_action.lower() or "proceed" in v.recommended_action.lower():
                    checklist.append(f"☐ {v.recommended_action}")

            elif st_val == "CONFLICTING":
                items.append(EmergencyDigestItem(
                    item_id=f"DIG-{v.claim_id}",
                    priority_level=3,
                    category="DEBUNKED RUMOR",
                    title=f"⚠️ RUMOR ALERT: \"{v.claim_text}\"",
                    key_action=f"Disregard false claim. {v.official_evidence.excerpt if v.official_evidence else ''}",
                    deadline="Immediate notice",
                    status_badge="🟠 CONFLICTING",
                    source_note=f"Flagged non-official message ({v.source_name})",
                    why_flagged_summary=v.explanation,
                    verification_detail=v
                ))
                warnings.append(f"Do not circulate rumors regarding '{v.location}'. Official advisory confirms normal/safe status.")

            elif st_val == "UNSUPPORTED":
                items.append(EmergencyDigestItem(
                    item_id=f"DIG-{v.claim_id}",
                    priority_level=4,
                    category="UNVERIFIED CLAIM",
                    title=f"❓ UNVERIFIED: \"{v.claim_text}\"",
                    key_action="Awaiting official verification. Rely only on District Command broadcasts.",
                    deadline="Pending confirmation",
                    status_badge="🔴 UNSUPPORTED",
                    source_note=f"Unverified source ({v.source_name})",
                    why_flagged_summary=v.explanation,
                    verification_detail=v
                ))
                warnings.append(f"Unverified claims circulating for {v.location}. Treat with high caution.")

            elif st_val == "STALE":
                items.append(EmergencyDigestItem(
                    item_id=f"DIG-{v.claim_id}",
                    priority_level=3,
                    category="OBSOLETE ADVISORY",
                    title=f"⚠️ SUPERSEDED: \"{v.claim_text}\"",
                    key_action="Follow newest official advisory.",
                    deadline="Obsolete",
                    status_badge="⚠️ STALE",
                    source_note=f"Outdated post ({v.source_name})",
                    why_flagged_summary=v.explanation,
                    verification_detail=v
                ))

        # Sort items: Priority 1 first
        items.sort(key=lambda x: x.priority_level)

        # Standard safety checklist additions if empty
        if not checklist:
            checklist = [
                "☐ Evacuate designated red zones before deadline",
                "☐ Move to nearest operational relief shelter",
                "☐ Carry identity documents, medications and clean water",
                "☐ Keep emergency mobile phones charged",
                "☐ Follow official verified updates on Toll-Free 1077"
            ]

        return EmergencyDigest(
            digest_title="🛡️ NeuroSym Crisis — Emergency Intelligence Digest",
            region=region_name,
            generated_at=datetime.utcnow().strftime("%d %b %Y, %H:%M UTC"),
            total_alerts_processed=total_alerts,
            total_events_clustered=total_clusters,
            noise_reduction_percentage=noise_red,
            counts_by_status=status_counts,
            items=items,
            shareable_checklist=list(dict.fromkeys(checklist)),
            warnings=list(dict.fromkeys(warnings))
        )


digest_generator = EmergencyDigestGenerator()
