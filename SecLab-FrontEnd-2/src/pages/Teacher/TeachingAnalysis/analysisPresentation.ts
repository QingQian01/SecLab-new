export type PresentationTone = 'neutral' | 'info' | 'success' | 'warning' | 'danger'

export function getRiskPresentation(level?: string | null): { label: string; tone: PresentationTone } {
  const normalized = String(level || '').toLowerCase()
  if (normalized === 'high') return { label: '高风险', tone: 'danger' }
  if (normalized === 'medium') return { label: '需关注', tone: 'warning' }
  if (normalized === 'low') return { label: '基本掌握', tone: 'success' }
  return { label: '样本不足', tone: 'neutral' }
}

export function getTimelineEventPresentation(
  eventType?: string | null,
  outcome?: string | null,
): { label: string; tone: PresentationTone } {
  const type = String(eventType || '').toUpperCase()
  const normalizedOutcome = String(outcome || '').toLowerCase()
  if (type === 'COMMAND' && normalizedOutcome === 'failed') return { label: '命令执行失败', tone: 'danger' }
  if (type === 'COMMAND' && normalizedOutcome === 'recovered') return { label: '重试后成功', tone: 'success' }
  if (type === 'COMMAND') return { label: '执行命令', tone: 'info' }
  if (type === 'ERROR') return { label: '遇到报错', tone: 'danger' }
  if (type === 'HINT') return { label: '请求提示', tone: 'warning' }
  if (type === 'AI') return { label: 'AI 协作', tone: 'info' }
  if (type === 'ATTEMPT') return { label: '提交作答', tone: normalizedOutcome === 'success' ? 'success' : 'warning' }
  if (type === 'SUCCESS') return { label: '实验验证成功', tone: 'success' }
  if (type === 'LAB_START') return { label: '开始安全实验', tone: 'info' }
  return { label: '学习事件', tone: 'neutral' }
}

export function normalizeEvidenceCount(value?: number | null): number {
  return Math.max(0, Number.isFinite(Number(value)) ? Number(value) : 0)
}
