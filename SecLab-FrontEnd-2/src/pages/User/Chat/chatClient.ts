const AGENT_BASE_URL = import.meta.env.VITE_AGENT_BASE_URL || 'http://localhost:8010'

type ParsedDifyEvent = {
  answer: string
  conversationId: string
  error: string
}

type StreamAiChatOptions = {
  query: string
  conversationId?: string
  user?: string
  inputs?: Record<string, unknown>
  onAnswer: (chunk: string) => void
}

export function parseDifySseLine(line: string): ParsedDifyEvent | null {
  const trimmed = line.trim()
  if (!trimmed.startsWith('data:')) return null

  const payload = trimmed.slice(5).trim()
  if (!payload || payload === '[DONE]') return null

  try {
    const event = JSON.parse(payload) as Record<string, unknown>
    return {
      answer: typeof event.answer === 'string' ? event.answer : '',
      conversationId: typeof event.conversation_id === 'string' ? event.conversation_id : '',
      error: typeof event.error === 'string' ? event.error : '',
    }
  } catch {
    return null
  }
}

export async function streamAiChat(options: StreamAiChatOptions): Promise<{ conversationId: string }> {
  const response = await fetch(`${AGENT_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: options.query,
      conversation_id: options.conversationId || '',
      user: options.user || 'student',
      inputs: options.inputs || {},
    }),
  })

  if (!response.ok || !response.body) {
    throw new Error('AI 服务暂时不可用')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let conversationId = options.conversationId || ''

  const consumeLine = (line: string) => {
    const event = parseDifySseLine(line)
    if (!event) return
    if (event.error) throw new Error(event.error)
    if (event.conversationId) conversationId = event.conversationId
    if (event.answer) options.onAnswer(event.answer)
  }

  while (true) {
    const { done, value } = await reader.read()
    buffer += decoder.decode(value, { stream: !done })
    const lines = buffer.split(/\r?\n/)
    buffer = lines.pop() || ''
    lines.forEach(consumeLine)
    if (done) break
  }

  if (buffer.trim()) consumeLine(buffer)
  return { conversationId }
}
