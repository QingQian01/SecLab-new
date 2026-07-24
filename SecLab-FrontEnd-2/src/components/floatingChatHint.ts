export interface LabHintContext {
  moduleId?: unknown
  moduleName?: unknown
  experimentId?: unknown
  experimentTitle?: unknown
  currentTask?: unknown
  labSessionId?: unknown
  containerName?: unknown
  targetUrl?: unknown
  userId?: unknown
  classId?: unknown
  courseId?: unknown
}

export interface LabHintRequest {
  visibleMessage: string
  inputs: {
    hint_request: true
    lab_context: LabHintContext
  }
}

export function buildLabHintRequest(context: LabHintContext): LabHintRequest {
  return {
    visibleMessage: '请分析我当前的实验进展，并给出下一步提示。',
    inputs: {
      hint_request: true,
      lab_context: context,
    },
  }
}

export function summarizeToolObservation(observation: string): {
  failed: boolean
  text: string
} {
  const normalized = String(observation || '').toLowerCase()
  const failed = [
    'tool invoke error',
    'status code 4',
    'status code 5',
    '<!doctype html',
    '"success":false',
  ].some((marker) => normalized.includes(marker))

  return failed
    ? { failed: true, text: '暂时无法读取实验数据' }
    : { failed: false, text: '实验数据读取完成' }
}

export function shouldShowAgentToolCalls(inputs: Record<string, unknown>): boolean {
  return inputs.hint_request !== true && inputs.lab_runtime_context !== true
}

export function resolveLabChatInputs(
  pendingInputs: Record<string, unknown>,
  context: LabHintContext,
): Record<string, unknown> {
  if (Object.keys(pendingInputs).length > 0) {
    return pendingInputs
  }
  if (!String(context.containerName || '').trim()) {
    return {}
  }
  return {
    lab_runtime_context: true,
    lab_context: context,
  }
}

export function visibleAgentToolCalls<
  T extends { status?: string; observation?: string },
>(toolCalls: T[] | undefined): T[] {
  return (toolCalls || []).filter((toolCall) => (
    toolCall.status !== 'error'
    && !summarizeToolObservation(toolCall.observation || '').failed
  ))
}

export function sanitizeAssistantAnswer(answer: string): string {
  let visible = String(answer || '')
    .replace(/<think\b[^>]*>[\s\S]*?<\/think\s*>/gi, '')
    .replace(/<think\b[^>]*>[\s\S]*$/gi, '')
    .replace(/<\/think\s*>/gi, '')

  const partialOpeningTags = ['<', '<t', '<th', '<thi', '<thin', '<think']
  const lower = visible.toLowerCase()
  const partialTag = partialOpeningTags.find((tag) => lower.endsWith(tag))
  if (partialTag) {
    visible = visible.slice(0, -partialTag.length)
  }

  return visible.replace(/^\s+/, '')
}
