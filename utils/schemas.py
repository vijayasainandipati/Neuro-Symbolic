"""
Data models and schemas for NeuroSym Crisis.
Emergency Information Digest & Rumor Filter.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


class SourceType(str, Enum):
    OFFICIAL = "official"
    NEWS = "news"
    COMMUNITY = "community"
    CITIZEN = "citizen"
    SOCIAL_MEDIA = "social_media"


class VerificationStatus(str, Enum):
    SUPPORTED = "SUPPORTED"       # 🟢 Official / corroborated fact
    CONFLICTING = "CONFLICTING"   # 🟠 Contradicts official evidence (rumor / misinformation)
    UNSUPPORTED = "UNSUPPORTED"   # 🔴 No credible evidence found (unverified claim)
    STALE = "STALE"               # ⚠️ Older claim contradicted / superseded by newer official update


class StanceType(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    NEUTRAL = "NEUTRAL"
    UNKNOWN = "UNKNOWN"


@dataclass
class Alert:
    id: str
    text: str
    source: str
    source_type: SourceType = SourceType.SOCIAL_MEDIA
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    location_hint: Optional[str] = None
    scenario: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "source": self.source,
            "source_type": self.source_type.value if isinstance(self.source_type, SourceType) else self.source_type,
            "timestamp": self.timestamp,
            "location_hint": self.location_hint,
            "scenario": self.scenario,
            "metadata": self.metadata
        }


@dataclass
class ExtractedClaim:
    alert_id: str
    event_type: str              # e.g., "flood", "shelter", "hospital", "road_closure", "cyclone", "evacuation"
    location: str                # e.g., "Zone A", "North River Bridge", "Shelter A"
    claim: str                   # e.g., "North River Bridge is closed"
    action: str                  # e.g., "Evacuate", "Take SH-44", "Do not enter"
    deadline_time: str           # e.g., "Before 6:00 PM", "Current", "Until 10:00 PM"
    severity: str = "HIGH"       # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    confidence: float = 0.9
    raw_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "event_type": self.event_type,
            "location": self.location,
            "claim": self.claim,
            "action": self.action,
            "deadline_time": self.deadline_time,
            "severity": self.severity,
            "confidence": self.confidence,
            "raw_text": self.raw_text
        }


@dataclass
class EvidenceMatch:
    doc_id: str
    doc_title: str
    excerpt: str
    relevance_score: float
    stance: StanceType = StanceType.UNKNOWN
    issuing_authority: str = "District Authority"
    doc_timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "doc_title": self.doc_title,
            "excerpt": self.excerpt,
            "relevance_score": self.relevance_score,
            "stance": self.stance.value if isinstance(self.stance, StanceType) else self.stance,
            "issuing_authority": self.issuing_authority,
            "doc_timestamp": self.doc_timestamp
        }


@dataclass
class AlertCluster:
    cluster_id: str
    event_type: str
    location: str
    alerts: List[Alert] = field(default_factory=list)
    representative_claim: Optional[ExtractedClaim] = None
    summary: str = ""
    report_count: int = 0
    sources_summary: Dict[str, int] = field(default_factory=dict)
    has_official_source: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "event_type": self.event_type,
            "location": self.location,
            "report_count": len(self.alerts),
            "summary": self.summary,
            "sources_summary": self.sources_summary,
            "has_official_source": self.has_official_source,
            "representative_claim": self.representative_claim.to_dict() if self.representative_claim else None,
            "alert_ids": [a.id for a in self.alerts]
        }


@dataclass
class VerificationResult:
    claim_id: str
    cluster_id: str
    event_type: str
    location: str
    claim_text: str
    source_name: str
    source_type: SourceType
    source_priority_weight: float
    status: VerificationStatus
    rule_triggered: str
    rule_description: str
    confidence: float
    official_evidence: Optional[EvidenceMatch] = None
    all_evidence: List[EvidenceMatch] = field(default_factory=list)
    explanation: str = ""
    recommended_action: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "cluster_id": self.cluster_id,
            "event_type": self.event_type,
            "location": self.location,
            "claim_text": self.claim_text,
            "source_name": self.source_name,
            "source_type": self.source_type.value if isinstance(self.source_type, SourceType) else self.source_type,
            "source_priority_weight": self.source_priority_weight,
            "status": self.status.value if isinstance(self.status, VerificationStatus) else self.status,
            "rule_triggered": self.rule_triggered,
            "rule_description": self.rule_description,
            "confidence": self.confidence,
            "official_evidence": self.official_evidence.to_dict() if self.official_evidence else None,
            "explanation": self.explanation,
            "recommended_action": self.recommended_action,
            "timestamp": self.timestamp
        }


@dataclass
class EmergencyDigestItem:
    item_id: str
    priority_level: int         # 1: Critical Emergency, 2: Official Operational, 3: Warning/Conflict, 4: Unverified
    category: str               # "EVACUATION", "SHELTER", "TRAFFIC", "HEALTH", "MISINFORMATION"
    title: str
    key_action: str
    deadline: str
    status_badge: str           # 🟢 SUPPORTED | 🟠 CONFLICTING | 🔴 UNSUPPORTED | ⚠️ STALE
    source_note: str
    why_flagged_summary: str
    verification_detail: Optional[VerificationResult] = None


@dataclass
class EmergencyDigest:
    digest_title: str
    region: str
    generated_at: str
    total_alerts_processed: int
    total_events_clustered: int
    noise_reduction_percentage: float
    counts_by_status: Dict[str, int] = field(default_factory=dict)
    items: List[EmergencyDigestItem] = field(default_factory=list)
    shareable_checklist: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "digest_title": self.digest_title,
            "region": self.region,
            "generated_at": self.generated_at,
            "total_alerts_processed": self.total_alerts_processed,
            "total_events_clustered": self.total_events_clustered,
            "noise_reduction_percentage": self.noise_reduction_percentage,
            "counts_by_status": self.counts_by_status,
            "shareable_checklist": self.shareable_checklist,
            "warnings": self.warnings,
            "items_count": len(self.items)
        }
