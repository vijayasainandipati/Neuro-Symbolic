"""
Layer 5 - Freshness & Temporal Precedence Analyzer.
Detects outdated reports superseded by newer official bulletins.
Answers: "Is this emergency message obsolete due to newer authoritative updates?"
"""

from datetime import datetime
from typing import List, Dict, Optional, Tuple
from utils.schemas import Alert, SourceType


class FreshnessAnalyzer:
    """
    Evaluates chronological order of claims and determines whether an alert is stale.
    """

    @staticmethod
    def parse_iso(ts_str: str) -> datetime:
        try:
            ts_str = ts_str.rstrip("Z")
            return datetime.fromisoformat(ts_str)
        except Exception:
            return datetime.utcnow()

    def check_staleness(
        self,
        alert: Alert,
        all_alerts: List[Alert],
        contradicting_official: bool
    ) -> Tuple[bool, Optional[str]]:
        """
        Checks if an alert's claim has been superseded by a newer official notice.
        """
        if alert.source_type == SourceType.OFFICIAL:
            return False, None

        if not alert.timestamp:
            return False, None

        alert_time = self.parse_iso(alert.timestamp)

        for other in all_alerts:
            if other.id == alert.id:
                continue
            if other.source_type == SourceType.OFFICIAL:
                other_time = self.parse_iso(other.timestamp)
                # If official alert is strictly newer
                if (other_time - alert_time).total_seconds() > 300:  # At least 5 mins newer
                    loc_match = False
                    if alert.location_hint and other.location_hint:
                        if alert.location_hint.strip().lower() == other.location_hint.strip().lower():
                            loc_match = True

                    if not loc_match:
                        # Check keyword match
                        for kw in ["bridge", "bypass", "shelter", "hospital", "pass", "underpass"]:
                            if kw in alert.text.lower() and kw in other.text.lower():
                                loc_match = True
                                break

                    if loc_match:
                        return True, f"Superseded by newer official bulletin at {other.timestamp} issued by '{other.source}'"

        return False, None
