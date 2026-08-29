# 🛡️ NeuroSym Crisis

### **Emergency Information Intelligence + Offline Emergency Mesh**
> *Turning noisy disaster chaos into verified event intelligence & guaranteeing communication when cellular networks fail.*

---

> ### 💬 **The Core Pitch**
> *"During disasters, governments face two lethal bottlenecks: **Information Chaos** (hundreds of conflicting rumors) and **Communication Failure** (cellular towers going dark). **NeuroSym Crisis** solves both: it gives control rooms a pre-dissemination AI intelligence layer to verify and synthesize emergency digests, paired with an offline phone-to-phone emergency mesh (BLE/Wi-Fi Direct) to keep vital SOS alerts moving even with zero internet."*

---

## 🔄 Dual-Engine Architecture (PRD v2.0)

```text
                             DISASTER EVENT
                                   │
                                   ↓
                         INFORMATION CHAOS & OUTAGE
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         ↓                                                   ↓
   PROBLEM 1: INFORMATION CHAOS                        PROBLEM 2: NETWORK FAILURE
         │                                                   │
         ↓                                                   ↓
   AI VERIFICATION & EVENT CLUSTERING                  OFFLINE MOBILE MESH
   (LLM Extraction + RAG + Symbolic Rules)             (BLE / Wi-Fi Direct Store-and-Forward)
         │                                                   │
         └─────────────────────────┬─────────────────────────┘
                                   ↓
                       🏛️ GOVERNMENT CONTROL ROOM
                       (11 Events, 6 Conflicts, 3 Offline SOS)
                                   ↓
                         HUMAN OFFICER APPROVAL
                                   ↓
                    📢 AUTHORIZE & DUAL BROADCAST
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         ↓                                                   ↓
   SACHET / CAP BROADCAST GATEWAYS                     OFFLINE CITIZEN P2P MESH
   (Public SMS / Web / App Feeds)                      (Hop-by-Hop Phone Relay)
```

---

## 📱 Offline Store-and-Forward Mesh Network

When internet and cellular infrastructure collapses:

```text
   [Citizen A (Trapped)] ──── BLE Beaconing ───➔ [Citizen B (Shopkeeper Device)]
                                                              │
                                                        Wi-Fi Direct
                                                              ↓
   [DDMA Government Gateway] ⮜── Wi-Fi Aware ─── [Citizen C (Volunteer Node)]
```

* **Packet Structure:** `message_id`, `sender_id`, `type` (`SOS_MEDICAL`, `SOS_RESCUE`, `REPORT_HAZARD`), `priority` (`CRITICAL`), `location` (`lat`, `lon`), `timestamp`, `hop_count`, `ttl`.
* **Zero Internet Required:** Uses local SQLite / Room storage to buffer packets until peer discovery occurs.
* **Bi-Directional:** Citizens send multi-hop SOS alerts; Government broadcasts verified emergency digests back through the mesh.
  * ✓ Time identified: `Before 6 PM`
  * ✓ Message clarity: `Good`
* **Citizen Preview Card:** 🔴 `FLOOD ALERT` — `Zone A residents are advised to evacuate before 6 PM.`
* **Approve & Send:** Generates published Alert ID (e.g. `NC-2026-0081`), records recipients (`4,820 citizens`), and links directly to citizen view.

---

### 👥 Portal 2: Citizen Receive Portal

#### **Screen 3: Citizen Home / Emergency Feed**
* **Header:** `🇮🇳 EMERGENCY INFORMATION | Kanyakumari District | Last updated: 14:35 ● System Active`
* **Active Emergencies Feed:**
  * 🔴 **FLOOD — Zone A:** *"Residents are advised to evacuate before 6:00 PM."* &bull; `[ View details → ]`
  * 🟠 **INFORMATION WARNING:** *"A message circulating online claims that Shelter A is closed. This conflicts with the latest official information."* &bull; `[ Check information → ]`

#### **Screen 4: Emergency Detail & Rumor Verification**
* **Emergency Detail View:**
  * **WHAT IS HAPPENING?** Rising water levels have been reported in Zone A.
  * **WHAT SHOULD YOU DO?** 1. Evacuate before 6 PM, 2. Move to designated shelter, 3. Follow official updates.
  * **SHELTER:** Shelter A (Open until 10 PM).
  * **SOURCE:** District Disaster Management Authority (🟢 `VERIFIED OFFICIAL INFORMATION`).
* **Information Verification (Hero Feature):**
  * **CLAIM:** *"Shelter A is closed."* (Source: Community message • Time: 14:31)
  * **STATUS:** 🟠 **CONFLICTING INFORMATION** *(Never "Fake News")*
  * **OFFICIAL INFORMATION:** *"Shelter A remains operational until 10 PM."* (Source: District Emergency Authority • Updated: 14:35)
  * **WHY IS THIS FLAGGED?** The claim conflicts with the latest official emergency information. Official information has higher source priority.

---

## 🎨 Visual Design System

| Element | Specification |
| :--- | :--- |
| **Background** | Off-white (`#F7F7F5`) |
| **Cards** | Clean White (`#FFFFFF`) with thin borders (`#D9D9D9`) |
| **Primary Text** | Dark Charcoal (`#202020`) |
| **Secondary Text** | Medium Grey (`#666666`) |
| **Typography** | `Inter` / `Noto Sans` (Standard Indian Government Document Hierarchy) |
| **Border Radius** | 4px–6px subtle rounded corners |
| **Status Indicators** | 🟢 **Verified/Supported** (`#15803d`) &bull; 🟠 **Conflicting** (`#b45309`) &bull; 🔴 **Urgent/Unsupported** (`#b91c1c`) |

## 📚 Official Evidence Retrieval (RAG) Architecture

> **The RAG is NOT a chatbot and NOT web search.**  
> It is an **Official Evidence Retrieval Engine** that grounds incoming disaster messages against verified sovereign guidance documents (NDMA, SACHET, IMD, CWC, TNSDMA, Kanyakumari DDMA).

```text
1. INCOMING MESSAGE
   "Shelter A is closed and flooded." (Community WhatsApp)
          │
          ▼
2. LLM STRUCTURED EXTRACTION
   Event: Cyclone & Flood | Location: Zone A | Entity: Shelter A | Action: CLOSED | Time: 14:30 IST
          │
          ▼
3. HYBRID METADATA FILTER & RETRIEVAL
   Filter: [District=Kanyakumari, Hazard=Cyclone, Authority=Tier 1-2] + Semantic Search
          │
          ▼
4. RETRIEVED OFFICIAL EVIDENCE (EVIDENCE PACK)
   "Shelter A (Govt Model School) is FULLY OPERATIONAL (OPEN 24/7) with 350 available spaces."
   Source: District Relief Commissioner Bulletin Ref: KK_SHELTER_2026_02 | Updated: 14:35 IST
          │
          ▼
5. SYMBOLIC CONFLICT COMPARISON
   Claim: CLOSED vs Evidence: OPEN_24_7 ➔ Direct Contradiction
   Rule Applied: RULE_3_OFFICIAL_CONFLICT (Tier 1 Sovereign > Tier 5 Community)
          │
          ▼
6. VERIFICATION DECISION
   Status: 🟠 CONFLICTING (Flagged with explainable reason)
          │
          ▼
7. HUMAN OFFICER APPROVAL
   Officer reviews evidence ➔ Authorizes synthesized 4-Q digest ➔ Broadcasts to citizens
```

### 📁 Knowledge Base Folder Structure

```text
knowledge_base/
├── national/
│   └── ndma_flood_sop.txt             # NDMA Flood SOP & evacuation cutoffs
├── alerts/
│   └── sachet_alert_examples.txt      # SACHET / CAP warning bulletins & rumor neutralization protocols
├── weather/
│   └── imd_cyclone_warning.txt        # IMD Cyclone Varun storm surge & windspeed tracking
├── flood/
│   └── cwc_flood_bulletin.txt         # Central Water Commission river levels & bridge scour data
├── tamilnadu/
│   └── tnsdma_disaster_plan.txt       # State disaster response framework & DEOC inter-agency standards
└── kanyakumari/
    ├── evacuation_plan.txt            # Mandatory Zone A evacuation order & SH-44 green corridor
    └── shelter_directory.txt          # Active shelter registry (Shelter A open 24/7 with 350 spaces)
```

### 🏷️ Chunk Metadata Schema

| Field | Example Value | Description |
| :--- | :--- | :--- |
| `document_id` | `KK_EVAC_2026_01` | Unique sovereign document reference |
| `source` | `Kanyakumari DDMA` | Issuing government agency / department |
| `authority` | `Tier 1` | Tier 1 (Sovereign) / Tier 2 (Police/Services) / Tier 3 (IMD/CWC) |
| `hazard` | `Cyclone & Flood` | Disaster hazard category for pre-filtering |
| `district` | `Kanyakumari` | Geographic administrative boundary |
| `language` | `English / Tamil` | Document publication language |
| `issued_date` | `2026-08-29` | Timestamp for temporal freshness calculation |
| `expiry_date` | `2026-08-30` | Document validity expiration |
| `section` | `Evacuation Order` | Heading-aware context anchor |

---

## ⚖️ Symbolic Logic Rules Catalog (`reasoning/symbolic_rules.py`)

| Rule ID | Name | Trigger Condition | Output Status | Confidence |
| :--- | :--- | :--- | :--- | :--- |
| `RULE_1` | **Official Supported** | Source = Official $\land$ Grounded in Official Guidance | 🟢 **SUPPORTED** | 99% |
| `RULE_2` | **Community Corroborated** | Source $\neq$ Official $\land$ Official Evidence Corroborates | 🔵 **CORROBORATED** | 89% |
| `RULE_3` | **Authoritative Contradiction** | Source $\neq$ Official $\land$ Official Evidence Contradicts | 🟠 **CONFLICTING** *(Rumor)* | 96% |
| `RULE_4` | **Absence of Evidence** | No authoritative record or unverified assertion | 🔴 **UNSUPPORTED** | 88% |
| `RULE_5` | **Temporal Supersession** | Older alert contradicted by newer official update | ⚪ **OUTDATED** | 94% |

---

## 🧪 6 Proof-of-Concept (POC) Validation Scenarios

| Scenario | Objective | Output / Demo Result |
| :--- | :--- | :--- |
| **Scenario A** | **Duplicate Flood Alerts** | Fuses redundant flood messages into single unified event with ~71% noise reduction. |
| **Scenario B** | **Conflicting Shelter Rumors** | Detects "Shelter A closed" rumor; flags `CONFLICTING` against official open status. |
| **Scenario C** | **Unsupported Alarmist Claims** | Filters ungrounded claims (e.g. "all hospitals closed", "dam burst", "drinking saltwater"). |
| **Scenario D** | **Official Evacuation Directives** | Prioritizes sovereign disaster authorities with tier-1 confidence weighting. |
| **Scenario E** | **Stale Emergency Messages** | Detects obsolete route reports superseded by newer police closure advisories. |
| **Scenario F** | **Full Multi-Source Pipeline (WOW Demo)** | Ingests 12 incoming alerts $\rightarrow$ clusters $\rightarrow$ filters $\rightarrow$ produces verified digest and checklist. |

---

## 🚀 Quickstart & Usage

### 1. Installation
```bash
git clone <repo-url>
cd "Neuro-Symbolic - Copy"
pip install -r requirements.txt
```

### 2. Run POC Simulation Suite
```bash
python poc_simulation.py
```

### 3. Run Pipeline via CLI
```bash
# Run pipeline on all alerts
python main.py run

# Verify single custom text or voice transcript
python main.py verify "Shelter A is closed and flooded" --source "WhatsApp Group"
```

### 4. Launch Government & Citizen Portal UI

- **Direct Open:** Simply double-click [`index.html`](file:///c:/Users/Vijayasai/Desktop/Neuro-Symbolic%20-%20Copy/index.html) in your browser.
- **Local HTTP Server:**
```bash
python -m http.server 8000
```
- **One-Click Interactive Launcher:**
```bash
python run_portal.py
```

---

## 📂 Project Structure

```text
neurosym-crisis/
│
├── index.html                          # Root entry point for Government & Citizen Portal
├── web/
│   ├── index.html                      # Standalone Government Control Room & Citizen Portal
│   ├── css/
│   │   └── styles.css                  # Modern Indian Government design system (Inter, Clean UI)
│   └── js/
│       └── app.js                      # Neuro-Symbolic Verification Engine & UI logic
│
├── data/
│   ├── alerts.json                     # 60+ Realistic disaster alerts across 6 scenarios
│   └── knowledge_base/                 # Sovereign disaster advisories & ground-truth data
│       ├── evacuation_guidelines.txt
│       ├── shelter_status.txt
│       ├── hospital_status.txt
│       ├── road_closure.txt
│       └── cyclone_advisory.txt
│
├── models/
│   ├── embeddings.py                   # Semantic text embeddings & cosine distance
│   └── llm_extractor.py                # Location, Action, Deadline, Claim extraction
│
├── pipeline/
│   ├── ingestion.py                    # Ingestion, cleaning, voice transcript parsing
│   ├── source_classifier.py            # Authority tiering & priority weights
│   ├── clustering.py                   # Semantic duplicate & event clustering
│   ├── extraction.py                   # Structured claim extraction stage
│   ├── retrieval.py                    # RAG evidence retrieval & stance scoring
│   ├── freshness.py                    # Temporal precedence & staleness analyzer
│   ├── verification.py                 # Pipeline neuro-symbolic orchestrator
│   └── digest.py                       # Emergency Digest & Shareable Checklist generator
│
├── reasoning/
│   ├── symbolic_rules.py               # Deterministic First-Order Logic rules
│   ├── verification_engine.py          # Neuro-symbolic verification with explainability
│   └── audit_logger.py                 # Audit trail logger (audit_log.json)
│
├── utils/
│   ├── schemas.py                      # Data models & schemas
│   └── metrics.py                      # Precision, Recall, F1, Noise reduction metrics
│
├── tests/
│   └── test_neuro_symbolic.py          # Automated test suite (all 7 layers)
│
├── poc_simulation.py                   # Benchmark runner for Scenarios A-F
├── audit_log.json                      # Real-time decision traces
├── run_portal.py                       # Interactive launcher script
├── main.py                             # Unified CLI tool
├── requirements.txt                    # Cleaned dependencies (numpy, pydantic, requests)
└── README.md                           # Documentation
```

---

## ⚖️ License
MIT License. Developed for T3.5 Emergency Information Intelligence.
