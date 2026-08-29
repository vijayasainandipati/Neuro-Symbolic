"""
Layer 4 - Event Clustering & Information Fusion.
Clusters duplicate and related emergency alerts into unified Event entities.
Answers: "Which alerts are referring to the same physical crisis incident?"
"""

from typing import List, Dict, Any
from collections import defaultdict
import numpy as np
from utils.schemas import Alert, AlertCluster, ExtractedClaim, SourceType
from models.embeddings import embedding_engine
from models.llm_extractor import llm_extractor


class EventClusterer:
    """
    Semantic clustering engine combining location/event grouping with embedding distance.
    Fuses multiple incoming reports into a single actionable incident record.
    """

    def __init__(self, similarity_threshold: float = 0.50):
        self.similarity_threshold = similarity_threshold

    def cluster_alerts(self, alerts: List[Alert]) -> List[AlertCluster]:
        if not alerts:
            return []

        # 1. Extract preliminary claims for all alerts
        claims = [llm_extractor.extract_from_text(a.id, a.text) for a in alerts]

        # 2. Group by (Location, Event Type) key as primary semantic partition
        groups: Dict[str, List[int]] = defaultdict(list)
        for idx, (alert, claim) in enumerate(zip(alerts, claims)):
            loc_norm = claim.location.strip().lower()
            evt_norm = claim.event_type.strip().lower()
            key = f"{loc_norm}::{evt_norm}"
            groups[key].append(idx)

        clusters: List[AlertCluster] = []
        cluster_counter = 1

        for group_key, indices in groups.items():
            loc_name = claims[indices[0]].location
            evt_name = claims[indices[0]].event_type

            # If small group, keep together
            if len(indices) <= 6:
                cluster = self._build_cluster(
                    f"EVENT-{cluster_counter:02d}",
                    evt_name,
                    loc_name,
                    [alerts[i] for i in indices],
                    [claims[i] for i in indices]
                )
                clusters.append(cluster)
                cluster_counter += 1
            else:
                # Sub-cluster using embeddings if group is large
                sub_alerts = [alerts[i] for i in indices]
                sub_claims = [claims[i] for i in indices]
                texts = [a.text for a in sub_alerts]
                vecs = embedding_engine.get_embeddings_batch(texts)

                assigned = set()
                for i in range(len(sub_alerts)):
                    if i in assigned:
                        continue
                    sub_idx = [i]
                    assigned.add(i)
                    for j in range(i + 1, len(sub_alerts)):
                        if j not in assigned:
                            sim = embedding_engine.cosine_similarity(vecs[i], vecs[j])
                            if sim >= self.similarity_threshold:
                                sub_idx.append(j)
                                assigned.add(j)

                    cluster = self._build_cluster(
                        f"EVENT-{cluster_counter:02d}",
                        evt_name,
                        loc_name,
                        [sub_alerts[k] for k in sub_idx],
                        [sub_claims[k] for k in sub_idx]
                    )
                    clusters.append(cluster)
                    cluster_counter += 1

        # Sort clusters: official sources / higher report counts first
        clusters.sort(key=lambda c: (c.has_official_source, len(c.alerts)), reverse=True)
        return clusters

    def _build_cluster(
        self,
        cluster_id: str,
        event_type: str,
        location: str,
        alerts: List[Alert],
        claims: List[ExtractedClaim]
    ) -> AlertCluster:
        sources_summary: Dict[str, int] = defaultdict(int)
        has_official = False

        for a in alerts:
            stype = a.source_type.value if isinstance(a.source_type, SourceType) else str(a.source_type)
            sources_summary[stype] += 1
            if a.source_type == SourceType.OFFICIAL:
                has_official = True

        # Choose the most authoritative claim as representative
        # Priority: Official alert claim > first claim
        rep_claim = claims[0]
        for a, c in zip(alerts, claims):
            if a.source_type == SourceType.OFFICIAL:
                rep_claim = c
                break

        summary = f"{location} {event_type.capitalize()} Incident ({len(alerts)} related reports from {len(sources_summary)} source types)"

        return AlertCluster(
            cluster_id=cluster_id,
            event_type=event_type,
            location=location,
            alerts=alerts,
            representative_claim=rep_claim,
            summary=summary,
            report_count=len(alerts),
            sources_summary=dict(sources_summary),
            has_official_source=has_official
        )
