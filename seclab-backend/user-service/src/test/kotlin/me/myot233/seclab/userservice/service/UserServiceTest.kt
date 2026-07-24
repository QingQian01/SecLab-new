package me.myot233.seclab.userservice.service

import me.myot233.seclab.userservice.dto.RegisterRequest
import me.myot233.seclab.userservice.entity.SchoolClassEntity
import me.myot233.seclab.userservice.entity.TeachingClassEntity
import me.myot233.seclab.userservice.entity.TeachingClassStatus
import me.myot233.seclab.userservice.entity.TeachingClassStudentEntity
import me.myot233.seclab.userservice.entity.UserEntity
import me.myot233.seclab.userservice.repository.SchoolClassRepository
import me.myot233.seclab.userservice.repository.TeachingClassRepository
import me.myot233.seclab.userservice.repository.TeachingClassStudentRepository
import me.myot233.seclab.userservice.repository.UserRepository
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test
import org.mockito.ArgumentCaptor
import org.mockito.Mockito.any
import org.mockito.Mockito.mock
import org.mockito.Mockito.never
import org.mockito.Mockito.verify
import org.mockito.Mockito.`when`
import java.util.Optional

class UserServiceTest {
    private val userRepository = mock(UserRepository::class.java)
    private val classRepository = mock(SchoolClassRepository::class.java)
    private val teachingClassRepository = mock(TeachingClassRepository::class.java)
    private val teachingClassStudentRepository = mock(TeachingClassStudentRepository::class.java)
    private val passwordService = mock(PasswordService::class.java)
    private val jwtTokenService = mock(JwtTokenService::class.java)
    private val service = UserService(
        userRepository,
        classRepository,
        teachingClassRepository,
        teachingClassStudentRepository,
        passwordService,
        jwtTokenService,
    )

    @Test
    fun `registration joins every active teaching class with the same administrative class name`() {
        val schoolClass = SchoolClassEntity(classId = 12, className = "网安232班")
        val teachingClass = TeachingClassEntity(
            teachingClassId = 101,
            className = "网络安全232班",
            status = TeachingClassStatus.ACTIVE,
        )
        `when`(userRepository.existsByUserStudentNumber("QA26072201")).thenReturn(false)
        `when`(classRepository.findById(12)).thenReturn(Optional.of(schoolClass))
        `when`(passwordService.encode("Seclab123!")).thenReturn("encoded")
        `when`(userRepository.save(any(UserEntity::class.java))).thenAnswer { invocation ->
            invocation.getArgument<UserEntity>(0).also { it.userId = 291 }
        }
        `when`(teachingClassRepository.findAllByStatus(TeachingClassStatus.ACTIVE))
            .thenReturn(listOf(teachingClass))
        `when`(teachingClassStudentRepository.existsByTeachingClassIdAndStudentId(101, 291)).thenReturn(false)

        service.register(registerRequest())

        val membership = ArgumentCaptor.forClass(TeachingClassStudentEntity::class.java)
        verify(teachingClassStudentRepository).save(membership.capture())
        assertEquals(101, membership.value.teachingClassId)
        assertEquals(291, membership.value.studentId)
        assertEquals("MANUAL", membership.value.source)
    }

    @Test
    fun `registration does not duplicate an existing teaching class membership`() {
        val schoolClass = SchoolClassEntity(classId = 12, className = "网安232班")
        val teachingClass = TeachingClassEntity(
            teachingClassId = 101,
            className = "网络安全232班",
            status = TeachingClassStatus.ACTIVE,
        )
        `when`(userRepository.existsByUserStudentNumber("QA26072201")).thenReturn(false)
        `when`(classRepository.findById(12)).thenReturn(Optional.of(schoolClass))
        `when`(passwordService.encode("Seclab123!")).thenReturn("encoded")
        `when`(userRepository.save(any(UserEntity::class.java))).thenAnswer { invocation ->
            invocation.getArgument<UserEntity>(0).also { it.userId = 291 }
        }
        `when`(teachingClassRepository.findAllByStatus(TeachingClassStatus.ACTIVE))
            .thenReturn(listOf(teachingClass))
        `when`(teachingClassStudentRepository.existsByTeachingClassIdAndStudentId(101, 291)).thenReturn(true)

        service.register(registerRequest())

        verify(teachingClassStudentRepository, never()).save(any(TeachingClassStudentEntity::class.java))
    }

    private fun registerRequest() = RegisterRequest().apply {
        userStudentNumber = "QA26072201"
        userPassword = "Seclab123!"
        userName = "回归学生"
        userEmail = "qa26072201@example.com"
        classId = 12
    }
}
