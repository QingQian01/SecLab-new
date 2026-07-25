package me.myot233.seclab.dockerservice

import org.springframework.context.annotation.Configuration
import org.springframework.web.socket.config.annotation.EnableWebSocket
import org.springframework.web.socket.config.annotation.WebSocketConfigurer
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry

/**
 * WebSocket 端点注册。
 *
 * 把 [TtyLogHandler] 暴露到 `/ws/tty/{containerName}`，供前端旁路监听容器 TTY/日志。
 *
 * 设计要点：
 * - `setAllowedOriginPatterns("*")`：兼容 dev 模式 Vite 代理与生产 nginx 反代；
 *   若未来部署在公网，应替换为具体白名单 origin。
 * - 不引入 STOMP/SockJS：原始 WebSocket 即可满足"服务端 → 客户端"单向日志推送需求，
 *   减少依赖与协议复杂度。
 *
 * 路径变量 `{containerName}` 由 Spring WebSocket 自动匹配，[TtyLogHandler] 从 URI path 解析。
 */
@Configuration
@EnableWebSocket
class WebSocketConfig(
    private val ttyLogHandler: TtyLogHandler,
) : WebSocketConfigurer {

    override fun registerWebSocketHandlers(registry: WebSocketHandlerRegistry) {
        registry.addHandler(ttyLogHandler, "/ws/tty/{containerName}")
            .setAllowedOriginPatterns("*")
    }
}