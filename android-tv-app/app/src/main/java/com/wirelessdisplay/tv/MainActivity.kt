package com.wirelessdisplay.tv

import android.os.Bundle
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.focusable
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.lifecycle.viewmodel.compose.viewModel
import com.wirelessdisplay.tv.ui.MainViewModel
import com.wirelessdisplay.tv.ui.screens.*
import com.wirelessdisplay.tv.ui.theme.WirelessDisplayTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Keep screen on while displaying
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        // Full screen immersive mode
        window.decorView.systemUiVisibility = (
            android.view.View.SYSTEM_UI_FLAG_FULLSCREEN
            or android.view.View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
            or android.view.View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        )

        setContent {
            WirelessDisplayTheme {
                WirelessDisplayApp()
            }
        }
    }
}

@Composable
fun WirelessDisplayApp(viewModel: MainViewModel = viewModel()) {
    var showManualDialog by remember { mutableStateOf(false) }
    var connectionView by remember { mutableStateOf(false) }

    val devices by viewModel.devices.collectAsState()
    val connectionState by viewModel.connectionState.collectAsState()
    val displayStats by viewModel.displayStats.collectAsState()
    val qualityLevel by viewModel.qualityLevel.collectAsState()
    val showControls by viewModel.showControls.collectAsState()
    val isScanning by viewModel.isScanning.collectAsState()

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Transparent)
            .focusable()
    ) {
        when {
            connectionState.isConnecting -> {
                ConnectingOverlay()
            }

            connectionState.isConnected -> {
                // Display view with overlay
                DisplayScreen(
                    stats = displayStats,
                    showControls = showControls,
                    onToggleControls = { viewModel.toggleControls() },
                    onDisconnect = { viewModel.disconnect() },
                    quality = qualityLevel,
                    onQualityChange = { viewModel.setQuality(it) }
                )
            }

            connectionView -> {
                DeviceListScreen(
                    devices = devices,
                    isScanning = isScanning,
                    onScanClick = { viewModel.startDiscovery() },
                    onDeviceClick = {
                        viewModel.connect(it)
                    },
                    onManualEntryClick = { showManualDialog = true }
                )
            }

            else -> {
                DeviceListScreen(
                    devices = devices,
                    isScanning = isScanning,
                    onScanClick = {
                        viewModel.startDiscovery()
                        connectionView = true
                    },
                    onDeviceClick = {
                        viewModel.connect(it)
                    },
                    onManualEntryClick = { showManualDialog = true }
                )
            }
        }

        // Error overlay
        if (connectionState.errorMessage != null && !connectionState.isConnecting) {
            ErrorOverlay(
                message = connectionState.errorMessage!!,
                onDismiss = { /* Reset error state */ }
            )
        }

        // Manual entry dialog
        if (showManualDialog) {
            ManualEntryDialog(
                onDismiss = { showManualDialog = false },
                onConfirm = { ip, port ->
                    showManualDialog = false
                    viewModel.connectManual(ip, port)
                }
            )
        }
    }
}

@Composable
fun DisplayScreen(
    stats: com.wirelessdisplay.tv.domain.model.DisplayStats,
    showControls: Boolean,
    onToggleControls: () -> Unit,
    onDisconnect: () -> Unit,
    quality: com.wirelessdisplay.tv.domain.model.QualityLevel,
    onQualityChange: (com.wirelessdisplay.tv.domain.model.QualityLevel) -> Unit
) {
    Box(modifier = Modifier.fillMaxSize()) {
        // Full-screen display background
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color.Black)
        )

        // Controls overlay
        DisplayOverlay(
            showControls = showControls,
            connectionState = com.wirelessdisplay.tv.domain.model.ConnectionState(isConnected = true),
            stats = stats,
            quality = quality,
            onToggleControls = onToggleControls,
            onDisconnect = onDisconnect,
            onQualityChange = onQualityChange
        )
    }
}