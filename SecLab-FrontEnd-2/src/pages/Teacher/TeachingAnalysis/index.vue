<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  getApiErrorMessage,
  getGeneratedQuestionSummary,
  getTeachingClassAnalysis,
  getTeachingClasses,
  getTeachingClassStudentAnalysis,
  getTeachingClassStudentProfile,
  getTeachingClassStudents,
  startTeachingClassAnalysis,
  startTeachingClassStudentAnalysis,
  type TeacherGeneratedQuestionSummary,
  type TeacherStudentProfileResponseDto,
  type TeachingClassAnalysisDto,
  type TeachingClassDto,
  type TeachingClassStudentDto,
  type TeachingStudentAnalysisDto,
} from '../../../api'
import '../teacher-page.css'

const route = useRoute()
const router = useRouter()
const classes = ref<TeachingClassDto[]>([])
const selectedClassId = ref<number | null>(null)
const activeTab = ref<'class' | 'student'>('class')
const students = ref<TeachingClassStudentDto[]>([])
const selectedStudentId = ref<number | null>(null)
const studentSearch = ref('')
const questionSummary = ref<TeacherGeneratedQuestionSummary | null>(null)
const classAnalysis = ref<TeachingClassAnalysisDto | null>(null)
const studentProfile = ref<TeacherStudentProfileResponseDto | null>(null)
const studentAnalysis = ref<TeachingStudentAnalysisDto | null>(null)
const loading = ref(true)
const classDataLoading = ref(false)
const studentDataLoading = ref(false)
const classAnalysing = ref(false)
const studentAnalysing = ref(false)
const pageError = ref('')
const classError = ref('')
const studentError = ref('')

const selectedClass = computed(() => classes.value.find((item) => item.teachingClassId === selectedClassId.value) || null)
const selectedStudent = computed(() => students.value.find((item) => item.studentId === selectedStudentId.value) || null)
const filteredStudents = computed(() => {
  const keyword = studentSearch.value.trim().toLowerCase()
  if (!keyword) return students.value
  return students.value.filter((item) => [item.studentName, item.studentNumber, item.administrativeClass]
    .some((value) => String(value || '').toLowerCase().includes(keyword)))
})
const classProblems = computed(() => classAnalysis.value?.analysis?.commonProblems || [])
const generatedQuestionCount = computed(() => questionSummary.value?.items
  .reduce((total, item) => total + item.generatedQuestionCount, 0) || 0)
const incorrectQuestionCount = computed(() => questionSummary.value?.items
  .reduce((total, item) => total + item.incorrectCount, 0) || 0)

const formatDateTime = (value?: string | null) => value
  ? new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
  }).format(new Date(value))
  : '暂无记录'
const formatScore = (value?: number | null) => typeof value === 'number' ? value.toFixed(1) : '—'

const loadClasses = async () => {
  loading.value = true
  pageError.value = ''
  try {
    classes.value = (await getTeachingClasses()).filter((item) => item.status !== 'ARCHIVED')
    const queryId = Number(route.query.classId)
    const initialId = Number.isFinite(queryId) && classes.value.some((item) => item.teachingClassId === queryId)
      ? queryId
      : classes.value[0]?.teachingClassId
    selectedClassId.value = initialId || null
  } catch (error) {
    pageError.value = getApiErrorMessage(error, '教学班加载失败，请稍后重试。')
  } finally {
    loading.value = false
  }
}

const loadClassData = async () => {
  if (!selectedClassId.value) return
  const classId = selectedClassId.value
  classDataLoading.value = true
  classError.value = ''
  selectedStudentId.value = null
  studentProfile.value = null
  studentAnalysis.value = null
  const [studentResult, summaryResult, analysisResult] = await Promise.allSettled([
    getTeachingClassStudents(classId),
    getGeneratedQuestionSummary(classId),
    getTeachingClassAnalysis(classId),
  ])
  if (classId !== selectedClassId.value) return
  students.value = studentResult.status === 'fulfilled' ? studentResult.value : []
  questionSummary.value = summaryResult.status === 'fulfilled' ? summaryResult.value : null
  classAnalysis.value = analysisResult.status === 'fulfilled' ? analysisResult.value : null
  if (studentResult.status === 'rejected') {
    classError.value = getApiErrorMessage(studentResult.reason, '学生名单加载失败。')
  }
  selectedStudentId.value = students.value[0]?.studentId || null
  classDataLoading.value = false
}

const loadStudentData = async () => {
  if (!selectedClassId.value || !selectedStudentId.value) return
  const classId = selectedClassId.value
  const studentId = selectedStudentId.value
  studentDataLoading.value = true
  studentError.value = ''
  const [profileResult, analysisResult] = await Promise.allSettled([
    getTeachingClassStudentProfile(classId, studentId),
    getTeachingClassStudentAnalysis(classId, studentId),
  ])
  if (classId !== selectedClassId.value || studentId !== selectedStudentId.value) return
  studentProfile.value = profileResult.status === 'fulfilled' ? profileResult.value : null
  studentAnalysis.value = analysisResult.status === 'fulfilled' ? analysisResult.value : null
  if (profileResult.status === 'rejected') {
    studentError.value = getApiErrorMessage(profileResult.reason, '学生学习数据加载失败。')
  }
  studentDataLoading.value = false
}

const runClassAnalysis = async () => {
  if (!selectedClassId.value) return
  classAnalysing.value = true
  classError.value = ''
  try {
    classAnalysis.value = await startTeachingClassAnalysis(selectedClassId.value)
  } catch (error) {
    classError.value = getApiErrorMessage(error, '本次分析未完成，已保留上一次成功结果。')
  } finally {
    classAnalysing.value = false
  }
}

const runStudentAnalysis = async () => {
  if (!selectedClassId.value || !selectedStudentId.value) return
  studentAnalysing.value = true
  studentError.value = ''
  try {
    studentAnalysis.value = await startTeachingClassStudentAnalysis(
      selectedClassId.value,
      selectedStudentId.value,
    )
  } catch (error) {
    studentError.value = getApiErrorMessage(error, '本次分析未完成，已保留上一次成功结果。')
  } finally {
    studentAnalysing.value = false
  }
}

watch(selectedClassId, (classId) => {
  if (!classId) return
  void router.replace({ query: { ...route.query, classId: String(classId) } })
  void loadClassData()
})
watch(selectedStudentId, () => void loadStudentData())
onMounted(() => void loadClasses())
</script>

<template>
  <div class="teacher-page analysis-page">
    <header class="page-head">
      <div>
        <h1>教学分析</h1>
        <p>结合学生画像、学习记录和生成题表现，辅助备课与个别指导。分析只在点击后开始。</p>
      </div>
      <select v-model="selectedClassId" class="class-select" aria-label="选择教学班">
        <option v-for="item in classes" :key="item.teachingClassId" :value="item.teachingClassId">
          {{ item.academicYear }}学年 第{{ item.semester }}学期 · {{ item.className }}
        </option>
      </select>
    </header>

    <div v-if="loading" class="panel loading-state">正在加载教学班…</div>
    <div v-else-if="pageError" class="panel error-state">
      {{ pageError }} <button class="secondary-button" @click="loadClasses">重新加载</button>
    </div>
    <div v-else-if="!selectedClass" class="panel empty-state">
      <strong>还没有可分析的教学班</strong>
      先创建本学期教学班并导入学生，学习数据会从学生端同步到这里。
      <div class="empty-action"><RouterLink class="primary-button" to="/teacher/classes">前往教学班</RouterLink></div>
    </div>

    <template v-else>
      <section class="analysis-context panel">
        <div>
          <span>当前教学班</span>
          <strong>{{ selectedClass.className }}</strong>
          <small>{{ selectedClass.academicYear }}学年 · 第{{ selectedClass.semester }}学期</small>
        </div>
        <div class="context-stat"><span>学生</span><strong>{{ selectedClass.studentCount }}</strong></div>
        <div class="context-stat"><span>已同步生成题</span><strong>{{ generatedQuestionCount }}</strong></div>
        <div class="context-stat"><span>错答记录</span><strong>{{ incorrectQuestionCount }}</strong></div>
      </section>

      <div class="analysis-tabs" role="tablist">
        <button :class="{ active: activeTab === 'class' }" @click="activeTab = 'class'">班级分析</button>
        <button :class="{ active: activeTab === 'student' }" @click="activeTab = 'student'">学生分析</button>
      </div>

      <div v-if="classDataLoading" class="panel loading-state">正在读取最新学习数据…</div>
      <template v-else-if="activeTab === 'class'">
        <div v-if="classError" class="notice error analysis-notice">{{ classError }}</div>
        <section class="panel result-panel">
          <div class="panel-head">
            <div>
              <h2>班级学习情况</h2>
              <p v-if="classAnalysis?.analysis">最近分析：{{ formatDateTime(classAnalysis.generatedAt) }}</p>
              <p v-else>生成题和学习记录会持续同步，分析由教师手动发起。</p>
            </div>
            <button class="primary-button" :disabled="classAnalysing" @click="runClassAnalysis">
              {{ classAnalysing ? '正在分析…' : classAnalysis?.analysis ? '重新分析' : '开始分析' }}
            </button>
          </div>

          <div v-if="classAnalysis?.analysis" class="result-body">
            <p class="overall-comment">{{ classAnalysis.analysis.overallComment }}</p>
            <div v-if="classProblems.length" class="problem-list">
              <article v-for="(item, index) in classProblems" :key="`${item.title}-${index}`" class="problem-card">
                <div class="problem-index">{{ index + 1 }}</div>
                <div>
                  <div class="problem-title"><strong>{{ item.title }}</strong><span>涉及 {{ item.studentCount }} 人</span></div>
                  <p>{{ item.evidence }}</p>
                  <div class="teacher-action"><span>教学建议</span>{{ item.teacherAction }}</div>
                  <div v-if="item.questionIds.length" class="evidence-row">
                    依据题目：<code v-for="id in item.questionIds" :key="id">{{ id }}</code>
                  </div>
                </div>
              </article>
            </div>
          </div>
          <div v-else class="empty-state compact-empty">
            <strong>尚未进行班级分析</strong>
            点击“开始分析”后，系统会根据当前教学班已有的真实学习记录生成一次结果。
          </div>
        </section>

        <section class="panel evidence-panel">
          <div class="panel-head"><div><h2>生成题反映的问题</h2><p>学生端生成内容实时同步，教师可直接查看。</p></div></div>
          <div v-if="questionSummary?.items.length" class="evidence-table-wrap">
            <table class="data-table">
              <thead><tr><th>知识点</th><th>涉及学生</th><th>生成题</th><th>错答</th><th>错答率</th></tr></thead>
              <tbody><tr v-for="item in questionSummary.items" :key="String(item.knowledgePointId)">
                <td><strong>{{ item.knowledgePointName }}</strong></td>
                <td>{{ item.studentCount }}</td><td>{{ item.generatedQuestionCount }}</td><td>{{ item.incorrectCount }}</td>
                <td>{{ Math.round(item.incorrectRate * 100) }}%</td>
              </tr></tbody>
            </table>
          </div>
          <div v-else class="empty-state compact-empty">本教学班暂无学生生成题记录。</div>
        </section>
      </template>

      <template v-else>
        <div class="student-analysis-grid">
          <aside class="panel student-list-panel">
            <div class="student-search"><input v-model="studentSearch" placeholder="搜索姓名或学号" /></div>
            <button
              v-for="student in filteredStudents"
              :key="student.studentId"
              class="student-row"
              :class="{ active: selectedStudentId === student.studentId }"
              @click="selectedStudentId = student.studentId"
            >
              <span class="student-avatar">{{ (student.studentName || '学').slice(0, 1) }}</span>
              <span><strong>{{ student.studentName || '未填写姓名' }}</strong><small>{{ student.studentNumber }} · {{ student.administrativeClass || '未填写行政班' }}</small></span>
            </button>
            <div v-if="!filteredStudents.length" class="empty-state compact-empty">没有匹配的学生。</div>
          </aside>

          <section class="panel student-result-panel">
            <div v-if="!selectedStudent" class="empty-state"><strong>请选择学生</strong>从左侧名单中选择一名学生查看学习情况。</div>
            <div v-else-if="studentDataLoading" class="loading-state">正在读取 {{ selectedStudent.studentName || selectedStudent.studentNumber }} 的学习数据…</div>
            <template v-else>
              <div class="panel-head">
                <div><h2>{{ selectedStudent.studentName || '未填写姓名' }}</h2><p>{{ selectedStudent.studentNumber }} · 最近活跃 {{ formatDateTime(selectedStudent.recentActivityAt) }}</p></div>
                <button class="primary-button" :disabled="studentAnalysing" @click="runStudentAnalysis">
                  {{ studentAnalysing ? '正在分析…' : studentAnalysis?.analysis ? '重新分析' : '开始分析' }}
                </button>
              </div>
              <div v-if="studentError" class="notice error analysis-notice">{{ studentError }}</div>
              <div class="student-result-body">
                <div class="profile-score-grid">
                  <div><span>综合</span><strong>{{ formatScore(studentProfile?.latestProfile?.overall_score) }}</strong></div>
                  <div><span>知识掌握</span><strong>{{ formatScore(studentProfile?.latestProfile?.knowledge_mastery_score) }}</strong></div>
                  <div><span>排障能力</span><strong>{{ formatScore(studentProfile?.latestProfile?.troubleshooting_score) }}</strong></div>
                  <div><span>自主学习</span><strong>{{ formatScore(studentProfile?.latestProfile?.autonomy_score) }}</strong></div>
                  <div><span>学习投入</span><strong>{{ formatScore(studentProfile?.latestProfile?.engagement_score) }}</strong></div>
                </div>

                <div v-if="studentAnalysis?.analysis" class="student-analysis-content">
                  <div class="analysis-time">最近分析：{{ formatDateTime(studentAnalysis.generatedAt) }}</div>
                  <p class="overall-comment">{{ studentAnalysis.analysis.overallComment }}</p>
                  <article v-for="item in studentAnalysis.analysis.focusAreas" :key="item.dimension" class="focus-card">
                    <div><strong>{{ item.label }}</strong><span :class="`priority-${item.priority || 'medium'}`">{{ item.priority === 'high' ? '优先关注' : '持续观察' }}</span></div>
                    <p>{{ item.evidence }}</p>
                    <div class="teacher-action"><span>建议做法</span>{{ item.teacherAction }}</div>
                  </article>
                </div>
                <div v-else class="empty-state compact-empty">
                  <strong>尚未进行学生分析</strong>
                  当前可查看 {{ studentProfile?.recentAttempts.length || 0 }} 条近期作答和 {{ studentProfile?.personalSignals?.length || 0 }} 条学习信号。点击“开始分析”后生成结果。
                </div>
              </div>
            </template>
          </section>
        </div>
      </template>
    </template>
  </div>
</template>

<style scoped>
.class-select { min-width: 330px; min-height: 40px; padding: 0 12px; border: 1px solid #d5dee9; border-radius: 7px; background: #fff; color: #27364e; font-size: 13px; }
.analysis-context { display: grid; grid-template-columns: minmax(280px, 1fr) repeat(3, 150px); align-items: stretch; margin-bottom: 18px; overflow: hidden; }
.analysis-context > div { display: grid; align-content: center; min-height: 94px; padding: 18px 22px; border-right: 1px solid #edf0f4; }
.analysis-context > div:last-child { border-right: 0; }
.analysis-context span, .analysis-context small { color: #7d899a; font-size: 12px; }
.analysis-context strong { margin: 5px 0 3px; color: #182843; font-size: 18px; }
.context-stat { text-align: center; }
.context-stat strong { font-size: 25px; }
.analysis-tabs { display: flex; gap: 24px; margin: 0 0 14px; border-bottom: 1px solid #dfe5ed; }
.analysis-tabs button { padding: 11px 2px; border: 0; border-bottom: 2px solid transparent; background: none; color: #718096; font-size: 14px; font-weight: 650; cursor: pointer; }
.analysis-tabs button.active { border-color: #245eae; color: #174d93; }
.result-panel, .evidence-panel { margin-bottom: 18px; }
.result-body, .student-result-body { padding: 22px; }
.overall-comment { margin: 0 0 20px; padding: 14px 16px; border-left: 3px solid #2c67b5; background: #f5f8fc; color: #35455d; font-size: 13px; line-height: 1.75; }
.problem-list { display: grid; gap: 12px; }
.problem-card { display: grid; grid-template-columns: 30px 1fr; gap: 12px; padding: 16px; border: 1px solid #e3e8ef; border-radius: 8px; }
.problem-index { display: grid; width: 28px; height: 28px; place-items: center; border-radius: 6px; background: #eaf1fb; color: #1f5ca9; font-size: 12px; font-weight: 750; }
.problem-title { display: flex; justify-content: space-between; gap: 15px; }
.problem-title strong { font-size: 14px; }
.problem-title span { color: #8b5d18; font-size: 12px; }
.problem-card p, .focus-card p { margin: 8px 0; color: #637187; font-size: 12px; line-height: 1.65; }
.teacher-action { padding: 10px 12px; border-radius: 6px; background: #f7f9fc; color: #35445a; font-size: 12px; line-height: 1.6; }
.teacher-action span { margin-right: 8px; color: #1f5ca9; font-weight: 700; }
.evidence-row { margin-top: 9px; color: #8a96a6; font-size: 11px; }
.evidence-row code { margin-left: 6px; padding: 2px 5px; border-radius: 4px; background: #f1f3f6; }
.evidence-table-wrap { overflow-x: auto; }
.analysis-notice { margin: 0 0 12px; }
.compact-empty { padding: 34px 20px; }
.empty-action { margin-top: 16px; }
.student-analysis-grid { display: grid; grid-template-columns: 300px minmax(0, 1fr); gap: 16px; align-items: start; }
.student-list-panel { max-height: 690px; overflow: auto; }
.student-search { position: sticky; top: 0; z-index: 2; padding: 13px; border-bottom: 1px solid #edf0f4; background: #fff; }
.student-search input { width: 100%; height: 38px; padding: 0 11px; border: 1px solid #d8e0ea; border-radius: 7px; outline: none; }
.student-row { display: flex; width: 100%; gap: 10px; padding: 12px 14px; border: 0; border-bottom: 1px solid #edf0f4; background: #fff; color: #2e3c52; text-align: left; cursor: pointer; }
.student-row:hover, .student-row.active { background: #f3f7fc; }
.student-row.active { box-shadow: inset 3px 0 #2865b5; }
.student-avatar { display: grid; width: 34px; height: 34px; flex: 0 0 auto; place-items: center; border-radius: 50%; background: #e8eef7; color: #245690; font-weight: 700; }
.student-row strong, .student-row small { display: block; }
.student-row strong { font-size: 13px; }
.student-row small { margin-top: 4px; color: #8894a5; font-size: 11px; }
.profile-score-grid { display: grid; grid-template-columns: repeat(5, 1fr); margin-bottom: 20px; border: 1px solid #e5eaf0; border-radius: 8px; overflow: hidden; }
.profile-score-grid div { display: grid; gap: 5px; padding: 14px; border-right: 1px solid #e8edf3; }
.profile-score-grid div:last-child { border-right: 0; }
.profile-score-grid span { color: #7d899a; font-size: 11px; }
.profile-score-grid strong { color: #1c4f91; font-size: 20px; }
.analysis-time { margin-bottom: 9px; color: #8894a6; font-size: 11px; }
.focus-card { margin-top: 11px; padding: 15px; border: 1px solid #e3e8ef; border-radius: 8px; }
.focus-card > div:first-child { display: flex; align-items: center; justify-content: space-between; }
.focus-card strong { font-size: 14px; }
.focus-card > div:first-child span { padding: 3px 7px; border-radius: 999px; font-size: 10px; }
.priority-high { background: #fff0e8; color: #a84c18; }
.priority-medium, .priority-low { background: #edf3fb; color: #356196; }
@media (max-width: 1080px) {
  .analysis-context { grid-template-columns: 1fr 1fr; }
  .analysis-context > div { border-bottom: 1px solid #edf0f4; }
  .student-analysis-grid { grid-template-columns: 250px minmax(0, 1fr); }
  .profile-score-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 820px) {
  .class-select { width: 100%; min-width: 0; }
  .analysis-context, .student-analysis-grid { grid-template-columns: 1fr; }
  .student-list-panel { max-height: 320px; }
  .profile-score-grid { grid-template-columns: repeat(2, 1fr); }
  .panel-head { flex-direction: column; }
  .panel-head .primary-button { width: 100%; }
}
</style>
