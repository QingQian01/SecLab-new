import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { moduleRoute, readModuleCatalog } from '../moduleCatalog'

describe('student module catalog', () => {
  it('reads the real API payload without adding local catalog rows', () => {
    const result = readModuleCatalog({
      isSuccess: 1,
      status: 200,
      message: 'success',
      data: [{
        id: 1,
        name: 'SQL注入基础实验',
        description: '后端目录说明',
        difficulty: 3,
        type: 'Web安全',
        status: 'available',
        estimatedTime: '3-4小时',
        score: 65,
        courseId: 1,
      }],
    })

    expect(result).toHaveLength(1)
    expect(result[0].courseId).toBe(1)
    expect(result[0].description).toBe('后端目录说明')
  })

  it('routes the start action to the selected experiment', () => {
    expect(moduleRoute(7)).toBe('/user/module/7')
    expect(moduleRoute(7, 3)).toBe('/user/module/7?courseId=3')
  })

  it('submits experiment evidence with the persisted course id', () => {
    const source = readFileSync(new URL('../../Module/index.vue', import.meta.url), 'utf8')
    expect(source).not.toContain('course_id: null')
    expect(source).toContain('course_id: experiment.value.courseId ?? null')
  })

  it('does not start an SQL target for a module without a configured environment', () => {
    const source = readFileSync(new URL('../../Module/index.vue', import.meta.url), 'utf8')
    expect(source).toContain("return null;")
    expect(source).toContain('本实验暂未配置靶机环境')
    expect(source).not.toContain('默认使用SQL注入靶机')
  })

  it('offers an explicit course choice for multi-course modules', () => {
    const source = readFileSync(new URL('../index.vue', import.meta.url), 'utf8')
    expect(source).toContain('选择实验所属课程')
    expect(source).toContain('chooseModuleCourse(courseId)')
    expect(source).not.toContain('请从具体课程页面进入')
  })
})
