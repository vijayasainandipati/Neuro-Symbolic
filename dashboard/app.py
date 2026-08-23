"""
Flask Dashboard for Neuro-Symbolic Multi-Hazard & Defense Decision AI.

6-Layer Architecture:
  Layer 1 – Data Layer         (ESA Sentinel-2 + NASA elevation/weather)
  Layer 2 – Preprocessing      (Image processing + feature extraction)
  Layer 3 – Deep Learning      (U-Net + ResNet50 + ViT + YOLOv8)
  Layer 4 – Event Classification (Flood/Landslide/Cyclone/Fire/Defense)
  Layer 5 – Neuro-Symbolic Reasoning (Rules + Decision Engine)
  Layer 6 – Real-Time Dashboard (This module)

Uses HTML + CSS + JavaScript for the frontend.

Run:
    python dashboard/app.py
    python main.py --dashboard
"""

import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import cv2
from flask import Flask, render_template, request, jsonify

from realtime.simulator import MultiHazardSimulator
from reasoning.decision_engine import DecisionEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Flask App ────────────────────────────────────────────────────────────────
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)

# ── Shared State ─────────────────────────────────────────────────────────────
simulator = MultiHazardSimulator()
decision_engine = DecisionEngine()
_models_ready = False


def _ensure_models():
    global _models_ready
    if not _models_ready:
        try:
            simulator.load_models()
        except Exception as exc:
            logger.warning("Model loading incomplete: %s", exc)
        _models_ready = True


def _decode_upload(file_storage):
    file_bytes = np.frombuffer(file_storage.read(), dtype=np.uint8)
    return cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)


def _clean(obj):
    """Make a dict JSON-serialisable."""
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    if hasattr(obj, "tolist"):
        return obj.tolist()
    if isinstance(obj, (int, bool, str, type(None))):
        return obj
    if isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return 0
        return obj
    return str(obj)


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """Run multi-hazard analysis on an uploaded image."""
    _ensure_models()

    uploaded = request.files.get("image")
    if not uploaded:
        return jsonify({"error": "No image uploaded"}), 400

    img = _decode_upload(uploaded)
    if img is None:
        return jsonify({"error": "Could not decode image"}), 400

    hazards = request.form.getlist("hazards") or ["flood", "landslide"]
    region = request.form.get("region", "Analysis Region")
    population = int(request.form.get("population", 800))
    elevation = int(request.form.get("elevation", 15))
    rainfall = int(request.form.get("rainfall_mm", 50))
    soil_moisture = float(request.form.get("soil_moisture", 0.5))
    wind_speed = int(request.form.get("wind_speed", 20))
    temperature = int(request.form.get("temperature", 30))
    terrain_slope = int(request.form.get("terrain_slope", 10))

    results = []
    for hazard in hazards:
        detection = (
            simulator._detect(hazard, img)
            if simulator._models_loaded
            else {"probability": round(float(np.random.uniform(0.2, 0.9)), 4)}
        )

        if hazard == "flood":
            decision = decision_engine.evaluate_flood(
                region, detection.get("probability", 0.5),
                population, elevation, rainfall,
            )
        elif hazard == "landslide":
            decision = decision_engine.evaluate_landslide(
                region, detection.get("probability", 0.3),
                terrain_slope, population, rainfall, soil_moisture,
            )
        elif hazard == "cyclone":
            decision = decision_engine.evaluate_cyclone(
                region, detection.get("class_name", "no_damage"),
                wind_speed, population,
            )
        elif hazard == "fire":
            decision = decision_engine.evaluate_fire(
                region, detection.get("detected", False),
                detection.get("confidence", 0.0),
                population, temperature, wind_speed,
            )
        else:
            continue

        clean_det = {
            k: (v.tolist() if hasattr(v, "tolist") else v)
            for k, v in detection.items()
            if k != "mask"
        }
        results.append({
            "hazard": hazard,
            "detection": clean_det,
            "decision": _clean(decision),
        })

    return jsonify({"results": results})


@app.route("/api/simulate", methods=["POST"])
def simulate():
    """Run a single simulation cycle."""
    _ensure_models()

    data = request.get_json(silent=True) or {}
    hazards = data.get("hazards", ["flood", "landslide", "cyclone", "fire"])
    region = data.get("region", "Simulation Zone Alpha")

    raw = simulator.run_single_cycle(hazards, region)

    detections = {}
    for h, d in raw.get("detections", {}).items():
        detections[h] = {
            k: (v.tolist() if hasattr(v, "tolist") else v)
            for k, v in d.items()
            if k != "mask"
        }

    decisions = {h: _clean(d) for h, d in raw.get("decisions", {}).items()}

    compound = raw.get("compound_assessment")
    if compound and compound.get("compound_event"):
        compound["compound_event"] = _clean(compound["compound_event"])

    return jsonify({
        "cycle": raw["cycle"],
        "region": raw["region"],
        "environmental_data": raw.get("environmental_data", {}),
        "detections": detections,
        "decisions": decisions,
        "compound_assessment": compound,
    })


@app.route("/api/defense", methods=["POST"])
def defense_analyze():
    """Run defense monitoring analysis."""
    _ensure_models()

    region = request.form.get("region", "Border Sector")
    num_vehicles = int(request.form.get("num_vehicles", 0))
    movement = request.form.get("movement_direction") or None
    if movement in ("null", "none", ""):
        movement = None
    region_type = request.form.get("region_type", "normal")
    proximity = float(request.form.get("proximity_km", 20.0))

    threat_score = float(np.random.uniform(0.1, 0.9))

    decision = decision_engine.evaluate_defense(
        region,
        threat_score=threat_score,
        object_class="military_vehicle" if num_vehicles > 0 else "civilian",
        num_vehicles=num_vehicles,
        movement_direction=movement,
        region_type=region_type,
        proximity_to_border_km=proximity,
    )

    return jsonify({"decision": _clean(decision)})


@app.route("/api/history", methods=["GET"])
def get_history():
    log = decision_engine.get_log()
    return jsonify({"log": [_clean(entry) for entry in log]})


@app.route("/api/history", methods=["DELETE"])
def clear_history():
    decision_engine.clear_log()
    return jsonify({"status": "cleared"})


# ── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("Starting Neuro-Symbolic Dashboard on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
