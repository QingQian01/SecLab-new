package me.myot233.seclab.dockerservice

/**
 * 靶场白名单与元数据。
 *
 * - 供 [DockerController] / [TtyLogHandler] / [FrustrationTracker] 共用，
 *   避免在多处重复定义靶机容器名 → 端口 / lab_key 的映射。
 * - [labTaskSummary] 为 Phase 1 静态任务摘要；后续可改为从 experiment-module-service 动态拉取。
 */
object LabAllowlist {

    val labs: Map<String, LabTarget> = mapOf(
        "sqli" to LabTarget("sqli-lab-web-1", 8091, "SQL 注入靶场：基于 union 的注入与盲注实验"),
        "xss" to LabTarget("xss-lab-web-1", 8092, "XSS 靶场：反射型 / 存储型跨站脚本实验"),
        "csrf" to LabTarget("csrf-lab-web-1", 8093, "CSRF 靶场：跨站请求伪造实验"),
        "cmd" to LabTarget("command-inject-web-1", 8090, "命令注入靶场：管道符与命令拼接实验"),
        "upload" to LabTarget("file-upload-lab-web-1", 8094, "文件上传靶场：绕过校验与 webshell 实验"),
        "dir" to LabTarget("directory-traversal-lab-web-1", 8095, "目录遍历靶场：路径穿越与任意文件读取实验"),
    )

    /** 容器名是否在白名单内（大小写不敏感） */
    fun isAllowed(containerName: String): Boolean {
        val lower = containerName.lowercase()
        return labs.values.any { it.containerName.equals(lower, ignoreCase = true) }
    }

    /** 由容器名反查 lab_key（如 sqli-lab-web-1 -> sqli） */
    fun labKeyOf(containerName: String): String? =
        labs.entries.firstOrNull { it.value.containerName.equals(containerName, ignoreCase = true) }?.key

    /** 由容器名反查 LabTarget */
    fun targetOf(containerName: String): LabTarget? =
        labs.values.firstOrNull { it.containerName.equals(containerName, ignoreCase = true) }

    /** 由 lab_key 反查 LabTarget（大小写不敏感） */
    fun targetByKey(labKey: String): LabTarget? = labs[labKey.lowercase()]
}

/**
 * 靶机元数据。
 *
 * @param containerName docker 容器名（如 sqli-lab-web-1）
 * @param hostPort 宿主机暴露端口
 * @param labTaskSummary 当前靶机任务摘要，注入 Dify 作为 RAG 检索键之一
 */
data class LabTarget(
    val containerName: String,
    val hostPort: Int,
    val labTaskSummary: String,
)
