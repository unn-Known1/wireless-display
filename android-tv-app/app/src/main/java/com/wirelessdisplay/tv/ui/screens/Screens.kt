package com.wirelessdisplay.tv.ui.screens

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.focusable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.wirelessdisplay.tv.domain.model.ConnectionState
import com.wirelessdisplay.tv.domain.model.DisplayDevice
import com.wirelessdisplay.tv.domain.model.DisplayStats
import com.wirelessdisplay.tv.domain.model.QualityLevel
import com.wirelessdisplay.tv.ui.theme.*

@Composable
fun DeviceListScreen(
    devices: List<DisplayDevice>,
    isScanning: Boolean,
    onScanClick: () -> Unit,
    onDeviceClick: (DisplayDevice) -> Unit,
    onManualEntryClick: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Background)
            .padding(32.dp)
    ) {
        Text(
            text = "Wireless Display",
            style = MaterialTheme.typography.headlineLarge,
            color = OnBackground
        )

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = "Select a device to connect",
            style = MaterialTheme.typography.bodyLarge,
            color = TextSecondary
        )

        Spacer(modifier = Modifier.height(24.dp))

        Button(
            onClick = onScanClick,
            enabled = !isScanning,
            colors = ButtonDefaults.buttonColors(
                containerColor = Primary,
                contentColor = OnPrimary
            ),
            modifier = Modifier.fillMaxWidth(0.5f)
        ) {
            if (isScanning) {
                CircularProgressIndicator(
                    modifier = Modifier.size(20.dp),
                    color = OnPrimary,
                    strokeWidth = 2.dp
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text("Scanning...")
            } else {
                Icon(imageVector = Icons.Default.Search, contentDescription = null)
                Spacer(modifier = Modifier.width(8.dp))
                Text("Scan for Devices")
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        if (devices.isEmpty() && !isScanning) {
            Box(
                modifier = Modifier.fillMaxWidth(),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "No devices found. Tap scan or enter IP manually.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = TextSecondary
                )
            }
        } else {
            LazyColumn(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(devices) { device ->
                    DeviceItem(device = device, onClick = { onDeviceClick(device) })
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        OutlinedButton(
            onClick = onManualEntryClick,
            colors = ButtonDefaults.outlinedButtonColors(contentColor = Primary),
            modifier = Modifier.fillMaxWidth(0.5f)
        ) {
            Icon(imageVector = Icons.Default.Edit, contentDescription = null)
            Spacer(modifier = Modifier.width(8.dp))
            Text("Enter IP Manually")
        }
    }
}

@Composable
fun DeviceItem(device: DisplayDevice, onClick: () -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .focusable(),
        colors = CardDefaults.cardColors(containerColor = Surface),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = Icons.Default.Tv,
                contentDescription = null,
                tint = Primary,
                modifier = Modifier.size(40.dp)
            )
            Spacer(modifier = Modifier.width(16.dp))
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = device.name,
                    style = MaterialTheme.typography.titleMedium,
                    color = OnSurface,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                Text(
                    text = "${device.host}:${device.port}",
                    style = MaterialTheme.typography.bodySmall,
                    color = TextSecondary
                )
            }
            Icon(imageVector = Icons.Default.ChevronRight, contentDescription = null, tint = TextSecondary)
        }
    }
}

@Composable
fun ManualEntryDialog(onDismiss: () -> Unit, onConfirm: (String, Int) -> Unit) {
    var ipAddress by remember { mutableStateOf("") }
    var port by remember { mutableStateOf("5900") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Manual Connection", color = OnBackground) },
        text = {
            Column {
                OutlinedTextField(
                    value = ipAddress,
                    onValueChange = { ipAddress = it },
                    label = { Text("IP Address") },
                    singleLine = true,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = Primary,
                        unfocusedBorderColor = TextSecondary
                    ),
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(16.dp))
                OutlinedTextField(
                    value = port,
                    onValueChange = { port = it },
                    label = { Text("Port") },
                    singleLine = true,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = Primary,
                        unfocusedBorderColor = TextSecondary
                    ),
                    modifier = Modifier.fillMaxWidth()
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    val portInt = port.toIntOrNull() ?: 5900
                    onConfirm(ipAddress, portInt)
                },
                enabled = ipAddress.isNotBlank()
            ) { Text("Connect", color = Primary) }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel", color = TextSecondary) }
        },
        containerColor = Surface
    )
}

@Composable
fun DisplayOverlay(
    showControls: Boolean,
    connectionState: ConnectionState,
    stats: DisplayStats,
    quality: QualityLevel,
    onToggleControls: () -> Unit,
    onDisconnect: () -> Unit,
    onQualityChange: (QualityLevel) -> Unit
) {
    Box(modifier = Modifier.fillMaxSize()) {
        if (connectionState.isConnected) {
            FloatingActionButton(
                onClick = onToggleControls,
                modifier = Modifier
                    .align(Alignment.BottomEnd)
                    .padding(24.dp),
                containerColor = if (showControls) Primary else Surface.copy(alpha = 0.7f),
                contentColor = OnPrimary,
                shape = CircleShape
            ) {
                Icon(
                    imageVector = if (showControls) Icons.Default.ExpandMore else Icons.Default.Menu,
                    contentDescription = "Toggle controls"
                )
            }
        }

        AnimatedVisibility(
            visible = showControls && connectionState.isConnected,
            enter = slideInVertically(initialOffsetY = { it }),
            exit = slideOutVertically(targetOffsetY = { it }),
            modifier = Modifier.align(Alignment.BottomCenter)
        ) {
            ControlPanel(
                connectionState = connectionState,
                stats = stats,
                quality = quality,
                onDisconnect = onDisconnect,
                onQualityChange = onQualityChange
            )
        }
    }
}

@Composable
fun ControlPanel(
    connectionState: ConnectionState,
    stats: DisplayStats,
    quality: QualityLevel,
    onDisconnect: () -> Unit,
    onQualityChange: (QualityLevel) -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 24.dp, vertical = 80.dp),
        colors = CardDefaults.cardColors(containerColor = Surface.copy(alpha = 0.95f)),
        shape = RoundedCornerShape(16.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        imageVector = if (connectionState.isConnected) Icons.Default.CheckCircle else Icons.Default.Error,
                        contentDescription = null,
                        tint = if (connectionState.isConnected) Success else Error,
                        modifier = Modifier.size(24.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = if (connectionState.isConnected) "Connected" else "Disconnected",
                        style = MaterialTheme.typography.titleMedium,
                        color = OnSurface
                    )
                }
                Button(
                    onClick = onDisconnect,
                    colors = ButtonDefaults.buttonColors(containerColor = Error, contentColor = OnPrimary)
                ) {
                    Icon(imageVector = Icons.Default.Close, contentDescription = null, modifier = Modifier.size(18.dp))
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("Disconnect")
                }
            }

            Spacer(modifier = Modifier.height(16.dp))
            Divider(color = SurfaceVariant)
            Spacer(modifier = Modifier.height(16.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                StatItem(icon = Icons.Default.Speed, label = "Latency", value = "${stats.latency}ms")
                StatItem(icon = Icons.Default.Speed, label = "FPS", value = "${stats.fps}")
                StatItem(icon = Icons.Default.AspectRatio, label = "Resolution", value = stats.resolution.ifEmpty { "---" })
            }

            Spacer(modifier = Modifier.height(16.dp))
            Divider(color = SurfaceVariant)
            Spacer(modifier = Modifier.height(16.dp))

            Text(
                text = "Quality",
                style = MaterialTheme.typography.labelMedium,
                color = TextSecondary
            )

            Spacer(modifier = Modifier.height(8.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                QualityLevel.values().forEach { level ->
                    FilterChip(
                        selected = quality == level,
                        onClick = { onQualityChange(level) },
                        label = { Text(level.name) },
                        colors = FilterChipDefaults.filterChipColors(
                            selectedContainerColor = Primary,
                            selectedLabelColor = OnPrimary
                        )
                    )
                }
            }
        }
    }
}

@Composable
fun StatItem(icon: ImageVector, label: String, value: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Icon(imageVector = icon, contentDescription = null, tint = Primary, modifier = Modifier.size(24.dp))
        Spacer(modifier = Modifier.height(4.dp))
        Text(text = value, style = MaterialTheme.typography.titleMedium, color = OnSurface)
        Text(text = label, style = MaterialTheme.typography.labelSmall, color = TextSecondary)
    }
}

@Composable
fun ConnectingOverlay() {
    Box(
        modifier = Modifier.fillMaxSize().background(Background.copy(alpha = 0.9f)),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            CircularProgressIndicator(color = Primary, modifier = Modifier.size(48.dp))
            Spacer(modifier = Modifier.height(16.dp))
            Text(text = "Connecting...", style = MaterialTheme.typography.titleMedium, color = OnBackground)
        }
    }
}

@Composable
fun ErrorOverlay(message: String, onDismiss: () -> Unit) {
    Box(
        modifier = Modifier.fillMaxSize().background(Background.copy(alpha = 0.9f)),
        contentAlignment = Alignment.Center
    ) {
        Card(colors = CardDefaults.cardColors(containerColor = Surface), shape = RoundedCornerShape(16.dp)) {
            Column(
                modifier = Modifier.padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Icon(imageVector = Icons.Default.Error, contentDescription = null, tint = Error, modifier = Modifier.size(48.dp))
                Spacer(modifier = Modifier.height(16.dp))
                Text(text = message, style = MaterialTheme.typography.bodyMedium, color = OnSurface)
                Spacer(modifier = Modifier.height(16.dp))
                Button(onClick = onDismiss, colors = ButtonDefaults.buttonColors(containerColor = Primary)) {
                    Text("OK")
                }
            }
        }
    }
}