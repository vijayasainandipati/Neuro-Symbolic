"""
Neuro-Symbolic Multi-Hazard & Defense Decision AI — Main Orchestrator

6-Layer Architecture:
  Layer 1 – Data Layer           (ESA Sentinel-2 + NASA MODIS/DEM/Weather)
  Layer 2 – Preprocessing        (Image Processing + Feature Extraction)
  Layer 3 – Deep Learning        (U-Net + ResNet50 + ViT + YOLOv8)
  Layer 4 – Event Classification (Flood / Landslide / Cyclone / Fire / Defense)
  Layer 5 – Neuro-Symbolic       (Symbolic Rules + Decision Engine)
  Layer 6 – Real-Time Dashboard  (Flask + HTML/CSS — launch separately)

Usage
─────
  python main.py                   # Multi-hazard disaster monitoring
  python main.py --defense         # Defense-only monitoring
  python main.py --combined        # Both disaster + defense
  python main.py --dashboard       # Launch Flask dashboard
  python main.py --train flood     # Train a specific model
"""

import os
import sys
import time
import logging
import argparse

sys.path.insert(0, os.path.dirname(__file__))

from realtime.simulator import MultiHazardSimulator
from reasoning.decision_engine import DecisionEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────
POLL_INTERVAL_SECONDS = 30

DISASTER_REGIONS = [
    {"name": "Kerala Sector 4", "hazards": ["flood", "landslide"],
     "population": 900, "elevation": 5, "rainfall_mm": 120, "soil_moisture": 0.7},
    {"name": "Assam North", "hazards": ["flood", "cyclone"],
     "population": 1200, "elevation": 12, "rainfall_mm": 80, "soil_moisture": 0.5},
    {"name": "Bihar Delta", "hazards": ["flood", "fire"],
     "population": 650, "elevation": 8, "rainfall_mm": 150, "soil_moisture": 0.8},
    {"name": "Rajasthan Arid Zone", "hazards": ["fire", "landslide"],
     "population": 200, "elevation": 350, "rainfall_mm": 10, "soil_moisture": 0.15},
]

DEFENSE_SECTORS = [
    {"name": "Border Sector Alpha", "num_vehicles": 5,
     "movement_direction": "border", "region_type": "restricted_zone",
     "proximity_to_border_km": 2.5},
    {"name": "Coastal Zone Bravo", "num_vehicles": 2,
     "movement_direction": "lateral", "region_type": "border",
     "proximity_to_border_km": 8.0},
    {"name": "Inland Sector Charlie", "num_vehicles": 0,
     "movement_direction": None, "region_type": "normal",
     "proximity_to_border_km": 30.0},
]


def print_header(title):
    print()
    print("═" * 60)
    print(f"  {title}")
    print("═" * 60)


def print_decision_block(label, decision, domain="DISASTER"):
    """Pretty-print a decision from the engine."""
    level_key = "threat_level" if domain == "DEFENSE" else "alert_level"
    level = decision.get(level_key, "N/A")

    print()
    print("═" * 56)
    print(f"  Region:          {decision.get('region', label)}")
    print(f"  Domain:          {domain}")
    print(f"  Event Type:      {decision.get('event_type', 'unknown').upper()}")
    print(f"  ────────────────────────────────────────────────")
    print(f"  {level_key.replace('_', ' ').title()}: {level}")
    print(f"  Priority:        {decision.get('priority', 0)}")

    for reason in decision.get("reasons", []):
        print(f"  Reason: {reason}")

    print("  Actions:")
    for action in decision.get("actions", []):
        print(f"    • {action}")

    print("═" * 56)


# ── Disaster Monitoring ─────────────────────────────────────────────────────
def run_disaster_monitoring(simulator, decision_engine, max_cycles=None):
    """Continuous multi-hazard disaster monitoring."""

    print_header("Neuro-Symbolic MULTI-HAZARD Disaster Pipeline")
    logger.info("Hazard models: U-Net (flood) + ResNet50 (landslide) + ViT (cyclone) + YOLOv8 (fire)")
    logger.info("Layers: Data → Preprocessing → DL Detection → Classification → Symbolic Rules → Dashboard")

    cycle = 0
    while max_cycles is None or cycle < max_cycles:
        cycle += 1
        logger.info("── Cycle %d ──", cycle)

        for region in DISASTER_REGIONS:
            logger.info("Processing region: %s  (%s)", region["name"], ", ".join(region["hazards"]))

            results = simulator.run_single_cycle(
                hazard_types=region["hazards"],
                region_name=region["name"],
            )

            for hazard, decision in results["decisions"].items():
                print_decision_block(region["name"], decision, domain="DISASTER")

            # Multi-hazard compound events
            compound = results.get("compound_assessment")
            if compound and compound.get("compound_event"):
                ce = compound["compound_event"]
                print()
                print("  ⚠️  COMPOUND EVENT DETECTED")
                print(f"  Alert Level: {ce.get('alert_level', 'RED')}")
                for r in ce.get("reasons", []):
                    print(f"  {r}")

        logger.info("Cycle %d complete. Sleeping %d seconds...", cycle, POLL_INTERVAL_SECONDS)
        time.sleep(POLL_INTERVAL_SECONDS)


# ── Defense Monitoring ───────────────────────────────────────────────────────
def run_defense_monitoring(simulator, decision_engine, max_cycles=None):
    """Continuous defense / border monitoring."""

    print_header("Neuro-Symbolic DEFENSE Monitoring Pipeline")
    logger.info("Detection model: YOLOv8 (defense objects)")
    logger.info("Layers: Surveillance → DL Detection → Threat Classification → Defense Rules → Alerts")

    cycle = 0
    while max_cycles is None or cycle < max_cycles:
        cycle += 1
        logger.info("── Cycle %d ──", cycle)

        for sector in DEFENSE_SECTORS:
            logger.info("Processing sector: %s", sector["name"])

            import numpy as np
            decision = decision_engine.evaluate_defense(
                region_name=sector["name"],
                threat_score=np.random.uniform(0.1, 0.95),
                object_class="military_vehicle" if sector["num_vehicles"] > 0 else "civilian",
                num_vehicles=sector["num_vehicles"],
                movement_direction=sector["movement_direction"],
                region_type=sector["region_type"],
                proximity_to_border_km=sector["proximity_to_border_km"],
            )

            print_decision_block(sector["name"], decision, domain="DEFENSE")

        logger.info("Cycle %d complete. Sleeping %d seconds...", cycle, POLL_INTERVAL_SECONDS)
        time.sleep(POLL_INTERVAL_SECONDS)


# ── Combined Mode ────────────────────────────────────────────────────────────
def run_combined(simulator, decision_engine, max_cycles=None):
    """Run both disaster and defense monitoring in each cycle."""

    print_header("Neuro-Symbolic COMBINED Multi-Hazard & Defense Pipeline")
    logger.info("All 5 models active: U-Net + ResNet50 + ViT + YOLOv8-Fire + YOLOv8-Defense")

    cycle = 0
    while max_cycles is None or cycle < max_cycles:
        cycle += 1
        logger.info("── Cycle %d ──", cycle)

        # Disaster regions
        for region in DISASTER_REGIONS:
            results = simulator.run_single_cycle(
                hazard_types=region["hazards"],
                region_name=region["name"],
            )
            for hazard, decision in results["decisions"].items():
                print_decision_block(region["name"], decision, domain="DISASTER")

        # Defense sectors
        import numpy as np
        for sector in DEFENSE_SECTORS:
            decision = decision_engine.evaluate_defense(
                region_name=sector["name"],
                threat_score=np.random.uniform(0.1, 0.95),
                object_class="military_vehicle" if sector["num_vehicles"] > 0 else "civilian",
                num_vehicles=sector["num_vehicles"],
                movement_direction=sector["movement_direction"],
                region_type=sector["region_type"],
                proximity_to_border_km=sector["proximity_to_border_km"],
            )
            print_decision_block(sector["name"], decision, domain="DEFENSE")

        logger.info("Cycle %d complete. Sleeping %d seconds...", cycle, POLL_INTERVAL_SECONDS)
        time.sleep(POLL_INTERVAL_SECONDS)


# ── Training Entry Point ────────────────────────────────────────────────────
def run_training(model_name):
    """Train a specific hazard model."""
    from training.train_models import ModelTrainer

    print_header(f"Training {model_name.upper()} Model")

    trainer = ModelTrainer(model_type=model_name)
    logger.info("ModelTrainer initialized for %s", model_name)
    logger.info("Provide a dataset directory to begin training.")
    logger.info("Example: trainer.train_segmentation(train_loader, val_loader, epochs=50)")


# ── Dashboard ────────────────────────────────────────────────────────────────
def launch_dashboard():
    """Launch the Flask HTML/CSS dashboard."""
    import subprocess

    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard", "app.py")
    logger.info("Launching Flask dashboard: %s", dashboard_path)
    subprocess.run([sys.executable, dashboard_path], check=False)


# ── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Neuro-Symbolic Multi-Hazard & Defense Decision AI",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--defense", action="store_true",
                       help="Run defense monitoring only")
    group.add_argument("--combined", action="store_true",
                       help="Run disaster + defense monitoring together")
    group.add_argument("--dashboard", action="store_true",
                       help="Launch Flask dashboard")
    group.add_argument("--train", type=str, metavar="MODEL",
                       choices=["flood", "landslide", "cyclone", "fire", "defense"],
                       help="Train a specific model (flood|landslide|cyclone|fire|defense)")

    parser.add_argument("--cycles", type=int, default=None,
                        help="Max monitoring cycles (default: infinite)")
    args = parser.parse_args()

    simulator = MultiHazardSimulator()
    decision_engine = DecisionEngine()

    try:
        simulator.load_models()
    except Exception as e:
        logger.warning("Model loading incomplete (will use simulated detections): %s", e)

    if args.dashboard:
        launch_dashboard()
    elif args.train:
        run_training(args.train)
    elif args.defense:
        run_defense_monitoring(simulator, decision_engine, max_cycles=args.cycles)
    elif args.combined:
        run_combined(simulator, decision_engine, max_cycles=args.cycles)
    else:
        run_disaster_monitoring(simulator, decision_engine, max_cycles=args.cycles)
