import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

import {
  buildLabHintRequest,
  sanitizeAssistantAnswer,
  resolveLabChatInputs,
  shouldShowAgentToolCalls,
  summarizeToolObservation,
  visibleAgentToolCalls,
} from './floatingChatHint'

const chatSource = readFileSync(new URL('./FloatingChat.vue', import.meta.url), 'utf8')
const buttonSource = readFileSync(new URL('./FloatingChatButton.vue', import.meta.url), 'utf8')

describe('floating lab hint request', () => {
  it('keeps machine context out of the visible student message', () => {
    const request = buildLabHintRequest({
      moduleId: 1,
      moduleName: 'SQL 注入',
      experimentId: 1,
      experimentTitle: 'SQL注入基础实验',
      labSessionId: 'lab-1784808524320',
      containerName: 'sqli-lab-web-1',
      targetUrl: 'http://localhost:8091/index.php',
      userId: 295,
      classId: 12,
      courseId: 1,
    })

    expect(request.visibleMessage).toBe('请分析我当前的实验进展，并给出下一步提示。')
    expect(request.visibleMessage).not.toContain('容器名')
    expect(request.visibleMessage).not.toContain('用户ID')
    expect(request.inputs.hint_request).toBe(true)
    expect(request.inputs.lab_context.containerName).toBe('sqli-lab-web-1')
  })

  it('does not expose model reasoning in the student chat', () => {
    expect(chatSource).not.toContain('思考过程')
    expect(chatSource).not.toContain('showThinking')
    expect(chatSource).not.toContain('completeThinking')
  })

  it('does not expose raw tool errors or HTML responses', () => {
    expect(
      summarizeToolObservation(
        'tool invoke error: Request failed with status code 404 and <!DOCTYPE html>',
      ),
    ).toEqual({
      failed: true,
      text: '暂时无法读取实验数据',
    })
    expect(summarizeToolObservation('{"success":true,"logs":"..."}')).toEqual({
      failed: false,
      text: '实验数据读取完成',
    })
  })

  it('does not render redundant Dify tool calls for a locally enriched hint', () => {
    expect(shouldShowAgentToolCalls({ hint_request: true })).toBe(false)
    expect(shouldShowAgentToolCalls({ lab_runtime_context: true })).toBe(false)
    expect(shouldShowAgentToolCalls({})).toBe(true)
  })

  it('adds local runtime context to ordinary messages during a lab', () => {
    const context = {
      containerName: 'sqli-lab-web-1',
      experimentTitle: 'SQL注入基础实验',
    }

    expect(resolveLabChatInputs({}, context)).toEqual({
      lab_runtime_context: true,
      lab_context: context,
    })
    expect(resolveLabChatInputs({ hint_request: true }, context)).toEqual({
      hint_request: true,
    })
    expect(resolveLabChatInputs({}, {})).toEqual({})
  })

  it('hides failed tool cards restored from chat history', () => {
    expect(
      visibleAgentToolCalls([
        {
          id: 'failed',
          status: 'done',
          observation: 'tool invoke error: Request failed with status code 404',
        },
        {
          id: 'success',
          status: 'done',
          observation: '{"success":true}',
        },
      ]).map((toolCall) => toolCall.id),
    ).toEqual(['success'])
  })

  it('removes completed and streaming reasoning blocks from the answer', () => {
    expect(
      sanitizeAssistantAnswer('<think>internal reasoning</think>给学生的正式提示'),
    ).toBe('给学生的正式提示')
    expect(sanitizeAssistantAnswer('<think>still reasoning')).toBe('')
    expect(sanitizeAssistantAnswer('正常回答<thi')).toBe('正常回答')
  })

  it('asks before sending a timed hint', () => {
    expect(buttonSource).not.toContain('窗口开着就直接在聊天里发提示')
    expect(buttonSource).not.toMatch(/else\s*\{\s*pendingHint\.value\s*=\s*true/)
  })
})
