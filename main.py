"""
Main CLI Entrypoint for NeuroSym Crisis.
Emergency Information Intelligence & Rumor Filter.
"""

import sys
import os
import argparse
import webbrowser
import subprocess

# Ensure UTF-8 output on Windows terminal
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pipeline.ingestion import AlertIngestionPipeline
from pipeline.clustering import EventClusterer
from pipeline.verification import VerificationPipeline
from pipeline.digest import EmergencyDigestGenerator
from models.llm_extractor import llm_extractor
from poc_simulation import POCSimulationRunner


def run_full_pipeline(scenario_filter=None):
    print("=" * 80)
    print("🛡️  NEUROSYM CRISIS — EMERGENCY INFORMATION INTELLIGENCE PIPELINE")
    print("=" * 80)

    ingestion = AlertIngestionPipeline()
    clusterer = EventClusterer()
    verifier = VerificationPipeline()
    digest_gen = EmergencyDigestGenerator()

    alerts = ingestion.load_alerts(filter_scenario=scenario_filter)
    print(f"📥 Loaded {len(alerts)} alerts.")

    clusters = clusterer.cluster_alerts(alerts)
    print(f"🔗 Semantic Clustering: {len(clusters)} unified event clusters.")

    results = verifier.verify_alerts(alerts, clusters)
    print(f"🔍 Neuro-Symbolic Verification completed for {len(results)} alerts.")

    digest = digest_gen.generate_digest(alerts, clusters, results)
    print(f"\n🚨 Emergency Digest Generated for {digest.region}")
    print(f"📊 Status Breakdown: {digest.counts_by_status}")
    print(f"📉 Noise Reduction Ratio: {digest.noise_reduction_percentage}%\n")

    print("--- ACTIONABLE EMERGENCY DIGEST ---")
    for idx, item in enumerate(digest.items[:5]):
        print(f"[{item.status_badge}] {item.title}")
        print(f"   Action: {item.key_action}")
        print(f"   Note:   {item.source_note}\n")

    print("--- SHAREABLE CHECKLIST ---")
    for chk in digest.shareable_checklist:
        print(f"  {chk}")
    print("=" * 80)


def verify_single_text(text: str, source: str = "Citizen Report", source_type: str = "citizen"):
    ingestion = AlertIngestionPipeline()
    verifier = VerificationPipeline()

    alert = ingestion.ingest_single(text, source, source_type)
    claim = llm_extractor.extract_from_text(alert.id, alert.text)
    res = verifier.engine.verify_claim(alert, claim)

    print("\n" + "=" * 60)
    print("🔍 SINGLE ALERT VERIFICATION RESULT")
    print("=" * 60)
    print(f"Claim:          \"{res.claim_text}\"")
    print(f"Source:         {res.source_name} ({res.source_type.value})")
    print(f"Decision:       {res.status.value} (Confidence: {res.confidence * 100:.1f}%)")
    print(f"Rule:           {res.rule_triggered}")
    print(f"Explanation:    {res.explanation}")
    print(f"Action:         {res.recommended_action}")
    if res.official_evidence:
        print(f"Evidence Doc:   {res.official_evidence.doc_title}")
        print(f"Evidence Quote: \"{res.official_evidence.excerpt}\"")
    print("=" * 60)


def open_web_portal():
    html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "index.html"))
    print(f"🌐 Opening Government & Citizen Portal in your default browser:\n{html_path}")
    webbrowser.open(f"file:///{html_path}")


def main():
    parser = argparse.ArgumentParser(description="NeuroSym Crisis CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run full pipeline on dataset")
    run_parser.add_argument("--scenario", type=str, default=None, help="Filter by scenario ID (e.g. 'Scenario F')")

    # POC command
    subparsers.add_parser("poc", help="Run 6-scenario POC benchmark simulation")

    # Web portal command
    subparsers.add_parser("web", help="Open the Government & Citizen HTML Portal")
    subparsers.add_parser("dashboard", help="Open the Government & Citizen HTML Portal")

    # Verify single text command
    verify_parser = subparsers.add_parser("verify", help="Verify a single text message")
    verify_parser.add_argument("text", type=str, help="Alert text or speech transcript")
    verify_parser.add_argument("--source", type=str, default="Citizen Message", help="Source name")
    verify_parser.add_argument("--source-type", type=str, default="social_media", help="Source type")

    args = parser.parse_args()

    if args.command == "poc":
        runner = POCSimulationRunner()
        runner.run_all_scenarios()
    elif args.command in ["web", "dashboard"]:
        open_web_portal()
    elif args.command == "verify":
        verify_single_text(args.text, args.source, args.source_type)
    else:
        run_full_pipeline(scenario_filter=getattr(args, "scenario", None))


if __name__ == "__main__":
    main()
