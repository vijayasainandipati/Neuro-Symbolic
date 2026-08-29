package com.neurosym.p2p.bluetooth

import java.util.UUID

object BleConstants {
    // Standard NeuroSym Fixed BLE Service UUID
    val SERVICE_UUID: UUID = UUID.fromString("7f3a0001-8b2c-4e91-a4c7-123456789abc")
    
    // Emergency Message Transfer Characteristic UUID
    val CHARACTERISTIC_MESSAGE_UUID: UUID = UUID.fromString("7f3a0002-8b2c-4e91-a4c7-123456789abc")
    
    // ACK Confirmation Characteristic UUID
    val CHARACTERISTIC_ACK_UUID: UUID = UUID.fromString("7f3a0003-8b2c-4e91-a4c7-123456789abc")

    const val MAX_RETRIES = 3
    const val ACK_TIMEOUT_MS = 2000L
}
