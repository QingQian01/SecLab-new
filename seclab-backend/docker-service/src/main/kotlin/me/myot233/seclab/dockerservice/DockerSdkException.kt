package me.myot233.seclab.dockerservice

/**
 * Docker SDK 调用统一异常。
 *
 * - 由 [DockerSdkService] 在 SDK 调用失败时抛出，承载 exitCode（若可获取）与 stderr。
 * - 由 [DockerController] 在 `runSdk()` 替换层 catch 后转 [SdkRunResult.Failure]，
 *   保持对外响应体向后兼容（前端不感知底层已从 CLI 切到 SDK）。
 *
 * @param message 异常摘要
 * @param exitCode 命令退出码（不可获取时为 -1）
 * @param stderr 原始 stderr 输出（可为空字符串）
 * @param cause 上游异常（可选）
 */
class DockerSdkException(
    message: String,
    val exitCode: Int = -1,
    val stderr: String = "",
    cause: Throwable? = null,
) : RuntimeException(message, cause)
