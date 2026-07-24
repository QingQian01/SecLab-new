import { afterEach, describe, expect, it, vi } from 'vitest'
import { parseDifySseLine, streamAiChat } from './chatClient'

describe('chatClient', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('extracts answer chunks and conversation id from Dify events', () => {
    expect(parseDifySseLine('data: {"event":"message","answer":"你好","conversation_id":"conv-1"}')).toEqual({
      answer: '你好',
      conversationId: 'conv-1',
      error: '',
    })
  })

  it('calls the local AI service without a browser-side API key', async () => {
    const encoder = new TextEncoder()
    const reader = {
      read: vi.fn()
        .mockResolvedValueOnce({
          done: false,
          value: encoder.encode('data: {"event":"message","answer":"你好","conversation_id":"conv-1"}\n\n'),
        })
        .mockResolvedValueOnce({ done: true, value: undefined }),
    }
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      body: { getReader: () => reader },
    })
    vi.stubGlobal('fetch', fetchMock)
    const chunks: string[] = []

    const result = await streamAiChat({
      query: '你好',
      user: 'student-294',
      onAnswer: (chunk) => chunks.push(chunk),
    })

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8010/api/chat',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      query: '你好',
      conversation_id: '',
      user: 'student-294',
      inputs: {},
    })
    expect(chunks).toEqual(['你好'])
    expect(result.conversationId).toBe('conv-1')
  })
})
