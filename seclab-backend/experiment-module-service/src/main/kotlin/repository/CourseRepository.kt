package repository

import entity.CourseEntity
import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.data.jpa.repository.Query

interface CourseRepository : JpaRepository<CourseEntity, Int> {
    @Query("select coalesce(max(c.id), 0) from CourseEntity c")
    fun findMaxId(): Int
}
