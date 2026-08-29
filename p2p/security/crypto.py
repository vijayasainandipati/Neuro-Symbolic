"""
Cryptographic Security & Digital Signature Engine for P2P Emergency Alerts.
Allows Government Control Rooms to digitally sign alerts so citizen devices can verify authenticity
without internet connectivity, preventing spoofing or malicious panic injection.
"""

import hmac
import hashlib
import json
from typing import Tuple
from p2p.protocol.message import P2PMessage

# Sovereign Root Signing Key (For demo/prototype, hardcoded root secret; in production: Ed25519 private key)
GOVERNMENT_SOVEREIGN_SECRET = b"NEUROSYM_SOVEREIGN_GOVT_KEY_KANYAKUMARI_DDMA_2026"
SOVEREIGN_ISSUER_TAG = "GOVERNMENT_DDMA"


class P2PSecurityEngine:
    @staticmethod
    def _compute_payload_hash(msg: P2PMessage) -> bytes:
        """Constructs canonical payload bytes for signing (excluding mutable relay fields)."""
        canonical_data = {
            "id": msg.id,
            "type": msg.type,
            "priority": msg.priority,
            "issuer": msg.issuer,
            "timestamp": msg.timestamp,
            "location": msg.location,
            "message": msg.message
        }
        canonical_str = json.dumps(canonical_data, sort_keys=True, separators=(',', ':'))
        return canonical_str.encode('utf-8')

    @classmethod
    def sign_alert(cls, msg: P2PMessage, secret_key: bytes = GOVERNMENT_SOVEREIGN_SECRET) -> P2PMessage:
        """Signs an official emergency message using the Sovereign Government key."""
        payload_bytes = cls._compute_payload_hash(msg)
        sig = hmac.new(secret_key, payload_bytes, hashlib.sha256).hexdigest()
        msg.signature = f"SIG_DDMA_{sig[:32]}"
        return msg

    @classmethod
    def verify_alert(cls, msg: P2PMessage, secret_key: bytes = GOVERNMENT_SOVEREIGN_SECRET) -> Tuple[bool, str]:
        """
        Verifies if an alert was signed by the official government authority.
        Returns (is_authentic, verification_status_label).
        """
        if not msg.signature or not msg.signature.startswith("SIG_DDMA_"):
            return False, "[UNVERIFIED_COMMUNITY_CLAIM]"

        sig_val = msg.signature.replace("SIG_DDMA_", "")
        payload_bytes = cls._compute_payload_hash(msg)
        expected_sig = hmac.new(secret_key, payload_bytes, hashlib.sha256).hexdigest()[:32]

        if hmac.compare_digest(sig_val, expected_sig):
            return True, "[AUTHENTICATED_GOVERNMENT_ALERT]"
        else:
            return False, "[FORGED_OR_TAMPERED_ALERT]"
