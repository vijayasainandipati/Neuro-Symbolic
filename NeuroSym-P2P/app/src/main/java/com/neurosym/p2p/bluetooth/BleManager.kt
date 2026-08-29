package com.neurosym.p2p.bluetooth

import android.Manifest
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.content.ContextCompat
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import java.util.UUID

data class DiscoveredNode(
    val nodeId: String,
    val deviceAddress: String,
    val rssi: Int,
    val role: String = "Citizen + Relay",
    val status: String = "ACTIVE",
    val lastSeen: Long = System.currentTimeMillis()
)

class BleManager(private val context: Context) {

    private val bluetoothManager: BluetoothManager? =
        context.getSystemService(Context.BLUETOOTH_SERVICE) as? BluetoothManager
    val bluetoothAdapter: BluetoothAdapter? = bluetoothManager?.adapter

    // Local Node ID generated once per device
    val localNodeId: String by lazy {
        val prefs = context.getSharedPreferences("neurosym_prefs", Context.MODE_PRIVATE)
        var id = prefs.getString("node_id", null)
        if (id == null) {
            id = "NS-" + UUID.randomUUID().toString().substring(0, 4).uppercase()
            prefs.edit().putString("node_id", id).apply()
        }
        id
    }

    private val _isBluetoothEnabled = MutableStateFlow(bluetoothAdapter?.isEnabled == true)
    val isBluetoothEnabled: StateFlow<Boolean> = _isBluetoothEnabled

    private val _isAdvertising = MutableStateFlow(false)
    val isAdvertising: StateFlow<Boolean> = _isAdvertising

    private val _isScanning = MutableStateFlow(false)
    val isScanning: StateFlow<Boolean> = _isScanning

    private val _discoveredNodes = MutableStateFlow<List<DiscoveredNode>>(emptyList())
    val discoveredNodes: StateFlow<List<DiscoveredNode>> = _discoveredNodes

    val advertiser = BleAdvertiser(context, bluetoothAdapter, localNodeId)
    val scanner = BleScanner(context, bluetoothAdapter)

    fun hasRequiredPermissions(): Boolean {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val scan = ContextCompat.checkSelfPermission(context, Manifest.permission.BLUETOOTH_SCAN) == PackageManager.PERMISSION_GRANTED
            val adv = ContextCompat.checkSelfPermission(context, Manifest.permission.BLUETOOTH_ADVERTISE) == PackageManager.PERMISSION_GRANTED
            val conn = ContextCompat.checkSelfPermission(context, Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED
            return scan && adv && conn
        } else {
            val loc = ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
            return loc
        }
    }

    fun startMeshOperations() {
        if (!hasRequiredPermissions() || bluetoothAdapter?.isEnabled != true) return

        advertiser.startAdvertising { success ->
            _isAdvertising.value = success
        }

        scanner.startScanning { node ->
            val current = _discoveredNodes.value.toMutableList()
            val existingIdx = current.indexOfFirst { it.nodeId == node.nodeId || it.deviceAddress == node.deviceAddress }
            if (existingIdx >= 0) {
                current[existingIdx] = node
            } else {
                current.add(node)
            }
            _discoveredNodes.value = current
        }
        _isScanning.value = true
    }

    fun stopMeshOperations() {
        advertiser.stopAdvertising()
        scanner.stopScanning()
        _isAdvertising.value = false
        _isScanning.value = false
    }
}
