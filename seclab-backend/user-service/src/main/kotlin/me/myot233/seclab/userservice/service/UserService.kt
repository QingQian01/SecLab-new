package me.myot233.seclab.userservice.service

import me.myot233.seclab.userservice.dto.AdminUserCreateRequest
import me.myot233.seclab.userservice.dto.AdminUserListData
import me.myot233.seclab.userservice.dto.AdminUserListItemResponse
import me.myot233.seclab.userservice.dto.AdminUserUpdateRequest
import me.myot233.seclab.userservice.dto.LoginData
import me.myot233.seclab.userservice.dto.LoginRequest
import me.myot233.seclab.userservice.dto.LoginResponse
import me.myot233.seclab.userservice.dto.RegisterRequest
import me.myot233.seclab.userservice.dto.UserProfileResponse
import me.myot233.seclab.userservice.dto.UserUpdateRequest
import me.myot233.seclab.userservice.entity.SchoolClassEntity
import me.myot233.seclab.userservice.entity.TeachingClassStatus
import me.myot233.seclab.userservice.entity.TeachingClassStudentEntity
import me.myot233.seclab.userservice.entity.UserEntity
import me.myot233.seclab.userservice.entity.UserRole
import me.myot233.seclab.userservice.exception.ApiException
import me.myot233.seclab.userservice.repository.SchoolClassRepository
import me.myot233.seclab.userservice.repository.TeachingClassRepository
import me.myot233.seclab.userservice.repository.TeachingClassStudentRepository
import me.myot233.seclab.userservice.repository.UserRepository
import org.springframework.data.domain.PageRequest
import org.springframework.data.domain.Sort
import org.springframework.http.HttpStatus
import org.springframework.stereotype.Service
import org.springframework.transaction.annotation.Transactional
import java.time.format.DateTimeFormatter

@Service
class UserService(
    private val userRepository: UserRepository,
    private val classRepository: SchoolClassRepository,
    private val teachingClassRepository: TeachingClassRepository,
    private val teachingClassStudentRepository: TeachingClassStudentRepository,
    private val passwordService: PasswordService,
    private val jwtTokenService: JwtTokenService,
) {
    @Transactional
    fun login(request: LoginRequest): LoginResponse {
        val studentNumber = normalizeRequired(request.userStudentNumber, "Student number")
        val password = normalizeRequired(request.userPassword, "Password")
        val user = userRepository.findByUserStudentNumber(studentNumber)
            ?: throw ApiException(401, "Student number or password is incorrect", HttpStatus.UNAUTHORIZED)

        requireActiveUser(user)

        val checkResult = passwordService.verify(password, user.userPassword)
        if (!checkResult.matched) {
            throw ApiException(401, "Student number or password is incorrect", HttpStatus.UNAUTHORIZED)
        }

        if (checkResult.shouldUpgrade) {
            user.userPassword = passwordService.encode(password)
        }

        val token = jwtTokenService.generate(user)
        return LoginResponse(loginData = user.toLoginData(token))
    }

    @Transactional
    fun register(request: RegisterRequest) {
        val studentNumber = normalizeRequired(request.userStudentNumber, "Student number")
        val password = normalizeRequired(request.userPassword, "Password")
        val userName = normalizeRequired(request.userName, "Name")
        val userEmail = normalizeRequiredEmail(request.userEmail)

        if (studentNumber.length > 13) {
            throw ApiException(400, "Student number must be 13 characters or fewer")
        }
        if (password.length < 6) {
            throw ApiException(400, "Password must be at least 6 characters long")
        }
        if (password.length > 72) {
            throw ApiException(400, "Password must be 72 characters or fewer")
        }
        if (userRepository.existsByUserStudentNumber(studentNumber)) {
            throw ApiException(400, "Student number already exists")
        }

        val user = UserEntity(
            userStudentNumber = studentNumber,
            userPassword = passwordService.encode(password),
            userTel = normalizePhone(request.userTel),
            userImage = normalizeImage(request.userImage),
            userName = userName,
            userAcademy = normalizeOptional(request.userAcademy),
            userEmail = userEmail,
            userGender = normalizeGender(request.userGender),
            classInfo = resolveClass(request.classId, request.userClass),
            isAdmin = false,
            userRole = UserRole.STUDENT,
            isDeleted = 0,
        )
        val saved = userRepository.save(user)
        joinMatchingTeachingClasses(saved)
    }

    private fun joinMatchingTeachingClasses(user: UserEntity) {
        val studentId = user.userId ?: return
        val administrativeClass = user.classInfo?.className?.trim()?.takeIf { it.isNotEmpty() } ?: return
        teachingClassRepository
            .findAllByStatus(TeachingClassStatus.ACTIVE)
            .filter { canonicalClassName(it.className) == canonicalClassName(administrativeClass) }
            .filter { it.teachingClassId != null }
            .forEach { teachingClass ->
                val teachingClassId = teachingClass.teachingClassId ?: return@forEach
                if (!teachingClassStudentRepository.existsByTeachingClassIdAndStudentId(teachingClassId, studentId)) {
                    teachingClassStudentRepository.save(
                        TeachingClassStudentEntity(
                            teachingClassId = teachingClassId,
                            studentId = studentId,
                            source = "MANUAL",
                        ),
                    )
                }
            }
    }

    private fun canonicalClassName(value: String): String =
        value
            .trim()
            .lowercase()
            .replace(Regex("\\s+"), "")
            .replace("网络安全", "网安")
            .removeSuffix("班")

    @Transactional(readOnly = true)
    fun getProfile(token: String?): UserProfileResponse {
        val payload = jwtTokenService.parse(token)
        val user = findUserOrThrow(payload.userId)
        requireActiveUser(user)
        return user.toProfileResponse()
    }

    @Transactional
    fun updateProfile(token: String?, request: UserUpdateRequest): UserProfileResponse {
        val payload = jwtTokenService.parse(token)
        val user = findUserOrThrow(payload.userId)
        requireActiveUser(user)

        normalizeOptional(request.userName)?.let { user.userName = it }
        normalizeOptional(request.userTel)?.let { user.userTel = normalizePhone(it) }
        normalizeOptional(request.userAcademy)?.let { user.userAcademy = it }
        normalizeOptional(request.userEmail)?.let { user.userEmail = normalizeRequiredEmail(it) }
        request.userGender?.let { user.userGender = normalizeGender(it) }
        request.userImage?.let { user.userImage = normalizeImage(it) }

        if (request.classId != null || !request.userClass.isNullOrBlank()) {
            user.classInfo = resolveClass(request.classId, request.userClass)
        }

        return user.toProfileResponse()
    }

    @Transactional(readOnly = true)
    fun listStudentsForAdmin(
        token: String?,
        page: Int,
        pageSize: Int,
        keyword: String?,
        academy: String?,
        className: String?,
        classId: Long?,
        status: String?,
        gender: Int?,
    ): AdminUserListData {
        val currentUser = requireAdminUser(token)
        requireActiveUser(currentUser)

        if (page < 1) {
            throw ApiException(400, "page must be greater than or equal to 1")
        }
        if (pageSize !in 1..200) {
            throw ApiException(400, "pageSize must be between 1 and 200")
        }

        val pageable = PageRequest.of(
            page - 1,
            pageSize,
            Sort.by(
                Sort.Order.desc("createTime"),
                Sort.Order.desc("userId"),
            ),
        )

        val students = userRepository.searchStudentsForAdmin(
            keyword = normalizeOptional(keyword),
            academy = normalizeOptional(academy),
            className = normalizeOptional(className),
            classId = classId?.takeIf { it > 0 },
            deletedFlag = normalizeStatusFilter(status),
            gender = normalizeGenderFilter(gender),
            pageable = pageable,
        )

        return AdminUserListData(
            list = students.content.map { it.toAdminUserListItemResponse() },
            total = students.totalElements,
            page = page,
            pageSize = pageSize,
        )
    }

    @Transactional
    fun createStudentForAdmin(token: String?, request: AdminUserCreateRequest): AdminUserListItemResponse {
        val currentUser = requireAdminUser(token)
        requireActiveUser(currentUser)

        val studentNumber = normalizeRequired(request.userStudentNumber, "Student number")
        val userName = normalizeRequired(request.userName, "Name")
        val userEmail = normalizeEmail(request.userEmail)
        val userTel = normalizePhone(request.userTel)

        if (studentNumber.length > 13) {
            throw ApiException(400, "Student number must be 13 characters or fewer")
        }
        if (userRepository.existsByUserStudentNumber(studentNumber)) {
            throw ApiException(400, "Student number already exists")
        }

        val saved = userRepository.save(
            UserEntity(
                userStudentNumber = studentNumber,
                userPassword = passwordService.encode(DEFAULT_RESET_PASSWORD),
                userTel = userTel,
                userImage = null,
                userName = userName,
                userAcademy = normalizeOptional(request.userAcademy),
                userEmail = userEmail,
                userGender = normalizeGender(request.userGender),
                classInfo = resolveClass(request.classId, request.userClass),
                isAdmin = false,
                userRole = UserRole.STUDENT,
                isDeleted = 0,
            ),
        )

        return saved.toAdminUserListItemResponse()
    }

    @Transactional
    fun updateStudentForAdmin(token: String?, userId: Long, request: AdminUserUpdateRequest): AdminUserListItemResponse {
        val currentUser = requireAdminUser(token)
        requireActiveUser(currentUser)

        val user = requireManageableStudent(userId)
        user.userName = normalizeRequired(request.userName, "Name")
        user.userTel = normalizePhone(request.userTel)
        user.userAcademy = normalizeOptional(request.userAcademy)
        user.userEmail = normalizeEmail(request.userEmail)
        user.userGender = normalizeGender(request.userGender)

        if (request.classId != null || !request.userClass.isNullOrBlank()) {
            user.classInfo = resolveClass(request.classId, request.userClass)
        }

        return user.toAdminUserListItemResponse()
    }

    @Transactional
    fun deleteStudentForAdmin(token: String?, userId: Long) {
        val currentUser = requireAdminUser(token)
        requireActiveUser(currentUser)

        val user = requireManageableStudent(userId)
        user.isDeleted = 1
    }

    @Transactional
    fun resetStudentPasswordForAdmin(token: String?, userId: Long) {
        val currentUser = requireAdminUser(token)
        requireActiveUser(currentUser)

        val user = requireManageableStudent(userId)
        user.userPassword = passwordService.encode(DEFAULT_RESET_PASSWORD)
    }

    private fun resolveClass(classId: Long?, className: String?): SchoolClassEntity {
        if (classId != null && classId > 0) {
            val existingClass = classRepository.findById(classId).orElse(null)
            if (existingClass != null) {
                return existingClass
            }
        }

        val normalizedClassName = normalizeOptional(className) ?: DEFAULT_CLASS_NAME
        return classRepository.findFirstByClassName(normalizedClassName)
            ?: classRepository.save(
                SchoolClassEntity(
                    className = normalizedClassName,
                    classDetail = DEFAULT_CLASS_DETAIL,
                    isEnd = 0,
                ),
            )
    }

    private fun normalizeRequired(value: String?, fieldName: String): String =
        normalizeOptional(value) ?: throw ApiException(400, "$fieldName is required")

    private fun normalizeRequiredEmail(value: String?): String =
        normalizeEmail(value) ?: throw ApiException(400, "Email is required")

    private fun normalizeOptional(value: String?): String? =
        value?.trim()?.takeIf { it.isNotEmpty() }

    private fun normalizeImage(value: String?): String? {
        val normalized = normalizeOptional(value) ?: return null
        if (normalized.length > 255) {
            throw ApiException(400, "Avatar URL must be 255 characters or fewer")
        }
        return normalized
    }

    private fun normalizeStatusFilter(status: String?): Int? {
        val normalized = normalizeOptional(status)?.lowercase() ?: return 0
        return when (normalized) {
            "all" -> null
            "active", "enabled", "normal" -> 0
            "disabled", "inactive", "locked" -> 1
            else -> throw ApiException(400, "status only supports active, disabled, or all")
        }
    }

    private fun normalizeGenderFilter(gender: Int?): Int? {
        if (gender == null) {
            return null
        }
        if (gender !in setOf(0, 1, 2)) {
            throw ApiException(400, "Gender only supports 0, 1, or 2")
        }
        return gender
    }

    private fun normalizePhone(value: String?): String? {
        val normalized = normalizeOptional(value) ?: return null
        if (normalized.length > 11 || normalized.any { !it.isDigit() }) {
            throw ApiException(400, "Phone number must contain 11 digits or fewer")
        }
        return normalized
    }

    private fun normalizeEmail(value: String?): String? {
        val normalized = normalizeOptional(value) ?: return null
        if (!EMAIL_REGEX.matches(normalized)) {
            throw ApiException(400, "Email format is invalid")
        }
        return normalized
    }

    private fun normalizeGender(value: Int?): Int {
        val normalized = value ?: 2
        if (normalized !in setOf(0, 1, 2)) {
            throw ApiException(400, "Gender only supports 0, 1, or 2")
        }
        return normalized
    }

    private fun requireAdminUser(token: String?): UserEntity {
        val payload = jwtTokenService.parse(token)
        val user = findUserOrThrow(payload.userId)
        requireActiveUser(user)
        if (user.isAdmin != true) {
            throw ApiException(403, "Only admin accounts can access this endpoint", HttpStatus.FORBIDDEN)
        }
        return user
    }

    private fun requireManageableStudent(userId: Long): UserEntity {
        val user = findUserOrThrow(userId)
        if (user.isAdmin == true) {
            throw ApiException(403, "Admin accounts cannot be managed from the student list", HttpStatus.FORBIDDEN)
        }
        if (user.isDeleted == 1) {
            throw ApiException(400, "The target account is already disabled", HttpStatus.BAD_REQUEST)
        }
        return user
    }

    private fun findUserOrThrow(userId: Long): UserEntity =
        userRepository.findById(userId).orElseThrow {
            ApiException(404, "User does not exist", HttpStatus.NOT_FOUND)
        }

    private fun requireActiveUser(user: UserEntity) {
        if (user.isDeleted == 1) {
            throw ApiException(403, "This account is disabled", HttpStatus.FORBIDDEN)
        }
    }

    private fun resolveUserRole(user: UserEntity): String {
        return user.userRole.name.lowercase()
    }

    private companion object {
        const val DEFAULT_RESET_PASSWORD = "123456"
        const val DEFAULT_CLASS_NAME = "Cyber Security 232"
        const val DEFAULT_CLASS_DETAIL = "Created automatically by user-service"
        val EMAIL_REGEX = Regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$")
    }

    private fun UserEntity.toLoginData(token: String): LoginData =
        LoginData(
            userId = userId ?: 0,
            userStudentNumber = userStudentNumber,
            userImage = userImage,
            userName = userName,
            classId = classInfo?.classId,
            className = classInfo?.className,
            role = resolveUserRole(this),
            status = if (isDeleted == 1) "disabled" else "active",
            token = token,
        )

    private fun UserEntity.toProfileResponse(): UserProfileResponse =
        UserProfileResponse(
            userId = userId ?: 0,
            userStudentNumber = userStudentNumber,
            userTel = userTel,
            userImage = userImage,
            userName = userName,
            userAcademy = userAcademy,
            userClass = classInfo?.className,
            userEmail = userEmail,
            userGender = userGender,
            classId = classInfo?.classId,
            createTime = createTime?.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME),
            role = resolveUserRole(this),
            status = if (isDeleted == 1) "disabled" else "active",
        )

    private fun UserEntity.toAdminUserListItemResponse(): AdminUserListItemResponse =
        AdminUserListItemResponse(
            userId = userId ?: 0,
            userStudentNumber = userStudentNumber,
            userName = userName,
            userAcademy = userAcademy,
            userClass = classInfo?.className,
            userEmail = userEmail,
            userTel = userTel,
            userGender = userGender,
            classId = classInfo?.classId,
            createTime = createTime?.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME),
            status = if (isDeleted == 1) "disabled" else "active",
        )
}
