package com.neurosym.p2p.bluetooth

import android.annotation.SuppressLint
import android.bluetooth.BluetoothAdapter
import android.bluetooth.le.AdvertiseCallback
import android.bluetooth.le.AdvertiseData
import android.bluetooth.le.AdvertiseSettings
import android.bluetooth.le.BluetoothLeAdvertiser
import android.content.Context
import android.os.ParcelUuid
import android.util.Log
import java.nio.charset.StandardCharsets

class BleAdvertiser(
    private val context: Context,
    private val bluetoothAdapter: BluetoothAdapter?,
    private val localNodeId: String
) {
    private val TAG = "NeuroSymAdvertiser"
    private var advertiser: BluetoothLeAdvertiser? = null
    private var advertiseCallback: AdvertiseCallback? = null

    @SuppressLint("MissingPermission")
    fun startAdvertising(onStatusChanged: (Boolean) -> Unit) {
        advertiser = bluetoothAdapter?.bluetoothLeAdvertiser
        if (advertiser == null) {
            Log.e(TAG, "BLE Advertiser not supported on this hardware.")
            onStatusChanged(false)
            return
        }

        val settings = AdvertiseSettings.Builder()
            .setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY)
            .setTxPowerLevel(AdvertiseSettings.ADVERTISE_TX_POWER_HIGH)
            .setConnectable(true)
            .setTimeout(0)
            .build()

        val serviceUuid = ParcelUuid(BleConstants.SERVICE_UUID)
        val nodePayload = localNodeId.toByteArray(StandardCharsets.UTF_8)

        val data = AdvertiseData.Builder()
            .setIncludeDeviceName(false)
            .addServiceUuid(serviceUuid)
            .addServiceData(serviceUuid, nodePayload)
            .build()

        advertiseCallback = object : AdvertiseCallback() {
            override fun onStartSuccess(settingsInEffect: AdvertiseSettings?) {
                super.onStartSuccess(settingsInEffect)
                Log.i(TAG, "BLE Advertising started for Node: $localNodeId")
                onStatusChanged(true)
            }

            override fun onStartFailure(errorCode: Int) {
                super.onStartFailure(errorCode)
                Log.e(TAG, "BLE Advertising failed with error code: $errorCode")
                onStatusChanged(false)
            }
        }

        try {
            advertiser?.startAdvertising(settings, data, advertiseCallback)
        } catch (e: SecurityException) {
            Log.e(TAG, "SecurityException while starting BLE advertising: ${e.message}")
            onStatusChanged(false)
        }
    }

    @SuppressLint("MissingPermission")
    fun stopAdvertising() {
        if (advertiseCallback != null) {
            try {
                advertiser?.stopAdvertising(advertiseCallback)
            } catch (e: Exception) {
                Log.e(TAG, "Error stopping advertising: ${e.message}")
            }
            advertiseCallback = null
        }
    }
}
