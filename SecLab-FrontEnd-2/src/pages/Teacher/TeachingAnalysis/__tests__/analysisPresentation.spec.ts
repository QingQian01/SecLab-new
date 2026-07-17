import { describe, expect, it } from 'vitest'
import {
  findMatchingRiskItem,
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

  it('matches a class problem to its clickable risk details', () => {
    const matched = findMatchingRiskItem(
      {
        title: 'XSS 输出上下文判断不稳定',
        evidence: '11 名学生在文本、属性与脚本上下文中出现错误。',
        questionIds: ['question-xss-1'],
      },
      [
        {
          courseName: 'Web 安全',
          knowledgePointName: 'XSS 与 CSRF 攻击',
          knowledgeCategory: 'XSS',
          studentCount: 32,
          attemptedStudentCount: 11,
          incorrectStudentCount: 9,
          attemptedCount: 15,
          incorrectCount: 9,
          incorrectRate: 60,
          riskLevel: 'high',
          affectedStudents: [{ studentId: 261, studentName: '陈宇航' }],
          representativeQuestions: [{ generatedQuestionId: 'question-xss-1', title: 'XSS 输出编码判断' }],
        },
      ],
    )

    expect(matched?.knowledgePointName).toBe('XSS 与 CSRF 攻击')
    expect(matched?.affectedStudents[0].studentName).toBe('陈宇航')
  })
})
