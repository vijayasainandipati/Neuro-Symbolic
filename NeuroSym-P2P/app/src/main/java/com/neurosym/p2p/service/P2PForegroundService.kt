package com.neurosym.p2p.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.neurosym.p2p.ble.P2PBluetoothEngine
import com.neurosym.p2p.notification.EmergencyNotificationManager

class P2PForegroundService : Service() {

    private lateinit var bleEngine: P2PBluetoothEngine
    private lateinit var notificationManager: EmergencyNotificationManager
    private val FOREGROUND_CHANNEL_ID = "neurosym_p2p_service"

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        
        notificationManager = EmergencyNotificationManager(this)
        bleEngine = P2PBluetoothEngine(this) { message ->
            notificationManager.dispatchSystemAlert(message)
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val notification = createForegroundNotification()
        startForeground(1, notification)
        
        bleEngine.startEngine()
        
        return START_STICKY
    }

    override fun onDestroy() {
        super.onDestroy()
        bleEngine.stopEngine()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun createForegroundNotification(): Notification {
        return NotificationCompat.Builder(this, FOREGROUND_CHANNEL_ID)
            .setContentTitle("NeuroSym P2P Mesh Active")
            .setContentText("Listening for critical emergency broadcasts...")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                FOREGROUND_CHANNEL_ID,
                "P2P Service",
                NotificationManager.IMPORTANCE_LOW
            )
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            manager.createNotificationChannel(channel)
        }
    }
}
