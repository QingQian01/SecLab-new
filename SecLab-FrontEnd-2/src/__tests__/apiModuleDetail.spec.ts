import { beforeEach, describe, expect, it, vi } from 'vitest'
import axios from 'axios'
import { getModuleDetail } from '../api'

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
  },
}))

describe('getModuleDetail', () => {
  beforeEach(() => vi.clearAllMocks())

  it('loads module metadata from the experiment-module service', async () => {
    vi.mocked(axios.get).mockResolvedValue({
      status: 200,
      data: {
        status: 200,
        message: 'success',
        data: {
          id: 1,
          name: 'SQL注入基础实验',
          description: '真实目录说明',
          difficulty: 3,
          courseId: 1,
          courseIds: [1],
        },
      },
    })

    const result = await getModuleDetail(1)

    expect(axios.get).toHaveBeenCalledWith('http://localhost:8084/stu/module/1', undefined)
    expect(result.isSuccess).toBe(1)
    expect(result.data.name).toBe('SQL注入基础实验')
    expect(result.data.courseId).toBe(1)
    expect(result.data.taskPoints.length).toBeGreaterThan(0)
  })

  it('passes the selected course through for a multi-course module', async () => {
    vi.mocked(axios.get).mockResolvedValue({
      status: 200,
      data: {
        status: 200,
        message: 'success',
        data: {
          id: 2,
          name: '跨课程实验',
          description: '真实目录说明',
          difficulty: 2,
          courseId: 7,
          courseIds: [3, 7],
        },
      },
    })

    const result = await getModuleDetail(2, 7)

    expect(axios.get).toHaveBeenCalledWith(
      'http://localhost:8084/stu/module/2',
      { params: { courseId: 7 } },
    )
    expect(result.data.courseId).toBe(7)
  })

  it('does not attach SQL questions to an unknown persisted module', async () => {
    vi.mocked(axios.get).mockResolvedValue({
      status: 200,
      data: {
        status: 200,
        message: 'success',
        data: {
          id: 99,
          name: '教师新建实验',
          description: '教师录入的说明',
          difficulty: 2,
          courseId: 7,
          courseIds: [7],
        },
      },
    })

    const result = await getModuleDetail(99, 7)

    expect(result.data.name).toBe('教师新建实验')
    expect(result.data.taskPoints).toEqual([])
    expect(result.data.targetMachine).toBeUndefined()
  })
})
