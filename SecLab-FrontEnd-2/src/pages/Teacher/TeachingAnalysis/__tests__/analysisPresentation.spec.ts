import { describe, expect, it } from 'vitest'
import {
  getRiskPresentation,
  getTimelineEventPresentation,
  normalizeEvidenceCount,
} from '../analysisPresentation'

describe('teaching analysis presentation', () => {
  it('maps risk levels to stable teacher-facing labels', () => {
    expect(getRiskPresentation('high')).toEqual({ label: '高风险', tone: 'danger' })
    expect(getRiskPresentation('medium')).toEqual({ label: '需关注', tone: 'warning' })
    expect(getRiskPresentation('low')).toEqual({ label: '基本掌握', tone: 'success' })
  })

  it('describes failed and recovered commands as different learning outcomes', () => {
    expect(getTimelineEventPresentation('COMMAND', 'failed').label).toBe('命令执行失败')
    expect(getTimelineEventPresentation('COMMAND', 'recovered').label).toBe('重试后成功')
    expect(getTimelineEventPresentation('HINT').label).toBe('请求提示')
  })

  it('never presents a negative evidence count', () => {
    expect(normalizeEvidenceCount(-2)).toBe(0)
    expect(normalizeEvidenceCount(7)).toBe(7)
  })
})
