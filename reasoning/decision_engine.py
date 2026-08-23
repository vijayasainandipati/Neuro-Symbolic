"""
Neuro-Symbolic Decision Engine.

Combines AI predictions + contextual features + symbolic rules
to produce final decisions and action recommendations.

Architecture:
  Model Predictions
       ↓
  Context Features (population, terrain, weather)
       ↓
  Symbolic Rule Engine
       ↓
  Decision Score
       ↓
  Action Recommendation

The Decision Engine is the core orchestrator that:
  1. Receives neural network predictions for all hazard types
  2. Extracts contextual features from environmental data
  3. Applies symbolic reasoning rules
  4. Generates explainable decisions with audit trails
  5. Handles compound multi-hazard scenarios
  6. Produces ensemble predictions for improved accuracy

Example:
  Flood Risk = HIGH
  Action = Evacuate
  Reason = Flood probability 85% + population 900 + low elevation
"""

import logging
from datetime import datetime, timezone

from reasoning.symbolic_rules import (
    flood_rule,
    landslide_rule,
    cyclone_rule,
    fire_rule,
    defense_rule,
    multi_hazard_rules,
)

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    Multi-hazard neuro-symbolic decision engine.

    Orchestrates symbolic reasoning over neural network outputs
    for all event types: floods, landslides, cyclones, fires,
    and defense monitoring.

    Maintains a decision log for full traceability and audit.
    """

    def __init__(self):
        self.decision_log = []

    # ── Individual Hazard Evaluation ─────────────────────────────────────

    def evaluate_flood(
        self, region_name, flood_prob, population, elevation=None, rainfall_mm=0
    ):
        """Run symbolic reasoning for flood event."""
        decision = flood_rule(flood_prob, population, elevation, rainfall_mm)
        return self._log_decision(region_name, decision)

    def evaluate_landslide(
        self, region_name, landslide_prob, terrain_slope, population,
        rainfall_mm=0, soil_moisture=0.5,
    ):
        """Run symbolic reasoning for landslide event."""
        decision = landslide_rule(
            landslide_prob, terrain_slope, population, rainfall_mm, soil_moisture
        )
        return self._log_decision(region_name, decision)

    def evaluate_cyclone(
        self, region_name, damage_class, wind_speed_kmh, population,
        infrastructure_density=0.5,
    ):
        """Run symbolic reasoning for cyclone impact."""
        decision = cyclone_rule(
            damage_class, wind_speed_kmh, population, infrastructure_density
        )
        return self._log_decision(region_name, decision)

    def evaluate_fire(
        self, region_name, fire_detected, confidence, population,
        temperature_c=25, wind_speed_kmh=0,
    ):
        """Run symbolic reasoning for fire event."""
        decision = fire_rule(
            fire_detected, confidence, population, temperature_c, wind_speed_kmh
        )
        return self._log_decision(region_name, decision)

    def evaluate_defense(
        self, region_name, threat_score, object_class="civilian",
        num_vehicles=0, movement_direction=None,
        region_type="normal", proximity_to_border_km=None,
    ):
        """Run symbolic reasoning for defense monitoring."""
        decision = defense_rule(
            threat_score, object_class, num_vehicles,
            movement_direction, region_type, proximity_to_border_km,
        )
        return self._log_decision(region_name, decision)

    # ── Multi-Hazard Assessment ──────────────────────────────────────────

    def evaluate_multi_hazard(self, region_name, events):
        """
        Evaluate multiple simultaneous hazards and check for
        compound event scenarios.

        Parameters
        ----------
        region_name : str
            Region identifier.
        events : list[dict]
            List of individual event parameters, each with
            'event_type' and relevant parameters.

        Returns
        -------
        dict
            Comprehensive multi-hazard assessment.
        """
        individual_decisions = []

        for event in events:
            event_type = event.get("event_type")

            if event_type == "flood":
                dec = flood_rule(
                    event["probability"], event["population"],
                    event.get("elevation"), event.get("rainfall_mm", 0),
                )
            elif event_type == "landslide":
                dec = landslide_rule(
                    event["probability"], event["terrain_slope"],
                    event["population"], event.get("rainfall_mm", 0),
                    event.get("soil_moisture", 0.5),
                )
            elif event_type == "cyclone":
                dec = cyclone_rule(
                    event["damage_class"], event["wind_speed_kmh"],
                    event["population"], event.get("infrastructure_density", 0.5),
                )
            elif event_type == "fire":
                dec = fire_rule(
                    event["fire_detected"], event["confidence"],
                    event["population"], event.get("temperature_c", 25),
                    event.get("wind_speed_kmh", 0),
                )
            elif event_type == "defense":
                dec = defense_rule(
                    event["threat_score"], event.get("object_class", "civilian"),
                    event.get("num_vehicles", 0), event.get("movement_direction"),
                    event.get("region_type", "normal"),
                    event.get("proximity_to_border_km"),
                )
            else:
                continue

            individual_decisions.append(dec)

        # Check for compound events
        compound = multi_hazard_rules(individual_decisions)

        # Overall assessment
        all_decisions = individual_decisions[:]
        if compound:
            all_decisions.append(compound)

        max_priority = max((d["priority"] for d in all_decisions), default=0)
        all_actions = []
        all_reasons = []
        for d in all_decisions:
            all_actions.extend(d["actions"])
            all_reasons.extend(d["reasons"])

        # Determine overall alert level from highest priority
        alert_map = {5: "RED", 4: "ORANGE", 3: "YELLOW", 2: "BLUE", 1: "GREEN"}
        overall_alert = alert_map.get(max_priority, "GREEN")

        result = {
            "event_type": "multi_hazard",
            "region": region_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_alert_level": overall_alert,
            "overall_priority": max_priority,
            "all_actions": list(dict.fromkeys(all_actions)),  # deduplicate
            "all_reasons": all_reasons,
            "individual_decisions": individual_decisions,
            "compound_event": compound,
        }

        self.decision_log.append(result)
        return result

    # ── Ensemble Prediction ──────────────────────────────────────────────

    def ensemble_decision(self, predictions, weights=None):
        """
        Ensemble decision combining multiple model predictions.

        To reach 90%+ accuracy, uses:
          1. Transfer learning (pretrained backbones)
          2. Data augmentation (training-time)
          3. Ensemble models (inference-time averaging)

        Formula:
          Prediction = w1*(CNN) + w2*(Transformer) + ... + wN*(ModelN)

        Parameters
        ----------
        predictions : dict
            Model name → probability mapping.
        weights : dict or None
            Model name → weight mapping. Default: equal weights.

        Returns
        -------
        dict
            Ensemble prediction with individual contributions.
        """
        if not predictions:
            return {"ensemble_probability": 0.0, "contributions": {}}

        if weights is None:
            weights = {k: 1.0 / len(predictions) for k in predictions}

        total_weight = sum(weights.get(k, 0) for k in predictions)
        if total_weight == 0:
            total_weight = 1.0

        ensemble_prob = sum(
            predictions[k] * weights.get(k, 0) / total_weight
            for k in predictions
        )

        contributions = {
            k: {
                "prediction": round(v, 4),
                "weight": round(weights.get(k, 0), 4),
                "contribution": round(v * weights.get(k, 0) / total_weight, 4),
            }
            for k, v in predictions.items()
        }

        return {
            "ensemble_probability": round(ensemble_prob, 4),
            "num_models": len(predictions),
            "contributions": contributions,
        }

    # ── Decision Logging ─────────────────────────────────────────────────

    def _log_decision(self, region_name, decision):
        """Log a decision with metadata."""
        record = {
            "region": region_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **decision,
        }
        self.decision_log.append(record)

        alert_key = decision.get("alert_level") or decision.get("threat_level", "UNKNOWN")
        logger.info(
            "[%s] %s | %s: %s | Actions: %s",
            record["timestamp"],
            region_name,
            decision["event_type"].upper(),
            alert_key,
            "; ".join(decision.get("actions", [])),
        )
        return record

    def get_log(self, event_type=None):
        """Return the decision log, optionally filtered by event type."""
        if event_type is None:
            return list(self.decision_log)
        return [r for r in self.decision_log if r.get("event_type") == event_type]

    def get_highest_priority(self):
        """Return the highest-priority active decision."""
        if not self.decision_log:
            return None
        return max(self.decision_log, key=lambda x: x.get("priority", 0))

    def clear_log(self):
        """Clear the decision log."""
        self.decision_log.clear()
