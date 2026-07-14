import { ref } from 'vue'

export const CONTAINER_NAMES: Record<number, string> = {
  1: 'sqli-lab-web-1',
  2: 'xss-lab-web-1',
  3: 'csrf-lab-web-1',
  4: 'cmd-inject-web-1',
  5: 'upload-lab-web-1',
  6: 'dir-lab-web-1',
}

export const currentLabContainer = ref<string>('')
export const labStartTime = ref<Date | null>(null)
export const isLabRunning = ref<boolean>(false)

export interface LabEvent {
  event_id: string
  event_type: string
  event_time: string
  [key: string]: any
}

const labEvents = ref<LabEvent[]>([])

let labSessionId = ''

function generateId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`
}

export function setLabRunning(containerName: string) {
  currentLabContainer.value = containerName
  labStartTime.value = new Date()
  isLabRunning.value = true
  labSessionId = `lab-${Date.now()}`
  labEvents.value = []
  labEvents.value.push({
    event_id: generateId('evt-lab-start'),
    event_type: 'LAB_START',
    event_time: new Date().toISOString(),
    container_name: containerName,
    extra: {}
  })
}

export function clearLab() {
  currentLabContainer.value = ''
  labStartTime.value = null
  isLabRunning.value = false
  labSessionId = ''
  labEvents.value = []
}

export function getLabSessionId() {
  return labSessionId
}

export function addLabEvent(event: Partial<LabEvent> & { event_type: string }) {
  labEvents.value.push({
    event_id: event.event_id || generateId('evt'),
    event_type: event.event_type,
    event_time: new Date().toISOString(),
    ...event
  })
}

export function getLabEvents() {
  return labEvents.value
}

export function getLabDurationSeconds() {
  if (!labStartTime.value) return 0
  return Math.round((Date.now() - labStartTime.value.getTime()) / 1000)
}

