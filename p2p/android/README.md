# 📱 NeuroSym Crisis — Offline P2P Android Mesh

This directory contains the native Android implementation for the **Store-and-Forward Offline Emergency Relay Node** using Bluetooth Low Energy (BLE).

---

## 🏗️ Architecture

```text
               GOVERNMENT CONTROL ROOM (PHONE 1)
                              │
                        BLE Advertising
                              ▼
                     RELAY NODE A (PHONE 2)
                              │
                        BLE Store & Forward
                              ▼
                     RELAY NODE B (PHONE 3)
                              │
                        BLE Store & Forward
                              ▼
                     RELAY NODE C (PHONE 4)
                              │
                        BLE Store & Forward
                              ▼
                   TARGET CITIZEN DEVICE (PHONE 5)
```

---

## 🔑 Key Features
1. **Zero Internet Requirement:** Uses BLE GATT server/client and periodic advertising packets.
2. **Deduplication Engine:** `message_id` tracking prevents infinite packet relay loops.
3. **Hop Count & TTL Decay:** Decrements TTL from 5 &rarr; 1, capping bandwidth and battery consumption.
4. **Sovereign Digital Signature Verification:** Verifies HMAC-SHA256 signature to guarantee only official government alerts show as `[AUTHENTICATED_GOVERNMENT_ALERT]`.

---

## 🧪 Simulation Test
To test the full 5-phone offline multi-hop relay on any terminal:
```powershell
python p2p/test_5_nodes.py
```
