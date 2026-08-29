"""
P2P Emergency Message Protocol for NeuroSym Crisis.
Defines standard compact serialization, hop-tracking, TTL decay, and deduplication keys.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, Any, Optional


@dataclass
class P2PMessage:
    id: str
    type: str = "EMERGENCY"  # EMERGENCY, SOS_RESCUE, SOS_MEDICAL, HAZARD_REPORT, TEST_ALERT
    priority: str = "CRITICAL"  # CRITICAL, HIGH, MEDIUM
    issuer: str = "GOVERNMENT_DDMA"  # GOVERNMENT_DDMA, CITIZEN_NODE
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ttl: int = 5
    hop_count: int = 0
    location: str = "ZONE_A"
    message: str = "Evacuate Zone A immediately via State Highway 44 before 6 PM."
    signature: str = ""  # Cryptographic signature from sovereign government key

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "P2PMessage":
        return cls(
            id=data["id"],
            type=data.get("type", "EMERGENCY"),
            priority=data.get("priority", "CRITICAL"),
            issuer=data.get("issuer", "GOVERNMENT_DDMA"),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            ttl=int(data.get("ttl", 5)),
            hop_count=int(data.get("hop_count", 0)),
            location=data.get("location", "ZONE_A"),
            message=data.get("message", ""),
            signature=data.get("signature", "")
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(',', ':'))

    @classmethod
    def from_json(cls, json_str: str) -> "P2PMessage":
        return cls.from_dict(json.loads(json_str))

    def to_bytes(self) -> bytes:
        return self.to_json().encode('utf-8')

    @classmethod
    def from_bytes(cls, raw_bytes: bytes) -> "P2PMessage":
        return cls.from_json(raw_bytes.decode('utf-8'))

    def prepare_for_relay(self) -> Optional["P2PMessage"]:
        """Increments hop count and decrements TTL for store-and-forward relay."""
        if self.ttl <= 1:
            return None  # Expired, do not forward
        return P2PMessage(
            id=self.id,
            type=self.type,
            priority=self.priority,
            issuer=self.issuer,
            timestamp=self.timestamp,
            ttl=self.ttl - 1,
            hop_count=self.hop_count + 1,
            location=self.location,
            message=self.message,
            signature=self.signature
        )
