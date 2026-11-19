package service

import dto.LabPackageDto
import dto.ModuleMutationRequest
import entity.LabPackageEntity
import repository.LabPackageRepository
import org.slf4j.LoggerFactory
import org.springframework.beans.factory.annotation.Value
import org.springframework.http.HttpStatus
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional
import org.springframework.web.multipart.MultipartFile
import org.springframework.web.server.ResponseStatusException
import java.nio.file.FileSystems
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths
import java.nio.file.StandardCopyOption
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import java.util.Locale

/**
 * 实验包上传与登记服务。
 *
 * 本期范围（与用户确认）：
 * - 仅做 zip 落盘 + 元数据登记到 lab_package 表
 * - 可选创建 module 并关联 lab_package.module_id
 * - 不调 docker build，不修改 LabAllowlist，不启动容器
 *
 * 安全考虑：
 * - 校验文件扩展名与大小
 * - lab_key 唯一性 + 字符白名单（防止目录穿越/注入）
 * - 落盘文件名用 时间戳-随机后缀 + .zip，不直接使用用户提供的文件名
 * - 落盘到配置目录的子目录，校验最终路径仍在存储根目录内
 */
@Service
class LabPackageService(
    private val labPackageRepository: LabPackageRepository,
    private val catalogQueryService: CatalogQueryService,
    @Value("\${seclab.lab-package.storage-dir:./lab-packages}") private val storageDir: String,
    @Value("\${seclab.lab-package.max-size-bytes:268435456}") private val maxFileSizeBytes: Long,
) {
    private val logger = LoggerFactory.getLogger(LabPackageService::class.java)
    private val labKeyPattern = Regex("^[a-z0-9][a-z0-9-]{0,63}$")
    private val timeFormatter = DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss", Locale.ROOT)

    data class UploadCommand(
        val labKey: String,
        val imageName: String?,
        val hostPort: Int?,
        val flag: String?,
        val moduleName: String?,
        val moduleDescription: String?,
        val moduleDifficulty: Int?,
        val moduleType: String?,
        val remark: String?,
    )

    @Transactional
    fun upload(file: MultipartFile, command: UploadCommand, uploaderId: Long): LabPackageDto {
        // 1. 基本校验
        validateLabKey(command.labKey)
        validateFile(file)
        if (labPackageRepository.existsByLabKey(command.labKey)) {
            throw ResponseStatusException(HttpStatus.CONFLICT, "实验标识已存在：${command.labKey}")
        }
        if (command.hostPort != null && (command.hostPort !in 1..65535)) {
            throw IllegalArgumentException("宿主端口必须在 1-65535 之间")
        }

        // 2. 落盘
        val storedPath = persistFile(file, command.labKey)

        // 3. 可选创建 module
        var moduleId: Int? = null
        val moduleName = command.moduleName?.trim()
        if (!moduleName.isNullOrEmpty()) {
            val moduleDescription = command.moduleDescription?.trim()?.takeIf { it.isNotEmpty() }
                ?: "教师上传实验包自动创建的实验模块：${command.labKey}"
            val created = try {
                catalogQueryService.createModule(
                    ModuleMutationRequest(
                        moduleName = moduleName,
                        moduleDescription = moduleDescription,
                        difficulty = command.moduleDifficulty,
                        type = command.moduleType?.trim()?.takeIf { it.isNotEmpty() },
                    ),
                )
            } catch (ex: Exception) {
                // 创建 module 失败时回滚已落盘的 zip，避免悬挂文件
                runCatching { Files.deleteIfExists(storedPath) }
                    .onFailure { logger.warn("删除已落盘 zip 失败 path={}", storedPath, it) }
                throw ex
            }
            moduleId = created.id
        }

        // 4. 登记到 lab_package
        val entity = labPackageRepository.save(
            LabPackageEntity(
                moduleId = moduleId,
                labKey = command.labKey,
                imageName = command.imageName?.trim()?.takeIf { it.isNotEmpty() },
                hostPort = command.hostPort,
                flag = command.flag?.trim()?.takeIf { it.isNotEmpty() },
                packagePath = storedPath.toString().replace('\\', '/'),
                originalFilename = file.originalFilename?.take(255),
                sizeBytes = file.size,
                uploadedBy = uploaderId,
                status = "UPLOADED",
                remark = command.remark?.trim()?.takeIf { it.isNotEmpty() },
            ),
        )
        logger.info(
            "lab_package uploaded: id={}, labKey={}, moduleId={}, size={}, uploader={}",
            entity.id, entity.labKey, entity.moduleId, entity.sizeBytes, uploaderId,
        )
        return toDto(entity)
    }

    fun listAll(): List<LabPackageDto> =
        labPackageRepository.findAll()
            .sortedByDescending { it.id }
            .map(::toDto)

    private fun validateLabKey(labKey: String) {
        val trimmed = labKey.trim()
        if (trimmed.isEmpty()) {
            throw IllegalArgumentException("实验标识不能为空")
        }
        if (!labKeyPattern.matches(trimmed)) {
            throw IllegalArgumentException("实验标识只能包含小写字母、数字和连字符，且以字母或数字开头（≤64 字符）")
        }
    }

    private fun validateFile(file: MultipartFile) {
        if (file.isEmpty) {
            throw IllegalArgumentException("上传文件不能为空")
        }
        if (file.size > maxFileSizeBytes) {
            throw IllegalArgumentException("上传文件大小超过限制（${maxFileSizeBytes / 1024 / 1024}MB）")
        }
        val original = file.originalFilename?.lowercase(Locale.ROOT) ?: ""
        if (!original.endsWith(".zip")) {
            throw IllegalArgumentException("仅支持上传 .zip 实验包")
        }
    }

    /**
     * 将上传的 zip 落盘到 {storageDir}/{labKey}/{时间戳}-{随机}.zip。
     * 返回相对 storageDir 的相对路径（用作 package_path）。
     */
    private fun persistFile(file: MultipartFile, labKey: String): Path {
        val root = Paths.get(storageDir).toAbsolutePath().normalize()
        Files.createDirectories(root)

        val safeLabKey = labKey.replace(FileSystems.getDefault().separator, "")
        val dir = root.resolve(safeLabKey).normalize()
        if (!dir.startsWith(root)) {
            // 理论上不会触发，因为 labKey 已被白名单校验
            throw ResponseStatusException(HttpStatus.BAD_REQUEST, "实验标识包含非法路径片段")
        }
        Files.createDirectories(dir)

        val timestamp = LocalDateTime.now().format(timeFormatter)
        val randomSuffix = (1..6).joinToString("") { (('a'..'z') + ('0'..'9')).random().toString() }
        val targetName = "${timestamp}-${randomSuffix}.zip"
        val target = dir.resolve(targetName).normalize()
        if (!target.startsWith(root)) {
            throw ResponseStatusException(HttpStatus.BAD_REQUEST, "目标落盘路径越界")
        }

        file.inputStream.use { input ->
            Files.copy(input, target, StandardCopyOption.REPLACE_EXISTING)
        }
        // 返回相对 storageDir 的路径，便于跨环境迁移
        return root.relativize(target)
    }

    private fun toDto(entity: LabPackageEntity): LabPackageDto =
        LabPackageDto(
            id = entity.id,
            moduleId = entity.moduleId,
            labKey = entity.labKey,
            imageName = entity.imageName,
            hostPort = entity.hostPort,
            flag = entity.flag,
            packagePath = entity.packagePath,
            originalFilename = entity.originalFilename,
            sizeBytes = entity.sizeBytes,
            uploadedBy = entity.uploadedBy,
            status = entity.status,
            remark = entity.remark,
            createdAt = entity.createdAt.toString(),
            updatedAt = entity.updatedAt.toString(),
        )
}
