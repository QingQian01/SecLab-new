package controller

import dto.ApiResponse
import dto.LabPackageDto
import service.CatalogAuthService
import service.LabPackageService
import org.springframework.web.bind.annotation.GetMapping
import org.springframework.web.bind.annotation.PostMapping
import org.springframework.web.bind.annotation.RequestHeader
import org.springframework.web.bind.annotation.RequestMapping
import org.springframework.web.bind.annotation.RequestParam
import org.springframework.web.bind.annotation.RequestPart
import org.springframework.web.bind.annotation.RestController
import org.springframework.web.multipart.MultipartFile

/**
 * 教师上传实验包（zip）接口。
 *
 * 本期范围：仅上传 + 元数据登记，不做 docker build / 启动。
 *
 * 路由：前端通过 EXPERIMENT_MODULE_BASE_URL（默认 http://localhost:8084）直接访问，
 * 不经 gateway，因此无需在 gateway 配置路由。
 */
@RestController
@RequestMapping("/lab-package")
class LabPackageController(
    private val labPackageService: LabPackageService,
    private val catalogAuthService: CatalogAuthService,
) {
    @PostMapping("/upload")
    fun upload(
        @RequestPart("file") file: MultipartFile,
        @RequestParam("labKey") labKey: String,
        @RequestParam("imageName", required = false) imageName: String?,
        @RequestParam("hostPort", required = false) hostPort: Int?,
        @RequestParam("flag", required = false) flag: String?,
        @RequestParam("moduleName", required = false) moduleName: String?,
        @RequestParam("moduleDescription", required = false) moduleDescription: String?,
        @RequestParam("moduleDifficulty", required = false) moduleDifficulty: Int?,
        @RequestParam("moduleType", required = false) moduleType: String?,
        @RequestParam("remark", required = false) remark: String?,
        @RequestHeader(name = "Authorization", required = false) authorization: String?,
    ): ApiResponse<LabPackageDto> {
        val currentUser = catalogAuthService.requireTeacherOrAdmin(authorization)
        val dto = labPackageService.upload(
            file = file,
            command = LabPackageService.UploadCommand(
                labKey = labKey,
                imageName = imageName,
                hostPort = hostPort,
                flag = flag,
                moduleName = moduleName,
                moduleDescription = moduleDescription,
                moduleDifficulty = moduleDifficulty,
                moduleType = moduleType,
                remark = remark,
            ),
            uploaderId = currentUser.userId,
        )
        return ApiResponse.success(dto, "实验包上传成功")
    }

    @GetMapping
    fun list(): ApiResponse<List<LabPackageDto>> =
        ApiResponse.success(labPackageService.listAll())
}
