"""
Dashboard Visualization Module.

Provides visualization functions for the Streamlit dashboard:
  - Event maps with risk regions
  - Risk level indicators
  - AI explanation panels
  - Decision timeline charts
  - Model comparison charts
"""

import numpy as np

try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


# ── Alert/Threat Colour Maps ────────────────────────────────────────────────
ALERT_COLORS = {
    "RED": "#FF0000",
    "ORANGE": "#FF8C00",
    "YELLOW": "#FFD700",
    "BLUE": "#1E90FF",
    "GREEN": "#32CD32",
}

THREAT_COLORS = {
    "CRITICAL": "#FF0000",
    "HIGH": "#FF8C00",
    "ELEVATED": "#FFD700",
    "GUARDED": "#1E90FF",
    "SAFE": "#32CD32",
}

ALERT_ICONS = {
    "RED": "🔴", "ORANGE": "🟠", "YELLOW": "🟡",
    "BLUE": "🔵", "GREEN": "🟢",
}

THREAT_ICONS = {
    "CRITICAL": "🔴", "HIGH": "🟠", "ELEVATED": "🟡",
    "GUARDED": "🔵", "SAFE": "🟢",
}

HAZARD_ICONS = {
    "flood": "🌊", "landslide": "🏔️", "cyclone": "🌀",
    "fire": "🔥", "defense": "🛡️", "compound": "⚠️",
}


def get_alert_icon(alert_level):
    """Get emoji icon for an alert level."""
    return ALERT_ICONS.get(alert_level, "⚪")


def get_threat_icon(threat_level):
    """Get emoji icon for a threat level."""
    return THREAT_ICONS.get(threat_level, "⚪")


def get_hazard_icon(hazard_type):
    """Get emoji icon for a hazard type."""
    return HAZARD_ICONS.get(hazard_type, "❓")


def format_decision_card(decision):
    """
    Format a decision into a dashboard-ready display card.

    Returns
    -------
    dict with formatted display fields.
    """
    event_type = decision.get("event_type", "unknown")
    icon = get_hazard_icon(event_type)

    if event_type == "defense":
        level = decision.get("threat_level", "SAFE")
        level_icon = get_threat_icon(level)
    else:
        level = decision.get("alert_level", "GREEN")
        level_icon = get_alert_icon(level)

    return {
        "icon": icon,
        "event_type": event_type.replace("_", " ").title(),
        "level": level,
        "level_icon": level_icon,
        "region": decision.get("region", "Unknown"),
        "priority": decision.get("priority", 0),
        "actions": decision.get("actions", []),
        "reasons": decision.get("reasons", []),
        "timestamp": decision.get("timestamp", ""),
    }


def create_risk_gauge(probability, title="Risk Level"):
    """
    Create a gauge chart showing risk probability.

    Returns a Plotly figure or None if Plotly unavailable.
    """
    if not HAS_PLOTLY:
        return None

    color = "#32CD32"
    if probability > 0.8:
        color = "#FF0000"
    elif probability > 0.6:
        color = "#FF8C00"
    elif probability > 0.4:
        color = "#FFD700"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=probability * 100,
        title={"text": title},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 30], "color": "#E8F5E9"},
                {"range": [30, 60], "color": "#FFF9C4"},
                {"range": [60, 80], "color": "#FFE0B2"},
                {"range": [80, 100], "color": "#FFCDD2"},
            ],
        },
        number={"suffix": "%"},
    ))
    fig.update_layout(height=250, margin=dict(t=40, b=10, l=30, r=30))
    return fig


def create_multi_hazard_chart(detections):
    """
    Create a bar chart comparing hazard probabilities.

    Parameters
    ----------
    detections : dict
        hazard_type → detection result mapping.

    Returns a Plotly figure or None.
    """
    if not HAS_PLOTLY:
        return None

    hazards = []
    probs = []
    colors = []

    color_map = {
        "flood": "#1E90FF",
        "landslide": "#8B4513",
        "cyclone": "#9370DB",
        "fire": "#FF4500",
        "defense": "#2F4F4F",
    }

    for hazard, data in detections.items():
        hazards.append(hazard.title())
        prob = data.get("probability", data.get("confidence", data.get("threat_score", 0)))
        probs.append(prob * 100)
        colors.append(color_map.get(hazard, "#808080"))

    fig = go.Figure(go.Bar(
        x=hazards,
        y=probs,
        marker_color=colors,
        text=[f"{p:.1f}%" for p in probs],
        textposition="auto",
    ))
    fig.update_layout(
        title="Multi-Hazard Detection Probabilities",
        yaxis_title="Probability (%)",
        yaxis_range=[0, 100],
        height=350,
    )
    return fig


def create_decision_timeline(decision_log, max_entries=20):
    """
    Create a timeline of recent decisions.

    Parameters
    ----------
    decision_log : list[dict]
        Decision log entries.
    max_entries : int
        Max entries to display.

    Returns a Plotly figure or None.
    """
    if not HAS_PLOTLY or not decision_log:
        return None

    recent = decision_log[-max_entries:]

    timestamps = list(range(len(recent)))
    priorities = [d.get("priority", 0) for d in recent]
    labels = [d.get("event_type", "unknown") for d in recent]
    colors = []

    for d in recent:
        p = d.get("priority", 0)
        if p >= 5:
            colors.append("#FF0000")
        elif p >= 4:
            colors.append("#FF8C00")
        elif p >= 3:
            colors.append("#FFD700")
        elif p >= 2:
            colors.append("#1E90FF")
        else:
            colors.append("#32CD32")

    fig = go.Figure(go.Scatter(
        x=timestamps,
        y=priorities,
        mode="markers+lines",
        marker=dict(size=12, color=colors),
        text=labels,
        hovertemplate="Event: %{text}<br>Priority: %{y}<extra></extra>",
    ))
    fig.update_layout(
        title="Decision Timeline",
        xaxis_title="Event Sequence",
        yaxis_title="Priority Level",
        yaxis_range=[0, 6],
        height=300,
    )
    return fig


def format_innovation_comparison():
    """
    Return the neuro-symbolic vs traditional AI comparison table data.
    """
    return {
        "Feature": [
            "Decision Explainability",
            "Uncertainty Quantification",
            "Policy Compliance",
            "Multi-Source Fusion",
            "Audit Trail",
            "Multi-Hazard Coverage",
            "Defense Integration",
        ],
        "Traditional DL": [
            "❌ Black-box",
            "❌ Point estimates",
            "❌ Not enforced",
            "❌ Single model",
            "❌ No logging",
            "❌ Single hazard",
            "❌ Separate system",
        ],
        "Neuro-Symbolic AI (Ours)": [
            "✅ Symbolic rule trace + explanations",
            "✅ Bayesian posterior + confidence",
            "✅ Symbolic rules enforce policy",
            "✅ Ensemble (CNN + ViT + YOLO) + Bayesian",
            "✅ Full decision log with timestamps",
            "✅ Flood + Landslide + Cyclone + Fire",
            "✅ Unified defense monitoring",
        ],
    }
