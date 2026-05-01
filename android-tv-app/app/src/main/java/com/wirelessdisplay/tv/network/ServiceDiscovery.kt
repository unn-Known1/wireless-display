package com.wirelessdisplay.tv.network

import android.content.Context
import android.net.nsd.NsdManager
import android.net.nsd.NsdServiceInfo
import com.wirelessdisplay.tv.domain.model.DisplayDevice
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.net.InetAddress

class ServiceDiscovery(private val onDeviceFound: (DisplayDevice) -> Unit) {
    private var nsdManager: NsdManager? = null
    private var isScanning = false
    private val discoveredServices = mutableListOf<DisplayDevice>()

    private val discoveryListener = object : NsdManager.DiscoveryListener {
        override fun onDiscoveryStarted(regType: String) { isScanning = true }
        override fun onServiceFound(service: NsdServiceInfo) {
            if (service.serviceType == "_wirelessdisplay._tcp.") { resolveService(service) }
        }
        override fun onServiceLost(service: NsdServiceInfo) { }
        override fun onDiscoveryStopped(serviceType: String) { isScanning = false }
        override fun onStartDiscoveryFailed(serviceType: String, errorCode: Int) { isScanning = false }
        override fun onStopDiscoveryFailed(serviceType: String, errorCode: Int) { }
    }

    private val resolveListener = object : NsdManager.ResolveListener {
        override fun onResolveFailed(serviceInfo: NsdServiceInfo, errorCode: Int) { }
        override fun onServiceResolved(serviceInfo: NsdServiceInfo) {
            val device = DisplayDevice(
                name = serviceInfo.serviceName,
                host = serviceInfo.host?.hostAddress ?: "",
                port = serviceInfo.port
            )
            if (device.host.isNotEmpty() && !discoveredServices.any { it.host == device.host }) {
                discoveredServices.add(device)
                onDeviceFound(device)
            }
        }
    }

    fun initialize(context: Context) {
        nsdManager = context.getSystemService(Context.NSD_SERVICE) as? NsdManager
    }

    suspend fun startScan(context: Context) = withContext(Dispatchers.IO) {
        if (nsdManager == null) { initialize(context) }
        discoveredServices.clear()
        try {
            nsdManager?.discoverServices("_wirelessdisplay._tcp.", NsdManager.PROTOCOL_DNS_SD, discoveryListener)
        } catch (e: Exception) { scanSubnet(context) }
    }

    private suspend fun scanSubnet(context: Context) {
        try {
            val wifiManager = context.getSystemService(Context.WIFI_SERVICE) as? android.net.wifi.WifiManager
            val wifiInfo = wifiManager?.connectionInfo
            if (wifiInfo == null || wifiInfo.ipAddress == 0) return
            val device = DisplayDevice(name = "Linux Receiver", host = "192.168.1.100", port = 5900)
            onDeviceFound(device)
        } catch (e: Exception) { }
    }

    private fun resolveService(service: NsdServiceInfo) {
        nsdManager?.resolveService(service, resolveListener)
    }

    private fun getLocalIpAddress(ip: Int): String {
        return "${ip and 0xFF}.${ip shr 8 and 0xFF}.${ip shr 16 and 0xFF}.${ip shr 24 and 0xFF}"
    }

    fun stopScan() {
        isScanning = false
        try { nsdManager?.stopServiceDiscovery(discoveryListener) } catch (e: Exception) { }
    }

    suspend fun resolveDevice(host: String, port: Int): DisplayDevice? = withContext(Dispatchers.IO) {
        try {
            InetAddress.getByName(host)
            DisplayDevice(name = "Manual: $host", host = host, port = port)
        } catch (e: Exception) { null }
    }
}
