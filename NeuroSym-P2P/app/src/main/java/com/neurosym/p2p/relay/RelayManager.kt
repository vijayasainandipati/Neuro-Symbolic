package com.neurosym.p2p.relay

import android.bluetooth.BluetoothAdapter
import android.content.Context
import android.util.Log
import com.neurosym.p2p.bluetooth.BleManager
import com.neurosym.p2p.bluetooth.DiscoveredNode
import com.neurosym.p2p.bluetooth.GattClient
import com.neurosym.p2p.messaging.EmergencyMessage
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.util.Collections
import java.util.concurrent.ConcurrentHashMap

class RelayManager(
    private val context: Context,
    private val bleManager: BleManager
) {
    private val TAG = "NeuroSymRelayManager"
    private val gattClient = GattClient(context)
    private val scope = CoroutineScope(Dispatchers.IO)

    // Algorithm 5: Message Deduplication cache
    private val seenMessageIds = Collections.synchronizedSet(HashSet<String>())
    
    // Store received messages locally
    val storedMessages = ConcurrentHashMap<String, EmergencyMessage>()

    fun onMessageReceived(
        message: EmergencyMessage,
        fromAddress: String,
        onNotificationNeeded: (EmergencyMessage) -> Unit
    ) {
        // Algorithm 5: Duplicate check
        if (seenMessageIds.contains(message.messageId)) {
            Log.d(TAG, "Duplicate message dropped: ${message.messageId}")
            return
        }

        seenMessageIds.add(message.messageId)
        storedMessages[message.messageId] = message
        Log.i(TAG, "Stored emergency alert ${message.messageId} locally.")

        // Show local Android system notification
        onNotificationNeeded(message)

        // Algorithm 6: TTL check & Store-and-Forward relaying
        if (message.ttl > 1) {
            val relayPacket = message.prepareForRelay()
            if (relayPacket != null) {
                scope.launch {
                    attemptRelay(relayPacket, excludeAddress = fromAddress)
                }
            }
        } else {
            Log.i(TAG, "Message ${message.messageId} TTL exhausted (TTL: ${message.ttl}). Stopping relay.")
        }
    }

    private fun attemptRelay(packet: EmergencyMessage, excludeAddress: String) {
        // Algorithm 2: Select best candidate based on RSSI
        val candidate = selectBestRelayNode(excludeAddress)
        if (candidate == null) {
            Log.w(TAG, "No candidate peer available right now for store-and-forward. Retaining in local storage.")
            return
        }

        Log.i(TAG, "Forwarding packet ${packet.messageId} to best relay candidate: ${candidate.nodeId} (${candidate.rssi} dBm)")

        gattClient.sendMessageToPeer(
            deviceAddress = candidate.deviceAddress,
            message = packet,
            bluetoothAdapter = bleManager.bluetoothAdapter
        ) { success, log ->
            if (success) {
                Log.i(TAG, "Relay successful -> ${candidate.nodeId}: $log")
            } else {
                Log.w(TAG, "Relay attempt failed -> ${candidate.nodeId}: $log. Will retry when next node is scanned.")
            }
        }
    }

    private fun selectBestRelayNode(excludeAddress: String): DiscoveredNode? {
        val now = System.currentTimeMillis()
        return bleManager.discoveredNodes.value
            .filter { it.deviceAddress != excludeAddress && (now - it.lastSeen) < 15000 }
            .maxByOrNull { it.rssi } // Strongest RSSI
    }
}
