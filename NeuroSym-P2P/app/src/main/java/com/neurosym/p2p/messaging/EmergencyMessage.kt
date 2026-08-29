package com.neurosym.p2p.messaging

import org.json.JSONObject
import java.util.UUID

/**
 * Standard Compact Emergency Message Protocol for NeuroSym P2P.
 */
data class EmergencyMessage(
    val messageId: String = "NS-" + UUID.randomUUID().toString().substring(0, 8).uppercase(),
    val sourceId: String = "GOV-001",
    val type: String = "CYCLONE",
    val priority: String = "CRITICAL",
    val location: String = "Zone A",
    val message: String = "Evacuate Zone A before 6:00 PM via State Highway 44.",
    val timestamp: Long = System.currentTimeMillis(),
    val ttl: Int = 5,
    val hops: Int = 0,
    val signature: String = "SIG_DDMA_ROOT_AUTHENTIC"
) {
    fun toJson(): String {
        val json = JSONObject()
        json.put("messageId", messageId)
        json.put("sourceId", sourceId)
        json.put("type", type)
        json.put("priority", priority)
        json.put("location", location)
        json.put("message", message)
        json.put("timestamp", timestamp)
        json.put("ttl", ttl)
        json.put("hops", hops)
        json.put("signature", signature)
        return json.toString()
    }

    fun prepareForRelay(): EmergencyMessage? {
        if (ttl <= 1) return null
        return this.copy(ttl = ttl - 1, hops = hops + 1)
    }

    companion object {
        fun fromJson(jsonStr: String): EmergencyMessage {
            val json = JSONObject(jsonStr)
            return EmergencyMessage(
                messageId = json.optString("messageId", "NS-UNKNOWN"),
                sourceId = json.optString("sourceId", "UNKNOWN"),
                type = json.optString("type", "GENERAL"),
                priority = json.optString("priority", "HIGH"),
                location = json.optString("location", "District"),
                message = json.optString("message", ""),
                timestamp = json.optLong("timestamp", System.currentTimeMillis()),
                ttl = json.optInt("ttl", 5),
                hops = json.optInt("hops", 0),
                signature = json.optString("signature", "")
            )
        }
    }
}
