package me.myot233.seclab.experimentmoduleservice.service

import com.fasterxml.jackson.databind.ObjectMapper
import org.springframework.beans.factory.annotation.Value
import org.springframework.http.HttpStatus
import org.springframework.jdbc.core.JdbcTemplate
import org.springframework.stereotype.Service
import org.springframework.web.server.ResponseStatusException
import java.security.MessageDigest
import java.time.Instant
import java.util.Base64
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

data class CatalogAuthContext(
    val userId: Long,
    val role: String,
)

@Service
class CatalogAuthService(
    private val objectMapper: ObjectMapper,
    private val jdbcTemplate: JdbcTemplate,
    @Value("\${seclab.jwt.secret}") private val secret: String,
) {
    fun requireTeacherOrAdmin(authorizationHeader: String?): CatalogAuthContext {
        val token = extractBearerToken(authorizationHeader)
        val userId = parseUserId(token)
        val user = jdbcTemplate.query(
            """
            SELECT user_id, COALESCE(is_admin + 0, 0) AS is_admin
            FROM `user`
            WHERE user_id = ? AND COALESCE(is_deleted, 0) = 0
            LIMIT 1
            """.trimIndent(),
            { rs, _ ->
                mapOf(
                    "userId" to rs.getLong("user_id"),
                    "isAdmin" to rs.getInt("is_admin"),
                )
            },
            userId,
        ).firstOrNull() ?: throw ResponseStatusException(HttpStatus.UNAUTHORIZED, "Token user does not exist")

        if (user["isAdmin"] == 1) {
            return CatalogAuthContext(userId = userId, role = "admin")
        }

        val managedClassCount = jdbcTemplate.queryForObject(
            """
            SELECT COUNT(*)
            FROM `class`
            WHERE COALESCE(is_end, 0) = 0 AND admin_id = ?
            """.trimIndent(),
            Int::class.java,
            userId,
        ) ?: 0
        if (managedClassCount > 0) {
            return CatalogAuthContext(userId = userId, role = "teacher")
        }

        throw ResponseStatusException(HttpStatus.FORBIDDEN, "Only teacher or admin accounts can modify course modules")
    }

    private fun extractBearerToken(authorizationHeader: String?): String {
        val raw = authorizationHeader?.trim().orEmpty()
        if (!raw.startsWith("Bearer ", ignoreCase = true)) {
            throw ResponseStatusException(HttpStatus.UNAUTHORIZED, "Bearer token is required")
        }
        return raw.substringAfter(" ").trim().takeIf { it.isNotEmpty() }
            ?: throw ResponseStatusException(HttpStatus.UNAUTHORIZED, "Bearer token is required")
    }

    private fun parseUserId(token: String): Long {
        val parts = token.split(".")
        if (parts.size != 3) {
            throw ResponseStatusException(HttpStatus.UNAUTHORIZED, "Token format is invalid")
        }
        val signingInput = "${parts[0]}.${parts[1]}"
        if (!MessageDigest.isEqual(sign(signingInput).toByteArray(), parts[2].toByteArray())) {
            throw ResponseStatusException(HttpStatus.UNAUTHORIZED, "Token signature is invalid")
        }
        val payloadJson = String(Base64.getUrlDecoder().decode(parts[1]), Charsets.UTF_8)
        val payload = objectMapper.readTree(payloadJson)
        val exp = payload.get("exp")?.asLong()
            ?: throw ResponseStatusException(HttpStatus.UNAUTHORIZED, "Token expiration is missing")
        if (Instant.now().epochSecond >= exp) {
            throw ResponseStatusException(HttpStatus.UNAUTHORIZED, "Token has expired")
        }
        return payload.get("sub")?.asText()?.toLongOrNull()
            ?: throw ResponseStatusException(HttpStatus.UNAUTHORIZED, "Token subject is missing")
    }

    private fun sign(value: String): String {
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(secret.toByteArray(Charsets.UTF_8), "HmacSHA256"))
        return Base64.getUrlEncoder().withoutPadding().encodeToString(mac.doFinal(value.toByteArray(Charsets.UTF_8)))
    }
}
