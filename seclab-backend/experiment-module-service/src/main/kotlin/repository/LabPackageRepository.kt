package repository

import entity.LabPackageEntity
import org.springframework.data.jpa.repository.JpaRepository

interface LabPackageRepository : JpaRepository<LabPackageEntity, Long> {
    fun existsByLabKey(labKey: String): Boolean
}
