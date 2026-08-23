"""
Neuro-Symbolic Reasoning Engine.

Combines neural network predictions with symbolic logic rules
to produce explainable, auditable decisions for both disaster
response and defense monitoring domains.
"""

import logging
from datetime import datetime, timezone

from symbolic.policy_rules import decision_rules
from symbolic.defense_rules import defense_decision_rules

logger = logging.getLogger(__name__)


class ReasoningEngine:
    """
    Orchestrates symbolic reasoning over neural network outputs.

    Supports dual-domain operation:
      - Disaster response (flood detection → evacuation rules)
      - Defense monitoring (threat detection → border security rules)

    The engine maintains a decision log so every recommendation
    is traceable and auditable.
    """

    def __init__(self):
        self.decision_log = []

    def evaluate(self, region_name, flood_prob, population, elevation=None):
        """
        Run symbolic reasoning for a single region (disaster domain).

        Parameters
        ----------
        region_name : str
            Human-readable region identifier.
        flood_prob : float
            Neural network flood probability (0-1).
        population : int
            Population count in the grid cell.
        elevation : float or None
            Elevation in metres above sea level.

        Returns
        -------
        dict
            Full decision record including region, timestamp, reasons,
            and actions.
        """
        decision = decision_rules(flood_prob, population, elevation)

        record = {
            "domain": "disaster",
            "region": region_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **decision,
        }

        self.decision_log.append(record)

        logger.info(
            "[%s] %s | Alert: %s | Reasons: %s | Actions: %s",
            record["timestamp"],
            region_name,
            decision["alert_level"],
            "; ".join(decision.get("reasons", [])),
            "; ".join(decision["actions"]),
        )

        return record

    def evaluate_defense(
        self,
        region_name,
        threat_score,
        object_class="civilian",
        num_vehicles=0,
        movement_direction=None,
        region_type="normal",
        proximity_to_border_km=None,
    ):
        """
        Run symbolic reasoning for a region (defense domain).

        Parameters
        ----------
        region_name : str
            Region identifier.
        threat_score : float
            Neural network threat probability (0-1).
        object_class : str
            Detected object class.
        num_vehicles : int
            Detected vehicle count.
        movement_direction : str or None
            'border', 'inland', 'lateral', or None.
        region_type : str
            'restricted_zone', 'border', or 'normal'.
        proximity_to_border_km : float or None
            Distance to nearest border.

        Returns
        -------
        dict
            Full defense decision record.
        """
        decision = defense_decision_rules(
            threat_score=threat_score,
            object_class=object_class,
            num_vehicles=num_vehicles,
            movement_direction=movement_direction,
            region_type=region_type,
            proximity_to_border_km=proximity_to_border_km,
        )

        record = {
            "domain": "defense",
            "region": region_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **decision,
        }

        self.decision_log.append(record)

        logger.info(
            "[%s] DEFENSE %s | Threat: %s | Reasons: %s | Actions: %s",
            record["timestamp"],
            region_name,
            decision["threat_level"],
            "; ".join(decision.get("reasons", [])),
            "; ".join(decision["actions"]),
        )

        return record

    def evaluate_batch(self, regions):
        """
        Evaluate multiple regions and return sorted by priority (highest first).

        Parameters
        ----------
        regions : list[dict]
            Each dict must have keys: name, flood_prob, population.
            Optional key: elevation.

        Returns
        -------
        list[dict]
            Decision records sorted by descending priority.
        """
        results = []
        for r in regions:
            rec = self.evaluate(
                region_name=r["name"],
                flood_prob=r["flood_prob"],
                population=r["population"],
                elevation=r.get("elevation"),
            )
            results.append(rec)

        results.sort(key=lambda x: x["priority"], reverse=True)
        return results

    def get_log(self, domain=None):
        """
        Return the decision log, optionally filtered by domain.

        Parameters
        ----------
        domain : str or None
            'disaster', 'defense', or None for all.
        """
        if domain is None:
            return list(self.decision_log)
        return [r for r in self.decision_log if r.get("domain") == domain]

    def clear_log(self):
        """Clear the decision log."""
        self.decision_log.clear()
