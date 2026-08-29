package com.neurosym.p2p.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.neurosym.p2p.ble.P2PBluetoothEngine

@Composable
fun MainScreen(bleEngine: P2PBluetoothEngine, modifier: Modifier = Modifier) {
    val isScanning by bleEngine.isScanning.collectAsState()
    val discoveredNodes by bleEngine.discoveredNodes.collectAsState()
    val messageLog by bleEngine.messageLog.collectAsState()

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(Color(0xFF0F172A))
            .padding(16.dp)
    ) {
        // Header
        Text(
            text = "NEUROSYM P2P",
            color = Color.White,
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold
        )
        Text(
            text = "Emergency Mesh Communication",
            color = Color.Gray,
            fontSize = 14.sp,
            modifier = Modifier.padding(bottom = 24.dp)
        )

        // Status Panel
        Card(
            colors = CardDefaults.cardColors(containerColor = Color(0xFF1E293B)),
            modifier = Modifier.fillMaxWidth().padding(bottom = 24.dp)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("P2P Network", color = Color.White)
                    Text(
                        if (isScanning) "ACTIVE (Scanning)" else "STOPPED",
                        color = if (isScanning) Color.Green else Color.Red,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }

        // Discovered Nodes
        Text(
            text = "Nearby Mesh Nodes (${discoveredNodes.size})",
            color = Color.White,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(bottom = 8.dp)
        )
        
        if (discoveredNodes.isEmpty()) {
            Text("No nodes discovered yet.", color = Color.Gray, modifier = Modifier.padding(bottom = 16.dp))
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(max = 200.dp)
                    .padding(bottom = 16.dp)
            ) {
                items(discoveredNodes.toList()) { node ->
                    Card(
                        colors = CardDefaults.cardColors(containerColor = Color(0xFF1E293B)),
                        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)
                    ) {
                        Column(modifier = Modifier.padding(12.dp)) {
                            Text(node.deviceId, color = Color.White, fontWeight = FontWeight.Bold)
                            Text("RSSI: ${node.rssi} dBm", color = Color.Gray, fontSize = 12.sp)
                        }
                    }
                }
            }
        }

        // Message Log
        Text(
            text = "Live Mesh Traffic",
            color = Color.White,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(bottom = 8.dp)
        )
        
        Card(
            colors = CardDefaults.cardColors(containerColor = Color.Black),
            modifier = Modifier.fillMaxWidth().weight(1f)
        ) {
            LazyColumn(modifier = Modifier.padding(12.dp)) {
                items(messageLog) { log ->
                    Text(
                        text = log,
                        color = Color.Green,
                        fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace,
                        fontSize = 12.sp,
                        modifier = Modifier.padding(vertical = 2.dp)
                    )
                }
            }
        }
    }
}
