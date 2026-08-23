"""
Neuro-Symbolic Reasoning Rules.

Expert-encoded symbolic rules for multi-hazard disaster response
and defense monitoring. These rules represent domain knowledge
that complements neural network predictions.

Instead of just prediction, the system applies rules written in logic:

  IF flood_probability > 0.8
  AND population_density > 500
  THEN evacuation_alert

This is the main innovation of the neuro-symbolic approach:
combining data-driven AI with human-interpretable rules.

Rule Categories:
  - Flood response rules
  - Landslide evacuation rules
  - Cyclone impact response rules
  - Urban fire response rules
  - Defense/border security rules
  - Multi-hazard compound event rules
"""


def flood_rule(prob, population, elevation=None, rainfall_mm=0):
    """
    Symbolic flood response rules.

    Logic:
      IF flood_probability > 0.8 AND population > 500 → Evacuation Alert
      IF flood_probability > 0.6 AND population > 200 → Evacuation Warning
      IF flood_probability > 0.6 → Monitor
      IF flood_probability > 0.4 AND elevation < 10 → Low-Elevation Alert
      IF flood_probability > 0.3 → Increase Monitoring
      ELSE → Safe

    Parameters
    ----------
    prob : float
        Neural network flood probability (0-1).
    population : int
        Population count in the grid cell.
    elevation : float or None
        Elevation in metres above sea level.
    rainfall_mm : float
        Rainfall in last 24h.

    Returns
    -------
    dict with alert_level, actions, reasons, priority.
    """
    actions = []
    reasons = []
    alert_level = "GREEN"
    priority = 0

    # Rule 1: Critical flood + dense population
    if prob > 0.8 and population > 500:
        alert_level = "RED"
        priority = 5
        actions.append("Evacuate Region Immediately")
        actions.append("Deploy Rescue Teams")
        actions.append("Activate Emergency Shelters")
        reasons.append(
            f"Flood probability ({prob:.1%}) exceeded critical "
            f"threshold (80%) with high population density ({population})"
        )

    # Rule 2: High flood + moderate population
    elif prob > 0.6 and population > 200:
        alert_level = "ORANGE"
        priority = 4
        actions.append("Issue Evacuation Warning")
        actions.append("Pre-position Rescue Boats")
        actions.append("Alert Medical Teams")
        reasons.append(
            f"Flood probability ({prob:.1%}) exceeded high "
            f"threshold (60%) with moderate population ({population})"
        )

    # Rule 3: Moderate flood risk
    elif prob > 0.6:
        alert_level = "YELLOW"
        priority = 3
        actions.append("Send Monitoring Drone")
        actions.append("Notify Local Authorities")
        reasons.append(
            f"Flood probability ({prob:.1%}) exceeded moderate threshold (60%)"
        )

    # Rule 4: Low-elevation amplifier
    elif prob > 0.4 and elevation is not None and elevation < 10:
        alert_level = "YELLOW"
        priority = 3
        actions.append("Low-Elevation Alert: Monitor Water Levels")
        actions.append("Prepare Sandbag Barriers")
        reasons.append(
            f"Flood probability ({prob:.1%}) combined with "
            f"low elevation ({elevation}m < 10m) increases risk"
        )

    # Rule 5: Mild concern
    elif prob > 0.3:
        alert_level = "BLUE"
        priority = 2
        actions.append("Increase Satellite Monitoring Frequency")
        reasons.append(
            f"Flood probability ({prob:.1%}) above monitoring threshold (30%)"
        )

    # Rule 6: Safe
    else:
        alert_level = "GREEN"
        priority = 1
        actions.append("No action required — region is safe")
        reasons.append(
            f"Flood probability ({prob:.1%}) below all risk thresholds"
        )

    # Rainfall amplifier
    if rainfall_mm > 150 and priority < 4:
        reasons.append(
            f"Heavy rainfall ({rainfall_mm}mm) may escalate flood risk"
        )
        actions.append("Monitor rainfall trend closely")

    return {
        "event_type": "flood",
        "alert_level": alert_level,
        "actions": actions,
        "reasons": reasons,
        "priority": priority,
        "flood_probability": round(prob, 4),
        "population": population,
        "elevation": elevation,
    }


def landslide_rule(prob, terrain_slope, population, rainfall_mm=0, soil_moisture=0.5):
    """
    Symbolic landslide response rules.

    Logic:
      IF landslide_prob > 0.8 AND slope > 30 → Critical Alert
      IF landslide_prob > 0.6 AND rainfall > 100 → High Alert
      IF landslide_prob > 0.5 AND soil_moisture > 0.8 → Elevated Alert
      IF landslide_prob > 0.4 → Monitor
      ELSE → Safe
    """
    actions = []
    reasons = []
    alert_level = "GREEN"
    priority = 0

    if prob > 0.8 and terrain_slope > 30:
        alert_level = "RED"
        priority = 5
        actions.append("Evacuate Hillside Communities Immediately")
        actions.append("Close Mountain Roads")
        actions.append("Deploy Geological Survey Team")
        reasons.append(
            f"Landslide probability ({prob:.1%}) critical on steep terrain "
            f"(slope={terrain_slope}°)"
        )

    elif prob > 0.6 and rainfall_mm > 100:
        alert_level = "ORANGE"
        priority = 4
        actions.append("Issue Landslide Warning")
        actions.append("Evacuate Vulnerable Settlements")
        actions.append("Restrict Vehicle Movement on Slopes")
        reasons.append(
            f"Landslide probability ({prob:.1%}) elevated with heavy "
            f"rainfall ({rainfall_mm}mm)"
        )

    elif prob > 0.5 and soil_moisture > 0.8:
        alert_level = "YELLOW"
        priority = 3
        actions.append("Monitor Soil Stability")
        actions.append("Alert Communities Near Slopes")
        reasons.append(
            f"Landslide probability ({prob:.1%}) with saturated soil "
            f"(moisture={soil_moisture:.1f})"
        )

    elif prob > 0.4:
        alert_level = "BLUE"
        priority = 2
        actions.append("Increase Terrain Monitoring")
        actions.append("Review Drainage Systems")
        reasons.append(
            f"Landslide probability ({prob:.1%}) above monitoring threshold"
        )

    else:
        alert_level = "GREEN"
        priority = 1
        actions.append("No action required — terrain stable")
        reasons.append(f"Landslide probability ({prob:.1%}) within safe range")

    if population > 500 and priority >= 3:
        actions.append(f"Priority: {population} residents in affected area")

    return {
        "event_type": "landslide",
        "alert_level": alert_level,
        "actions": actions,
        "reasons": reasons,
        "priority": priority,
        "landslide_probability": round(prob, 4),
        "terrain_slope": terrain_slope,
        "population": population,
    }


def cyclone_rule(damage_class, wind_speed_kmh, population, infrastructure_density=0.5):
    """
    Symbolic cyclone impact response rules.

    Logic:
      IF damage = severe AND wind > 120 → Emergency Response
      IF damage = moderate AND population > 500 → Evacuation Warning
      IF damage = minor → Monitor and Prepare
      ELSE → Safe

    Parameters
    ----------
    damage_class : str
        From ViT model: 'no_damage', 'minor_damage', 'moderate_damage', 'severe_damage'
    wind_speed_kmh : float
        Wind speed in km/h.
    population : int
        Population in affected area.
    infrastructure_density : float
        Infrastructure density index (0-1).
    """
    actions = []
    reasons = []
    alert_level = "GREEN"
    priority = 0

    if damage_class == "severe_damage" and wind_speed_kmh > 120:
        alert_level = "RED"
        priority = 5
        actions.append("Declare State of Emergency")
        actions.append("Deploy National Disaster Response Force")
        actions.append("Evacuate Coastal Population Immediately")
        actions.append("Suspend All Transportation")
        reasons.append(
            f"Severe cyclone damage detected with extreme winds "
            f"({wind_speed_kmh}km/h) — Category 3+ impact"
        )

    elif damage_class == "severe_damage" or (
        damage_class == "moderate_damage" and wind_speed_kmh > 80
    ):
        alert_level = "RED"
        priority = 5
        actions.append("Full Evacuation of Affected Zones")
        actions.append("Deploy Emergency Medical Teams")
        actions.append("Activate All Shelters")
        reasons.append(
            f"Severe/moderate cyclone damage with strong winds ({wind_speed_kmh}km/h)"
        )

    elif damage_class == "moderate_damage" and population > 500:
        alert_level = "ORANGE"
        priority = 4
        actions.append("Issue Cyclone Warning")
        actions.append("Prepare Evacuation Routes")
        actions.append("Stock Emergency Supplies")
        reasons.append(
            f"Moderate cyclone damage in densely populated area ({population})"
        )

    elif damage_class == "minor_damage":
        alert_level = "YELLOW"
        priority = 3
        actions.append("Issue Weather Advisory")
        actions.append("Secure Loose Structures")
        actions.append("Monitor Cyclone Path")
        reasons.append("Minor cyclone damage detected — monitor progression")

    else:
        alert_level = "GREEN"
        priority = 1
        actions.append("No cyclone impact detected — continue monitoring")
        reasons.append("No significant cyclone damage observed")

    if infrastructure_density > 0.7 and priority >= 3:
        reasons.append(
            f"High infrastructure density ({infrastructure_density:.1f}) "
            f"increases potential damage"
        )

    return {
        "event_type": "cyclone",
        "alert_level": alert_level,
        "actions": actions,
        "reasons": reasons,
        "priority": priority,
        "damage_class": damage_class,
        "wind_speed_kmh": wind_speed_kmh,
        "population": population,
    }


def fire_rule(fire_detected, confidence, population, temperature_c=25, wind_speed_kmh=0):
    """
    Symbolic urban fire response rules.

    Logic:
      IF fire_detected AND confidence > 0.8 AND population > 500 → Emergency
      IF fire_detected AND confidence > 0.6 → High Alert
      IF smoke_detected → Monitor
      ELSE → Safe

    Parameters
    ----------
    fire_detected : bool
        Whether fire was detected by the model.
    confidence : float
        Detection confidence (0-1).
    population : int
        Population in affected area.
    temperature_c : float
        Ambient temperature.
    wind_speed_kmh : float
        Wind speed (affects fire spread).
    """
    actions = []
    reasons = []
    alert_level = "GREEN"
    priority = 0

    if fire_detected and confidence > 0.8 and population > 500:
        alert_level = "RED"
        priority = 5
        actions.append("Deploy Fire Brigade Immediately")
        actions.append("Evacuate Nearby Residents")
        actions.append("Activate Fire Hydrant Network")
        actions.append("Request Aerial Firefighting Support")
        reasons.append(
            f"Fire detected with high confidence ({confidence:.1%}) "
            f"in populated area ({population})"
        )

    elif fire_detected and confidence > 0.6:
        alert_level = "ORANGE"
        priority = 4
        actions.append("Alert Fire Department")
        actions.append("Prepare Evacuation Routes")
        actions.append("Deploy Ground Assessment Team")
        reasons.append(f"Fire detected with confidence {confidence:.1%}")

    elif fire_detected and confidence > 0.3:
        alert_level = "YELLOW"
        priority = 3
        actions.append("Investigate Potential Fire")
        actions.append("Pre-position Fire Response Units")
        reasons.append(
            f"Possible fire detected (confidence={confidence:.1%}) — verification needed"
        )

    else:
        alert_level = "GREEN"
        priority = 1
        actions.append("No fire detected — area safe")
        reasons.append("No fire signatures detected in imagery")

    # Wind amplifier
    if fire_detected and wind_speed_kmh > 30:
        reasons.append(
            f"Wind speed ({wind_speed_kmh}km/h) may accelerate fire spread"
        )
        if priority < 5:
            actions.append("Establish Firebreak in Wind Direction")

    # Temperature amplifier
    if fire_detected and temperature_c > 40:
        reasons.append(
            f"Extreme heat ({temperature_c}°C) increases fire intensity"
        )

    return {
        "event_type": "fire",
        "alert_level": alert_level,
        "actions": actions,
        "reasons": reasons,
        "priority": priority,
        "fire_detected": fire_detected,
        "confidence": round(confidence, 4),
        "population": population,
    }


def defense_rule(
    threat_score,
    object_class="civilian",
    num_vehicles=0,
    movement_direction=None,
    region_type="normal",
    proximity_to_border_km=None,
):
    """
    Symbolic defense/border security rules.

    Logic:
      IF vehicles > 3 AND moving toward border AND restricted zone → CRITICAL
      IF threat_score > 0.7 AND military objects near border → HIGH
      IF temporary installations detected → ELEVATED
      IF unusual vehicle count in border zone → ELEVATED
      IF moderate threat indicators → GUARDED
      ELSE → SAFE

    Parameters
    ----------
    threat_score : float
        Neural network threat probability (0-1).
    object_class : str
        Detected object class.
    num_vehicles : int
        Count of detected military vehicles.
    movement_direction : str or None
        'border', 'inland', 'lateral', or None.
    region_type : str
        'restricted_zone', 'border', or 'normal'.
    proximity_to_border_km : float or None
        Distance to nearest border.
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

    # Rule 1: Critical — armoured vehicles toward border in restricted zone
    if num_vehicles > 3 and movement_direction == "border" and is_restricted:
        threat_level = "CRITICAL"
        priority = 5
        actions.append("Alert Military Command Immediately")
        actions.append("Deploy Rapid Reaction Force")
        actions.append("Activate Border Defense Systems")
        reasons.append(
            f"{num_vehicles} armoured vehicles moving toward border "
            f"in restricted zone"
        )

    # Rule 2: High — military objects near border
    elif (
        threat_score > 0.7
        and object_class in ("military_vehicle", "troop_formation", "tank")
        and near_border
    ):
        threat_level = "HIGH"
        priority = 4
        actions.append("Initiate Aerial Surveillance")
        actions.append("Brief Regional Command")
        actions.append("Increase Border Patrol Frequency")
        reasons.append(
            f"High threat score ({threat_score:.1%}) with {object_class} "
            f"detected within {proximity_to_border_km:.1f}km of border"
        )

    # Rule 3: Elevated — temporary installations
    elif object_class == "temporary_installation" and threat_score > 0.5:
        threat_level = "ELEVATED"
        priority = 3
        actions.append("Deploy Reconnaissance Drone")
        actions.append("Monitor Installation Activity")
        actions.append("Log for Pattern Analysis")
        reasons.append(
            f"Temporary installation detected with threat score {threat_score:.1%}"
        )

    # Rule 4: Elevated — unusual vehicle count in border zone
    elif num_vehicles > 2 and is_border:
        threat_level = "ELEVATED"
        priority = 3
        actions.append("Increase Satellite Monitoring")
        actions.append("Cross-reference Movement Patterns")
        reasons.append(f"{num_vehicles} vehicles detected in border zone")

    # Rule 5: Guarded — moderate threat
    elif threat_score > 0.4 or (
        object_class not in ("civilian", "no_object") and threat_score > 0.3
    ):
        threat_level = "GUARDED"
        priority = 2
        actions.append("Flag for Analyst Review")
        actions.append("Schedule Follow-up Scan")
        reasons.append(
            f"Moderate threat indicators: score={threat_score:.1%}, "
            f"class={object_class}"
        )

    # Rule 6: Safe
    else:
        threat_level = "SAFE"
        priority = 1
        actions.append("Routine monitoring — no anomalies detected")
        reasons.append("All indicators within normal parameters")

    return {
        "event_type": "defense",
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


def multi_hazard_rules(events):
    """
    Compound event rules when multiple hazards co-occur.

    Handles cascading disaster scenarios:
      - Cyclone + Flood (storm surge)
      - Landslide + Flood (debris dam failure)
      - Fire + Wind (rapid fire spread)

    Parameters
    ----------
    events : list[dict]
        List of individual event decisions from above rules.

    Returns
    -------
    dict
        Compound event assessment with escalated priority.
    """
    event_types = {e["event_type"] for e in events}
    max_priority = max((e["priority"] for e in events), default=0)

    compound_reasons = []
    compound_actions = []
    compound_alert = "GREEN"

    # Cyclone + Flood → Storm surge scenario
    if "cyclone" in event_types and "flood" in event_types:
        compound_alert = "RED"
        compound_reasons.append(
            "COMPOUND EVENT: Cyclone + Flood detected — potential storm surge"
        )
        compound_actions.append("Evacuate ALL coastal areas immediately")
        compound_actions.append("Deploy maritime rescue assets")
        max_priority = max(max_priority, 5)

    # Landslide + Flood → Dam failure risk
    if "landslide" in event_types and "flood" in event_types:
        compound_alert = "RED"
        compound_reasons.append(
            "COMPOUND EVENT: Landslide + Flood — debris dam formation risk"
        )
        compound_actions.append("Monitor upstream debris accumulation")
        compound_actions.append("Evacuate downstream communities")
        max_priority = max(max_priority, 5)

    # Fire + high winds → Rapid spread
    fire_events = [e for e in events if e["event_type"] == "fire" and e.get("fire_detected")]
    if fire_events:
        # Check if wind data suggests rapid spread
        for e in events:
            if e["event_type"] == "cyclone" or (
                "wind_speed_kmh" in e and e.get("wind_speed_kmh", 0) > 40
            ):
                compound_alert = "RED" if compound_alert != "RED" else compound_alert
                compound_reasons.append(
                    "COMPOUND EVENT: Fire + Strong winds — rapid spread risk"
                )
                compound_actions.append("Establish emergency firebreaks")
                max_priority = max(max_priority, 5)
                break

    if not compound_reasons:
        return None  # No compound events detected

    return {
        "event_type": "compound",
        "alert_level": compound_alert,
        "actions": compound_actions,
        "reasons": compound_reasons,
        "priority": max_priority,
        "constituent_events": [e["event_type"] for e in events],
    }
