package com.neurosym.p2p.bluetooth

import android.annotation.SuppressLint
import android.bluetooth.BluetoothAdapter
import android.bluetooth.le.BluetoothLeScanner
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanFilter
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.Context
import android.os.ParcelUuid
import android.util.Log
import java.nio.charset.StandardCharsets

class BleScanner(
    private val context: Context,
    private val bluetoothAdapter: BluetoothAdapter?
) {
    private val TAG = "NeuroSymScanner"
    private var scanner: BluetoothLeScanner? = null
    private var scanCallback: ScanCallback? = null

    @SuppressLint("MissingPermission")
    fun startScanning(onNodeFound: (DiscoveredNode) -> Unit) {
        scanner = bluetoothAdapter?.bluetoothLeScanner
        if (scanner == null) {
            Log.e(TAG, "BLE Scanner not available on this device.")
            return
        }

        val serviceUuid = ParcelUuid(BleConstants.SERVICE_UUID)
        val filter = ScanFilter.Builder()
            .setServiceUuid(serviceUuid)
            .build()

        val settings = ScanSettings.Builder()
            .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            .setReportDelay(0)
            .build()

        scanCallback = object : ScanCallback() {
            override fun onScanResult(callbackType: Int, result: ScanResult?) {
                super.onScanResult(callbackType, result)
                result?.let {
                    val record = it.scanRecord ?: return
                    val address = it.device.address
                    val rssi = it.rssi

                    // Extract Node ID from Service Data
                    val serviceData = record.getServiceData(serviceUuid)
                    val nodeId = if (serviceData != null && serviceData.isNotEmpty()) {
                        String(serviceData, StandardCharsets.UTF_8)
                    } else {
                        "NS-" + address.takeLast(4).replace(":", "").uppercase()
                    }

                    val node = DiscoveredNode(
                        nodeId = nodeId,
                        deviceAddress = address,
                        rssi = rssi,
                        role = "Citizen + Relay",
                        status = "ACTIVE",
                        lastSeen = System.currentTimeMillis()
                    )
                    onNodeFound(node)
                }
            }

            override fun onScanFailed(errorCode: Int) {
                super.onScanFailed(errorCode)
                Log.e(TAG, "BLE Scan failed with error: $errorCode")
            }
        }

        try {
            scanner?.startScan(listOf(filter), settings, scanCallback)
            Log.i(TAG, "BLE Scanning active for UUID: ${BleConstants.SERVICE_UUID}")
        } catch (e: SecurityException) {
            Log.e(TAG, "SecurityException while starting BLE scan: ${e.message}")
        }
    }

    @SuppressLint("MissingPermission")
    fun stopScanning() {
        if (scanCallback != null) {
            try {
                scanner?.stopScan(scanCallback)
            } catch (e: Exception) {
                Log.e(TAG, "Error stopping scan: ${e.message}")
            }
            scanCallback = null
        }
    }
}
