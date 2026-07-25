package me.myot233.seclab.dockerservice

import com.github.dockerjava.api.DockerClient
import com.github.dockerjava.core.DefaultDockerClientConfig
import com.github.dockerjava.core.DockerClientImpl
import com.github.dockerjava.zerodep.ZerodepDockerHttpClient
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration

/**
 * Docker Java SDK 客户端配置。
 *
 * - 替换原 [DockerController] 内的 `ProcessBuilder("docker", ...)` CLI 调用方式。
 * - 默认 docker host 走 `seclab.docker.host` 配置；未配置时按平台默认：
 *     - Linux/macOS: `unix:///var/run/docker.sock`
 *     - Windows: `npipe:////./pipe/docker_engine`
 * - 也允许通过环境变量 `DOCKER_HOST` 覆盖（与 docker CLI 行为一致）。
 */
@Configuration
class DockerSdkConfig {

    private val log = LoggerFactory.getLogger(javaClass)

    @Value("\${seclab.docker.host:}")
    private lateinit var configuredHost: String

    @Bean(destroyMethod = "close")
    fun dockerClient(): DockerClient {
        val host = resolveDockerHost()
        log.info("Initializing Docker SDK client with host={}", host)
        val config = DefaultDockerClientConfig.createDefaultConfigBuilder()
            .withDockerHost(host)
            .build()
        val httpClient = ZerodepDockerHttpClient.Builder()
            .dockerHost(config.dockerHost)
            .sslConfig(config.sslConfig)
            .build()
        return DockerClientImpl.getInstance(config, httpClient)
    }

    private fun resolveDockerHost(): String {
        if (configuredHost.isNotBlank()) return configuredHost
        System.getenv("DOCKER_HOST")?.takeIf { it.isNotBlank() }?.let { return it }
        val osName = System.getProperty("os.name").lowercase()
        return if (osName.contains("win")) {
            "npipe:////./pipe/docker_engine"
        } else {
            "unix:///var/run/docker.sock"
        }
    }
}
