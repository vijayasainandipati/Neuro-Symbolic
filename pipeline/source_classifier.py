"""
Layer 2 & 4 - Source Trust & Priority Classifier.
Calculates source authority weights and priority hierarchy.
"""

from typing import Dict, Tuple
from utils.schemas import SourceType, Alert


class SourceClassifier:
    """
    Classifies source reliability and assigns deterministic priority tiers.
    Official > Verified News > First Responders/Community > Citizens > Unverified Social Media
    """
    SOURCE_TIERS: Dict[SourceType, Tuple[int, float, str]] = {
        SourceType.OFFICIAL: (1, 1.0, "Tier 1: Sovereign Disaster Authority / Police / IMD"),
        SourceType.NEWS: (2, 0.8, "Tier 2: Verified Regional News & Media Desks"),
        SourceType.COMMUNITY: (3, 0.6, "Tier 3: First Responders / Ward Committees / NGOs"),
        SourceType.CITIZEN: (4, 0.4, "Tier 4: Eye-Witness Citizen Reports"),
        SourceType.SOCIAL_MEDIA: (5, 0.2, "Tier 5: Unverified Social Media / Forwarded Messaging")
    }

    OFFICIAL_IDENTIFIERS = [
        "ddma", "disaster management", "ndrf", "sdrf", "police", "imd", "meteorological",
        "incois", "relief commission", "district magistrate", "water resources", "fire & rescue",
        "health & medical", "municipal corporation", "electricity board"
    ]

    def classify_source(self, source_name: str, source_type: SourceType) -> Tuple[SourceType, float, str]:
        source_lower = source_name.lower()
        if any(kw in source_lower for kw in self.OFFICIAL_IDENTIFIERS):
            resolved_type = SourceType.OFFICIAL
        else:
            resolved_type = source_type

        tier, weight, desc = self.SOURCE_TIERS.get(
            resolved_type, (5, 0.2, "Tier 5: Unverified Social Media")
        )
        return resolved_type, weight, desc

    def get_priority_weight(self, alert: Alert) -> float:
        resolved_type, weight, _ = self.classify_source(alert.source, alert.source_type)
        return weight
