"""
Bluetooth Low Energy (BLE) Store-and-Forward Relay Node Engine.
Implements neighbor discovery, local message verification, store-and-forward relay state machine,
and hop-by-hop message routing for offline environments.
"""

from typing import List, Dict, Any, Optional, Tuple
from p2p.protocol.message import P2PMessage
from p2p.security.crypto import P2PSecurityEngine
from p2p.storage.store import LocalMeshStore


class BLERelayNode:
    def __init__(self, node_id: str, role: str = "RELAY_NODE", db_path: str = ":memory:"):
        self.node_id = node_id
        self.role = role  # GOVERNMENT_GATEWAY, RELAY_NODE, CITIZEN_DEVICE
        self.store = LocalMeshStore(db_path=db_path)
        self.nearby_peers: List[str] = []
        self.received_alerts: List[Dict[str, Any]] = []

    def discover_peers(self, peers: List[str]):
        """Simulates BLE advertisement scan discovering nearby active nodes."""
        self.nearby_peers = [p for p in peers if p != self.node_id]

    def receive_packet(self, raw_bytes: bytes, from_node: str) -> Tuple[bool, str, Optional[P2PMessage]]:
        """
        Receives a raw BLE packet:
        1. Deserializes message
        2. Checks deduplication (Already received? YES -> DROP, NO -> Process)
        3. Verifies cryptographic signature (Authentic vs Unverified)
        4. Stores in local offline database
        5. Displays / buffers for relay if TTL > 0
        """
        try:
            msg = P2PMessage.from_bytes(raw_bytes)
        except Exception as e:
            return False, f"MALFORMED_PACKET: {e}", None

        # 1. Deduplication check
        if self.store.has_seen(msg.id):
            return False, f"DUPLICATE_DROPPED (ID: {msg.id})", None

        # 2. Cryptographic Authenticity Verification
        is_authentic, auth_status = P2PSecurityEngine.verify_alert(msg)

        # 3. Store locally in SQLite database
        self.store.save_message(msg)

        # 4. Record in received alerts cache
        alert_record = {
            "msg_id": msg.id,
            "from_node": from_node,
            "message": msg.message,
            "location": msg.location,
            "priority": msg.priority,
            "hop_count": msg.hop_count,
            "ttl": msg.ttl,
            "is_authentic": is_authentic,
            "auth_status": auth_status
        }
        self.received_alerts.append(alert_record)

        return True, f"ACCEPTED ({auth_status})", msg

    def forward_to_peer(self, msg: P2PMessage, target_peer: "BLERelayNode") -> Tuple[bool, str]:
        """Transfers store-and-forward packet to next BLE neighbor."""
        relay_packet = msg.prepare_for_relay()
        if not relay_packet:
            return False, f"TTL_EXPIRED (TTL was {msg.ttl})"

        raw_bytes = relay_packet.to_bytes()
        accepted, status, received_msg = target_peer.receive_packet(raw_bytes, from_node=self.node_id)
        if accepted:
            self.store.log_relay(msg.id, target_peer.node_id)
            return True, f"RELAY_SUCCESS -> {target_peer.node_id} ({status})"
        else:
            return False, f"RELAY_REJECTED by {target_peer.node_id} ({status})"

    def broadcast_to_nearby(self, target_nodes: List["BLERelayNode"]) -> List[Tuple[str, bool, str]]:
        """Broadcasts all pending messages with TTL > 0 to all connected nearby nodes."""
        results = []
        pending = self.store.get_pending_relays()
        for msg in pending:
            for peer in target_nodes:
                if peer.node_id in self.nearby_peers:
                    success, log_msg = self.forward_to_peer(msg, peer)
                    results.append((peer.node_id, success, log_msg))
        return results
