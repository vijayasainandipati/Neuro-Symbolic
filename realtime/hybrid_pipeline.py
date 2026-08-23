"""
Multi-Model Hybrid Architecture Pipeline.

Dual-Domain Neuro-Symbolic System combining:

  DISASTER DOMAIN                    DEFENSE DOMAIN
  ───────────────                    ──────────────
  Satellite Images                   Surveillance Images
       ↓                                  ↓
  ResNet50 / U-Net / ViT             Defense Object Classifier
       ↓                                  ↓
  Bayesian Evidence Fusion           Threat Score Estimator
       ↓                                  ↓
  Knowledge Graph Reasoning          Defense Rules Engine
       ↓                                  ↓
  Symbolic Rule Engine               Border Security Decisions
       ↓                                  ↓
  Explainable AI (Grad-CAM)          XAI Explanations
       ↓                                  ↓
  Decision Support System            Defense Dashboard
"""

import os
import sys
import logging
import cv2
import torch
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.flood_cnn import FloodCNN
from models.resnet_flood import ResNetFloodClassifier, ResNetFloodSegmentor
from models.conv_lstm import ConvLSTMPredictor
from models.vision_transformer import VisionTransformerFlood
from models.defense_detector import DefenseObjectClassifier, ThreatScoreEstimator
from symbolic.reasoning_engine import ReasoningEngine
from symbolic.knowledge_graph import DisasterKnowledgeGraph
from symbolic.bayesian_network import BayesianDecisionNetwork
from realtime.streaming import SlidingWindowPredictor, EventDrivenAlertSystem
from utils.explainability import (
    get_gradcam_for_model,
    overlay_heatmap,
    ExplanationGenerator,
)

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")


class HybridPipeline:
    """
    End-to-end dual-domain neuro-symbolic hybrid pipeline.

    Orchestrates multiple deep learning models, symbolic reasoning,
    and explainable AI for both disaster response and defense monitoring.
    """

    def __init__(self, device=None):
        self.device = device or torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        # ── Disaster Deep Learning Models ────────────────────────────────
        self.unet = None
        self.resnet_classifier = None
        self.resnet_segmentor = None
        self.convlstm = None
        self.vit = None

        # ── Defense Deep Learning Models ─────────────────────────────────
        self.defense_classifier = None
        self.threat_estimator = None

        # ── Symbolic Reasoning ───────────────────────────────────────────
        self.reasoning_engine = ReasoningEngine()
        self.knowledge_graph = DisasterKnowledgeGraph()
        self.bayesian_network = BayesianDecisionNetwork()

        # ── Explainable AI ───────────────────────────────────────────────
        self.explanation_generator = ExplanationGenerator()

        # ── Real-Time Processing ─────────────────────────────────────────
        self.sliding_windows = {}   # region_name → SlidingWindowPredictor
        self.alert_system = EventDrivenAlertSystem(cooldown_seconds=300)

        self._load_models()

    def _load_models(self):
        """Load all available model weights."""

        # U-Net
        self.unet = FloodCNN().to(self.device)
        unet_path = os.path.join(MODELS_DIR, "flood_model.pth")
        if os.path.isfile(unet_path):
            self.unet.load_state_dict(
                torch.load(unet_path, map_location=self.device, weights_only=True)
            )
            logger.info("Loaded U-Net weights from %s", unet_path)
        self.unet.eval()

        # ResNet Classifier
        self.resnet_classifier = ResNetFloodClassifier(pretrained=True).to(self.device)
        resnet_cls_path = os.path.join(MODELS_DIR, "resnet_classifier.pth")
        if os.path.isfile(resnet_cls_path):
            self.resnet_classifier.load_state_dict(
                torch.load(resnet_cls_path, map_location=self.device, weights_only=True)
            )
            logger.info("Loaded ResNet classifier weights")
        self.resnet_classifier.eval()

        # ResNet Segmentor
        self.resnet_segmentor = ResNetFloodSegmentor(pretrained=True).to(self.device)
        resnet_seg_path = os.path.join(MODELS_DIR, "resnet_segmentor.pth")
        if os.path.isfile(resnet_seg_path):
            self.resnet_segmentor.load_state_dict(
                torch.load(resnet_seg_path, map_location=self.device, weights_only=True)
            )
            logger.info("Loaded ResNet segmentor weights")
        self.resnet_segmentor.eval()

        # ConvLSTM
        self.convlstm = ConvLSTMPredictor().to(self.device)
        convlstm_path = os.path.join(MODELS_DIR, "convlstm.pth")
        if os.path.isfile(convlstm_path):
            self.convlstm.load_state_dict(
                torch.load(convlstm_path, map_location=self.device, weights_only=True)
            )
            logger.info("Loaded ConvLSTM weights")
        self.convlstm.eval()

        # Vision Transformer
        self.vit = VisionTransformerFlood().to(self.device)
        vit_path = os.path.join(MODELS_DIR, "vit_flood.pth")
        if os.path.isfile(vit_path):
            self.vit.load_state_dict(
                torch.load(vit_path, map_location=self.device, weights_only=True)
            )
            logger.info("Loaded ViT weights")
        self.vit.eval()

        # ── Defense Models ───────────────────────────────────────────────
        self.defense_classifier = DefenseObjectClassifier().to(self.device)
        defense_cls_path = os.path.join(MODELS_DIR, "defense_classifier.pth")
        if os.path.isfile(defense_cls_path):
            self.defense_classifier.load_state_dict(
                torch.load(defense_cls_path, map_location=self.device, weights_only=True)
            )
            logger.info("Loaded Defense classifier weights")
        self.defense_classifier.eval()

        self.threat_estimator = ThreatScoreEstimator().to(self.device)
        threat_path = os.path.join(MODELS_DIR, "threat_estimator.pth")
        if os.path.isfile(threat_path):
            self.threat_estimator.load_state_dict(
                torch.load(threat_path, map_location=self.device, weights_only=True)
            )
            logger.info("Loaded Threat estimator weights")
        self.threat_estimator.eval()

    def _preprocess_image(self, image_input):
        """Load and preprocess an image to a tensor."""
        if isinstance(image_input, str):
            img = cv2.imread(image_input, cv2.IMREAD_COLOR)
            if img is None:
                raise IOError(f"Cannot read image: {image_input}")
        elif isinstance(image_input, np.ndarray):
            img = image_input
        else:
            raise TypeError(f"Unsupported image type: {type(image_input)}")

        img = cv2.resize(img, (256, 256))
        tensor = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
        return tensor.unsqueeze(0).to(self.device), img

    def predict_single_image(self, image_input, models=None):
        """
        Run flood detection with one or more models on a single image.

        Parameters
        ----------
        image_input : str or np.ndarray
        models : list[str], optional
            Which models to use. Default: all.
            Options: 'unet', 'resnet_classifier', 'resnet_segmentor', 'vit'

        Returns
        -------
        dict with per-model predictions.
        """
        if models is None:
            models = ["unet", "resnet_classifier", "resnet_segmentor", "vit"]

        tensor, raw_img = self._preprocess_image(image_input)
        results = {}

        with torch.no_grad():
            if "unet" in models:
                unet_out = self.unet(tensor)
                results["unet"] = {
                    "flood_probability": round(unet_out.mean().item(), 4),
                    "mask": unet_out.squeeze().cpu().numpy(),
                }

            if "resnet_classifier" in models:
                resnet_out = self.resnet_classifier(tensor)
                results["resnet_classifier"] = {
                    "flood_probability": round(resnet_out.item(), 4),
                }

            if "resnet_segmentor" in models:
                rseg_out = self.resnet_segmentor(tensor)
                results["resnet_segmentor"] = {
                    "flood_probability": round(rseg_out.mean().item(), 4),
                    "mask": rseg_out.squeeze().cpu().numpy(),
                }

            if "vit" in models:
                vit_out = self.vit(tensor)
                results["vit"] = {
                    "flood_probability": round(vit_out.item(), 4),
                }

        return results

    def generate_gradcam(self, image_input, models=None):
        """
        Generate Grad-CAM heatmaps for specified models.

        Parameters
        ----------
        image_input : str or np.ndarray
        models : list[str], optional
            Models to generate heatmaps for. Default: ['unet', 'resnet_classifier'].

        Returns
        -------
        dict mapping model_name → {'heatmap': np.ndarray, 'overlay': np.ndarray}
        """
        if models is None:
            models = ["unet", "resnet_classifier"]

        tensor, raw_img = self._preprocess_image(image_input)
        gradcam_results = {}

        model_map = {
            "unet": self.unet,
            "resnet_classifier": self.resnet_classifier,
            "resnet_segmentor": self.resnet_segmentor,
            "vit": self.vit,
        }

        for name in models:
            model = model_map.get(name)
            if model is None:
                continue
            heatmap = get_gradcam_for_model(model, name, tensor)
            overlay_img = overlay_heatmap(raw_img, heatmap)
            gradcam_results[name] = {
                "heatmap": heatmap,
                "overlay": overlay_img,
            }

        return gradcam_results

    def predict_sequence(self, image_sequence):
        """
        Run ConvLSTM prediction on a sequence of images.

        Parameters
        ----------
        image_sequence : list[str] or list[np.ndarray]
            Ordered sequence of satellite images.

        Returns
        -------
        dict with ConvLSTM temporal prediction.
        """
        frames = []
        for img in image_sequence:
            tensor, _ = self._preprocess_image(img)
            frames.append(tensor.squeeze(0))

        # Stack to (1, T, C, H, W)
        sequence = torch.stack(frames).unsqueeze(0).to(self.device)

        with torch.no_grad():
            prob = self.convlstm(sequence)

        return {
            "convlstm": {
                "flood_probability": round(prob.item(), 4),
                "num_frames": len(frames),
            }
        }

    def ensemble_predict(self, image_input):
        """
        Ensemble prediction: average probabilities from all models.

        Returns
        -------
        dict with individual and ensemble predictions.
        """
        individual = self.predict_single_image(image_input)

        probs = [v["flood_probability"] for v in individual.values()]
        ensemble_prob = round(sum(probs) / len(probs), 4) if probs else 0.0

        return {
            "individual_models": individual,
            "ensemble_probability": ensemble_prob,
            "num_models": len(probs),
        }

    def full_analysis(
        self,
        image_input,
        region_name="Unknown Region",
        population=500,
        elevation=10.0,
        rainfall_mm=0.0,
        soil_moisture=0.5,
    ):
        """
        Complete neuro-symbolic analysis pipeline with XAI explanations.

        1. Multi-model ensemble prediction
        2. Bayesian evidence fusion
        3. Knowledge graph reasoning
        4. Symbolic rule engine
        5. Sliding window smoothing
        6. Event-driven alerts
        7. Grad-CAM explanations
        8. Full narrative explanation

        Returns
        -------
        dict with comprehensive analysis results and explanations.
        """
        # ── Step 1: Ensemble neural prediction ───────────────────────────
        ensemble = self.ensemble_predict(image_input)
        nn_probability = ensemble["ensemble_probability"]

        # ── Step 2: Bayesian fusion ──────────────────────────────────────
        bayesian = self.bayesian_network.assess_risk({
            "satellite": nn_probability,
            "rainfall": rainfall_mm,
            "elevation": elevation,
            "soil_moisture": soil_moisture,
        })

        # ── Step 3: Knowledge graph ──────────────────────────────────────
        self.knowledge_graph.add_region(
            region_name, population, elevation, bayesian["posterior"]
        )
        kg_result = self.knowledge_graph.query_actions(region_name)

        # ── Step 4: Symbolic rule engine ─────────────────────────────────
        symbolic = self.reasoning_engine.evaluate(
            region_name, bayesian["posterior"], population, elevation
        )

        # ── Step 5: Sliding window ───────────────────────────────────────
        if region_name not in self.sliding_windows:
            self.sliding_windows[region_name] = SlidingWindowPredictor()
        sw = self.sliding_windows[region_name]
        sw.add_prediction(bayesian["posterior"])
        window_status = sw.get_status()

        # ── Step 6: Event alerts ─────────────────────────────────────────
        alert = self.alert_system.check_and_alert(
            region_name, bayesian["posterior"],
            extra_data={"population": population, "elevation": elevation},
        )

        # ── Step 7: Grad-CAM explanations ────────────────────────────────
        gradcam = self.generate_gradcam(image_input, models=["unet", "resnet_classifier"])

        # ── Step 8: Full narrative explanation ────────────────────────────
        explanation = self.explanation_generator.generate_full_explanation(
            ensemble_result=ensemble,
            bayesian_result=bayesian,
            symbolic_decision=symbolic,
            kg_result=kg_result,
            domain="disaster",
        )

        return {
            "region": region_name,
            "neural_network": ensemble,
            "bayesian_fusion": bayesian,
            "knowledge_graph": kg_result,
            "symbolic_decision": symbolic,
            "temporal_window": window_status,
            "alert": alert,
            "gradcam": gradcam,
            "explanation": explanation,
            "final_flood_probability": bayesian["posterior"],
            "final_risk_category": bayesian["risk_category"],
            "final_actions": symbolic["actions"],
        }

    def defense_analysis(
        self,
        image_input,
        region_name="Unknown Sector",
        num_vehicles=0,
        movement_direction=None,
        region_type="normal",
        proximity_to_border_km=None,
    ):
        """
        Complete defense/border-security analysis pipeline.

        1. Defense object classification
        2. Threat score estimation
        3. Defense symbolic reasoning
        4. XAI explanation

        Returns
        -------
        dict with defense analysis results and explanations.
        """
        tensor, raw_img = self._preprocess_image(image_input)

        # ── Step 1: Object classification ────────────────────────────────
        classification = self.defense_classifier.predict_with_confidence(tensor)

        # ── Step 2: Threat score ─────────────────────────────────────────
        with torch.no_grad():
            threat_score = self.threat_estimator(tensor).item()

        # ── Step 3: Defense symbolic reasoning ───────────────────────────
        defense_decision = self.reasoning_engine.evaluate_defense(
            region_name=region_name,
            threat_score=threat_score,
            object_class=classification["class_name"],
            num_vehicles=num_vehicles,
            movement_direction=movement_direction,
            region_type=region_type,
            proximity_to_border_km=proximity_to_border_km,
        )

        # ── Step 4: Explanation ──────────────────────────────────────────
        explanation = {
            "domain": "defense",
            "narrative": (
                f"[Defense Monitoring Explanation]\n"
                f"1. OBJECT DETECTION: Detected '{classification['class_name']}' "
                f"with {classification['confidence']:.1%} confidence.\n"
                f"2. THREAT ASSESSMENT: Threat score = {threat_score:.1%}.\n"
                f"3. POLICY DECISION: {defense_decision['threat_level']} — "
                + "; ".join(defense_decision.get("reasons", []))
            ),
            "reasons": defense_decision.get("reasons", []),
        }

        return {
            "region": region_name,
            "classification": classification,
            "threat_score": round(threat_score, 4),
            "defense_decision": defense_decision,
            "explanation": explanation,
            "final_threat_level": defense_decision["threat_level"],
            "final_actions": defense_decision["actions"],
        }
