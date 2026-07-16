<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import {
  getApiErrorMessage,
  getStudentTeacherAssignments,
  startStudentTeacherAssignment,
  type StudentTeacherAssignmentDto,
} from '../../../api'

const props = defineProps<{ userId: number }>()
const emit = defineEmits<{ openSession: [trainingSessionId: string] }>()
const assignments = ref<StudentTeacherAssignmentDto[]>([])
const loading = ref(false)
const startingId = ref<number | null>(null)
const error = ref('')

async function loadAssignments() {
  if (!props.userId) return
  loading.value = true
  error.value = ''
  try {
    assignments.value = (await getStudentTeacherAssignments(props.userId)).items
  } catch (cause) {
    error.value = getApiErrorMessage(cause, '教师布置任务加载失败。')
  } finally {
    loading.value = false
  }
}

async function startAssignment(item: StudentTeacherAssignmentDto) {
  if (item.trainingSessionId) {
    emit('openSession', item.trainingSessionId)
    return
  }
  startingId.value = item.interventionId
  error.value = ''
  try {
    const result = await startStudentTeacherAssignment(props.userId, item.interventionId)
    await loadAssignments()
    if (result.trainingSessionId) emit('openSession', result.trainingSessionId)
  } catch (cause) {
    error.value = getApiErrorMessage(cause, '专项训练生成失败，请稍后重试。')
  } finally {
    startingId.value = null
  }
}

watch(() => props.userId, () => void loadAssignments())
onMounted(() => void loadAssignments())
</script>

<template>
  <section v-if="loading || error || assignments.length" class="card bg-base-100 border border-base-200 shadow-sm">
    <div class="card-body gap-4">
      <div>
        <h2 class="card-title text-lg">教师布置的专项任务</h2>
        <p class="mt-1 text-sm text-base-content/60">完成训练后，结果会回流到教学分析，老师可查看干预前后的变化。</p>
      </div>
      <div v-if="error" class="alert alert-error py-3 text-sm">{{ error }}</div>
      <div v-if="loading" class="text-sm text-base-content/50">正在读取教师布置任务…</div>
      <div v-else class="grid gap-3 lg:grid-cols-2">
        <article v-for="item in assignments" :key="item.interventionId" class="rounded-box border border-base-200 bg-base-50 p-4">
          <div class="flex items-start justify-between gap-3">
            <div><div class="text-xs text-base-content/50">{{ item.className }} · {{ item.teacherName || '任课教师' }}</div><h3 class="mt-1 font-semibold text-base-content">{{ item.title }}</h3></div>
            <span class="badge badge-sm" :class="item.assignmentStatus === 'COMPLETED' ? 'badge-success' : item.assignmentStatus === 'STARTED' ? 'badge-info' : 'badge-warning'">{{ item.assignmentStatus === 'COMPLETED' ? '已完成' : item.assignmentStatus === 'STARTED' ? '进行中' : '待开始' }}</span>
          </div>
          <p class="mt-3 text-sm leading-6 text-base-content/65">{{ item.description || `围绕${item.knowledgePointName || '当前薄弱知识点'}完成专项训练。` }}</p>
          <div class="mt-3 flex flex-wrap gap-2 text-xs text-base-content/50"><span v-if="item.knowledgePointName" class="badge badge-outline badge-sm">{{ item.knowledgePointName }}</span><span>截止 {{ new Date(item.dueAt).toLocaleDateString('zh-CN') }}</span></div>
          <button class="btn btn-primary btn-sm mt-4" :disabled="startingId === item.interventionId || item.assignmentStatus === 'COMPLETED'" @click="startAssignment(item)">{{ startingId === item.interventionId ? '正在生成专项题…' : item.trainingSessionId ? '继续训练' : '开始专项训练' }}</button>
        </article>
      </div>
    </div>
  </section>
</template>
