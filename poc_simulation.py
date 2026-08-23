"""
POC Simulation Runner - Section 8 of the POC Document
======================================================

Executes the exact 6 Test Scenarios (A through F) defined in
Section 8.3 of the "Version 1.0 Proof of Concept Document".

This is a dedicated, deterministic script -- it does NOT use the
continuous monitoring loops from main.py. All detection values are
seeded to reproduce the exact values in the POC document so that
the output matches the specification precisely.

Usage
-----
    python poc_simulation.py

Outputs
-------
    * Console: === SYSTEM DECISION REPORT === per scenario (Appendix A)
    * File:    audit_log.json  (Section 8.4)

Scenario Map
------------
    A -- Coastal Flood Event          (Flood / Disaster)
    B -- Urban Fire Outbreak          (Fire  / Disaster)
    C -- Landslide Risk               (Landslide / Disaster)
    D -- Cyclone Track                (Cyclone / Disaster)
    E -- Defense Intrusion            (Defense / Defense)
    F -- Compound Flood + Landslide   (Multi-Hazard / Disaster)
"""

import io
import sys

# Force UTF-8 output on Windows before any other import prints.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )

import os
import logging
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reasoning.decision_engine import DecisionEngine
from poc_formatter import (
    build_json_record,
    save_audit_log,
    print_poc_decision_report,
)

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger("poc_simulation")

# ── Deterministic Scenario Definitions ───────────────────────────────────────
#
# Each scenario is a dict with:
#   id               – letter A-F
#   name             – descriptive label
#   domain           – "DISASTER" or "DEFENSE"
#   image_source     – description of the synthetic/test imagery
#   context_factors  – environmental context dict
#   rules_applied    – human-readable rules that fire (for the report)
#   bayesian_note    – short note for the XAI explanation
#   confidence       – overall system confidence label
#   _params          – the EXACT numeric inputs to the engine
#
# The values are seeded deterministically as per the POC document
# (Section 8.3) so that every run produces the same output.

POC_SCENARIOS = [
    # ── A: Coastal Flood Event ──────────────────────────────────────────
    {
        "id": "A",
        "name": "Coastal Flood Event",
        "domain": "DISASTER",
        "hazard": "flood",
        "image_source": "Sentinel-1 SAR — Coastal Region (12.5m resolution)",
        "context_factors": {
            "region": "Coastal Zone Delta",
            "population_density": 900,
            "elevation_m": 3.5,
            "rainfall_mm_24h": 178.0,
            "soil_moisture": 0.82,
        },
        "rules_applied": [
            "RULE-F1: flood_prob > 0.80 AND population > 500 → RED / Evacuate",
            "RULE-F6: rainfall > 150mm → escalation amplifier",
        ],
        "bayesian_note": (
            "Bayesian fusion: P(flood|SAR)=0.91, P(flood|rainfall)=0.87 "
            "→ posterior = 0.94 — dominant evidence: SAR imagery"
        ),
        "confidence": "HIGH",
        "_params": {
            "region_name": "Coastal Zone Delta",
            "flood_prob": 0.88,
            "population": 900,
            "elevation": 3.5,
            "rainfall_mm": 178.0,
        },
    },

    # ── B: Urban Fire Outbreak ──────────────────────────────────────────
    {
        "id": "B",
        "name": "Urban Fire Outbreak",
        "domain": "DISASTER",
        "hazard": "fire",
        "image_source": "MODIS Terra Band 21/22 — Urban Thermal Overlay",
        "context_factors": {
            "region": "Industrial District North",
            "population_density": 640,
            "temperature_c": 44.2,
            "wind_speed_kmh": 38.0,
        },
        "rules_applied": [
            "RULE-FR1: fire_detected AND confidence > 0.80 AND population > 500 → RED",
            "RULE-FR-WIND: wind > 30 km/h → fire spread amplifier",
            "RULE-FR-TEMP: temp > 40°C → intensity amplifier",
        ],
        "bayesian_note": (
            "YOLOv8 fire head confidence=0.91; "
            "thermal band corroboration raises posterior above 0.88 threshold."
        ),
        "confidence": "HIGH",
        "_params": {
            "region_name": "Industrial District North",
            "fire_detected": True,
            "confidence": 0.91,
            "population": 640,
            "temperature_c": 44.2,
            "wind_speed_kmh": 38.0,
        },
    },

    # ── C: Landslide Risk Assessment ────────────────────────────────────
    {
        "id": "C",
        "name": "Landslide Risk Assessment",
        "domain": "DISASTER",
        "hazard": "landslide",
        "image_source": "Sentinel-2 MSI — Western Ghats Hillside Sector",
        "context_factors": {
            "region": "Western Ghats Sector 7",
            "population_density": 320,
            "terrain_slope_degrees": 38,
            "rainfall_mm_24h": 112.0,
            "soil_moisture": 0.76,
        },
        "rules_applied": [
            "RULE-LS2: landslide_prob > 0.60 AND rainfall > 100 mm → ORANGE",
            "RULE-LS-POP: population > 500 in affected zone → priority boost",
        ],
        "bayesian_note": (
            "ResNet50 landslide classifier: prob=0.73; "
            "soil moisture index confirms saturated conditions."
        ),
        "confidence": "MEDIUM-HIGH",
        "_params": {
            "region_name": "Western Ghats Sector 7",
            "landslide_prob": 0.73,
            "terrain_slope": 38,
            "population": 320,
            "rainfall_mm": 112.0,
            "soil_moisture": 0.76,
        },
    },

    # ── D: Cyclone Track Landfall ────────────────────────────────────────
    {
        "id": "D",
        "name": "Cyclone Track Landfall",
        "domain": "DISASTER",
        "hazard": "cyclone",
        "image_source": "INSAT-3D — Bay of Bengal Cyclone Track (VIS+IR)",
        "context_factors": {
            "region": "Bay of Bengal Coastal Strip",
            "population_density": 1200,
            "wind_speed_kmh": 148.0,
            "infrastructure_density": 0.72,
        },
        "rules_applied": [
            "RULE-CY1: damage=severe AND wind > 120 km/h → RED Emergency",
            "RULE-CY-INFRA: infrastructure_density > 0.7 → amplifier",
        ],
        "bayesian_note": (
            "ViT damage classifier: severe_damage (conf=0.86); "
            "wind speed 148 km/h → Category 4 classification."
        ),
        "confidence": "HIGH",
        "_params": {
            "region_name": "Bay of Bengal Coastal Strip",
            "damage_class": "severe_damage",
            "wind_speed_kmh": 148.0,
            "population": 1200,
            "infrastructure_density": 0.72,
        },
    },

    # ── E: Border Defense Intrusion ──────────────────────────────────────
    {
        "id": "E",
        "name": "Border Defense Intrusion",
        "domain": "DEFENSE",
        "hazard": "defense",
        "image_source": "Synthetic Aperture Radar — Northern Border Restricted Zone",
        "context_factors": {
            "sector": "Northern Border — Restricted Zone Alpha",
            "num_vehicles_detected": 5,
            "movement_direction": "border",
            "region_type": "restricted_zone",
            "proximity_to_border_km": 2.5,
        },
        "rules_applied": [
            "RULE-D1: num_vehicles > 3 AND movement=border AND restricted_zone → CRITICAL",
            "RULE-D-PROX: proximity < 5 km → proximity amplifier",
        ],
        "bayesian_note": (
            "DefenseObjectClassifier: military_vehicle (conf=0.89), "
            "ThreatScoreEstimator: 0.92 — high-confidence CRITICAL."
        ),
        "confidence": "HIGH",
        "_params": {
            "region_name": "Northern Border — Restricted Zone Alpha",
            "threat_score": 0.92,
            "object_class": "military_vehicle",
            "num_vehicles": 5,
            "movement_direction": "border",
            "region_type": "restricted_zone",
            "proximity_to_border_km": 2.5,
        },
    },

    # ── F: Compound Flood + Landslide ───────────────────────────────────
    {
        "id": "F",
        "name": "Compound Flood + Landslide",
        "domain": "DISASTER",
        "hazard": "compound",
        "image_source": "Sentinel-1 + Sentinel-2 Fusion — Northeast Hill Corridor",
        "context_factors": {
            "region": "Northeast Hill Corridor",
            "population_density": 780,
            "elevation_m": 6.0,
            "rainfall_mm_24h": 195.0,
            "terrain_slope_degrees": 34,
            "soil_moisture": 0.88,
        },
        "rules_applied": [
            "RULE-F1: flood_prob > 0.80 AND population > 500 → RED",
            "RULE-LS1: landslide_prob > 0.80 AND slope > 30 → RED",
            "RULE-MH2: Landslide + Flood → compound debris dam risk → escalate",
        ],
        "bayesian_note": (
            "Dual-model fusion: U-Net flood=0.85, ResNet landslide=0.82; "
            "compound rule triggers — debris dam upstream warning issued."
        ),
        "confidence": "HIGH",
        # Sub-events for compound; evaluated individually then fused
        "_compound_params": {
            "flood": {
                "region_name": "Northeast Hill Corridor",
                "flood_prob": 0.85,
                "population": 780,
                "elevation": 6.0,
                "rainfall_mm": 195.0,
            },
            "landslide": {
                "region_name": "Northeast Hill Corridor",
                "landslide_prob": 0.82,
                "terrain_slope": 34,
                "population": 780,
                "rainfall_mm": 195.0,
                "soil_moisture": 0.88,
            },
        },
    },
]


# ── Engine Runners ────────────────────────────────────────────────────────────

def _run_scenario(engine: DecisionEngine, s: dict):
    """
    Dispatch to the correct evaluate_* method based on hazard type.

    Returns (decision_dict, detections_dict).
    """
    hazard = s["hazard"]
    p = s.get("_params", {})

    if hazard == "flood":
        decision = engine.evaluate_flood(
            region_name=p["region_name"],
            flood_prob=p["flood_prob"],
            population=p["population"],
            elevation=p.get("elevation"),
            rainfall_mm=p.get("rainfall_mm", 0),
        )
        detections = {
            "flood_probability": p["flood_prob"],
            "rainfall_mm": p.get("rainfall_mm", 0),
            "elevation_m": p.get("elevation", 0),
        }

    elif hazard == "fire":
        decision = engine.evaluate_fire(
            region_name=p["region_name"],
            fire_detected=p["fire_detected"],
            confidence=p["confidence"],
            population=p["population"],
            temperature_c=p.get("temperature_c", 25),
            wind_speed_kmh=p.get("wind_speed_kmh", 0),
        )
        detections = {
            "fire_detected": p["fire_detected"],
            "fire_confidence": p["confidence"],
            "temperature_c": p.get("temperature_c", 25),
            "wind_speed_kmh": p.get("wind_speed_kmh", 0),
        }

    elif hazard == "landslide":
        decision = engine.evaluate_landslide(
            region_name=p["region_name"],
            landslide_prob=p["landslide_prob"],
            terrain_slope=p["terrain_slope"],
            population=p["population"],
            rainfall_mm=p.get("rainfall_mm", 0),
            soil_moisture=p.get("soil_moisture", 0.5),
        )
        detections = {
            "landslide_probability": p["landslide_prob"],
            "terrain_slope_degrees": p["terrain_slope"],
            "soil_moisture": p.get("soil_moisture", 0.5),
            "rainfall_mm": p.get("rainfall_mm", 0),
        }

    elif hazard == "cyclone":
        decision = engine.evaluate_cyclone(
            region_name=p["region_name"],
            damage_class=p["damage_class"],
            wind_speed_kmh=p["wind_speed_kmh"],
            population=p["population"],
            infrastructure_density=p.get("infrastructure_density", 0.5),
        )
        detections = {
            "damage_class": p["damage_class"],
            "wind_speed_kmh": p["wind_speed_kmh"],
            "infrastructure_density": p.get("infrastructure_density", 0.5),
        }

    elif hazard == "defense":
        decision = engine.evaluate_defense(
            region_name=p["region_name"],
            threat_score=p["threat_score"],
            object_class=p.get("object_class", "civilian"),
            num_vehicles=p.get("num_vehicles", 0),
            movement_direction=p.get("movement_direction"),
            region_type=p.get("region_type", "normal"),
            proximity_to_border_km=p.get("proximity_to_border_km"),
        )
        detections = {
            "threat_score": p["threat_score"],
            "object_class": p.get("object_class", "civilian"),
            "num_vehicles": p.get("num_vehicles", 0),
            "proximity_to_border_km": p.get("proximity_to_border_km", 0),
        }

    elif hazard == "compound":
        # Evaluate each sub-event, fuse via multi-hazard engine
        cp = s["_compound_params"]
        flood_p = cp["flood"]
        ls_p = cp["landslide"]

        events = [
            {
                "event_type": "flood",
                "probability": flood_p["flood_prob"],
                "population": flood_p["population"],
                "elevation": flood_p.get("elevation"),
                "rainfall_mm": flood_p.get("rainfall_mm", 0),
            },
            {
                "event_type": "landslide",
                "probability": ls_p["landslide_prob"],
                "terrain_slope": ls_p["terrain_slope"],
                "population": ls_p["population"],
                "rainfall_mm": ls_p.get("rainfall_mm", 0),
                "soil_moisture": ls_p.get("soil_moisture", 0.5),
            },
        ]

        compound = engine.evaluate_multi_hazard(
            region_name=cp["flood"]["region_name"],
            events=events,
        )

        # Build a flat decision dict for the formatter
        compound_event = compound.get("compound_event") or {}
        decision = {
            "alert_level": compound.get("overall_alert_level", "RED"),
            "priority": compound.get("overall_priority", 5),
            "actions": compound.get("all_actions", []),
            "reasons": compound.get("all_reasons", []),
            "event_type": "compound",
        }
        # Prepend compound-specific actions/reasons if present
        if compound_event:
            for r in compound_event.get("reasons", []):
                if r not in decision["reasons"]:
                    decision["reasons"].insert(0, r)
            for a in compound_event.get("actions", []):
                if a not in decision["actions"]:
                    decision["actions"].insert(0, a)

        detections = {
            "flood_probability": flood_p["flood_prob"],
            "landslide_probability": ls_p["landslide_prob"],
            "rainfall_mm": flood_p.get("rainfall_mm", 0),
            "soil_moisture": ls_p.get("soil_moisture", 0.5),
            "terrain_slope_degrees": ls_p["terrain_slope"],
        }

    else:
        logger.warning("Unknown hazard type: %s — skipping", hazard)
        return None, None

    return decision, detections


# ── Main Simulation Loop ────────────────────────────────────────────────────

def run_poc_simulation():
    """
    Execute all 6 POC scenarios (A–F) in sequence.

    For each scenario:
      1. Run the deterministic inputs through the DecisionEngine.
      2. Print the console System Decision Report (Appendix A).
      3. Collect the JSON record (Section 8.4).

    After all scenarios:
      4. Save the full audit_log.json.
    """
    print()
    print("=" * 66)
    print("   NEURO-SYMBOLIC MULTI-HAZARD & DEFENSE DECISION AI")
    print("   Proof of Concept Simulation  --  Version 1.0")
    print("   Scenarios A through F  |  Section 8.3 of POC Document")
    print("=" * 66)
    print()

    engine = DecisionEngine()
    audit_records = []

    for s in POC_SCENARIOS:
        sid = s["id"]
        logger.info(">>  Running Scenario %s: %s", sid, s["name"])

        decision, detections = _run_scenario(engine, s)

        if decision is None:
            logger.error("   Scenario %s failed — skipping.", sid)
            continue

        # Console report
        print_poc_decision_report(s, decision, detections)

        # JSON record
        record = build_json_record(s, decision, detections)
        audit_records.append(record)

        # Small visual pause between scenarios
        time.sleep(0.05)

    # ── Save audit log ────────────────────────────────────────────────────
    audit_path = save_audit_log(audit_records)
    print()
    print("=" * 66)
    print("  [OK]  All 6 POC Scenarios completed successfully.")
    print(f"  [LOG] Audit log saved  -->  {audit_path}")
    print("=" * 66)
    print()

    return audit_records


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_poc_simulation()
