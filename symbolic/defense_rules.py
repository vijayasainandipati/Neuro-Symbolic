"""
Symbolic Defense Reasoning Rules.

Expert-encoded rules for border surveillance, threat classification,
and defense response decisions.  Mirrors the disaster policy rules
in structure but applies to defense/security scenarios.

Rule Categories:
  - Border surveillance (movement detection near borders)
  - Threat classification (armoured vehicles, installations, troop patterns)
  - Response escalation (alert military command, deploy surveillance)
"""


def defense_decision_rules(
    threat_score,
    object_class="civilian",
    num_vehicles=0,
    movement_direction=None,
    region_type="normal",
    proximity_to_border_km=None,
):
    """
    Apply symbolic reasoning for defense/border-security decisions.

    Parameters
    ----------
    threat_score : float
        Neural network threat probability (0-1).
    object_class : str
        Detected object class from DefenseObjectClassifier.
    num_vehicles : int
        Count of detected military vehicles in the tile.
    movement_direction : str or None
        Direction of detected movement ('border', 'inland', 'lateral', None).
    region_type : str
        Zone classification ('restricted_zone', 'border', 'normal').
    proximity_to_border_km : float or None
        Distance to nearest border in kilometres.

    Returns
    -------
    dict with 'threat_level', 'actions', 'priority', 'reasons'.
    """
    actions = []
    reasons = []
    threat_level = "SAFE"
    priority = 0

    is_restricted = region_type == "restricted_zone"
    is_border = region_type in ("border", "restricted_zone")
    near_border = (
        proximity_to_border_km is not None and proximity_to_border_km < 5
    )

    # ── Rule 1: Critical — armoured vehicles moving toward border ────────
    if (
        num_vehicles > 3
        and movement_direction == "border"
        and is_restricted
    ):
        threat_level = "CRITICAL"
        priority = 5
        actions.append("Alert Military Command Immediately")
        actions.append("Deploy Rapid Reaction Force")
        actions.append("Activate Border Defense Systems")
        reasons.append(
            f"{num_vehicles} armoured vehicles moving toward border "
            f"in restricted zone"
        )

    # ── Rule 2: High — military objects near border ──────────────────────
    elif (
        threat_score > 0.7
        and object_class in ("military_vehicle", "troop_movement")
        and near_border
    ):
        threat_level = "HIGH"
        priority = 4
        actions.append("Initiate Aerial Surveillance")
        actions.append("Brief Regional Command")
        actions.append("Increase Border Patrol Frequency")
        reasons.append(
            f"High threat score ({threat_score:.1%}) with "
            f"{object_class} detected within {proximity_to_border_km:.1f}km "
            f"of border"
        )

    # ── Rule 3: Elevated — temporary installations detected ──────────────
    elif (
        object_class == "temporary_installation"
        and threat_score > 0.5
    ):
        threat_level = "ELEVATED"
        priority = 3
        actions.append("Deploy Reconnaissance Drone")
        actions.append("Monitor Installation Activity")
        actions.append("Log for Pattern Analysis")
        reasons.append(
            f"Temporary installation detected with "
            f"threat score {threat_score:.1%}"
        )

    # ── Rule 4: Elevated — unusual vehicle count in border zone ──────────
    elif num_vehicles > 2 and is_border:
        threat_level = "ELEVATED"
        priority = 3
        actions.append("Increase Satellite Monitoring")
        actions.append("Cross-reference Movement Patterns")
        reasons.append(
            f"{num_vehicles} vehicles detected in border zone"
        )

    # ── Rule 5: Guarded — moderate threat signal ─────────────────────────
    elif threat_score > 0.4 or (
        object_class != "civilian" and threat_score > 0.3
    ):
        threat_level = "GUARDED"
        priority = 2
        actions.append("Flag for Analyst Review")
        actions.append("Schedule Follow-up Scan")
        reasons.append(
            f"Moderate threat indicators: score={threat_score:.1%}, "
            f"class={object_class}"
        )

    # ── Rule 6: Safe ─────────────────────────────────────────────────────
    else:
        threat_level = "SAFE"
        priority = 1
        actions.append("Routine monitoring — no anomalies detected")
        reasons.append("All indicators within normal parameters")

    return {
        "threat_level": threat_level,
        "actions": actions,
        "priority": priority,
        "reasons": reasons,
        "threat_score": round(threat_score, 4),
        "object_class": object_class,
        "num_vehicles": num_vehicles,
        "movement_direction": movement_direction,
        "region_type": region_type,
        "proximity_to_border_km": proximity_to_border_km,
    }
