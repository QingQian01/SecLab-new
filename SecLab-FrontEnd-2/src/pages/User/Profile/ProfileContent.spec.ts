import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

const source = readFileSync(new URL('./index.vue', import.meta.url), 'utf8')

describe('student profile content', () => {
  it('does not expose development-stage or implementation commentary', () => {
    expect(source).not.toContain('（后续增强）')
    expect(source).not.toContain('这一区域仍来自训练诊断链路')
    expect(source).not.toContain('主推荐来源已经统一')
    expect(source).not.toContain('正在同步数据库画像')
    expect(source).not.toContain('训练提交主链')
    expect(source).not.toContain('Session {{ activeTrainingSessionId }}')
  })
})
