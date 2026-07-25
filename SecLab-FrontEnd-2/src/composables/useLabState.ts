/**
 * useLabState - 全局靶机运行状态（跨组件共享）
 *
 * 用于 Module 页面 → FloatingChatButton / FloatingChat 的状态传递：
 *   - currentLabContainer : 当前运行的靶机容器名（空字符串=未启动）
 *   - labStartTime        : 靶机启动时刻
 *   - setLabRunning(name) : 靶机启动时调用
 *   - clearLab()          : 靶机关闭时调用
 *
 * Phase 3 新增（全域智能引导助手）：
 *   - guidanceAlerts      : proactive guidance 主动提示队列（SSE 流式接收）
 *   - ttyLogLines         : 最近 TTY 日志行（用于调试面板/触发源展示）
 *   - guidanceUnreadCount : 未读主动提示计数（FloatingChatButton 红点徽标）
 */
import { ref } from 'vue'

// 容器名 → 对人类友好的标签
export const CONTAINER_NAMES: Record<number, string> = {
  1: 'sqli-lab-web-1',
  2: 'xss-lab-web-1',
  3: 'csrf-lab-web-1',
  4: 'command-inject-web-1',
  5: 'file-upload-lab-web-1',
  6: 'directory-traversal-lab-web-1',
  15: 'stack-overflow-lab-web-1',
}

/** 当前靶机容器名，空字符串表示未启动 */
export const currentLabContainer = ref<string>('')

/** 靶机启动时刻 */
export const labStartTime = ref<Date | null>(null)

/** 实验是否进行中 */
export const isLabRunning = ref<boolean>(false)

export interface LabEvent {
  event_id: string
  event_type: string
  event_time: string
  [key: string]: any
}

export interface LabContext {
  moduleId?: number | string | null
  moduleName?: string
  experimentId?: number | string | null
  experimentTitle?: string
  currentTask?: string
  labSessionId?: string
  containerName?: string
  currentLabContainer?: string
  targetUrl?: string
  targetMachineUrl?: string
  userId?: number | string | null
  classId?: number | string | null
  courseId?: number | string | null
}

/**
 * Proactive Guidance 主动提示。
 * 由 /api/guidance/stream/{lab_session_id} SSE 推送的 chunk 累积而成。
 */
export interface GuidanceAlert {
  /** docker-service 生成的 signal_id（同一信号的所有 chunk 共享） */
  signal_id: string
  /** 触发原因：repeated_error / stuck_loop / repeated_command */
  trigger_reason: string
  /** 本地会话 ID（guidance-{lab_session_id}） */
  conversation_id?: string
  /** Dify 返回的 message_id（guidance_end 事件提供） */
  message_id?: string
  /** 错误上下文（error_signature / error_category / severity） */
  error_context?: {
    error_signature?: string
    error_category?: string
    severity?: string
  } | null
  /** 累积的诊断文本（chunk.content 拼接） */
  content: string
  /** 状态：streaming（接收中）/ done（完成）/ error（失败） */
  status: 'streaming' | 'done' | 'error'
  /** 错误消息（status=error 时填充） */
  error_message?: string
  /** 开始时间 ISO8601 */
  started_at: string
  /** 结束时间 ISO8601（status=done/error 时填充） */
  ended_at?: string
}

/** TTY 日志行（用于调试面板/触发源展示） */
export interface TtyLogLine {
  ts: string
  stream: 'stdout' | 'stderr'
  line: string
  container_name?: string
}

const labEvents = ref<LabEvent[]>([])
let labSessionId = ''
export const currentLabContext = ref<LabContext>({})

/** 主动提示队列（最近 50 条，按时间顺序） */
export const guidanceAlerts = ref<GuidanceAlert[]>([])
const GUIDANCE_ALERT_MAX = 50

/** TTY 日志行（最近 200 行，避免无界增长） */
export const ttyLogLines = ref<TtyLogLine[]>([])
const TTY_LOG_MAX = 200

/** 未读主动提示计数 */
export const guidanceUnreadCount = ref<number>(0)

function generateId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`
}

/** 靶机启动 */
export function setLabRunning(containerName: string, sessionId?: string) {
  currentLabContainer.value = containerName
  labStartTime.value = new Date()
  isLabRunning.value = true
  labSessionId = sessionId || `lab-${Date.now()}`
  currentLabContext.value = {
    ...currentLabContext.value,
    labSessionId,
    containerName,
    currentLabContainer: containerName
  }
  labEvents.value = [
    {
      event_id: generateId('evt-lab-start'),
      event_type: 'LAB_START',
      event_time: new Date().toISOString(),
      container_name: containerName,
      extra: {}
    }
  ]
}

/** 靶机关闭 */
export function clearLab() {
  currentLabContainer.value = ''
  labStartTime.value = null
  isLabRunning.value = false
  labSessionId = ''
  currentLabContext.value = {}
  labEvents.value = []
  // Phase 3: 同步清理 guidance / TTY 状态，避免泄漏到下次实验
  guidanceAlerts.value = []
  ttyLogLines.value = []
  guidanceUnreadCount.value = 0
}

export function setLabSessionId(sessionId: string) {
  labSessionId = sessionId
  currentLabContext.value = {
    ...currentLabContext.value,
    labSessionId: sessionId
  }
}

export function setLabContext(context: Partial<LabContext>) {
  currentLabContext.value = {
    ...currentLabContext.value,
    ...context
  }
}

export function getLabSessionId() {
  return labSessionId
}

export function addLabEvent(event: Partial<LabEvent> & { event_type: string }) {
  labEvents.value.push({
    event_id: event.event_id || generateId('evt'),
    event_type: event.event_type,
    event_time: event.event_time || new Date().toISOString(),
    ...event
  })
}

export function getLabEvents() {
  return [...labEvents.value]
}

export function getLabDurationSeconds() {
  if (!labStartTime.value) return 0
  return Math.round((Date.now() - labStartTime.value.getTime()) / 1000)
}

// ─────────────────────────────────────────
//  Phase 3: Proactive Guidance 状态管理
// ─────────────────────────────────────────

/**
 * 新增一条 guidance 主动提示（guidance_start 事件触发时调用）。
 * 同时把未读计数 +1。超过上限时丢弃最旧的一条。
 */
export function addGuidanceAlert(alert: GuidanceAlert) {
  guidanceAlerts.value.push(alert)
  if (guidanceAlerts.value.length > GUIDANCE_ALERT_MAX) {
    guidanceAlerts.value = guidanceAlerts.value.slice(-GUIDANCE_ALERT_MAX)
  }
  guidanceUnreadCount.value += 1
}

/**
 * 按 signal_id 更新已存在的 guidance 主动提示（chunk / error / guidance_end 事件）。
 * 找不到时静默忽略（可能在 clearLab 之后到达）。
 */
export function updateGuidanceAlert(
  signal_id: string,
  patch: Partial<GuidanceAlert>
) {
  const idx = guidanceAlerts.value.findIndex((a) => a.signal_id === signal_id)
  if (idx === -1) return
  // 用 splice 触发响应式更新（直接赋值属性可能不触发，取决于 patch 字段）
  guidanceAlerts.value[idx] = {
    ...guidanceAlerts.value[idx],
    ...patch
  }
}

/** 追加 chunk 文本到指定 signal_id 的 content 字段 */
export function appendGuidanceChunk(signal_id: string, content: string) {
  const idx = guidanceAlerts.value.findIndex((a) => a.signal_id === signal_id)
  if (idx === -1) return
  guidanceAlerts.value[idx] = {
    ...guidanceAlerts.value[idx],
    content: guidanceAlerts.value[idx].content + content
  }
}

/** 清空所有 guidance 主动提示（用于手动清除或测试） */
export function clearGuidanceAlerts() {
  guidanceAlerts.value = []
  guidanceUnreadCount.value = 0
}

/**
 * 标记所有 guidance 主动提示为已读（FloatingChat 打开时调用）。
 */
export function markGuidanceAlertsRead() {
  guidanceUnreadCount.value = 0
}

// ─────────────────────────────────────────
//  Phase 3: TTY 日志行管理
// ─────────────────────────────────────────

/**
 * 追加一条 TTY 日志行。超过上限时丢弃最旧的一条（FIFO）。
 * 上限 200 行，避免无界增长拖累前端性能。
 */
export function addTtyLogLine(line: TtyLogLine) {
  ttyLogLines.value.push(line)
  if (ttyLogLines.value.length > TTY_LOG_MAX) {
    ttyLogLines.value = ttyLogLines.value.slice(-TTY_LOG_MAX)
  }
}

/** 清空所有 TTY 日志行 */
export function clearTtyLogLines() {
  ttyLogLines.value = []
}
