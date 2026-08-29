package org.neurosym.crisis.mesh

import android.app.Service
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager
import android.bluetooth.le.*
import android.content.Context
import android.content.Intent
import android.os.IBinder
import android.os.ParcelUuid
import android.util.Log
import java.nio.charset.StandardCharsets
import java.util.*

/**
 * Android Foreground Service managing Offline BLE Mesh Discovery,
 * Packet Serialization, and Store-and-Forward Relaying.
 */
class EmergencyMeshService : Service() {

    private val TAG = "NeuroSymMeshService"
    private val MESH_SERVICE_UUID = UUID.fromString("0000FEAA-0000-1000-8000-00805F9B34FB")

    private lateinit var bluetoothManager: BluetoothManager
    private var bluetoothAdapter: BluetoothAdapter? = null
    private var bleAdvertiser: BluetoothLeAdvertiser? = null
    private var bleScanner: BluetoothLeScanner? = null

    private val seenMessageIds = Collections.synchronizedSet(HashSet<String>())

    override fun onCreate() {
        super.onCreate()
        bluetoothManager = getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
        bluetoothAdapter = bluetoothManager.adapter
        bleAdvertiser = bluetoothAdapter?.bluetoothLeAdvertiser
        bleScanner = bluetoothAdapter?.bluetoothLeScanner
        startMeshBroadcast()
        startMeshScanning()
    }

    private fun startMeshBroadcast() {
        val settings = AdvertiseSettings.Builder()
            .setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY)
            .setTxPowerLevel(AdvertiseSettings.ADVERTISE_TX_POWER_HIGH)
            .setConnectable(true)
            .build()

        val data = AdvertiseData.Builder()
            .setIncludeDeviceName(false)
            .addServiceUuid(ParcelUuid(MESH_SERVICE_UUID))
            .build()

        bleAdvertiser?.startAdvertising(settings, data, object : AdvertiseCallback() {
            override fun onStartSuccess(settingsInEffect: AdvertiseSettings) {
                Log.d(TAG, "BLE Mesh Advertising active.")
            }
            override fun onStartFailure(errorCode: Int) {
                Log.e(TAG, "BLE Mesh Advertising failed with code $errorCode")
            }
        })
    }

    private fun startMeshScanning() {
        val filter = ScanFilter.Builder()
            .setServiceUuid(ParcelUuid(MESH_SERVICE_UUID))
            .build()

        val scanSettings = ScanSettings.Builder()
            .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            .build()

        bleScanner?.startScan(listOf(filter), scanSettings, object : ScanCallback() {
            override fun onScanResult(callbackType: Int, result: ScanResult) {
                Log.d(TAG, "Discovered Mesh Node: ${result.device.address}")
            }
        })
    }

    fun handleIncomingPayload(rawJson: String): Boolean {
        try {
            // Deduplication logic: Check if message ID already processed
            val msgId = rawJson.substringAfter("\"id\":\"").substringBefore("\"")
            if (seenMessageIds.contains(msgId)) {
                Log.d(TAG, "Duplicate message dropped: $msgId")
                return false
            }
            seenMessageIds.add(msgId)
            Log.d(TAG, "New Emergency Packet Stored & Buffered: $rawJson")
            return true
        } catch (e: Exception) {
            Log.e(TAG, "Error handling payload: $e")
            return false
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
