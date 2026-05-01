package com.wirelessdisplay.tv.network

import com.wirelessdisplay.tv.domain.model.DisplayDevice
import com.wirelessdisplay.tv.domain.model.QualityLevel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.DataInputStream
import java.io.DataOutputStream
import java.net.Socket

class VncClient {
    private var socket: Socket? = null
    private var inputStream: DataInputStream? = null
    private var outputStream: DataOutputStream? = null
    private var isRunning = false
    private var frameWidth = 1920
    private var frameHeight = 1080

    suspend fun connect(device: DisplayDevice): Result<Boolean> = withContext(Dispatchers.IO) {
        try {
            socket = Socket(device.host, device.port)
            inputStream = DataInputStream(socket!!.getInputStream())
            outputStream = DataOutputStream(socket!!.getOutputStream())
            val serverVersion = ByteArray(12)
            inputStream!!.readFully(serverVersion)
            val clientVersion = "RFB 003.008\n"
            outputStream!!.writeBytes(clientVersion)
            val securityType = inputStream!!.readByte().toInt()
            if (securityType == 0) {
                val reasonLen = inputStream!!.readInt()
                val reason = ByteArray(reasonLen)
                inputStream!!.readFully(reason)
                return@withContext Result.failure(Exception(String(reason)))
            }
            if (securityType != 1) {
                inputStream!!.readFully(ByteArray(16))
                outputStream!!.write(ByteArray(16))
            }
            outputStream!!.writeByte(1)
            frameWidth = (inputStream!!.readShort().toInt() and 0xFFFF)
            frameHeight = (inputStream!!.readShort().toInt() and 0xFFFF)
            inputStream!!.readShort()
            inputStream!!.readByte()
            inputStream!!.readByte()
            inputStream!!.readShort()
            inputStream!!.readShort()
            inputStream!!.readShort()
            inputStream!!.readByte()
            inputStream!!.readByte()
            inputStream!!.readByte()
            inputStream!!.readFully(ByteArray(3))
            isRunning = true
            Result.success(true)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun requestFrame(quality: QualityLevel): Result<ByteArray> = withContext(Dispatchers.IO) {
        try {
            if (!isRunning || inputStream == null || outputStream == null) {
                return@withContext Result.failure(Exception("Not connected"))
            }
            outputStream!!.writeByte(3)
            outputStream!!.writeByte(0)
            outputStream!!.writeShort(0)
            outputStream!!.writeShort(0)
            outputStream!!.writeShort(frameWidth)
            outputStream!!.writeShort(frameHeight)
            outputStream!!.flush()
            val messageType = inputStream!!.readByte().toInt()
            if (messageType == 0) {
                inputStream!!.readByte()
                val numRects = inputStream!!.readShort().toInt() and 0xFFFF
                for (i in 0 until numRects) {
                    inputStream!!.readShort()
                    inputStream!!.readShort()
                    val w = inputStream!!.readShort().toInt() and 0xFFFF
                    val h = inputStream!!.readShort().toInt() and 0xFFFF
                    val encodingType = inputStream!!.readInt()
                    when (encodingType) {
                        0, -16, -23 -> {
                            val data = ByteArray(w * h * 4)
                            inputStream!!.readFully(data)
                            return@withContext Result.success(data)
                        }
                    }
                }
            }
            Result.success(ByteArray(0))
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    fun disconnect() {
        isRunning = false
        try {
            inputStream?.close()
            outputStream?.close()
            socket?.close()
        } catch (e: Exception) { }
        inputStream = null
        outputStream = null
        socket = null
    }
}
