"""
Launcher for NeuroSym Crisis Emergency Information System (Pure HTML/CSS/JS).
"""

import sys
import os
import webbrowser
import subprocess

def main():
    print("=" * 60)
    print("🛡️  NEUROSYM CRISIS — EMERGENCY INFORMATION SYSTEM")
    print("=" * 60)
    print("1. Open Government & Citizen Portal (index.html)")
    print("2. Run 6-Scenario Proof-of-Concept Suite (CLI)")
    print("3. Start Local Web Server (http://localhost:8000)")
    print("=" * 60)
    
    choice = input("Select option (1/2/3) [Default: 1]: ").strip() or "1"
    
    if choice == "1":
        html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "index.html"))
        print(f"\n🌐 Opening Web Portal in your default browser:\n{html_path}\n")
        webbrowser.open(f"file:///{html_path}")
    elif choice == "2":
        print("\n🧪 Running POC Simulation Suite...")
        subprocess.run([sys.executable, "poc_simulation.py"])
    elif choice == "3":
        print("\n🚀 Starting HTTP Server at http://localhost:8000 ...")
        subprocess.run([sys.executable, "-m", "http.server", "8000"])
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
