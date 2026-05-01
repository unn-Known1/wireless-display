package com.wirelessdisplay.tv.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.wirelessdisplay.tv.domain.model.ConnectionState
import com.wirelessdisplay.tv.domain.model.DisplayDevice
import com.wirelessdisplay.tv.domain.model.DisplayStats
import com.wirelessdisplay.tv.domain.model.QualityLevel
import com.wirelessdisplay.tv.network.ServiceDiscovery
import com.wirelessdisplay.tv.network.VncClient
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class MainViewModel(application: Application) : AndroidViewModel(application) {

    private val _devices = MutableStateFlow<List<DisplayDevice>>(emptyList())
    val devices: StateFlow<List<DisplayDevice>> = _devices.asStateFlow()

    private val _connectionState = MutableStateFlow(ConnectionState())
    val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()

    private val _displayStats = MutableStateFlow(DisplayStats())
    val displayStats: StateFlow<DisplayStats> = _displayStats.asStateFlow()

    private val _qualityLevel = MutableStateFlow(QualityLevel.MEDIUM)
    val qualityLevel: StateFlow<QualityLevel> = _qualityLevel.asStateFlow()

    private val _showControls = MutableStateFlow(false)
    val showControls: StateFlow<Boolean> = _showControls.asStateFlow()

    private val _isScanning = MutableStateFlow(false)
    val isScanning: StateFlow<Boolean> = _isScanning.asStateFlow()

    private val vncClient = VncClient()
    private val discovery = ServiceDiscovery { device ->
        _devices.value = _devices.value + device
    }

    private var frameLoopJob: Job? = null
    private var frameStartTime = System.currentTimeMillis()

    fun startDiscovery() {
        viewModelScope.launch {
            _isScanning.value = true
            _devices.value = emptyList()
            discovery.startScan(getApplication())
            _isScanning.value = false
        }
    }

    fun connect(device: DisplayDevice) {
        viewModelScope.launch {
            _connectionState.value = ConnectionState(isConnecting = true)

            val result = vncClient.connect(device)

            result.fold(
                onSuccess = {
                    _connectionState.value = ConnectionState(isConnected = true)
                    startFrameLoop()
                },
                onFailure = { error ->
                    _connectionState.value = ConnectionState(
                        isConnected = false,
                        errorMessage = error.message ?: "Connection failed"
                    )
                }
            )
        }
    }

    fun connectManual(host: String, port: Int) {
        viewModelScope.launch {
            val device = discovery.resolveDevice(host, port)
            if (device != null) {
                connect(device)
            } else {
                _connectionState.value = ConnectionState(
                    errorMessage = "Invalid address"
                )
            }
        }
    }

    fun disconnect() {
        frameLoopJob?.cancel()
        vncClient.disconnect()
        _connectionState.value = ConnectionState(isConnected = false)
    }

    fun setQuality(level: QualityLevel) {
        _qualityLevel.value = level
    }

    fun toggleControls() {
        _showControls.value = !_showControls.value
    }

    fun hideControls() {
        _showControls.value = false
    }

    private fun startFrameLoop() {
        frameLoopJob = viewModelScope.launch {
            while (_connectionState.value.isConnected) {
                frameStartTime = System.currentTimeMillis()

                val result = vncClient.requestFrame(_qualityLevel.value)

                result.fold(
                    onSuccess = { frameData ->
                        val elapsed = System.currentTimeMillis() - frameStartTime
                        _displayStats.value = _displayStats.value.copy(
                            latency = elapsed,
                            fps = (1000 / elapsed).toInt().coerceIn(0, 60),
                            resolution = "1920x1080"
                        )
                    },
                    onFailure = { /* Skip frame */ }
                )

                delay(33) // ~30 FPS
            }
        }
    }

    override fun onCleared() {
        super.onCleared()
        disconnect()
        discovery.stopScan()
    }
}