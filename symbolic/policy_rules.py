"""
Symbolic policy rules for disaster decision-making.

These rules encode expert domain knowledge:
  - Evacuation thresholds
  - Resource deployment logic
  - Alert escalation based on flood probability, population density, elevation
"""


def decision_rules(flood_prob, population, elevation=None):
    """
    Apply symbolic reasoning to generate a disaster response decision.

    Parameters
    ----------
    flood_prob : float
        Predicted flood probability from the neural network (0-1).
    population : int
        Estimated population in the affected grid cell.
    elevation : float or None
        Ground elevation in metres above sea level (optional).

    Returns
    -------
    dict
        Decision record with 'alert_level', 'actions', and 'priority'.
    """
    actions = []
    reasons = []
    alert_level = "GREEN"
    priority = 0

    # ── Rule 1: Critical flood + dense population ────────────────────────
    if flood_prob > 0.8 and population > 500:
        alert_level = "RED"
        priority = 5
        actions.append("Evacuate Region Immediately")
        actions.append("Deploy Rescue Teams")
        actions.append("Activate Emergency Shelters")
        reasons.append(
            f"Flood probability ({flood_prob:.1%}) exceeded critical "
            f"threshold (80%) with high population density ({population})"
        )

    # ── Rule 2: High flood + moderate population ─────────────────────────
    elif flood_prob > 0.6 and population > 200:
        alert_level = "ORANGE"
        priority = 4
        actions.append("Issue Evacuation Warning")
        actions.append("Pre-position Rescue Boats")
        actions.append("Alert Medical Teams")
        reasons.append(
            f"Flood probability ({flood_prob:.1%}) exceeded high "
            f"threshold (60%) with moderate population ({population})"
        )

    # ── Rule 3: Moderate flood risk ──────────────────────────────────────
    elif flood_prob > 0.6:
        alert_level = "YELLOW"
        priority = 3
        actions.append("Send Monitoring Drone")
        actions.append("Notify Local Authorities")
        reasons.append(
            f"Flood probability ({flood_prob:.1%}) exceeded moderate "
            f"threshold (60%)"
        )

    # ── Rule 4: Low-elevation amplifier ──────────────────────────────────
    elif flood_prob > 0.4 and elevation is not None and elevation < 10:
        alert_level = "YELLOW"
        priority = 3
        actions.append("Low-Elevation Alert: Monitor Water Levels")
        actions.append("Prepare Sandbag Barriers")
        reasons.append(
            f"Flood probability ({flood_prob:.1%}) combined with "
            f"low elevation ({elevation}m < 10m) increases risk"
        )

    # ── Rule 5: Mild concern ─────────────────────────────────────────────
    elif flood_prob > 0.3:
        alert_level = "BLUE"
        priority = 2
        actions.append("Increase Satellite Monitoring Frequency")
        reasons.append(
            f"Flood probability ({flood_prob:.1%}) above monitoring "
            f"threshold (30%)"
        )

    # ── Rule 6: Safe ─────────────────────────────────────────────────────
    else:
        alert_level = "GREEN"
        priority = 1
        actions.append("No action required – region is safe")
        reasons.append(
            f"Flood probability ({flood_prob:.1%}) below all risk "
            f"thresholds — region is safe"
        )

    return {
        "alert_level": alert_level,
        "actions": actions,
        "reasons": reasons,
        "priority": priority,
        "flood_probability": round(flood_prob, 4),
        "population": population,
        "elevation": elevation,
    }
