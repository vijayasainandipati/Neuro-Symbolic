"""
Explainable AI (XAI) Module for Neuro-Symbolic Defense AI.

Provides two complementary explanation mechanisms:

1. **Neural Explanations (Grad-CAM)**
   - Generates class activation maps highlighting which image regions
     drove the model's prediction.
   - Works with U-Net, ResNet, and ViT architectures.

2. **Symbolic Explanation Generator**
   - Traces the symbolic rule chain to produce human-readable
     justifications for every decision.
   - Links neural evidence → Bayesian fusion → rules → actions.
"""

import cv2
import numpy as np
import torch
import torch.nn.functional as F


# ═════════════════════════════════════════════════════════════════════════════
# Grad-CAM Implementation
# ═════════════════════════════════════════════════════════════════════════════

class GradCAM:
    """
    Gradient-weighted Class Activation Mapping.

    Highlights which spatial regions of the input image most influenced
    the flood prediction.  Works for any CNN that has a clearly
    identifiable "target layer" (typically the last convolutional block).

    Parameters
    ----------
    model : torch.nn.Module
        The neural network model.
    target_layer : torch.nn.Module
        The convolutional layer to compute activations from.
    """

    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer

        self._activations = None
        self._gradients = None

        # Register hooks
        self._fwd_hook = target_layer.register_forward_hook(self._save_activation)
        self._bwd_hook = target_layer.register_full_backward_hook(self._save_gradient)

    def _save_activation(self, module, input, output):
        self._activations = output.detach()

    def _save_gradient(self, module, grad_input, grad_output):
        self._gradients = grad_output[0].detach()

    def generate(self, input_tensor, target_class=None):
        """
        Generate a Grad-CAM heatmap for the given input.

        Parameters
        ----------
        input_tensor : torch.Tensor
            Model input, shape (1, C, H, W).
        target_class : int or None
            For multi-class models.  For binary (sigmoid) models, leave None.

        Returns
        -------
        np.ndarray
            Heatmap of shape (H, W) with values in [0, 1].
        """
        self.model.eval()
        output = self.model(input_tensor)

        # Handle different output shapes
        if output.dim() == 1 or (output.dim() == 2 and output.shape[1] == 1):
            # Binary / single-value — use the scalar output
            score = output.mean()
        elif output.dim() == 4:
            # Segmentation mask — average over spatial dims
            score = output.mean()
        else:
            if target_class is not None:
                score = output[0, target_class]
            else:
                score = output.max()

        self.model.zero_grad()
        score.backward(retain_graph=True)

        if self._gradients is None or self._activations is None:
            return np.zeros((input_tensor.shape[2], input_tensor.shape[3]))

        # Global-average-pool the gradients → channel weights
        weights = self._gradients.mean(dim=(2, 3), keepdim=True)  # (1, C, 1, 1)

        # Weighted combination of activation maps
        cam = (weights * self._activations).sum(dim=1, keepdim=True)  # (1, 1, H', W')
        cam = F.relu(cam)

        # Normalize to [0, 1]
        cam = cam.squeeze().cpu().numpy()
        if cam.max() > 0:
            cam = cam / cam.max()

        # Resize to input resolution
        cam = cv2.resize(cam, (input_tensor.shape[3], input_tensor.shape[2]))
        return cam

    def release(self):
        """Remove hooks to avoid memory leaks."""
        self._fwd_hook.remove()
        self._bwd_hook.remove()


def get_gradcam_for_model(model, model_name, input_tensor):
    """
    Convenience function: auto-select the target layer for known architectures.

    Parameters
    ----------
    model : nn.Module
    model_name : str
        One of 'unet', 'resnet_classifier', 'resnet_segmentor', 'vit'.
    input_tensor : torch.Tensor
        Shape (1, C, H, W).

    Returns
    -------
    np.ndarray
        Grad-CAM heatmap (H, W) in [0, 1].
    """
    target_layer_map = {
        "unet": lambda m: m.bottleneck,
        "resnet_classifier": lambda m: m.backbone.layer4,
        "resnet_segmentor": lambda m: m.encoder.layer4,
        "vit": lambda m: m.transformer.layers[-1],
    }

    layer_fn = target_layer_map.get(model_name)
    if layer_fn is None:
        return np.zeros((input_tensor.shape[2], input_tensor.shape[3]))

    try:
        target_layer = layer_fn(model)
    except (AttributeError, IndexError):
        return np.zeros((input_tensor.shape[2], input_tensor.shape[3]))

    cam = GradCAM(model, target_layer)
    try:
        heatmap = cam.generate(input_tensor)
    finally:
        cam.release()

    return heatmap


def overlay_heatmap(image, heatmap, alpha=0.5, colormap=cv2.COLORMAP_JET):
    """
    Overlay a Grad-CAM heatmap on the original image.

    Parameters
    ----------
    image : np.ndarray
        Original RGB image, uint8.
    heatmap : np.ndarray
        Grad-CAM map in [0, 1].
    alpha : float
        Blending factor.

    Returns
    -------
    np.ndarray
        Blended RGB image, uint8.
    """
    heatmap_uint8 = (heatmap * 255).astype(np.uint8)
    heatmap_color = cv2.applyColorMap(heatmap_uint8, colormap)
    heatmap_color = cv2.resize(heatmap_color, (image.shape[1], image.shape[0]))

    if image.shape[2] == 3 and heatmap_color.shape[2] == 3:
        blended = cv2.addWeighted(image, 1 - alpha, heatmap_color, alpha, 0)
    else:
        blended = image.copy()

    return blended


# ═════════════════════════════════════════════════════════════════════════════
# Symbolic Explanation Generator
# ═════════════════════════════════════════════════════════════════════════════

class ExplanationGenerator:
    """
    Generates human-readable explanations for neuro-symbolic decisions.

    Traces the full reasoning chain:
      Neural evidence → Bayesian fusion → Knowledge graph → Symbolic rules
    and produces a structured explanation with natural-language justifications.
    """

    def generate_neural_explanation(self, ensemble_result):
        """
        Explain which models contributed and how.

        Parameters
        ----------
        ensemble_result : dict
            Output from HybridPipeline.ensemble_predict().

        Returns
        -------
        dict with 'summary' (str) and 'details' (list[str]).
        """
        models = ensemble_result.get("individual_models", {})
        ensemble_prob = ensemble_result.get("ensemble_probability", 0)

        details = []
        high_models = []
        low_models = []

        for name, data in models.items():
            prob = data["flood_probability"]
            details.append(f"{name}: {prob:.1%} flood probability")
            if prob > 0.6:
                high_models.append(name)
            else:
                low_models.append(name)

        if ensemble_prob > 0.8:
            summary = (
                f"Strong flood signal detected across {len(high_models)} models "
                f"(ensemble: {ensemble_prob:.1%}). "
                f"High-confidence models: {', '.join(high_models) or 'none'}."
            )
        elif ensemble_prob > 0.5:
            summary = (
                f"Moderate flood indicators (ensemble: {ensemble_prob:.1%}). "
                f"Models in agreement: {len(high_models)}/{len(models)}."
            )
        else:
            summary = (
                f"Low flood probability (ensemble: {ensemble_prob:.1%}). "
                f"No strong flood signals detected."
            )

        return {"summary": summary, "details": details}

    def generate_bayesian_explanation(self, bayesian_result):
        """
        Explain how Bayesian fusion combined evidence sources.

        Parameters
        ----------
        bayesian_result : dict
            Output from BayesianDecisionNetwork.assess_risk().

        Returns
        -------
        dict with 'summary' and 'evidence_chain' (list[str]).
        """
        posterior = bayesian_result.get("posterior", 0)
        prior = bayesian_result.get("prior", 0.3)
        risk = bayesian_result.get("risk_category", "UNKNOWN")

        evidence_chain = [
            f"Prior flood probability: {prior:.1%}",
            f"Posterior after evidence fusion: {posterior:.1%}",
            f"Risk category: {risk}",
        ]

        contributions = bayesian_result.get("evidence_contributions", {})
        dominant_source = None
        max_ratio = 0

        for src, data in contributions.items():
            ratio = data.get("likelihood_ratio", 1.0)
            evidence_chain.append(
                f"  {src}: likelihood ratio = {ratio:.2f} "
                f"(P(e|flood)={data.get('P(evidence|flood)', 0):.3f}, "
                f"P(e|¬flood)={data.get('P(evidence|no_flood)', 0):.3f})"
            )
            if ratio > max_ratio:
                max_ratio = ratio
                dominant_source = src

        if posterior > prior * 1.5:
            direction = "significantly increased"
        elif posterior > prior:
            direction = "increased"
        elif posterior < prior * 0.5:
            direction = "significantly decreased"
        else:
            direction = "remained similar to"

        summary = (
            f"Bayesian fusion {direction} the flood estimate "
            f"(prior {prior:.1%} → posterior {posterior:.1%}). "
            f"Dominant evidence source: {dominant_source or 'N/A'}."
        )

        return {"summary": summary, "evidence_chain": evidence_chain}

    def generate_symbolic_explanation(self, symbolic_decision, kg_result=None):
        """
        Explain which symbolic rules fired and why.

        Parameters
        ----------
        symbolic_decision : dict
            Output from decision_rules() with 'reasons' list.
        kg_result : dict or None
            Output from knowledge graph query.

        Returns
        -------
        dict with 'summary', 'rule_trace' (list[str]),
        and 'kg_path' (list[str]).
        """
        alert = symbolic_decision.get("alert_level", "GREEN")
        reasons = symbolic_decision.get("reasons", [])
        actions = symbolic_decision.get("actions", [])
        flood_prob = symbolic_decision.get("flood_probability", 0)
        population = symbolic_decision.get("population", 0)
        elevation = symbolic_decision.get("elevation")

        rule_trace = [
            f"Input: flood_prob={flood_prob:.2%}, population={population}, "
            f"elevation={elevation}m",
            f"Matched alert level: {alert}",
        ]
        rule_trace.extend(f"Reason: {r}" for r in reasons)
        rule_trace.extend(f"Action: {a}" for a in actions)

        kg_path = []
        if kg_result and "reasoning_path" in kg_result:
            kg_path = kg_result["reasoning_path"]

        summary = (
            f"Alert {alert} triggered because: "
            + "; ".join(reasons) if reasons else f"Alert {alert} — check rule trace."
        )

        return {
            "summary": summary,
            "rule_trace": rule_trace,
            "kg_path": kg_path,
        }

    def generate_full_explanation(
        self,
        ensemble_result,
        bayesian_result,
        symbolic_decision,
        kg_result=None,
        domain="disaster",
    ):
        """
        Build a complete explanation covering all layers.

        Returns
        -------
        dict with keys 'neural', 'bayesian', 'symbolic', 'narrative'.
        """
        neural = self.generate_neural_explanation(ensemble_result)
        bayesian = self.generate_bayesian_explanation(bayesian_result)
        symbolic = self.generate_symbolic_explanation(symbolic_decision, kg_result)

        domain_label = "Disaster Response" if domain == "disaster" else "Defense Monitoring"

        narrative = (
            f"[{domain_label} Explanation]\n"
            f"1. NEURAL PERCEPTION: {neural['summary']}\n"
            f"2. EVIDENCE FUSION: {bayesian['summary']}\n"
            f"3. POLICY DECISION: {symbolic['summary']}"
        )

        return {
            "neural": neural,
            "bayesian": bayesian,
            "symbolic": symbolic,
            "narrative": narrative,
            "domain": domain,
        }
