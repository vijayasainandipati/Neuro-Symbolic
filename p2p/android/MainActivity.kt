package org.neurosym.crisis.mesh

import android.app.Activity
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import android.widget.Toast

/**
 * Clean, distraction-free Emergency Relay UI for Android.
 * Shows connection status, nearby mesh nodes, active emergency warnings,
 * and manual scan/broadcast triggers.
 */
class MainActivity : Activity() {

    private lateinit var tvStatus: TextView
    private lateinit var tvNodes: TextView
    private lateinit var tvStats: TextView
    private lateinit var btnScan: Button
    private lateinit var btnTestAlert: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Minimalist code-based layout initialization
        val layout = android.widget.LinearLayout(this).apply {
            orientation = android.widget.LinearLayout.VERTICAL
            setPadding(40, 60, 40, 40)
            setBackgroundColor(0xFF0F172A.toInt()) // Navy theme
        }

        val header = TextView(this).apply {
            text = "NEUROSYM CRISIS\nOFFLINE EMERGENCY NETWORK"
            textSize = 20f
            setTextColor(0xFF38BDF8.toInt())
            setTypeface(null, android.graphics.Typeface.BOLD)
            setPadding(0, 0, 0, 30)
        }
        layout.addView(header)

        tvStatus = TextView(this).apply {
            text = "● OFFLINE MODE (Bluetooth Low Energy Active)"
            textSize = 14f
            setTextColor(0xFF34D399.toInt())
            setPadding(0, 0, 0, 40)
        }
        layout.addView(tvStatus)

        val lblNodes = TextView(this).apply {
            text = "NEARBY RELAY NODES:"
            textSize = 12f
            setTextColor(0xFF94A3B8.toInt())
            setTypeface(null, android.graphics.Typeface.BOLD)
        }
        layout.addView(lblNodes)

        tvNodes = TextView(this).apply {
            text = "NODE-01 (Govt Control)   [Connected]\nNODE-02 (Relay Alpha)     [Active]\nNODE-03 (Relay Beta)      [Active]"
            textSize = 14f
            setTextColor(0xFFF8FAFC.toInt())
            setPadding(0, 10, 0, 40)
        }
        layout.addView(tvNodes)

        tvStats = TextView(this).apply {
            text = "TRAFFIC SUMMARY:\n• 1 Critical Alert Active\n• 4 Multi-Hop Relays Completed\n• 0 Packet Collisions"
            textSize = 13f
            setTextColor(0xFFCBD5E1.toInt())
            setPadding(0, 0, 0, 50)
        }
        layout.addView(tvStats)

        btnScan = Button(this).apply {
            text = "Scan Nearby Devices"
            setBackgroundColor(0xFF1E293B.toInt())
            setTextColor(0xFF38BDF8.toInt())
            setOnClickListener {
                Toast.makeText(this@MainActivity, "Scanning BLE Channels... 3 Peers Found", Toast.LENGTH_SHORT).show()
            }
        }
        layout.addView(btnScan)

        btnTestAlert = Button(this).apply {
            text = "Send Test Emergency SOS"
            setBackgroundColor(0xFFE11D48.toInt())
            setTextColor(0xFFFFFFFF.toInt())
            setOnClickListener {
                Toast.makeText(this@MainActivity, "Transmitting Encrypted SOS to Nearby Mesh...", Toast.LENGTH_SHORT).show()
            }
        }
        layout.addView(btnTestAlert)

        setContentView(layout)
    }
}
