package com.neurosym.p2p.notification

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.media.RingtoneManager
import android.os.Build
import androidx.core.app.NotificationCompat
import com.neurosym.p2p.MainActivity
import com.neurosym.p2p.messaging.EmergencyMessage

class EmergencyNotificationManager(private val context: Context) {
    private val CHANNEL_ID = "neurosym_emergency_alerts"
    private val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

    init {
        createNotificationChannel()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Emergency P2P Alerts",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Critical offline disaster alerts relayed via NeuroSym BLE mesh."
                enableVibration(true)
                vibrationPattern = longArrayOf(0, 500, 200, 500, 200, 1000)
            }
            notificationManager.createNotificationChannel(channel)
        }
    }

    fun dispatchSystemAlert(message: EmergencyMessage) {
        val soundUri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)

        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }
        val pendingIntent = PendingIntent.getActivity(context, 0, intent, PendingIntent.FLAG_IMMUTABLE)

        val title = "🚨 ${message.type} ALERT (${message.location})"
        val body = "${message.message}\n\n[Auth: ${message.signature.take(8)}... | Hops: ${message.hops}]"

        val builder = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setContentTitle(title)
            .setContentText(message.message)
            .setStyle(NotificationCompat.BigTextStyle().bigText(body))
            .setPriority(NotificationCompat.PRIORITY_MAX)
            .setSound(soundUri)
            .setVibrate(longArrayOf(0, 500, 200, 500))
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)

        notificationManager.notify(message.messageId.hashCode(), builder.build())
    }
}
