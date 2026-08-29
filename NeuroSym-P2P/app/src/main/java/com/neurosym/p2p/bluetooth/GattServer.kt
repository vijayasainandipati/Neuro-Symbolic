package com.neurosym.p2p.bluetooth

import android.annotation.SuppressLint
import android.bluetooth.*
import android.content.Context
import android.util.Log
import com.neurosym.p2p.messaging.EmergencyMessage
import java.nio.charset.StandardCharsets

class GattServer(
    private val context: Context,
    private val bluetoothManager: BluetoothManager?,
    private val onMessageReceived: (EmergencyMessage, BluetoothDevice) -> Unit
) {
    private val TAG = "NeuroSymGattServer"
    private var gattServer: BluetoothGattServer? = null

    @SuppressLint("MissingPermission")
    fun startServer() {
        if (bluetoothManager == null) return

        val callback = object : BluetoothGattServerCallback() {
            override fun onConnectionStateChange(device: BluetoothDevice?, status: Int, newState: Int) {
                super.onConnectionStateChange(device, status, newState)
                Log.d(TAG, "GATT Server Connection state: $newState for device ${device?.address}")
            }

            override fun onCharacteristicWriteRequest(
                device: BluetoothDevice?,
                requestId: Int,
                characteristic: BluetoothGattCharacteristic?,
                preparedWrite: Boolean,
                responseNeeded: Boolean,
                offset: Int,
                value: ByteArray?
            ) {
                super.onCharacteristicWriteRequest(device, requestId, characteristic, preparedWrite, responseNeeded, offset, value)

                if (characteristic?.uuid == BleConstants.CHARACTERISTIC_MESSAGE_UUID && value != null) {
                    val rawJson = String(value, StandardCharsets.UTF_8)
                    Log.i(TAG, "Received message payload over GATT: $rawJson")

                    try {
                        val message = EmergencyMessage.fromJson(rawJson)
                        device?.let { onMessageReceived(message, it) }

                        if (responseNeeded) {
                            gattServer?.sendResponse(device, requestId, BluetoothGatt.GATT_SUCCESS, offset, "ACK".toByteArray())
                        }
                    } catch (e: Exception) {
                        Log.e(TAG, "Error parsing incoming GATT message: ${e.message}")
                        if (responseNeeded) {
                            gattServer?.sendResponse(device, requestId, BluetoothGatt.GATT_FAILURE, offset, null)
                        }
                    }
                }
            }
        }

        gattServer = bluetoothManager.openGattServer(context, callback)

        val service = BluetoothGattService(BleConstants.SERVICE_UUID, BluetoothGattService.SERVICE_TYPE_PRIMARY)
        val charMessage = BluetoothGattCharacteristic(
            BleConstants.CHARACTERISTIC_MESSAGE_UUID,
            BluetoothGattCharacteristic.PROPERTY_WRITE or BluetoothGattCharacteristic.PROPERTY_READ,
            BluetoothGattCharacteristic.PERMISSION_WRITE or BluetoothGattCharacteristic.PERMISSION_READ
        )
        val charAck = BluetoothGattCharacteristic(
            BleConstants.CHARACTERISTIC_ACK_UUID,
            BluetoothGattCharacteristic.PROPERTY_READ or BluetoothGattCharacteristic.PROPERTY_NOTIFY,
            BluetoothGattCharacteristic.PERMISSION_READ
        )

        service.addCharacteristic(charMessage)
        service.addCharacteristic(charAck)
        gattServer?.addService(service)
        Log.i(TAG, "GATT Server initialized and listening for emergency transmissions.")
    }

    @SuppressLint("MissingPermission")
    fun stopServer() {
        gattServer?.close()
        gattServer = null
    }
}
