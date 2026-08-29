package com.neurosym.p2p.bluetooth

import android.annotation.SuppressLint
import android.bluetooth.*
import android.content.Context
import android.os.Handler
import android.os.Looper
import android.util.Log
import com.neurosym.p2p.messaging.EmergencyMessage
import java.nio.charset.StandardCharsets

class GattClient(private val context: Context) {

    private val TAG = "NeuroSymGattClient"
    private val handler = Handler(Looper.getMainLooper())

    @SuppressLint("MissingPermission")
    fun sendMessageToPeer(
        deviceAddress: String,
        message: EmergencyMessage,
        bluetoothAdapter: BluetoothAdapter?,
        onResult: (Boolean, String) -> Unit
    ) {
        val device = bluetoothAdapter?.getRemoteDevice(deviceAddress)
        if (device == null) {
            onResult(false, "Device not found: $deviceAddress")
            return
        }

        var isComplete = false
        var gattInstance: BluetoothGatt? = null

        val timeoutRunnable = Runnable {
            if (!isComplete) {
                isComplete = true
                gattInstance?.disconnect()
                gattInstance?.close()
                onResult(false, "Connection timed out to $deviceAddress")
            }
        }
        handler.postDelayed(timeoutRunnable, 5000)

        val gattCallback = object : BluetoothGattCallback() {
            override fun onConnectionStateChange(gatt: BluetoothGatt?, status: Int, newState: Int) {
                if (newState == BluetoothProfile.STATE_CONNECTED) {
                    Log.i(TAG, "GATT Connected to $deviceAddress. Discovering services...")
                    gatt?.discoverServices()
                } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                    gatt?.close()
                }
            }

            override fun onServicesDiscovered(gatt: BluetoothGatt?, status: Int) {
                if (status == BluetoothGatt.GATT_SUCCESS) {
                    val service = gatt?.getService(BleConstants.SERVICE_UUID)
                    val characteristic = service?.getCharacteristic(BleConstants.CHARACTERISTIC_MESSAGE_UUID)

                    if (characteristic != null) {
                        val payload = message.toJson().toByteArray(StandardCharsets.UTF_8)
                        characteristic.value = payload
                        characteristic.writeType = BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT
                        val writeInitiated = gatt.writeCharacteristic(characteristic)
                        Log.d(TAG, "Write initiated: $writeInitiated for $deviceAddress")
                    } else {
                        finish(false, "Emergency Characteristic not found")
                    }
                } else {
                    finish(false, "Service discovery failed: $status")
                }
            }

            override fun onCharacteristicWrite(
                gatt: BluetoothGatt?,
                characteristic: BluetoothGattCharacteristic?,
                status: Int
            ) {
                if (status == BluetoothGatt.GATT_SUCCESS) {
                    Log.i(TAG, "Packet successfully written to $deviceAddress (ACK received).")
                    finish(true, "ACK received from $deviceAddress")
                } else {
                    finish(false, "Write failed with status $status")
                }
            }

            private fun finish(success: Boolean, reason: String) {
                if (!isComplete) {
                    isComplete = true
                    handler.removeCallbacks(timeoutRunnable)
                    gattInstance?.disconnect()
                    gattInstance?.close()
                    onResult(success, reason)
                }
            }
        }

        gattInstance = device.connectGatt(context, false, gattCallback, BluetoothDevice.TRANSPORT_LE)
    }
}
