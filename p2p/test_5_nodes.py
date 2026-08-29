"""
NeuroSym Crisis — 5-Node Offline Multi-Hop P2P Simulation Benchmark.
Simulates end-to-end emergency message propagation across 5 physical devices:
Phone 1 (Government) -> Phone 2 (Relay A) -> Phone 3 (Relay B) -> Phone 4 (Relay C) -> Phone 5 (Citizen)
without internet or cellular connectivity.
"""

import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from p2p.protocol.message import P2PMessage
from p2p.security.crypto import P2PSecurityEngine
from p2p.bluetooth.relay_node import BLERelayNode


def run_5_phone_mesh_test():
    print("=" * 80)
    print("NEUROSYM CRISIS - 5-MOBILE OFFLINE STORE-AND-FORWARD P2P TEST")
    print("Environment: 100% Offline (Mobile Data: OFF | Wi-Fi: OFF | BLE: ACTIVE)")
    print("=" * 80)

    # 1. Initialize 5 Devices
    print("\n[Step 1] Initializing 5 Physical Mobile Nodes...")
    phone1_govt = BLERelayNode(node_id="PHONE_1_GOVT", role="GOVERNMENT_GATEWAY")
    phone2_relayA = BLERelayNode(node_id="PHONE_2_RELAY_A", role="RELAY_NODE")
    phone3_relayB = BLERelayNode(node_id="PHONE_3_RELAY_B", role="RELAY_NODE")
    phone4_relayC = BLERelayNode(node_id="PHONE_4_RELAY_C", role="RELAY_NODE")
    phone5_citizen = BLERelayNode(node_id="PHONE_5_CITIZEN", role="CITIZEN_DEVICE")

    # Set up physical topology (Linear multi-hop chain where Phone 1 cannot reach Phone 5 directly)
    phone1_govt.discover_peers(["PHONE_2_RELAY_A"])
    phone2_relayA.discover_peers(["PHONE_1_GOVT", "PHONE_3_RELAY_B"])
    phone3_relayB.discover_peers(["PHONE_2_RELAY_A", "PHONE_4_RELAY_C"])
    phone4_relayC.discover_peers(["PHONE_3_RELAY_B", "PHONE_5_CITIZEN"])
    phone5_citizen.discover_peers(["PHONE_4_RELAY_C"])

    print("   [OK] Phone 1 (Govt)     <---> Phone 2 (Relay A)")
    print("   [OK] Phone 2 (Relay A)  <---> Phone 3 (Relay B)")
    print("   [OK] Phone 3 (Relay B)  <---> Phone 4 (Relay C)")
    print("   [OK] Phone 4 (Relay C)  <---> Phone 5 (Citizen)")
    print("   * Note: Phone 1 and Phone 5 are out of direct radio range (Multi-hop relay required).")

    # 2. Government Creates and Digitally Signs Emergency Alert
    print("\n[Step 2] Government Control Room Generates & Digitally Signs Emergency Alert...")
    initial_alert = P2PMessage(
        id="NS-2026-001",
        type="EMERGENCY",
        priority="CRITICAL",
        issuer="GOVERNMENT_DDMA",
        ttl=5,
        hop_count=0,
        location="ZONE_A",
        message="CYCLONE & FLOOD WARNING: Zone A residents must evacuate before 6:00 PM via State Highway 44."
    )
    signed_alert = P2PSecurityEngine.sign_alert(initial_alert)
    phone1_govt.store.save_message(signed_alert)

    print(f"   Alert ID:    {signed_alert.id}")
    print(f"   Message:     \"{signed_alert.message}\"")
    print(f"   Signature:   {signed_alert.signature} (Cryptographically Signed)")
    print(f"   Initial TTL: {signed_alert.ttl} | Hops: {signed_alert.hop_count}")

    # 3. Hop-by-Hop Store-and-Forward Propagation
    print("\n[Step 3] Executing Hop-by-Hop BLE Store-and-Forward Propagation...")

    # HOP 1: Phone 1 -> Phone 2
    print("\n   --- HOP 1: Phone 1 (Govt) -> Phone 2 (Relay A) ---")
    success1, log1 = phone1_govt.forward_to_peer(signed_alert, phone2_relayA)
    print(f"   Status: {log1}")
    assert success1, "Hop 1 Failed!"

    # HOP 2: Phone 2 -> Phone 3
    print("\n   --- HOP 2: Phone 2 (Relay A) -> Phone 3 (Relay B) ---")
    msg_at_relayA = phone2_relayA.store.get_pending_relays()[0]
    success2, log2 = phone2_relayA.forward_to_peer(msg_at_relayA, phone3_relayB)
    print(f"   Status: {log2}")
    assert success2, "Hop 2 Failed!"

    # HOP 3: Phone 3 -> Phone 4
    print("\n   --- HOP 3: Phone 3 (Relay B) -> Phone 4 (Relay C) ---")
    msg_at_relayB = phone3_relayB.store.get_pending_relays()[0]
    success3, log3 = phone3_relayB.forward_to_peer(msg_at_relayB, phone4_relayC)
    print(f"   Status: {log3}")
    assert success3, "Hop 3 Failed!"

    # HOP 4: Phone 4 -> Phone 5 (Final Target Citizen)
    print("\n   --- HOP 4: Phone 4 (Relay C) -> Phone 5 (Citizen) ---")
    msg_at_relayC = phone4_relayC.store.get_pending_relays()[0]
    success4, log4 = phone4_relayC.forward_to_peer(msg_at_relayC, phone5_citizen)
    print(f"   Status: {log4}")
    assert success4, "Hop 4 Failed!"

    # 4. Verify Final Receipt on Citizen Device
    print("\n[Step 4] Verifying Final Receipt & Cryptographic Authenticity on Citizen Device...")
    citizen_messages = phone5_citizen.received_alerts
    assert len(citizen_messages) == 1, "Citizen device should have received exactly 1 alert"
    
    received = citizen_messages[0]
    print(f"   [CITIZEN SCREEN DISPLAY]:")
    print(f"      Security:    {received['auth_status']}")
    print(f"      Alert ID:    {received['msg_id']}")
    print(f"      Message:     \"{received['message']}\"")
    print(f"      Total Hops:  {received['hop_count']} hops taken")
    print(f"      Remaining:   TTL = {received['ttl']}")

    assert received["is_authentic"] is True, "Security validation failed!"
    assert received["hop_count"] == 4, "Hop count should be 4 after 4 intermediate transmissions"

    # 5. Anti-Looping & Deduplication Test
    print("\n[Step 5] Testing Mesh Deduplication & Loop Prevention...")
    print("   Attempting to re-transmit already received packet NS-2026-001 back to Phone 3...")
    duplicate_res, duplicate_log, _ = phone3_relayB.receive_packet(signed_alert.to_bytes(), from_node="ROGUE_OR_LOOP_NODE")
    print(f"   Result: {duplicate_log}")
    assert duplicate_res is False, "Deduplication failed: Duplicate message was not dropped!"
    print("   [PASS] Anti-looping verified: Message ID deduplication dropped duplicate packet immediately.")

    # 6. Anti-Tamper & Rogue Spoofing Test
    print("\n[Step 6] Testing Security Against Rogue Unverified Messages...")
    fake_alert = P2PMessage(
        id="FAKE-001",
        type="EMERGENCY",
        priority="CRITICAL",
        issuer="ANONYMOUS_BAD_ACTOR",
        message="Dam has exploded! Run to the mountains immediately!"
    )
    # Transmit unsigned fake alert to Citizen device
    fake_res, fake_log, _ = phone5_citizen.receive_packet(fake_alert.to_bytes(), from_node="ANON_PHONE")
    print(f"   Fake Alert Delivery Result: {fake_log}")
    citizen_fake_check = phone5_citizen.received_alerts[-1]
    print(f"   Citizen Security Label:     {citizen_fake_check['auth_status']}")
    assert citizen_fake_check["is_authentic"] is False, "Rogue message was incorrectly authenticated!"
    print("   [PASS] Spoofing protection verified: Non-government messages flagged as UNVERIFIED.")

    print("\n" + "=" * 80)
    print("ALL 5-NODE MULTI-HOP P2P TESTS PASSED SUCCESSFULLY!")
    print("Government -> Relay A -> Relay B -> Relay C -> Citizen Delivery: 100% VERIFIED")
    print("=" * 80)

if __name__ == "__main__":
    run_5_phone_mesh_test()
