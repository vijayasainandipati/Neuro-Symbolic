# 🛡️ Real-Time Neuro-Symbolic Dual-Domain Decision AI

A research-grade system that combines **deep learning** with **symbolic reasoning** and **explainable AI** to produce **transparent, real-time decisions** for both **disaster response** and **defense monitoring** from satellite / surveillance imagery.

> *"The system fuses deep learning perception (ResNet, U-Net, ViT, ConvLSTM) with symbolic reasoning algorithms (policy rules, knowledge graphs, Bayesian networks) and a Grad-CAM-based XAI layer. This neuro-symbolic architecture enables real-time detection, explainable decision recommendations, and dual-domain operation across disaster and defense scenarios."*

---

## 7-Layer Research Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  LAYER 1 — Data Sources                                         │
│  Sentinel-2 Satellite  +  Surveillance Feeds  +  Weather        │
│  + WorldPop Population  + NASA DEM Elevation  + Soil Moisture   │
└─────────────────────────────┬────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  LAYER 2 — Data Processing                                      │
│  Image preprocessing, resize, normalize, NDWI/NDVI,             │
│  geo-alignment, tiling                                          │
└─────────────────────────────┬────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  LAYER 3 — Deep Learning                                        │
│                                                                  │
│  DISASTER:                    DEFENSE:                           │
│  ResNet50 ──→ Features        DefenseObjectClassifier ──→ Class  │
│  U-Net    ──→ Flood Mask      ThreatScoreEstimator ──→ Score     │
│  ViT      ──→ Classification                                    │
│  ConvLSTM ──→ Temporal                                           │
│                                                                  │
│  Ensemble Average             Multi-class + Threat Score         │
└─────────────────────────────┬────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  LAYER 4 — Neuro-Symbolic Reasoning                             │
│                                                                  │
│  Bayesian Decision Network ──→ Evidence Fusion                   │
│  Knowledge Graph (NetworkX) ──→ Entity Relationships             │
│  Symbolic Rule Engine ──→ Disaster Policy Actions                │
│  Defense Rule Engine ──→ Border Security Actions                 │
└─────────────────────────────┬────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  LAYER 5 — Explainable AI (XAI)                                 │
│                                                                  │
│  Grad-CAM ──→ Spatial attention heatmaps                         │
│  Explanation Generator ──→ Natural-language reasoning trace      │
│  Full Narrative ──→ Neural + Bayesian + Symbolic chain           │
└─────────────────────────────┬────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  LAYER 6 — Decision Support System                              │
│                                                                  │
│  Sliding Window Predictor ──→ Temporal Smoothing                 │
│  Event-Driven Alerts ──→ Threshold Notifications                 │
│  Streamlit Dashboard ──→ Real-Time Visualization                 │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  LAYER 7 — Defense Monitoring                                    │
│                                                                  │
│  Object Detection (6 classes: civilian to aircraft/drone)        │
│  Threat Classification (SAFE → CRITICAL)                         │
│  Border Surveillance Rules (restricted zone, proximity)          │
└──────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
neuro-symbolic-defense-ai/
├── data/
│   ├── satellite_images/         # Sentinel-2 satellite images
│   ├── flood_masks/              # Binary flood segmentation masks
│   └── population/               # WorldPop population density grids
│
├── models/
│   ├── flood_cnn.py              # U-Net flood segmentation (skip connections)
│   ├── resnet_flood.py           # ResNet50 classifier + segmentor
│   ├── conv_lstm.py              # ConvLSTM temporal predictor + segmentor
│   ├── vision_transformer.py     # Vision Transformer (ViT) classifier
│   ├── defense_detector.py       # Defense object classifier + threat estimator
│   ├── dataset_loader.py         # PyTorch dataset with augmentation
│   └── train_model.py            # Training with BCE + Dice loss
│
├── realtime/
│   ├── satellite_stream.py       # Sentinel-2 Copernicus API data fetcher
│   ├── inference.py              # Single-model flood prediction
│   ├── hybrid_pipeline.py        # Dual-domain pipeline + XAI integration
│   └── streaming.py              # Sliding window + event-driven alerts
│
├── symbolic/
│   ├── policy_rules.py           # Expert decision rules (6-level) + reasons
│   ├── defense_rules.py          # Border surveillance + threat classification
│   ├── reasoning_engine.py       # Dual-domain orchestration + audit logging
│   ├── knowledge_graph.py        # NetworkX knowledge graph reasoning
│   └── bayesian_network.py       # Bayesian decision network
│
├── dashboard/
│   └── app.py                    # Streamlit dashboard (6 tabs, dual-domain)
│
├── utils/
│   ├── preprocessing.py          # NDWI, NDVI, image tiling
│   ├── metrics.py                # IoU, F1, Precision, Recall, Dice
│   └── explainability.py         # Grad-CAM + Symbolic Explanation Generator
│
├── main.py                       # Dual-domain pipeline (--defense flag)
├── poc_simulation.py             # [POC] Deterministic 6-scenario simulation (Section 8.3)
├── poc_formatter.py              # [POC] Console report + JSON audit log formatter
├── audit_log.json                # [POC] Auto-generated decision audit log (Section 8.4)
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the POC Simulation (No model weights needed)

```bash
python poc_simulation.py
```

This executes all **6 deterministic test scenarios** (A–F) and writes `audit_log.json`. No live data or trained weights are required.

### 3. Prepare Data (for full pipeline)

```
data/satellite_images/   <- RGB .jpg/.png satellite tiles
data/flood_masks/         <- Matching grayscale masks (same filenames)
```

### 4. Train the Models

```bash
python -m models.train_model
```

### 5. Launch the Dashboard

```bash
streamlit run dashboard/app.py
```

### 6. Run the Continuous Pipeline

```bash
python main.py                # Disaster monitoring (default)
python main.py --defense      # Defense monitoring mode
python main.py --combined     # Both disaster + defense
python main.py --cycles 3     # Limit to N cycles
```

> Set `COPERNICUS_USER` and `COPERNICUS_PASS` environment variables for live Sentinel-2 streaming.

---

## POC Simulation — Version 1.0

The `poc_simulation.py` script implements the **Prototype Simulation Plan** from Section 8 of the POC document. It runs 6 fully deterministic scenarios with seeded detection values, applies the neuro-symbolic rule engine, and produces structured outputs in two formats.

### Test Scenarios (Section 8.3)

| ID | Scenario | Domain | Input Image Source | Alert Level | Priority |
|----|----------|--------|--------------------|-------------|----------|
| **A** | Coastal Flood Event | DISASTER | Sentinel-1 SAR — Coastal Region | 🔴 RED | 5 |
| **B** | Urban Fire Outbreak | DISASTER | MODIS Terra Band 21/22 — Urban Thermal | 🔴 RED | 5 |
| **C** | Landslide Risk Assessment | DISASTER | Sentinel-2 MSI — Western Ghats | 🟠 ORANGE | 4 |
| **D** | Cyclone Track Landfall | DISASTER | INSAT-3D — Bay of Bengal Track | 🔴 RED | 5 |
| **E** | Border Defense Intrusion | DEFENSE | SAR — Northern Border Restricted Zone | 🔴 CRITICAL | 5 |
| **F** | Compound Flood + Landslide | DISASTER | Sentinel-1 + Sentinel-2 Fusion | 🔴 RED | 5 |

### Output Formats

**Console Report (Appendix A)** — printed per scenario:

```
==================================================================
         === SYSTEM DECISION REPORT ===
==================================================================
  Scenario ID  : A
  Scenario     : Coastal Flood Event
  Domain       : DISASTER
  Image Source : Sentinel-1 SAR -- Coastal Region (12.5m resolution)
  Timestamp    : 2026-04-06T14:14:54Z
------------------------------------------------------------------
  NEURAL DETECTIONS
  --------------------------------------------------------------
    Flood Probability              :  88.00%
    Rainfall Mm                    :  178.00%
    Elevation M                    :  3.50%
------------------------------------------------------------------
  CONTEXT FACTORS
  --------------------------------------------------------------
    Region                         :  Coastal Zone Delta
    Population Density             :  900
    Elevation M                    :  3.5
    Rainfall Mm 24H                :  178.0
------------------------------------------------------------------
  RULES APPLIED
  --------------------------------------------------------------
    >> RULE-F1: flood_prob > 0.80 AND population > 500 -> RED / Evacuate
    >> RULE-F6: rainfall > 150mm -> escalation amplifier
------------------------------------------------------------------
  DECISION OUTCOME
  --------------------------------------------------------------
    Alert Level                    :  [RED     ] RED
    Priority                       :  5

  Actions:
    *  Evacuate Region Immediately
    *  Deploy Rescue Teams
    *  Activate Emergency Shelters
    *  Monitor rainfall trend closely

  Reason(s):
    -> Flood probability (88.0%) exceeded critical threshold (80%)
       with high population density (900)
------------------------------------------------------------------
  XAI EXPLANATION
  --------------------------------------------------------------
  [Scenario A - DISASTER XAI Explanation]
    1. NEURAL PERCEPTION : flood_probability=88.00%, rainfall_mm=178.00%
    2. EVIDENCE FUSION   : Bayesian fusion: P(flood|SAR)=0.91,
                           P(flood|rainfall)=0.87 -> posterior=0.94
    3. POLICY DECISION   : RED triggered -- Flood probability (88.0%)
                           exceeded critical threshold (80%)
==================================================================
```

**JSON Audit Log (Section 8.4)** — written to `audit_log.json`:

```json
{
  "poc_version": "1.0",
  "generated_at": "2026-04-06T14:04:42Z",
  "total_scenarios": 6,
  "decisions": [
    {
      "scenario_id": "A",
      "scenario_name": "Coastal Flood Event",
      "domain": "DISASTER",
      "image_source": "Sentinel-1 SAR - Coastal Region (12.5m resolution)",
      "neural_detections": { "flood_probability": 0.88, "rainfall_mm": 178.0 },
      "context_factors": { "population_density": 900, "elevation_m": 3.5 },
      "rules_applied": [ "RULE-F1: flood_prob > 0.80 AND population > 500 -> RED" ],
      "alert_level": "RED",
      "priority": 5,
      "actions": [ "Evacuate Region Immediately", "Deploy Rescue Teams", "..." ],
      "xai_explanation": "[Scenario A - DISASTER XAI Explanation]\n  1. NEURAL PERCEPTION...",
      "audit_trail": {
        "engine_version": "1.0-POC",
        "rule_set": "neuro_symbolic_v1",
        "decision_method": "symbolic_rule_engine + bayesian_fusion"
      }
    }
  ]
}
```

---

## Deep Learning Model Stack

| Model | Domain | Type | Purpose | Key Feature |
|-------|--------|------|---------|-------------|
| **U-Net** | Disaster | Segmentation | Pixel-wise flood mask | Skip connections, BCE+Dice loss |
| **ResNet50** | Disaster | Classification / Segmentation | Transfer learning features | Pretrained ImageNet, frozen early layers |
| **Vision Transformer (ViT)** | Disaster | Classification | Global flood detection | Patch embeddings, self-attention |
| **ConvLSTM** | Disaster | Temporal | Flood progression | CNN spatial + LSTM temporal |
| **DefenseObjectClassifier** | Defense | Classification | 6-class object detection | CNN backbone → multi-class head |
| **ThreatScoreEstimator** | Defense | Regression | Threat score (0–1) | CNN backbone → sigmoid head |

### Defense Object Classes

| Class ID | Name | Description |
|----------|------|-------------|
| 0 | civilian | No threat — civilian activity |
| 1 | military_vehicle | Armoured or military transport |
| 2 | temporary_installation | Camps, temporary structures |
| 3 | troop_movement | Movement patterns indicating troop activity |
| 4 | naval_vessel | Maritime military vessel |
| 5 | aircraft_drone | Aircraft or unmanned aerial vehicle |

---

## Explainable AI (XAI) Layer

### Grad-CAM (Neural Explanation)

Grad-CAM highlights **which regions of the satellite image** caused the model's prediction by computing gradient-weighted class activation maps on the target convolutional layer.

```
Input Image → Model Forward Pass → Target Layer Activations
                                            ↓
                    Backprop Gradients → Channel Weights
                                            ↓
                    Weighted Sum → ReLU → Heatmap Overlay
```

Supported models: U-Net (bottleneck), ResNet (layer4), ViT (last transformer layer).

### Symbolic Explanation Generator

Produces a **full reasoning narrative** tracing every decision through the pipeline:

```
[Disaster Response Explanation]
1. NEURAL PERCEPTION: Strong flood signal detected across 3 models (ensemble: 91.2%).
   High-confidence models: unet, resnet_classifier, vit.
2. EVIDENCE FUSION: Bayesian fusion significantly increased the flood estimate
   (prior 30.0% → posterior 94.2%). Dominant evidence source: satellite.
3. POLICY DECISION: Alert RED triggered because: Flood probability (94.2%) exceeded
   critical threshold (80%) with high population density (900).
```

---

## Neuro-Symbolic Reasoning

### Disaster Policy Rules

| Condition | Alert Level | Actions | Reason |
|-----------|-------------|---------|--------|
| Flood > 80% & Pop > 500 | 🔴 RED | Evacuate, Deploy Rescue, Activate Shelters | Critical flood + dense population |
| Flood > 60% & Pop > 200 | 🟠 ORANGE | Warning, Pre-position Boats, Alert Medical | High flood + moderate population |
| Flood > 60% | 🟡 YELLOW | Send Drone, Notify Authorities | Moderate flood risk |
| Flood > 40% & Elev < 10m | 🟡 YELLOW | Low-Elevation Alert, Sandbags | Low elevation amplifies risk |
| Flood > 30% | 🔵 BLUE | Increase Monitoring | Above monitoring threshold |
| Flood ≤ 30% | 🟢 GREEN | Safe – No action | Below all thresholds |

### Defense Rules

| Condition | Threat Level | Actions |
|-----------|-------------|---------|
| Vehicles > 3, moving to border, restricted zone | 🔴 CRITICAL | Alert command, deploy reaction force, activate border defense |
| High threat (>70%) + military objects near border (<5km) | 🟠 HIGH | Aerial surveillance, brief command, increase patrols |
| Temporary installation + threat >50% | 🟡 ELEVATED | Recon drone, monitor, log for analysis |
| Multiple vehicles in border zone | 🟡 ELEVATED | Increase monitoring, cross-reference patterns |
| Moderate threat or non-civilian | 🔵 GUARDED | Flag for review, schedule follow-up |
| All normal | 🟢 SAFE | Routine monitoring |

### Knowledge Graph

```
Region → has_risk → Risk Level → triggers → Policy → deploys → Resources
```

### Bayesian Decision Network

Fuses evidence using Bayes' theorem:
- P(flood | satellite), P(flood | rainfall), P(flood | elevation), P(flood | soil moisture)
- Produces calibrated posterior with confidence score.

---

## Innovation: Neuro-Symbolic AI vs Traditional Deep Learning

| Feature | Traditional DL-Only | Our Neuro-Symbolic AI |
|---------|--------------------|-----------------------|
| Decision Explainability | ❌ Black-box predictions | ✅ Grad-CAM + rule trace + natural language |
| Uncertainty Quantification | ❌ Point estimates only | ✅ Bayesian posterior with confidence |
| Policy Compliance | ❌ Not enforced | ✅ Symbolic rules enforce domain policy |
| Multi-Source Fusion | ❌ Single model, single input | ✅ 4+ models + Bayesian + Knowledge Graph |
| Audit Trail | ❌ No logging | ✅ Full timestamped decision log |
| Domain Adaptability | ❌ Single domain | ✅ Disaster + Defense (dual-domain) |
| Human Oversight | ❌ No intervention points | ✅ Rule thresholds configurable by experts |
| Reasoning Transparency | ❌ Cannot explain why | ✅ KG path + Bayesian chain + rule reasons |

---

## Example Output (Continuous Pipeline — Disaster Mode)

```
  Region:          Kerala Sector 4
  Domain:          DISASTER
  Event Type:      FLOOD
  ------------------------------------------------
  Alert Level:     RED
  Priority:        5
  Reason: Flood probability (88.0%) exceeded critical
          threshold (80%) with high population density (900)
  Actions:
    * Evacuate Region Immediately
    * Deploy Rescue Teams
    * Activate Emergency Shelters
```

## Example Output (Continuous Pipeline — Defense Mode)

```
  Region:          Border Sector Alpha
  Domain:          DEFENSE
  Event Type:      DEFENSE
  ------------------------------------------------
  Threat Level:    CRITICAL
  Priority:        5
  Reason: 5 armoured vehicles moving toward border in restricted zone
  Actions:
    * Alert Military Command Immediately
    * Deploy Rapid Reaction Force
    * Activate Border Defense Systems
```

## Research Contribution

This project demonstrates:

- **Neuro-symbolic AI integration** — combining neural perception with symbolic reasoning for principled decision-making
- **Explainable AI (XAI)** — Grad-CAM spatial explanations + natural-language reasoning narratives
- **Dual-domain versatility** — same architecture handles disaster response AND defense monitoring
- **Multi-model ensemble** — ResNet + U-Net + ViT + ConvLSTM for robust predictions
- **Bayesian uncertainty reasoning** — calibrated probabilities from multiple evidence sources
- **Knowledge graph reasoning** — structured entity relationships for resource deployment
- **Real-time monitoring** — continuous satellite data processing with sliding window smoothing
- **Full auditability** — every decision traceable through the complete reasoning chain
- **POC-compliant simulation** — deterministic 6-scenario test suite with structured JSON audit logs

This type of system is studied by organizations including **DARPA**, **IBM Research**, and **ESA**.

---

## File Reference

| File | Description |
|------|-------------|
| `main.py` | Continuous multi-hazard + defense monitoring (CLI flags) |
| `poc_simulation.py` | POC simulation runner — Scenarios A–F, Section 8.3 |
| `poc_formatter.py` | Output formatter — Appendix A console + Section 8.4 JSON |
| `audit_log.json` | Auto-generated on each POC run — full structured audit |
| `reasoning/decision_engine.py` | Core neuro-symbolic decision orchestrator |
| `reasoning/symbolic_rules.py` | Symbolic rule functions for all hazard types |
| `realtime/simulator.py` | Real-time multi-hazard simulation engine |
| `symbolic/bayesian_network.py` | Bayesian evidence fusion network |
| `symbolic/knowledge_graph.py` | NetworkX knowledge graph reasoning |
| `dashboard/app.py` | Streamlit real-time dashboard |

## License

Research use only. See individual dataset licenses for data usage terms.
