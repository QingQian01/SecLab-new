<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  getApiErrorMessage,
  getKnowledgePointAiAnalysis,
  startKnowledgePointAiAnalysis,
  type KnowledgeAiAnalysisDto,
  type KnowledgeExerciseDto,
  type TeachingClassStudentDto,
} from '../../../../api'
import IssuePersonalizedPracticeDialog from './IssuePersonalizedPracticeDialog.vue'
import KnowledgeExerciseReview from './KnowledgeExerciseReview.vue'

const props = withDefaults(defineProps<{
  classId: number
  courseId: number
  knowledgePointId: number
  knowledgePointName: string
  affectedStudents: Array<{ studentId: number; studentName: string }>
  allStudents: TeachingClassStudentDto[]
  initialAnalysis?: KnowledgeAiAnalysisDto | null
}>(), { initialAnalysis: null })
const emit = defineEmits<{ issued: [] }>()

const data = ref<KnowledgeAiAnalysisDto | null>(props.initialAnalysis)
const loading = ref(false)
const analysing = ref(false)
const error = ref('')
const issueOpen = ref(false)
let mounted = false

const approvedCount = computed(() => data.value?.exercises.filter((item) => item.reviewStatus === 'APPROVED').length || 0)
const visibleError = computed(() => error.value || data.value?.lastErrorMessage || '')

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await getKnowledgePointAiAnalysis(props.classId, props.courseId, props.knowledgePointId)
  } catch (reason) {
    error.value = getApiErrorMessage(reason, 'AI 分析记录加载失败。')
  } finally {
    loading.value = false
  }
}

async function analyse() {
  analysing.value = true
  error.value = ''
  try {
    data.value = await startKnowledgePointAiAnalysis(props.classId, props.courseId, props.knowledgePointId)
  } catch (reason) {
    const failureMessage = getApiErrorMessage(reason, 'AI 分析失败，请稍后重试。')
    try {
      data.value = await getKnowledgePointAiAnalysis(props.classId, props.courseId, props.knowledgePointId)
    } catch {
      // 保留当前内存中的最近成功结果；提供方失败时不生成任何替代内容。
    }
    error.value = failureMessage
  } finally {
    analysing.value = false
  }
}

function replaceExercise(updated: KnowledgeExerciseDto) {
  if (!data.value) return
  data.value = { ...data.value, exercises: data.value.exercises.map((item) => item.exerciseId === updated.exerciseId ? updated : item) }
}

watch(() => [props.classId, props.courseId, props.knowledgePointId] as const, () => {
  data.value = props.initialAnalysis
  if (mounted) void load()
})
onMounted(() => {
  mounted = true
  if (!props.initialAnalysis) void load()
})
</script>

<template>
  <section class="ai-panel">
    <header class="ai-head"><h3>AI 分析与教师备课建议</h3><button type="button" :disabled="analysing" @click="analyse">{{ analysing ? 'AI 分析中…' : data?.analysis ? '重新分析' : '开始 AI 分析' }}</button></header>
    <div v-if="visibleError" class="ai-error">{{ visibleError }}</div>
    <div v-if="loading && !data" class="ai-state">正在读取分析记录…</div>
    <div v-else-if="!data?.analysis" class="ai-empty"><strong>暂无本知识点 AI 分析</strong></div>
    <template v-else>
      <section class="conclusion"><span>分析结论</span><p>{{ data.analysis.overallConclusion }}</p></section>
      <div class="advice-grid">
        <section><h4>普遍错误归因</h4><article v-for="item in data.analysis.commonMistakes" :key="item.title"><strong>{{ item.title }}</strong><p>{{ item.reason }}</p></article></section>
        <section><h4>下节课教学建议</h4><article v-for="item in data.analysis.teachingAdvice" :key="item.title"><strong>{{ item.title }}</strong><p>{{ item.action }}</p></article></section>
      </div>
      <section class="exercise-section">
        <header><h4>知识点例题</h4><strong>已审核通过 {{ approvedCount }}/{{ data.exercises.length }}</strong></header>
        <div class="exercise-list"><KnowledgeExerciseReview v-for="exercise in data.exercises" :key="exercise.exerciseId" :class-id="classId" :exercise="exercise" @changed="replaceExercise" /></div>
        <button class="issue-button" type="button" :disabled="approvedCount === 0" @click="issueOpen = true">下发已审核通过的练习</button>
      </section>
    </template>
    <IssuePersonalizedPracticeDialog
      :open="issueOpen"
      :class-id="classId"
      :course-id="courseId"
      :knowledge-point-id="knowledgePointId"
      :knowledge-point-name="knowledgePointName"
      :exercises="data?.exercises || []"
      :affected-students="affectedStudents"
      :all-students="allStudents"
      @close="issueOpen = false"
      @issued="emit('issued')"
    />
  </section>
</template>

<style scoped>
.ai-panel{padding:17px;border:1px solid #d9e4f0;border-radius:9px;background:#f6f9fd}.ai-head{display:flex;align-items:center;justify-content:space-between;gap:15px}.ai-head span{color:#2c65a8;font-size:9px;font-weight:700}.ai-head h3{margin:4px 0 0;color:#253750;font-size:15px}.ai-head button,.issue-button{padding:8px 11px;border:0;border-radius:6px;background:#2866ae;color:#fff;font-size:10px;font-weight:700;cursor:pointer}.ai-head button:disabled,.issue-button:disabled{opacity:.5;cursor:not-allowed}.ai-error{display:grid;gap:3px;margin-top:12px;padding:9px;border-radius:6px;background:#fff0ed;color:#a34136;font-size:10px}.ai-error small{color:#865f59}.ai-state,.ai-empty{margin-top:13px;padding:18px;border-radius:7px;background:#fff;color:#7d8999;font-size:10px;text-align:center}.ai-empty strong{color:#43536a;font-size:12px}.ai-empty p{margin:6px auto 0;max-width:470px;line-height:1.65}.conclusion{margin-top:13px;padding:12px;border-left:3px solid #2c69b2;background:#fff}.conclusion span{color:#2c63a5;font-size:9px;font-weight:700}.conclusion p{margin:5px 0 0;color:#34455c;font-size:11px;line-height:1.7}.advice-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px}.advice-grid>section{padding:12px;border:1px solid #e1e7ee;border-radius:7px;background:#fff}.advice-grid h4,.exercise-section h4{margin:0;color:#33445b;font-size:12px}.advice-grid article{margin-top:9px}.advice-grid strong{color:#42546b;font-size:10px}.advice-grid p{margin:3px 0 0;color:#6e7c8f;font-size:9px;line-height:1.6}.exercise-section{margin-top:13px}.exercise-section>header{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;margin-bottom:9px}.exercise-section>header p{margin:4px 0 0;color:#7c899b;font-size:9px}.exercise-section>header>strong{color:#2d7450;font-size:10px}.exercise-list{display:grid;gap:9px}.issue-button{display:block;margin:12px 0 0 auto;background:#2e7854}@media(max-width:650px){.ai-head,.exercise-section>header{align-items:flex-start;flex-direction:column}.advice-grid{grid-template-columns:1fr}}
</style>
