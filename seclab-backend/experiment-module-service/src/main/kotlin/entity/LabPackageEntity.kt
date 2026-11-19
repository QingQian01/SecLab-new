package entity

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.GeneratedValue
import jakarta.persistence.GenerationType
import jakarta.persistence.Id
import jakarta.persistence.Table
import java.time.LocalDateTime

@Entity
@Table(name = "lab_package")
class LabPackageEntity(
    @field:Id
    @field:GeneratedValue(strategy = GenerationType.IDENTITY)
    @field:Column(name = "id")
    val id: Long = 0L,
    @field:Column(name = "module_id")
    val moduleId: Int? = null,
    @field:Column(name = "lab_key", nullable = false)
    val labKey: String = "",
    @field:Column(name = "image_name")
    val imageName: String? = null,
    @field:Column(name = "host_port")
    val hostPort: Int? = null,
    @field:Column(name = "flag")
    val flag: String? = null,
    @field:Column(name = "package_path", nullable = false)
    val packagePath: String = "",
    @field:Column(name = "original_filename")
    val originalFilename: String? = null,
    @field:Column(name = "size_bytes")
    val sizeBytes: Long? = null,
    @field:Column(name = "uploaded_by")
    val uploadedBy: Long? = null,
    @field:Column(name = "status", nullable = false)
    val status: String = "UPLOADED",
    @field:Column(name = "remark")
    val remark: String? = null,
    @field:Column(name = "created_at", nullable = false, updatable = false)
    val createdAt: LocalDateTime = LocalDateTime.now(),
    @field:Column(name = "updated_at", nullable = false)
    val updatedAt: LocalDateTime = LocalDateTime.now(),
)
