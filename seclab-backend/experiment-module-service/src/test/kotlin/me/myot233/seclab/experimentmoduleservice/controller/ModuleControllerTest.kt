package me.myot233.seclab.experimentmoduleservice.controller

import me.myot233.seclab.experimentmoduleservice.dto.ModuleOverviewDto
import me.myot233.seclab.experimentmoduleservice.service.CatalogAuthService
import me.myot233.seclab.experimentmoduleservice.service.CatalogQueryService
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test
import org.mockito.Mockito.mock
import org.mockito.Mockito.`when`

class ModuleControllerTest {
    @Test
    fun `student module detail returns persisted catalog metadata`() {
        val queryService = mock(CatalogQueryService::class.java)
        val authService = mock(CatalogAuthService::class.java)
        val module = ModuleOverviewDto(
            id = 1,
            name = "SQL注入基础实验",
            description = "真实实验目录说明",
            difficulty = 3,
            type = "Web安全",
            status = "available",
            estimatedTime = "3-4小时",
            score = 65,
            courseId = 7,
            courseIds = listOf(7),
        )
        `when`(queryService.getModule(1, 7)).thenReturn(module)

        val response = ModuleController(queryService, authService).getModule(1, 7)

        assertEquals(1, response.data?.id)
        assertEquals(7, response.data?.courseId)
        assertEquals("SQL注入基础实验", response.data?.name)
    }
}
