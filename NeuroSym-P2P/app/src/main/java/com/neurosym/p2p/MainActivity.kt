package com.neurosym.p2p

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.ui.Modifier
import androidx.core.content.ContextCompat
import com.neurosym.p2p.ble.P2PBluetoothEngine
import com.neurosym.p2p.service.P2PForegroundService
import com.neurosym.p2p.ui.MainScreen
import com.neurosym.p2p.ui.theme.NeuroSymP2PTheme

class MainActivity : ComponentActivity() {

    private lateinit var bleEngine: P2PBluetoothEngine

    private val requestPermissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { permissions ->
            val allGranted = permissions.entries.all { it.value }
            if (allGranted) {
                startP2PService()
            } else {
                Toast.makeText(this, "Permissions required for P2P Mesh", Toast.LENGTH_LONG).show()
            }
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Use a dummy engine just for UI binding if service manages the real one
        // In a full app, we'd bind to the service to get the real engine instance.
        // For simplicity in this demo, we'll instantiate one here for UI updates,
        // and let the service run its own for background routing.
        bleEngine = P2PBluetoothEngine(this) { }
        
        setContent {
            NeuroSymP2PTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    MainScreen(
                        bleEngine = bleEngine,
                        modifier = Modifier.padding(innerPadding)
                    )
                }
            }
        }

        checkAndRequestPermissions()
    }

    private fun checkAndRequestPermissions() {
        val requiredPermissions = mutableListOf<String>()
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            requiredPermissions.add(Manifest.permission.BLUETOOTH_SCAN)
            requiredPermissions.add(Manifest.permission.BLUETOOTH_ADVERTISE)
            requiredPermissions.add(Manifest.permission.BLUETOOTH_CONNECT)
        } else {
            requiredPermissions.add(Manifest.permission.ACCESS_FINE_LOCATION)
        }
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            requiredPermissions.add(Manifest.permission.POST_NOTIFICATIONS)
        }

        val missingPermissions = requiredPermissions.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }

        if (missingPermissions.isNotEmpty()) {
            requestPermissionLauncher.launch(missingPermissions.toTypedArray())
        } else {
            startP2PService()
            bleEngine.startEngine() // Start UI engine
        }
    }

    private fun startP2PService() {
        val intent = Intent(this, P2PForegroundService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent)
        } else {
            startService(intent)
        }
    }
    
    override fun onDestroy() {
        super.onDestroy()
        bleEngine.stopEngine()
    }
}
