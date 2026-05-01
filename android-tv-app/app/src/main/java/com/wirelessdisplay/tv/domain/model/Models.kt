package com.wirelessdisplay.tv.domain.model

data class DisplayDevice(
    val name: String,
    val host: String,
    val port: Int = 5900
)

data class ConnectionState(
    val isConnected: Boolean = false,
    val isConnecting: Boolean = false,
    val errorMessage: String? = null
)

enum class QualityLevel {
    LOW, MEDIUM, HIGH
}

data class DisplayStats(
    val latency: Long = 0,
    val fps: Int = 0,
    val resolution: String = "",
    val quality: QualityLevel = QualityLevel.MEDIUM
)
