package dto

data class CourseSummaryDto(
    val id: Int,
    val name: String,
    val description: String,
    val difficulty: Int,
    val imageUrl: String,
    val type: String,
    val tags: List<String>,
    val status: String,
    val courseId: Int = id,
    val courseName: String = name,
    val courseDescription: String = description,
    val courseImage: String = imageUrl,
    val teacherName: String? = null,
    val category: String? = type,
    val createTime: String? = null,
    val createdBy: Long? = null,
    // 共享课程（createdBy == null）与本人创建的课程均可编辑；他人创建的课程不可编辑。
    // 这里默认 true，具体不可编辑场景由前端基于 createdBy 与当前用户判断。
    val creatorEditable: Boolean = true,
)

data class ModuleOverviewDto(
    val id: Int,
    val name: String,
    val description: String,
    val difficulty: Int,
    val type: String,
    val status: String,
    val estimatedTime: String,
    val score: Int,
    val prerequisites: List<Int> = emptyList(),
    val moduleId: Int = id,
    val moduleName: String = name,
    val moduleDescription: String = description,
    val courseId: Int? = null,
    val courseIds: List<Int> = emptyList(),
    val image: String? = null,
)

data class CourseMutationRequest(
    val courseName: String,
    val courseDescription: String,
    val difficulty: Int? = null,
    val imageUrl: String? = null,
    val teacherName: String? = null,
    val category: String? = null,
    val tags: List<String> = emptyList(),
    val status: String? = null,
)

data class ModuleMutationRequest(
    val moduleName: String,
    val moduleDescription: String,
    val difficulty: Int? = null,
    val type: String? = null,
    val image: String? = null,
)

/**
 * 实验包登记记录（教师上传 zip 后返回）。
 * 本期仅登记元数据，不触发 docker build / 启动。
 */
data class LabPackageDto(
    val id: Long,
    val moduleId: Int?,
    val labKey: String,
    val imageName: String?,
    val hostPort: Int?,
    val flag: String?,
    val packagePath: String,
    val originalFilename: String?,
    val sizeBytes: Long?,
    val uploadedBy: Long?,
    val status: String,
    val remark: String?,
    val createdAt: String?,
    val updatedAt: String?,
)
