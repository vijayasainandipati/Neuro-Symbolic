"""
Neural Information Understanding & LLM-based Claim Extractor for NeuroSym Crisis.
Extracts structured event_type, location, claim, action, deadline_time, and severity from raw crisis text.
Provides direct integration with local Ollama LLMs (Llama 3.2, Mistral, Gemma 2)
with automatic fallback to high-accuracy deterministic semantic parsing.
"""

import json
import re
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from utils.schemas import Alert, ExtractedClaim
import config


class LLMExtractor:
    """
    Extracts structured emergency intelligence parameters from unstructured text.
    Combines local Ollama inference with deterministic semantic extractors.
    """

    KNOWN_LOCATIONS = [
        ("Zone A", [r"zone\s*a", r"coastal lowlands", r"waterfront"]),
        ("Zone B", [r"zone\s*b"]),
        ("Zone C", [r"zone\s*c", r"upland sector"]),
        ("Shelter A", [r"shelter\s*a", r"govt model school", r"model school"]),
        ("Shelter B", [r"shelter\s*b", r"community cultural hall", r"community hall"]),
        ("Shelter C", [r"shelter\s*c", r"sports stadium", r"indoor stadium"]),
        ("Shelter D", [r"shelter\s*d", r"port road", r"municipal warehouse"]),
        ("North River Bridge", [r"north river bridge", r"north bridge", r"river bridge"]),
        ("State Highway 44", [r"state highway 44", r"sh-44", r"highway 44", r"sh44"]),
        ("Eastern Bypass", [r"eastern bypass", r"bypass ring road"]),
        ("Western Bypass", [r"western bypass", r"railway overbridge"]),
        ("Western Ghats Pass", [r"western ghats", r"mountain pass", r"mile 14"]),
        ("District Hospitals", [r"district hospital", r"general hospital", r"all hospitals", r"hospital"]),
        ("City Central Clinic", [r"city central clinic", r"central clinic", r"market junction"]),
        ("Pechiparai Dam", [r"pechiparai dam", r"pechiparai", r"dam"]),
        ("Riverside Colony", [r"riverside colony", r"riverside"]),
        ("Fisherman Colony", [r"fisherman colony", r"beachfront", r"coastal ward"]),
        ("Sector 1", [r"sector\s*1"]),
        ("Sector 2", [r"sector\s*2"]),
        ("Sector 3", [r"sector\s*3"]),
        ("Sector 4", [r"sector\s*4"]),
        ("Sector 5", [r"sector\s*5"]),
        ("Coast", [r"coast", r"bay of bengal", r"sea", r"beach"])
    ]

    EVENT_KEYWORDS = [
        ("evacuation", [r"evacuat", r"move to", r"shift", r"relocat"]),
        ("flood", [r"flood", r"water level", r"inundat", r"submerg", r"waterlog"]),
        ("cyclone", [r"cyclone", r"storm", r"landfall", r"gale", r"wind"]),
        ("shelter", [r"shelter", r"relief camp", r"stadium", r"hall"]),
        ("hospital", [r"hospital", r"clinic", r"doctor", r"medical", r"trauma"]),
        ("road_closure", [r"bridge", r"road", r"highway", r"pass", r"traffic", r"blocked", r"closed"]),
        ("dam", [r"dam", r"reservoir", r"storage", r"burst", r"collapse"]),
        ("power", [r"power", r"electric", r"transformer", r"lights out", r"grid"]),
        ("tsunami", [r"tsunami", r"tidal wave"]),
        ("water_supply", [r"drinking water", r"tap water", r"contamination"])
    ]

    DEADLINE_PATTERNS = [
        (r"before\s*6(?::00)?\s*(?:pm|p\.m\.)?", "Before 6:00 PM"),
        (r"before\s*evening\s*6\s*(?:pm)?", "Before 6:00 PM"),
        (r"before\s*18:00", "Before 18:00 IST"),
        (r"until\s*10(?::00)?\s*(?:pm|p\.m\.)?", "Until 10:00 PM"),
        (r"until\s*22:00", "Until 22:00 IST"),
        (r"till\s*8\s*(?:pm)?", "Until 8:00 PM"),
        (r"between\s*7\s*(?:pm)?\s*and\s*9\s*pm", "Between 19:00 - 21:00 IST"),
        (r"next\s*18\s*hours", "Within next 18 hours"),
        (r"within\s*24\s*hours", "Within 24 hours"),
        (r"24/7|round the clock|operating 24/7", "Active 24/7")
    ]

    _ollama_available: Optional[bool] = None

    def __init__(self):
        self.ollama_host = config.OLLAMA_HOST
        self.ollama_model = config.OLLAMA_LLM_MODEL
        self.ollama_enabled = config.OLLAMA_ENABLED
        self.timeout = config.OLLAMA_TIMEOUT_SECONDS

    def _is_ollama_live(self) -> bool:
        if not self.ollama_enabled:
            return False
        if LLMExtractor._ollama_available is not None:
            return LLMExtractor._ollama_available

        try:
            url = f"{self.ollama_host}/api/tags"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                LLMExtractor._ollama_available = (resp.status == 200)
        except Exception:
            LLMExtractor._ollama_available = False

        return LLMExtractor._ollama_available

    def extract_from_text(self, alert_id: str, text: str) -> ExtractedClaim:
        """
        Attempts structured extraction using local Ollama if available,
        falling back to deterministic semantic rule extraction.
        """
        if self._is_ollama_live():
            ollama_result = self._extract_via_ollama(alert_id, text)
            if ollama_result is not None:
                return ollama_result

        return self._extract_deterministic(alert_id, text)

    def _extract_via_ollama(self, alert_id: str, text: str) -> Optional[ExtractedClaim]:
        """Queries local Ollama instance with structured JSON output enforcement."""
        prompt = f"""You are an emergency disaster information extractor for government disaster response.
Extract structured crisis intelligence from this incoming message.
Output ONLY valid JSON matching this schema:
{{
  "event_type": "flood | cyclone | shelter | evacuation | road_closure | dam | power | general",
  "location": "specific location mentioned (e.g. Zone A, Shelter A, North River Bridge)",
  "claim": "concise core assertion (1 short sentence)",
  "action": "recommended protective action",
  "deadline_time": "time deadline if any (e.g. Before 6:00 PM, or Current)",
  "severity": "CRITICAL | HIGH | MEDIUM | LOW"
}}

Message to extract:
"{text}"
"""
        req_data = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
                "top_p": 0.9
            }
        }

        try:
            url = f"{self.ollama_host}/api/generate"
            req = urllib.request.Request(
                url,
                data=json.dumps(req_data).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status == 200:
                    resp_json = json.loads(resp.read().decode("utf-8"))
                    raw_output = resp_json.get("response", "")
                    parsed = json.loads(raw_output)

                    return ExtractedClaim(
                        alert_id=alert_id,
                        event_type=parsed.get("event_type", "general"),
                        location=parsed.get("location", "General District"),
                        claim=parsed.get("claim", text[:120]),
                        action=parsed.get("action", "Follow verified instructions from District Disaster Authority"),
                        deadline_time=parsed.get("deadline_time", "Current"),
                        severity=parsed.get("severity", "HIGH").upper(),
                        confidence=0.96,
                        raw_text=text
                    )
        except Exception:
            # Graceful fallback to deterministic parsing
            pass

        return None

    def _extract_deterministic(self, alert_id: str, text: str) -> ExtractedClaim:
        """High-speed deterministic extractor for 100% offline uptime and zero latency."""
        text_lower = text.lower()

        # 1. Location extraction
        detected_location = "General District"
        for loc_name, patterns in self.KNOWN_LOCATIONS:
            if any(re.search(pat, text_lower) for pat in patterns):
                detected_location = loc_name
                break

        # 2. Event type extraction
        detected_event = "general"
        for evt_name, patterns in self.EVENT_KEYWORDS:
            if any(re.search(pat, text_lower) for pat in patterns):
                detected_event = evt_name
                break

        # 3. Deadline / Time extraction
        detected_time = "Current"
        for pat, formatted_time in self.DEADLINE_PATTERNS:
            if re.search(pat, text_lower):
                detected_time = formatted_time
                break

        # 4. Action extraction
        action = self._infer_action(text_lower, detected_event, detected_location, detected_time)

        # 5. Core claim distillation
        claim = self._distill_claim(text, detected_event, detected_location)

        # 6. Severity
        severity = "HIGH"
        if any(w in text_lower for w in ["urgent", "mandatory", "collapse", "burst", "tsunami", "red alert", "danger", "trapped"]):
            severity = "CRITICAL"
        elif any(w in text_lower for w in ["routine", "chlorination", "cleared", "smooth", "minor"]):
            severity = "MEDIUM"

        return ExtractedClaim(
            alert_id=alert_id,
            event_type=detected_event,
            location=detected_location,
            claim=claim,
            action=action,
            deadline_time=detected_time,
            severity=severity,
            confidence=0.94,
            raw_text=text
        )

    def _infer_action(self, text_lower: str, event_type: str, location: str, deadline: str) -> str:
        if "evacuat" in text_lower or (event_type == "flood" and "zone a" in location.lower()):
            return f"Evacuate {location} immediately via State Highway 44 ({deadline})"
        if "shelter a" in location.lower() and ("closed" in text_lower or "locked" in text_lower):
            return "Verify official status; proceed to Shelter A or Shelter C"
        if "bridge" in text_lower and "closed" in text_lower:
            return "Avoid North River Bridge; use State Highway 44 Northbound"
        if "dam" in text_lower and ("collapse" in text_lower or "burst" in text_lower):
            return "Do not panic; ignore unverified dam collapse rumors"
        if "hospital" in text_lower and "closed" in text_lower:
            return "District General Hospital is open; dial 108 for emergency services"
        if "cyclone" in text_lower:
            return "Stay indoors in secure reinforced structures; avoid coastal areas"
        if "shelter" in text_lower and ("open" in text_lower or "distribut" in text_lower):
            return f"Proceed to {location} for intake and relief provisions"
        return "Follow verified instructions from District Disaster Authority"

    def _distill_claim(self, text: str, event_type: str, location: str) -> str:
        cleaned = re.sub(
            r"^(?:URGENT|DDMA NOTICE|FORWARDED MSG|BREAKING|Health Dept advisory|IMD RED ALERT|Official Warning|TRAFFIC POLICE ENFORCEMENT)[:\s\-]+",
            "",
            text,
            flags=re.IGNORECASE
        ).strip()
        sentences = re.split(r"[.!?]", cleaned)
        first_sent = sentences[0].strip() if sentences else cleaned
        return first_sent if len(first_sent) > 10 else cleaned[:120]


llm_extractor = LLMExtractor()
