<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getAiAnalysisHealth,
  getApiErrorMessage,
  getGeneratedQuestionSummary,
  getTeachingClassAnalysis,
  getTeachingClassInterventions,
  getTeachingClasses,
  getTeachingClassExperimentRiskMap,
  getTeachingClassStudentAnalysis,
  getTeachingClassStudentCapabilityEvidence,
  getTeachingClassStudentLearningReplay,
  getTeachingClassStudentProfile,
  getTeachingClassStudents,
  getTeachingClassCourses,
  getTeacherClassCourseQuestions,
  getTeacherStudentCourseQuestions,
  getTeacherCourseAnalysis,
  rebuildTeachingClassProfiles,
  startTeachingClassAnalysis,
  startTeachingClassStudentAnalysis,
  startTeacherCourseAnalysis,
  type AiAnalysisHealthDto,
  type CapabilityEvidenceResponseDto,
  type KnowledgeRiskItemDto,
  type LearningReplayResponseDto,
  type TeacherGeneratedQuestionSummary,
  type TeacherInterventionDto,
  type TeacherStudentProfileResponseDto,
  type TeachingClassAnalysisDto,
  type TeachingClassDto,
  type TeachingClassStudentDto,
  type TeachingStudentAnalysisDto,
  type TeachingClassCourseDto,
  type TeacherCourseQuestionsDto,
  type TeacherCourseAnalysisDto,
} from '../../../api'
import CapabilityEvidencePanel from './components/CapabilityEvidencePanel.vue'
import KnowledgeRiskPieChart from './components/KnowledgeRiskPieChart.vue'
import KnowledgeRiskDetailDrawer from './components/KnowledgeRiskDetailDrawer.vue'
import LearningReplayTimeline from './components/LearningReplayTimeline.vue'
import TeachingActionPanel from './components/TeachingActionPanel.vue'
import CourseQuestionRecords from './components/CourseQuestionRecords.vue'
import CourseAnalysisPanel from './components/CourseAnalysisPanel.vue'
import { findMatchingRiskItem, getRiskPresentation } from './analysisPresentation'
import '../teacher-page.css'

const route = useRoute()
const router = useRouter()
const classes = ref<TeachingClassDto[]>([])
const selectedClassId = ref<number | null>(null)
const activeTab = ref<'class' | 'student'>('class')
const students = ref<TeachingClassStudentDto[]>([])
const selectedStudentId = ref<number | null>(null)
const courses = ref<TeachingClassCourseDto[]>([])
const selectedCourseId = ref<number | null>(null)
const studentSearch = ref('')
const questionSummary = ref<TeacherGeneratedQuestionSummary | null>(null)
const classAnalysis = ref<TeachingClassAnalysisDto | null>(null)
const studentProfile = ref<TeacherStudentProfileResponseDto | null>(null)
const studentAnalysis = ref<TeachingStudentAnalysisDto | null>(null)
const capabilityEvidence = ref<CapabilityEvidenceResponseDto | null>(null)
const learningReplay = ref<LearningReplayResponseDto | null>(null)
const riskItems = ref<KnowledgeRiskItemDto[]>([])
const selectedRisk = ref<KnowledgeRiskItemDto | null>(null)
const riskDrawerOpen = ref(false)
const interventions = ref<TeacherInterventionDto[]>([])
const aiHealth = ref<AiAnalysisHealthDto | null>(null)
const classCourseQuestions = ref<TeacherCourseQuestionsDto | null>(null)
const studentCourseQuestions = ref<TeacherCourseQuestionsDto | null>(null)
const classCourseAnalysis = ref<TeacherCourseAnalysisDto | null>(null)
const studentCourseAnalysis = ref<TeacherCourseAnalysisDto | null>(null)
const courseDataLoading = ref(false)
const classCourseAnalysing = ref(false)
const studentCourseAnalysing = ref(false)
const courseError = ref('')
const loading = ref(true)
const classDataLoading = ref(false)
const studentDataLoading = ref(false)
const classAnalysing = ref(false)
const studentAnalysing = ref(false)
const rebuildingProfiles = ref(false)
const rebuildMessage = ref('')
const pageError = ref('')
const classError = ref('')
const studentError = ref('')
const expandedProblemIndex = ref<number | null>(null)

const selectedClass = computed(() => classes.value.find((item) => item.teachingClassId === selectedClassId.value) || null)
const selectedStudent = computed(() => students.value.find((item) => item.studentId === selectedStudentId.value) || null)
const selectedCourse = computed(() => courses.value.find((item) => item.courseId === selectedCourseId.value) || null)
const filteredStudents = computed(() => {
  const keyword = studentSearch.value.trim().toLowerCase()
  if (!keyword) return students.value
  return students.value.filter((item) => [item.studentName, item.studentNumber, item.administrativeClass]
    .some((value) => String(value || '').toLowerCase().includes(keyword)))
})
const classProblems = computed(() => classAnalysis.value?.analysis?.commonProblems || [])
const generatedQuestionCount = computed(() => questionSummary.value?.items.reduce((total, item) => total + item.generatedQuestionCount, 0) || 0)
const incorrectQuestionCount = computed(() => questionSummary.value?.items.reduce((total, item) => total + item.incorrectCount, 0) || 0)
const scoreCards = computed(() => [
  ['综合', studentProfile.value?.latestProfile?.overall_score],
  ['知识掌握', studentProfile.value?.latestProfile?.knowledge_mastery_score],
  ['排障能力', studentProfile.value?.latestProfile?.troubleshooting_score],
  ['自主学习', studentProfile.value?.latestProfile?.autonomy_score],
  ['AI 协同', studentProfile.value?.latestProfile?.ai_collaboration_score],
  ['学习投入', studentProfile.value?.latestProfile?.engagement_score],
] as const)

const formatDateTime = (value?: string | null) => value
  ? new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
  : '暂无记录'
const formatScore = (value?: number | null) => typeof value === 'number' ? value.toFixed(1) : '—'

async function loadClasses() {
  loading.value = true
  pageError.value = ''
  try {
    const [classResult, healthResult] = await Promise.allSettled([getTeachingClasses(), getAiAnalysisHealth()])
    if (classResult.status === 'rejected') throw classResult.reason
    classes.value = classResult.value.filter((item) => item.status !== 'ARCHIVED')
    aiHealth.value = healthResult.status === 'fulfilled' ? healthResult.value : null
    const queryId = Number(route.query.classId)
    const initialId = Number.isFinite(queryId) && classes.value.some((item) => item.teachingClassId === queryId)
      ? queryId : classes.value[0]?.teachingClassId
    selectedClassId.value = initialId || null
  } catch (error) {
    pageError.value = getApiErrorMessage(error, '教学班加载失败，请稍后重试。')
  } finally {
    loading.value = false
  }
}

async function loadInterventions() {
  if (!selectedClassId.value) return
  try {
    interventions.value = (await getTeachingClassInterventions(selectedClassId.value)).items
  } catch (error) {
    classError.value ||= getApiErrorMessage(error, '教学行动加载失败。')
  }
}

async function loadClassData() {
  if (!selectedClassId.value) return
  const classId = selectedClassId.value
  classDataLoading.value = true
  classError.value = ''
  rebuildMessage.value = ''
  selectedStudentId.value = null
  studentProfile.value = null
  studentAnalysis.value = null
  capabilityEvidence.value = null
  learningReplay.value = null
  const [studentResult, courseResult, summaryResult, analysisResult, interventionResult] = await Promise.allSettled([
    getTeachingClassStudents(classId),
    getTeachingClassCourses(classId),
    getGeneratedQuestionSummary(classId),
    getTeachingClassAnalysis(classId),
    getTeachingClassInterventions(classId),
  ])
  if (classId !== selectedClassId.value) return
  students.value = studentResult.status === 'fulfilled' ? studentResult.value : []
  courses.value = courseResult.status === 'fulfilled' ? courseResult.value : []
  questionSummary.value = summaryResult.status === 'fulfilled' ? summaryResult.value : null
  classAnalysis.value = analysisResult.status === 'fulfilled' ? analysisResult.value : null
  interventions.value = interventionResult.status === 'fulfilled' ? interventionResult.value.items : []
  riskItems.value = []
  selectedRisk.value = null
  riskDrawerOpen.value = false
  if (studentResult.status === 'rejected') classError.value = getApiErrorMessage(studentResult.reason, '学生名单加载失败。')
  selectedStudentId.value = students.value[0]?.studentId || null
  const queryCourseId = Number(route.query.courseId)
  const nextCourseId = courses.value.some((item) => item.courseId === queryCourseId)
    ? queryCourseId
    : courses.value.find((item) => item.courseId === 1)?.courseId || courses.value[0]?.courseId || null
  const courseChanged = selectedCourseId.value !== nextCourseId
  selectedCourseId.value = nextCourseId
  classDataLoading.value = false
  if (!courseChanged && nextCourseId) void loadCourseData()
  if (!nextCourseId) {
    classCourseQuestions.value = null
    studentCourseQuestions.value = null
    classCourseAnalysis.value = null
    studentCourseAnalysis.value = null
  }
}

async function loadCourseData() {
  if (!selectedClassId.value || !selectedCourseId.value) return
  const classId = selectedClassId.value
  const courseId = selectedCourseId.value
  courseDataLoading.value = true
  courseError.value = ''
  const [questionsResult, analysisResult, riskResult] = await Promise.allSettled([
    getTeacherClassCourseQuestions(classId, courseId),
    getTeacherCourseAnalysis(classId, courseId),
    getTeachingClassExperimentRiskMap(classId, courseId),
  ])
  if (classId !== selectedClassId.value || courseId !== selectedCourseId.value) return
  classCourseQuestions.value = questionsResult.status === 'fulfilled' ? questionsResult.value : null
  classCourseAnalysis.value = analysisResult.status === 'fulfilled' ? analysisResult.value : null
  riskItems.value = riskResult.status === 'fulfilled' ? riskResult.value.items : []
  selectedRisk.value = riskItems.value[0] || null
  riskDrawerOpen.value = false
  if (questionsResult.status === 'rejected') courseError.value = getApiErrorMessage(questionsResult.reason, '实验做题记录加载失败。')
  else if (riskResult.status === 'rejected') courseError.value = getApiErrorMessage(riskResult.reason, '本实验知识点错误分布加载失败。')
  courseDataLoading.value = false
  await loadStudentCourseData()
}

async function loadStudentCourseData() {
  if (!selectedClassId.value || !selectedCourseId.value || !selectedStudentId.value) return
  const classId = selectedClassId.value
  const courseId = selectedCourseId.value
  const studentId = selectedStudentId.value
  const [questionsResult, analysisResult] = await Promise.allSettled([
    getTeacherStudentCourseQuestions(classId, courseId, studentId),
    getTeacherCourseAnalysis(classId, courseId, studentId),
  ])
  if (classId !== selectedClassId.value || courseId !== selectedCourseId.value || studentId !== selectedStudentId.value) return
  studentCourseQuestions.value = questionsResult.status === 'fulfilled' ? questionsResult.value : null
  studentCourseAnalysis.value = analysisResult.status === 'fulfilled' ? analysisResult.value : null
    if (questionsResult.status === 'rejected') studentError.value = getApiErrorMessage(questionsResult.reason, '该学生的实验做题记录加载失败。')
}

async function loadStudentData() {
  if (!selectedClassId.value || !selectedStudentId.value) return
  const classId = selectedClassId.value
  const studentId = selectedStudentId.value
  studentDataLoading.value = true
  studentError.value = ''
  const [profileResult, analysisResult, evidenceResult, replayResult] = await Promise.allSettled([
    getTeachingClassStudentProfile(classId, studentId),
    getTeachingClassStudentAnalysis(classId, studentId),
    getTeachingClassStudentCapabilityEvidence(classId, studentId),
    getTeachingClassStudentLearningReplay(classId, studentId),
  ])
  if (classId !== selectedClassId.value || studentId !== selectedStudentId.value) return
  studentProfile.value = profileResult.status === 'fulfilled' ? profileResult.value : null
  studentAnalysis.value = analysisResult.status === 'fulfilled' ? analysisResult.value : null
  capabilityEvidence.value = evidenceResult.status === 'fulfilled' ? evidenceResult.value : null
  learningReplay.value = replayResult.status === 'fulfilled' ? replayResult.value : null
  if (profileResult.status === 'rejected') studentError.value = getApiErrorMessage(profileResult.reason, '学生学习数据加载失败。')
  studentDataLoading.value = false
  await loadStudentCourseData()
}

async function runClassCourseAnalysis() {
  if (!selectedClassId.value || !selectedCourseId.value) return
  classCourseAnalysing.value = true
  courseError.value = ''
  try { classCourseAnalysis.value = await startTeacherCourseAnalysis(selectedClassId.value, selectedCourseId.value) }
  catch (error) { courseError.value = getApiErrorMessage(error, '本实验分析失败，请稍后重试。') }
  finally { classCourseAnalysing.value = false }
}

async function runStudentCourseAnalysis() {
  if (!selectedClassId.value || !selectedCourseId.value || !selectedStudentId.value) return
  studentCourseAnalysing.value = true
  studentError.value = ''
  try { studentCourseAnalysis.value = await startTeacherCourseAnalysis(selectedClassId.value, selectedCourseId.value, selectedStudentId.value) }
  catch (error) { studentError.value = getApiErrorMessage(error, '该学生的实验分析失败，请稍后重试。') }
  finally { studentCourseAnalysing.value = false }
}

async function runClassAnalysis() {
  if (!selectedClassId.value) return
  classAnalysing.value = true
  classError.value = ''
  try { classAnalysis.value = await startTeachingClassAnalysis(selectedClassId.value) }
  catch (error) { classError.value = getApiErrorMessage(error, '班级分析失败，请稍后重试。') }
  finally { classAnalysing.value = false }
}

async function runStudentAnalysis() {
  if (!selectedClassId.value || !selectedStudentId.value) return
  studentAnalysing.value = true
  studentError.value = ''
  try { studentAnalysis.value = await startTeachingClassStudentAnalysis(selectedClassId.value, selectedStudentId.value) }
  catch (error) { studentError.value = getApiErrorMessage(error, '学生分析失败，请稍后重试。') }
  finally { studentAnalysing.value = false }
}

async function rebuildProfiles() {
  if (!selectedClassId.value) return
  rebuildingProfiles.value = true
  classError.value = ''
  try {
    const result = await rebuildTeachingClassProfiles(selectedClassId.value)
    rebuildMessage.value = `已更新 ${result.rebuiltCount}/${result.studentCount} 名学生画像${result.failedCount ? `，${result.failedCount} 名待重试` : ''}。`
    await loadStudentData()
  } catch (error) { classError.value = getApiErrorMessage(error, '学生画像更新失败。') }
  finally { rebuildingProfiles.value = false }
}

function selectRisk(item: KnowledgeRiskItemDto) {
  selectedRisk.value = item
  riskDrawerOpen.value = true
}

function toggleProblem(index: number) {
  expandedProblemIndex.value = expandedProblemIndex.value === index ? null : index
}

function problemRisk(item: { title: string; evidence: string; questionIds: string[] }) {
  return findMatchingRiskItem(item, riskItems.value)
}

watch(selectedClassId, (classId) => {
  if (!classId) return
  void router.replace({ query: { ...route.query, classId: String(classId) } })
  void loadClassData()
})
watch(selectedStudentId, () => void loadStudentData())
watch(selectedCourseId, (courseId) => {
  if (!courseId) return
  void router.replace({ query: { ...route.query, classId: String(selectedClassId.value), courseId: String(courseId) } })
  void loadCourseData()
})
onMounted(() => void loadClasses())
</script>

<template>
  <div class="teacher-page analysis-page">
    <header class="page-head">
      <h1>教学分析</h1>
      <select v-model="selectedClassId" class="class-select" aria-label="选择教学班">
        <option v-for="item in classes" :key="item.teachingClassId" :value="item.teachingClassId">{{ item.academicYear }}学年 · 第{{ item.semester }}学期 · {{ item.className }}</option>
      </select>
    </header>

    <div v-if="loading" class="panel loading-state">正在加载教学班…</div>
    <div v-else-if="pageError" class="panel error-state">{{ pageError }} <button class="secondary-button" @click="loadClasses">重新加载</button></div>
    <div v-else-if="!selectedClass" class="panel empty-state"><strong>暂无可分析的教学班</strong></div>

    <template v-else>
      <div v-if="aiHealth && (!aiHealth.configured || !aiHealth.providerReachable)" class="notice warning analysis-notice">AI 分析暂不可用，请稍后重试。</div>
      <section class="analysis-context panel">
        <div><span>当前教学班</span><strong>{{ selectedClass.className }}</strong><small>{{ selectedClass.academicYear }}学年 · 第{{ selectedClass.semester }}学期</small></div>
        <div class="context-stat"><span>本实验做题学生</span><strong>{{ classCourseQuestions?.summary.studentCount ?? 0 }}</strong></div>
        <div class="context-stat"><span>本实验题目</span><strong>{{ classCourseQuestions?.summary.questionCount ?? 0 }}</strong></div>
        <div class="context-stat"><span>最终错题</span><strong>{{ classCourseQuestions?.summary.incorrectQuestionCount ?? 0 }}</strong></div>
      </section>

      <section class="course-switcher panel">
        <div class="course-switcher-title"><span>分析实验</span><strong>{{ selectedCourse?.courseName || '请选择实验' }}</strong></div>
        <div class="course-tabs" role="listbox" aria-label="选择分析实验"><button v-for="course in courses" :key="course.courseId" :class="{ active: selectedCourseId === course.courseId }" @click="selectedCourseId = course.courseId"><span>{{ course.teachingOrder }}</span>{{ course.courseName }}</button></div>
      </section>
      <div v-if="courseError" class="notice error analysis-notice">{{ courseError }}</div>

      <div class="analysis-tabs" role="tablist"><button :class="{ active: activeTab === 'class' }" @click="activeTab = 'class'">班级实验分析</button><button :class="{ active: activeTab === 'student' }" @click="activeTab = 'student'">学生实验分析</button></div>
      <div v-if="classDataLoading" class="panel loading-state">正在读取最新学习数据…</div>

      <template v-else-if="activeTab === 'class'">
        <div v-if="classError" class="notice error analysis-notice">{{ classError }}</div>
        <div v-if="rebuildMessage" class="notice success analysis-notice">{{ rebuildMessage }}</div>
        <section class="panel result-panel"><CourseAnalysisPanel :data="classCourseAnalysis" :analysing="classCourseAnalysing" subject-label="班级" @analyse="runClassCourseAnalysis" /></section>
        <section class="panel result-panel"><CourseQuestionRecords :data="classCourseQuestions" :loading="courseDataLoading" scope-label="班级" /></section>
        <div class="supplement-title"><strong>跨实验辅助统计</strong></div>
        <section class="panel result-panel">
          <div class="panel-head"><div><h2>班级学习情况</h2><p v-if="classAnalysis?.analysis">最近分析：{{ formatDateTime(classAnalysis.generatedAt) }}</p></div><div class="head-actions"><button class="secondary-button" :disabled="rebuildingProfiles" @click="rebuildProfiles">{{ rebuildingProfiles ? '正在更新画像…' : '更新32人画像' }}</button><button class="primary-button" :disabled="classAnalysing" @click="runClassAnalysis">{{ classAnalysing ? '正在分析…' : classAnalysis?.analysis ? '重新分析' : '开始分析' }}</button></div></div>
          <div v-if="classAnalysis?.analysis" class="result-body"><p class="overall-comment">{{ classAnalysis.analysis.overallComment }}</p><div v-if="classProblems.length" class="problem-list"><article v-for="(item,index) in classProblems" :key="`${item.title}-${index}`" class="problem-card" :class="{ expanded: expandedProblemIndex === index }" role="button" :tabindex="0" :aria-expanded="expandedProblemIndex === index" @click="toggleProblem(index)" @keydown.enter.prevent="toggleProblem(index)"><div class="problem-index">{{ index+1 }}</div><div class="problem-main"><div class="problem-title"><strong>{{ item.title }}</strong><div class="problem-title-actions"><span>涉及 {{ item.studentCount }} 人</span><button type="button" class="problem-detail-button" @click.stop="toggleProblem(index)">{{ expandedProblemIndex === index ? '收起详情' : '查看详情' }}</button></div></div><p>{{ item.evidence }}</p><div class="teacher-action"><span>教学建议</span>{{ item.teacherAction }}</div><div v-if="expandedProblemIndex === index" class="problem-detail" @click.stop><template v-if="problemRisk(item)"><div class="problem-detail-summary"><div><span>对应知识点</span><strong>{{ problemRisk(item)?.knowledgePointName }}</strong></div><div><span>风险等级</span><strong :class="`risk-${getRiskPresentation(problemRisk(item)?.riskLevel).tone}`">{{ getRiskPresentation(problemRisk(item)?.riskLevel).label }}</strong></div><div><span>错题率</span><strong>{{ Math.round(Number(problemRisk(item)?.incorrectRate || 0) * 100) }}%</strong></div><div><span>错误记录</span><strong>{{ problemRisk(item)?.incorrectCount || 0 }} 条</strong></div></div><div class="problem-detail-section"><h4>涉及学生</h4><div class="student-chips"><span v-for="student in problemRisk(item)?.affectedStudents || []" :key="student.studentId">{{ student.studentName || `学生 ${student.studentId}` }}</span></div></div><div class="problem-detail-section"><h4>代表性错题</h4><div v-for="question in problemRisk(item)?.representativeQuestions || []" :key="question.generatedQuestionId" class="question-row">{{ question.title }}<small>{{ question.generatedQuestionId }}</small></div></div><button type="button" class="problem-action-link" @click="selectRisk(problemRisk(item)!)">打开知识点详情与 AI 分析</button></template><template v-else><div class="problem-detail-section"><h4>证据题目</h4><div class="student-chips"><span v-for="questionId in item.questionIds" :key="questionId">{{ questionId }}</span></div><p>当前问题已有班级分析证据，但还没有匹配到本实验的知识点错误记录。</p></div></template></div></div></article></div></div>
          <div v-else class="empty-state compact-empty"><strong>暂无班级 AI 分析</strong></div>
        </section>
        <section class="panel feature-panel"><KnowledgeRiskPieChart :items="riskItems" :selected-course-id="selectedCourseId!" @select="selectRisk" /></section>
        <KnowledgeRiskDetailDrawer
          :open="riskDrawerOpen"
          :class-id="selectedClassId!"
          :course-id="selectedCourseId!"
          :item="selectedRisk"
          :all-students="students"
          @close="riskDrawerOpen = false"
          @issued="loadInterventions"
        />
        <section class="panel feature-panel"><TeachingActionPanel :class-id="selectedClassId!" :students="students" :selected-risk="selectedRisk" :interventions="interventions" @changed="loadInterventions" /></section>
      </template>

      <template v-else>
        <div class="student-analysis-grid">
          <aside class="panel student-list-panel"><div class="student-search"><input v-model="studentSearch" placeholder="搜索姓名或学号" /></div><button v-for="student in filteredStudents" :key="student.studentId" class="student-row" :class="{ active: selectedStudentId === student.studentId }" @click="selectedStudentId = student.studentId"><span class="student-avatar">{{ (student.studentName || '学').slice(0,1) }}</span><span><strong>{{ student.studentName || '未填写姓名' }}</strong><small>{{ student.studentNumber }} · {{ student.administrativeClass || '未填写行政班' }}</small></span></button><div v-if="!filteredStudents.length" class="empty-state compact-empty">没有匹配的学生。</div></aside>
          <main class="student-content">
            <section class="panel student-result-panel"><CourseAnalysisPanel :data="studentCourseAnalysis" :analysing="studentCourseAnalysing" :subject-label="selectedStudent ? `${selectedStudent.studentName || selectedStudent.studentNumber}的` : '学生'" @analyse="runStudentCourseAnalysis" /></section>
            <section class="panel student-result-panel"><CourseQuestionRecords :data="studentCourseQuestions" :loading="studentDataLoading || courseDataLoading" :scope-label="selectedStudent ? `${selectedStudent.studentName || selectedStudent.studentNumber}的` : '学生'" /></section>
            <div class="supplement-title"><strong>跨实验五维画像</strong></div>
            <section class="panel student-result-panel">
              <div v-if="!selectedStudent" class="empty-state"><strong>请选择学生</strong>从左侧名单选择一名学生查看学习情况。</div>
              <div v-else-if="studentDataLoading" class="loading-state">正在读取 {{ selectedStudent.studentName || selectedStudent.studentNumber }} 的学习数据…</div>
              <template v-else><div class="panel-head"><div><h2>{{ selectedStudent.studentName || '未填写姓名' }} · 综合画像</h2><p>{{ selectedStudent.studentNumber }} · 最近活跃 {{ formatDateTime(selectedStudent.recentActivityAt) }}</p></div><button class="secondary-button" :disabled="studentAnalysing" @click="runStudentAnalysis">{{ studentAnalysing ? '正在更新…' : '更新综合画像分析' }}</button></div><div v-if="studentError" class="notice error analysis-notice">{{ studentError }}</div><div class="student-result-body"><div class="profile-score-grid"><div v-for="card in scoreCards" :key="card[0]"><span>{{ card[0] }}</span><strong>{{ formatScore(card[1]) }}</strong></div></div><div v-if="studentAnalysis?.analysis" class="student-analysis-content"><div class="analysis-time">跨实验分析更新于：{{ formatDateTime(studentAnalysis.generatedAt) }}</div><p class="overall-comment">{{ studentAnalysis.analysis.overallComment }}</p><article v-for="item in studentAnalysis.analysis.focusAreas" :key="item.dimension" class="focus-card"><div><strong>{{ item.label }}</strong><span :class="`priority-${item.priority || 'medium'}`">{{ item.priority === 'high' ? '优先关注' : '持续观察' }}</span></div><p>{{ item.evidence }}</p><div class="teacher-action"><span>建议做法</span>{{ item.teacherAction }}</div></article></div></div></template>
            </section>
            <section class="panel feature-panel"><CapabilityEvidencePanel :data="capabilityEvidence" /></section>
            <section class="panel feature-panel"><LearningReplayTimeline :items="learningReplay?.items || []" /></section>
          </main>
        </div>
      </template>
    </template>
  </div>
</template>

<style scoped>
.class-select{min-width:330px;min-height:40px;padding:0 12px;border:1px solid #d5dee9;border-radius:7px;background:#fff;color:#27364e;font-size:13px}.analysis-context{display:grid;grid-template-columns:minmax(280px,1fr) repeat(3,150px);align-items:stretch;margin-bottom:18px;overflow:hidden}.analysis-context>div{display:grid;align-content:center;min-height:94px;padding:18px 22px;border-right:1px solid #edf0f4}.analysis-context>div:last-child{border-right:0}.analysis-context span,.analysis-context small{color:#7d899a;font-size:12px}.analysis-context strong{margin:5px 0 3px;color:#182843;font-size:18px}.context-stat{text-align:center}.context-stat strong{font-size:25px}.analysis-tabs{display:flex;gap:24px;margin:0 0 14px;border-bottom:1px solid #dfe5ed}.analysis-tabs button{padding:11px 2px;border:0;border-bottom:2px solid transparent;background:none;color:#718096;font-size:14px;font-weight:650;cursor:pointer}.analysis-tabs button.active{border-color:#245eae;color:#174d93}.result-panel,.feature-panel{margin-bottom:18px}.feature-panel{padding:20px}.result-body,.student-result-body{padding:22px}.head-actions{display:flex;gap:9px}.overall-comment{margin:0 0 20px;padding:14px 16px;border-left:3px solid #2c67b5;background:#f5f8fc;color:#35455d;font-size:13px;line-height:1.75}.problem-list{display:grid;gap:12px}.problem-card{display:grid;grid-template-columns:30px 1fr;gap:12px;padding:16px;border:1px solid #e3e8ef;border-radius:8px}.problem-index{display:grid;width:28px;height:28px;place-items:center;border-radius:6px;background:#eaf1fb;color:#1f5ca9;font-size:12px;font-weight:750}.problem-title{display:flex;justify-content:space-between;gap:15px}.problem-title strong{font-size:14px}.problem-title span{color:#8b5d18;font-size:12px}.problem-card p,.focus-card p{margin:8px 0;color:#637187;font-size:12px;line-height:1.65}.teacher-action{padding:10px 12px;border-radius:6px;background:#f7f9fc;color:#35445a;font-size:12px;line-height:1.6}.teacher-action span{margin-right:8px;color:#1f5ca9;font-weight:700}.analysis-notice{margin:0 0 12px}.compact-empty{padding:34px 20px}.student-analysis-grid{display:grid;grid-template-columns:300px minmax(0,1fr);gap:16px;align-items:start}.student-list-panel{position:sticky;top:16px;max-height:calc(100vh - 50px);overflow:auto}.student-search{position:sticky;top:0;z-index:2;padding:13px;border-bottom:1px solid #edf0f4;background:#fff}.student-search input{width:100%;height:38px;padding:0 11px;border:1px solid #d8e0ea;border-radius:7px;outline:none}.student-row{display:flex;width:100%;gap:10px;padding:12px 14px;border:0;border-bottom:1px solid #edf0f4;background:#fff;color:#2e3c52;text-align:left;cursor:pointer}.student-row:hover,.student-row.active{background:#f3f7fc}.student-row.active{box-shadow:inset 3px 0 #2865b5}.student-avatar{display:grid;width:34px;height:34px;flex:0 0 auto;place-items:center;border-radius:50%;background:#e8eef7;color:#245690;font-weight:700}.student-row strong,.student-row small{display:block}.student-row strong{font-size:13px}.student-row small{margin-top:4px;color:#8894a5;font-size:11px}.student-content{min-width:0}.student-result-panel{margin-bottom:18px}.profile-score-grid{display:grid;grid-template-columns:repeat(6,1fr);margin-bottom:20px;border:1px solid #e5eaf0;border-radius:8px;overflow:hidden}.profile-score-grid div{display:grid;gap:5px;padding:14px;border-right:1px solid #e8edf3}.profile-score-grid div:last-child{border-right:0}.profile-score-grid span{color:#7d899a;font-size:11px}.profile-score-grid strong{color:#1c4f91;font-size:20px}.analysis-time{margin-bottom:9px;color:#8894a6;font-size:11px}.focus-card{margin-top:11px;padding:15px;border:1px solid #e3e8ef;border-radius:8px}.focus-card>div:first-child{display:flex;align-items:center;justify-content:space-between}.focus-card strong{font-size:14px}.focus-card>div:first-child span{padding:3px 7px;border-radius:999px;font-size:10px}.priority-high{background:#fff0e8;color:#a84c18}.priority-medium,.priority-low{background:#edf3fb;color:#356196}
.course-switcher{display:grid;grid-template-columns:230px minmax(0,1fr);gap:18px;margin-bottom:16px;padding:16px 18px}.course-switcher-title{display:grid;align-content:center;border-right:1px solid #e7ebf1}.course-switcher-title span,.course-switcher-title small{color:#7d899a;font-size:11px}.course-switcher-title strong{margin:5px 0;color:#1d3150;font-size:15px}.course-tabs{display:flex;gap:8px;overflow-x:auto;padding:2px}.course-tabs button{display:flex;align-items:center;gap:7px;flex:0 0 auto;padding:9px 11px;border:1px solid #dbe3ed;border-radius:7px;background:#fff;color:#526177;font-size:12px;cursor:pointer}.course-tabs button span{display:grid;width:20px;height:20px;place-items:center;border-radius:50%;background:#edf2f8;color:#46617f;font-size:10px}.course-tabs button.active{border-color:#2d68b5;background:#edf4fd;color:#174f98;font-weight:650}.course-tabs button.active span{background:#2b66b4;color:#fff}.supplement-title{display:flex;align-items:baseline;gap:10px;margin:25px 2px 12px}.supplement-title strong{color:#263750;font-size:15px}.supplement-title span{color:#8591a2;font-size:11px}
.problem-card{cursor:pointer;transition:border-color .16s ease,box-shadow .16s ease}.problem-card:hover,.problem-card:focus-visible,.problem-card.expanded{border-color:#9ebbe0;box-shadow:0 5px 16px rgba(31,84,148,.08);outline:none}.problem-main{min-width:0}.problem-title-actions{display:flex;align-items:center;gap:10px;white-space:nowrap}.problem-title-actions>span{color:#8b5d18;font-size:12px}.problem-detail-button{padding:5px 9px;border:1px solid #b9cce4;border-radius:5px;background:#fff;color:#205a9e;font-size:11px;cursor:pointer}.problem-detail{margin-top:14px;padding:15px;border-top:1px solid #e4eaf1;background:#fbfcfe;cursor:default}.problem-detail-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.problem-detail-summary>div{display:grid;gap:4px;padding:10px;border:1px solid #e4eaf1;border-radius:6px;background:#fff}.problem-detail-summary span,.problem-detail-section h4{margin:0;color:#7a8798;font-size:11px}.problem-detail-summary strong{color:#25364e;font-size:13px}.problem-detail-section{margin-top:13px}.student-chips{display:flex;flex-wrap:wrap;gap:7px;margin-top:7px}.student-chips span{padding:5px 9px;border-radius:999px;background:#eaf2fc;color:#225b9d;font-size:11px}.question-row{display:flex;width:100%;justify-content:space-between;gap:12px;margin-top:7px;padding:9px 10px;border:1px solid #e4eaf1;border-radius:6px;background:#fff;color:#35445a;text-align:left}.question-row small{color:#8b96a5}.problem-action-link{margin-top:13px;padding:8px 11px;border:0;border-radius:6px;background:#245fae;color:#fff;font-size:12px;cursor:pointer}.risk-danger{color:#b34238!important}.risk-warning{color:#9b681f!important}.risk-success{color:#28764a!important}
@media(max-width:1080px){.analysis-context{grid-template-columns:1fr 1fr}.analysis-context>div{border-bottom:1px solid #edf0f4}.student-analysis-grid{grid-template-columns:250px minmax(0,1fr)}.profile-score-grid{grid-template-columns:repeat(3,1fr)}}@media(max-width:820px){.class-select{width:100%;min-width:0}.analysis-context,.student-analysis-grid,.course-switcher{grid-template-columns:1fr}.course-switcher-title{padding-bottom:10px;border-right:0;border-bottom:1px solid #e7ebf1}.student-list-panel{position:static;max-height:320px}.profile-score-grid{grid-template-columns:repeat(2,1fr)}.panel-head{flex-direction:column}.head-actions{width:100%;flex-wrap:wrap}.head-actions button,.panel-head>.primary-button{flex:1}}
</style>
