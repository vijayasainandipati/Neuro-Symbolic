"""
Real-Time Simulation Engine.

Simulates continuous satellite data streaming and multi-hazard
detection for the prototype demonstration.

Algorithm:
  Load dataset image
       ↓
  Run AI detection models (flood, landslide, cyclone, fire, defense)
       ↓
  Extract contextual features
       ↓
  Apply symbolic rules
       ↓
  Generate decision
       ↓
  Update dashboard
       ↓
  Repeat every few seconds

This simulator enables real-time demonstration of the full
neuro-symbolic pipeline without requiring live satellite feeds.
"""

import os
import sys
import time
import logging

import cv2
import torch
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from realtime.data_stream import DataStream
from preprocessing.feature_extraction import FeatureExtractor
from reasoning.decision_engine import DecisionEngine

logger = logging.getLogger(__name__)


class MultiHazardSimulator:
    """
    Real-time multi-hazard simulation engine.

    Runs continuous detection loops for all hazard types,
    applying AI models and symbolic reasoning at configurable
    intervals.

    Features:
      - Real-time simulation with synthetic/real data
      - Multi-hazard concurrent monitoring
      - Compound event detection
      - Decision logging and audit trail
      - Dashboard-ready output format
    """

    def __init__(self, device=None, interval_seconds=5):
        """
        Parameters
        ----------
        device : torch.device or None
            Compute device (auto-selects GPU if available).
        interval_seconds : int
            Seconds between simulation cycles.
        """
        self.device = device or torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        self.interval = interval_seconds

        # Components
        self.data_stream = DataStream()
        self.feature_extractor = FeatureExtractor()
        self.decision_engine = DecisionEngine()

        # Models (lazy-loaded)
        self._models = {}
        self._models_loaded = False

        # State
        self.running = False
        self.cycle_count = 0
        self.latest_results = {}

    def load_models(self):
        """Load all detection models."""
        from models.flood_model import FloodUNet
        from models.landslide_model import LandslideResNet
        from models.cyclone_model import CycloneViT
        from models.fire_model import FireDetector
        from models.defense_detection import DefenseObjectDetector

        logger.info("Loading multi-hazard detection models...")

        self._models["flood"] = FloodUNet().to(self.device)
        self._models["landslide"] = LandslideResNet(pretrained=False).to(self.device)
        self._models["cyclone"] = CycloneViT().to(self.device)
        self._models["fire"] = FireDetector().to(self.device)
        self._models["defense"] = DefenseObjectDetector().to(self.device)

        # Load weights if available
        models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
        weight_map = {
            "flood": "flood_model.pth",
            "landslide": "landslide_model.pth",
            "cyclone": "cyclone_model.pth",
            "fire": "fire_model.pth",
            "defense": "defense_model.pth",
        }

        for name, filename in weight_map.items():
            path = os.path.join(models_dir, filename)
            if os.path.isfile(path):
                self._models[name].load_state_dict(
                    torch.load(path, map_location=self.device, weights_only=True)
                )
                logger.info("Loaded weights for %s", name)

        for model in self._models.values():
            model.eval()

        self._models_loaded = True
        logger.info("All models loaded on %s", self.device)

    def _preprocess(self, image, target_size=(256, 256)):
        """Preprocess image for model input."""
        img = cv2.resize(image, target_size)
        tensor = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
        return tensor.unsqueeze(0).to(self.device)

    def run_single_cycle(self, hazard_types=None, region_name="Simulated Region"):
        """
        Run one complete detection cycle across all hazard types.

        Parameters
        ----------
        hazard_types : list[str] or None
            Hazard types to simulate. Default: all.
        region_name : str
            Name for the simulated region.

        Returns
        -------
        dict
            Complete cycle results with all detections and decisions.
        """
        if not self._models_loaded:
            self.load_models()

        if hazard_types is None:
            hazard_types = ["flood", "landslide", "cyclone", "fire", "defense"]

        self.cycle_count += 1
        env_data = self.data_stream.get_environmental_data(region_name)

        results = {
            "cycle": self.cycle_count,
            "region": region_name,
            "environmental_data": env_data,
            "detections": {},
            "decisions": {},
        }

        events_for_multi_hazard = []

        for hazard in hazard_types:
            image = self.data_stream.get_next_image(
                "defense_objects" if hazard == "defense" else hazard
            )
            if image is None:
                continue

            # Run detection
            detection = self._detect(hazard, image)
            results["detections"][hazard] = detection

            # Apply symbolic rules
            decision = self._apply_rules(hazard, detection, env_data, region_name)
            results["decisions"][hazard] = decision

            # Collect for multi-hazard analysis
            if hazard != "defense":
                events_for_multi_hazard.append(decision)

        # Check for compound events
        if len(events_for_multi_hazard) > 1:
            compound = self.decision_engine.evaluate_multi_hazard(
                region_name, [
                    self._to_multi_hazard_event(d, env_data)
                    for d in events_for_multi_hazard
                ]
            )
            results["compound_assessment"] = compound

        self.latest_results = results
        return results

    def _detect(self, hazard_type, image):
        """Run AI detection model for a specific hazard type."""
        tensor = self._preprocess(image)

        with torch.no_grad():
            if hazard_type == "flood":
                output = self._models["flood"](tensor)
                prob = output.mean().item()
                return {
                    "probability": round(prob, 4),
                    "mask": output.squeeze().cpu().numpy(),
                }

            elif hazard_type == "landslide":
                output = self._models["landslide"](tensor)
                prob = output.item()
                return {
                    "probability": round(prob, 4),
                    "prediction": "landslide" if prob > 0.5 else "stable",
                }

            elif hazard_type == "cyclone":
                model = self._models["cyclone"]
                return model.predict_damage(tensor)

            elif hazard_type == "fire":
                model = self._models["fire"]
                return model.predict_fire(tensor)

            elif hazard_type == "defense":
                model = self._models["defense"]
                return model.predict_with_confidence(tensor)

        return {}

    def _apply_rules(self, hazard_type, detection, env_data, region_name):
        """Apply symbolic rules to a detection result."""
        if hazard_type == "flood":
            return self.decision_engine.evaluate_flood(
                region_name,
                detection["probability"],
                env_data["population_density"],
                env_data["elevation"],
                env_data["rainfall_mm"],
            )

        elif hazard_type == "landslide":
            return self.decision_engine.evaluate_landslide(
                region_name,
                detection["probability"],
                env_data["terrain_slope"],
                env_data["population_density"],
                env_data["rainfall_mm"],
                env_data["soil_moisture"],
            )

        elif hazard_type == "cyclone":
            return self.decision_engine.evaluate_cyclone(
                region_name,
                detection.get("class_name", "no_damage"),
                env_data["wind_speed_kmh"],
                env_data["population_density"],
                env_data["infrastructure_density"],
            )

        elif hazard_type == "fire":
            return self.decision_engine.evaluate_fire(
                region_name,
                detection.get("detected", False),
                detection.get("confidence", 0.0),
                env_data["population_density"],
                env_data["temperature_c"],
                env_data["wind_speed_kmh"],
            )

        elif hazard_type == "defense":
            return self.decision_engine.evaluate_defense(
                region_name,
                detection.get("threat_score", 0.0),
                detection.get("class_name", "civilian"),
                num_vehicles=0,
                movement_direction=None,
                region_type="normal",
                proximity_to_border_km=env_data["distance_to_border_km"],
            )

        return {}

    def _to_multi_hazard_event(self, decision, env_data):
        """Convert a decision back to multi-hazard event format."""
        event_type = decision.get("event_type", "unknown")

        if event_type == "flood":
            return {
                "event_type": "flood",
                "probability": decision.get("flood_probability", 0),
                "population": decision.get("population", 0),
                "elevation": decision.get("elevation"),
                "rainfall_mm": env_data.get("rainfall_mm", 0),
            }
        elif event_type == "landslide":
            return {
                "event_type": "landslide",
                "probability": decision.get("landslide_probability", 0),
                "terrain_slope": decision.get("terrain_slope", 0),
                "population": decision.get("population", 0),
                "rainfall_mm": env_data.get("rainfall_mm", 0),
                "soil_moisture": env_data.get("soil_moisture", 0.5),
            }
        elif event_type == "cyclone":
            return {
                "event_type": "cyclone",
                "damage_class": decision.get("damage_class", "no_damage"),
                "wind_speed_kmh": decision.get("wind_speed_kmh", 0),
                "population": decision.get("population", 0),
                "infrastructure_density": env_data.get("infrastructure_density", 0.5),
            }
        elif event_type == "fire":
            return {
                "event_type": "fire",
                "fire_detected": decision.get("fire_detected", False),
                "confidence": decision.get("confidence", 0),
                "population": decision.get("population", 0),
                "temperature_c": env_data.get("temperature_c", 25),
                "wind_speed_kmh": env_data.get("wind_speed_kmh", 0),
            }

        return {"event_type": event_type, "probability": 0, "population": 0}

    def run_continuous(self, hazard_types=None, max_cycles=None, callback=None):
        """
        Run continuous simulation loop.

        Parameters
        ----------
        hazard_types : list[str] or None
            Hazard types to monitor.
        max_cycles : int or None
            Stop after N cycles. None = run indefinitely.
        callback : callable or None
            Function called with results after each cycle.
        """
        self.running = True
        logger.info("Starting continuous simulation (interval=%ds)", self.interval)

        cycle = 0
        while self.running:
            cycle += 1
            if max_cycles and cycle > max_cycles:
                break

            region = f"Region-{(cycle - 1) % 5 + 1}"
            results = self.run_single_cycle(hazard_types, region)

            self._print_cycle_summary(results)

            if callback:
                callback(results)

            time.sleep(self.interval)

        logger.info("Simulation stopped after %d cycles", cycle)

    def stop(self):
        """Stop the continuous simulation."""
        self.running = False

    def _print_cycle_summary(self, results):
        """Print a formatted summary of one simulation cycle."""
        print()
        print("═" * 60)
        print(f"  Cycle {results['cycle']} | Region: {results['region']}")
        print("═" * 60)

        for hazard, detection in results["detections"].items():
            decision = results["decisions"].get(hazard, {})
            alert = decision.get("alert_level") or decision.get("threat_level", "N/A")

            if hazard == "flood":
                print(f"  🌊 Flood:     prob={detection['probability']:.2%}  alert={alert}")
            elif hazard == "landslide":
                print(f"  🏔️ Landslide: prob={detection['probability']:.2%}  alert={alert}")
            elif hazard == "cyclone":
                print(f"  🌀 Cyclone:   damage={detection.get('class_name', 'N/A')}  alert={alert}")
            elif hazard == "fire":
                print(f"  🔥 Fire:      detected={detection.get('detected', False)}  conf={detection.get('confidence', 0):.2%}  alert={alert}")
            elif hazard == "defense":
                tl = decision.get("threat_level", "N/A")
                print(f"  🛡️ Defense:   class={detection.get('class_name', 'N/A')}  threat={tl}")

            for action in decision.get("actions", []):
                print(f"      → {action}")

        # Compound events
        compound = results.get("compound_assessment")
        if compound and compound.get("compound_event"):
            ce = compound["compound_event"]
            print(f"  ⚠️ COMPOUND EVENT: {ce['alert_level']}")
            for reason in ce.get("reasons", []):
                print(f"      ⚡ {reason}")

        print("═" * 60)
