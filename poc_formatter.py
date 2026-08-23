"""
POC Formatter - Section 8.4 & Appendix A Output Compliance
===========================================================

Produces two output formats mandated by the
"Version 1.0 Proof of Concept Document":

  1. JSON structured decision record  ->  audit_log.json
  2. Console "=== SYSTEM DECISION REPORT ===" table  ->  stdout

Both formats are deterministic given the same scenario inputs.
"""

import io
import json
import os
import sys
from datetime import datetime, timezone

# Force UTF-8 output on Windows so box-drawing chars survive.
# Falls back gracefully if reconfigure is not available.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ts() -> str:
    """ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _bar(char="=", width=66) -> str:
    return char * width


def _section(title: str, char="-", width=66) -> str:
    return f"  {title}\n  {char * (width - 2)}"


# ── JSON Formatter ─────────────────────────────────────────────────────────────

def build_json_record(scenario: dict, decision: dict, detections: dict) -> dict:
    """
    Build a structured JSON record matching the POC Section 8.4 schema.

    Parameters
    ----------
    scenario : dict
        Scenario metadata (id, name, domain, image_source, …).
    decision : dict
        Output dict from DecisionEngine (alert/threat level, actions, …).
    detections : dict
        Neural detection values used as input to the engine.

    Returns
    -------
    dict
        JSON-serialisable decision record.
    """
    domain = scenario.get("domain", "DISASTER")
    sid = scenario.get("id", "X")
    name = scenario.get("name", "Unknown")
    image_source = scenario.get("image_source", "N/A")

    # Alert / threat level
    if domain == "DEFENSE":
        alert_val = decision.get("threat_level", "SAFE")
        alert_key = "threat_level"
    else:
        alert_val = decision.get("alert_level", "GREEN")
        alert_key = "alert_level"

    # Neural-layer summary
    neural_summary: dict = {}
    for k, v in detections.items():
        if isinstance(v, float):
            neural_summary[k] = round(v, 4)
        else:
            neural_summary[k] = v

    # Context factors (pass-through from scenario)
    context_factors = scenario.get("context_factors", {})

    # XAI explanation (generated from rules applied)
    rules_applied = scenario.get("rules_applied", [])
    xai_explanation = _generate_xai(scenario, decision, detections)

    record = {
        "scenario_id": sid,
        "scenario_name": name,
        "domain": domain,
        "timestamp": _ts(),
        "image_source": image_source,
        "neural_detections": neural_summary,
        "context_factors": context_factors,
        "rules_applied": rules_applied,
        alert_key: alert_val,
        "priority": decision.get("priority", 0),
        "actions": decision.get("actions", []),
        "reasons": decision.get("reasons", []),
        "xai_explanation": xai_explanation,
        "confidence": scenario.get("confidence", "HIGH"),
        "audit_trail": {
            "engine_version": "1.0-POC",
            "rule_set": "neuro_symbolic_v1",
            "decision_method": "symbolic_rule_engine + bayesian_fusion",
        },
    }

    return record


def _generate_xai(scenario: dict, decision: dict, detections: dict) -> str:
    """Generate a natural-language XAI explanation string."""
    domain = scenario.get("domain", "DISASTER")
    sid = scenario.get("id", "X")

    lines = [f"[Scenario {sid} - {domain} XAI Explanation]"]

    # Step 1: Neural perception
    neural_parts = []
    for k, v in detections.items():
        if isinstance(v, float):
            neural_parts.append(f"{k}={v:.2%}")
        else:
            neural_parts.append(f"{k}={v}")
    lines.append(f"  1. NEURAL PERCEPTION : {', '.join(neural_parts)}")

    # Step 2: Evidence fusion / Bayesian
    bayesian_note = scenario.get("bayesian_note", "")
    if bayesian_note:
        lines.append(f"  2. EVIDENCE FUSION   : {bayesian_note}")
    else:
        lines.append(f"  2. EVIDENCE FUSION   : Symbolic rules applied over neural detections.")

    # Step 3: Policy decision
    if domain == "DEFENSE":
        level = decision.get("threat_level", "SAFE")
    else:
        level = decision.get("alert_level", "GREEN")
    reasons = decision.get("reasons", [])
    reason_str = reasons[0] if reasons else "N/A"
    lines.append(f"  3. POLICY DECISION   : {level} triggered — {reason_str}")

    return "\n".join(lines)


def save_audit_log(records: list, output_path: str = None) -> str:
    """
    Append all scenario records to audit_log.json.

    Parameters
    ----------
    records : list[dict]
        List of JSON records from build_json_record().
    output_path : str or None
        File path override (default: <script dir>/audit_log.json).

    Returns
    -------
    str
        Absolute path to the written file.
    """
    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "audit_log.json"
        )

    wrapper = {
        "poc_version": "1.0",
        "generated_at": _ts(),
        "total_scenarios": len(records),
        "decisions": records,
    }

    with open(output_path, "w", encoding="utf-8") as fp:
        json.dump(wrapper, fp, indent=2, ensure_ascii=False)

    return output_path


# ── Console Report Formatter (Appendix A) ─────────────────────────────────────

def print_poc_decision_report(scenario: dict, decision: dict, detections: dict):
    """
    Print the exact "=== SYSTEM DECISION REPORT ===" block defined in
    Appendix A of the POC document to stdout.

    Parameters
    ----------
    scenario : dict
        Scenario metadata.
    decision : dict
        DecisionEngine output.
    detections : dict
        Neural layer detections.
    """
    W = 66
    domain = scenario.get("domain", "DISASTER")
    sid = scenario.get("id", "X")
    name = scenario.get("name", "Unknown Scenario")
    image_source = scenario.get("image_source", "N/A")

    if domain == "DEFENSE":
        alert_val = decision.get("threat_level", "SAFE")
        alert_label = "Threat Level"
    else:
        alert_val = decision.get("alert_level", "GREEN")
        alert_label = "Alert Level"

    # Alert level tag map (ASCII-safe)
    alert_tag = {
        "RED":      "[RED     ]",
        "ORANGE":   "[ORANGE  ]",
        "YELLOW":   "[YELLOW  ]",
        "BLUE":     "[BLUE    ]",
        "GREEN":    "[GREEN   ]",
        "CRITICAL": "[CRITICAL]",
        "HIGH":     "[HIGH    ]",
        "ELEVATED": "[ELEVATED]",
        "GUARDED":  "[GUARDED ]",
        "SAFE":     "[SAFE    ]",
    }
    emoji = alert_tag.get(alert_val, "[UNKNOWN ]")

    print()
    print(_bar("=", W))
    print(f"  {'=== SYSTEM DECISION REPORT ===':^{W - 4}}")
    print(_bar("=", W))
    print(f"  Scenario ID  : {sid}")
    print(f"  Scenario     : {name}")
    print(f"  Domain       : {domain}")
    print(f"  Image Source : {image_source}")
    print(f"  Timestamp    : {_ts()}")
    print(_bar("-", W))

    # -- Neural Detections --------------------------------------------------
    print(f"  NEURAL DETECTIONS")
    print(f"  {'-' * 62}")
    for k, v in detections.items():
        label = k.replace("_", " ").title()
        if isinstance(v, float):
            print(f"    {label:<30}:  {v:.2%}")
        else:
            print(f"    {label:<30}:  {v}")

    print(_bar("-", W))

    # -- Context Factors ----------------------------------------------------
    ctx = scenario.get("context_factors", {})
    if ctx:
        print(f"  CONTEXT FACTORS")
        print(f"  {'-' * 62}")
        for k, v in ctx.items():
            label = k.replace("_", " ").title()
            if isinstance(v, float):
                print(f"    {label:<30}:  {v}")
            else:
                print(f"    {label:<30}:  {v}")
        print(_bar("-", W))

    # -- Rules Applied -----------------------------------------------------
    rules = scenario.get("rules_applied", [])
    if rules:
        print(f"  RULES APPLIED")
        print(f"  {'-' * 62}")
        for r in rules:
            print(f"    >> {r}")
        print(_bar("-", W))

    # -- Decision Outcome --------------------------------------------------
    print(f"  DECISION OUTCOME")
    print(f"  {'-' * 62}")
    print(f"    {alert_label:<30}:  {emoji} {alert_val}")
    print(f"    {'Priority':<30}:  {decision.get('priority', 0)}")

    print(f"\n  Actions:")
    for action in decision.get("actions", []):
        print(f"    *  {action}")

    reasons = decision.get("reasons", [])
    if reasons:
        print(f"\n  Reason(s):")
        for r in reasons:
            print(f"    -> {r}")

    print(_bar("-", W))

    # -- XAI Explanation ---------------------------------------------------
    print(f"  XAI EXPLANATION")
    print(f"  {'-' * 62}")
    xai = _generate_xai(scenario, decision, detections)
    for line in xai.splitlines():
        print(f"  {line}")

    print(_bar("=", W))
