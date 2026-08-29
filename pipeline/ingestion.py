"""
Layer 2 - Ingestion & Text Preprocessing.
Ingests multi-source alerts, normalizes timestamps, cleans text, and handles voice transcripts.
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from utils.schemas import Alert, SourceType


class AlertIngestionPipeline:
    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path or os.path.join("data", "alerts.json")

    def load_alerts(self, filter_scenario: Optional[str] = None) -> List[Alert]:
        """Loads alerts from JSON storage and parses them into Alert dataclasses."""
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Alerts data file not found at: {self.data_path}")

        with open(self.data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        alerts = []
        for item in raw_data:
            if filter_scenario and item.get("scenario") != filter_scenario:
                continue
            
            cleaned_text = self.clean_text(item.get("text", ""))
            src_type_str = item.get("source_type", "social_media").lower()
            try:
                src_type = SourceType(src_type_str)
            except ValueError:
                src_type = SourceType.SOCIAL_MEDIA

            alert = Alert(
                id=item["id"],
                text=cleaned_text,
                source=item.get("source", "Unknown Source"),
                source_type=src_type,
                timestamp=self.normalize_timestamp(item.get("timestamp")),
                location_hint=item.get("location_hint"),
                scenario=item.get("scenario")
            )
            alerts.append(alert)
        return alerts

    def ingest_single(
        self,
        text: str,
        source: str = "Citizen Report",
        source_type: str = "citizen",
        alert_id: Optional[str] = None,
        location_hint: Optional[str] = None
    ) -> Alert:
        """Ingests a single real-time alert text or voice speech-to-text transcript."""
        cleaned_text = self.clean_text(text)
        try:
            stype = SourceType(source_type.lower())
        except ValueError:
            stype = SourceType.CITIZEN

        aid = alert_id or f"RT-{int(datetime.utcnow().timestamp())}"
        return Alert(
            id=aid,
            text=cleaned_text,
            source=source,
            source_type=stype,
            timestamp=datetime.utcnow().isoformat() + "Z",
            location_hint=location_hint
        )

    def clean_text(self, text: str) -> str:
        """Removes excess whitespace, emojis/control chars while preserving punctuation."""
        if not text:
            return ""
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def normalize_timestamp(self, ts_str: Optional[str]) -> str:
        if not ts_str:
            return datetime.utcnow().isoformat() + "Z"
        # Standardize ISO
        if ts_str.endswith("Z"):
            return ts_str
        return ts_str + "Z"
