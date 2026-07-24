<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  getApiErrorMessage,
  getGeneratedQuestionSummary,
  getTeacherCourseList,
  getTeacherGeneratedQuestionRecords,
  getTeachingClasses,
  setGeneratedQuestionTypical,
  type TeacherGeneratedQuestionRecord,
  type TeacherGeneratedQuestionSummary,
  type TeachingClassDto,
} from '../../../api'
import type { Course } from '../../../types/course'
import '../teacher-page.css'

const records = ref<TeacherGeneratedQuestionRecord[]>([])
const classes = ref<TeachingClassDto[]>([])
const courses = ref<Course[]>([])
const total = ref(0)
const loading = ref(true)
const error = ref('')
const selected = ref<TeacherGeneratedQuestionRecord | null>(null)
const summary = ref<TeacherGeneratedQuestionSummary | null>(null)
const summaryLoading = ref(false)
const page = ref(1)
const filters = ref({ teachingClassId: '', courseId: '', answerResult: '', typicalOnly: false, dateFrom: '', dateTo: '' })
let refreshTimer: number | undefined

const selectedClassName = computed(() => classes.value.find((item) => item.teachingClassId === Number(filters.value.teachingClassId))?.className || '')
const typeText = (value?: string | null) => ({ single_choice: '单选题', fill_blank: '填空题', short_answer: '简答题' }[value || ''] || value || '未分类')
const resultText = (item: TeacherGeneratedQuestionRecord) => !item.latestAttempt ? '未作答' : item.latestAttempt.isCorrect === true ? '正确' : item.latestAttempt.isCorrect === false ? '错误' : '已作答'
const resultClass = (item: TeacherGeneratedQuestionRecord) => !item.latestAttempt ? 'gray' : item.latestAttempt.isCorrect === true ? 'green' : item.latestAttempt.isCorrect === false ? 'red' : 'amber'
const formatTime = (value?: string | null) => value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '—'

const loadRecords = async (quiet = false) => {
  if (!quiet) loading.value = true
  error.value = ''
  try {
    const data = await getTeacherGeneratedQuestionRecords({
      teachingClassId: filters.value.teachingClassId ? Number(filters.value.teachingClassId) : undefined,
      courseId: filters.value.courseId ? Number(filters.value.courseId) : undefined,
      answerResult: filters.value.answerResult as '' | 'correct' | 'incorrect' | 'attempted' | 'unanswered',
      typicalOnly: filters.value.typicalOnly,
      dateFrom: filters.value.dateFrom || undefined,
      dateTo: filters.value.dateTo || undefined,
      page: page.value,
      size: 20,
    })
    records.value = data.items; total.value = data.total
  } catch (err) { error.value = getApiErrorMessage(err, '生成题记录加载失败，请稍后重试。') }
  finally { loading.value = false }
}

const loadSummary = async () => {
  if (!filters.value.teachingClassId) { summary.value = null; return }
  summaryLoading.value = true
  try { summary.value = await getGeneratedQuestionSummary(Number(filters.value.teachingClassId)) }
  catch { summary.value = null }
  finally { summaryLoading.value = false }
}

const applyFilters = async () => { page.value = 1; await Promise.all([loadRecords(), loadSummary()]) }
const resetFilters = () => { filters.value = { teachingClassId: '', courseId: '', answerResult: '', typicalOnly: false, dateFrom: '', dateTo: '' }; summary.value = null; void applyFilters() }
const toggleTypical = async (item: TeacherGeneratedQuestionRecord) => {
  const next = !item.isTypical
  try { await setGeneratedQuestionTypical(item.generatedQuestionId, next); item.isTypical = next; if (selected.value?.generatedQuestionId === item.generatedQuestionId) selected.value.isTypical = next }
  catch (err) { error.value = getApiErrorMessage(err, '代表题标记失败。') }
}
const goPage = (next: number) => { page.value = next; void loadRecords() }

onMounted(async () => {
  const [classResult, courseResult] = await Promise.allSettled([getTeachingClasses(), getTeacherCourseList()])
  classes.value = classResult.status === 'fulfilled' ? classResult.value : []
  courses.value = courseResult.status === 'fulfilled' ? courseResult.value : []
  await loadRecords()
  refreshTimer = window.setInterval(() => void loadRecords(true), 30000)
})
onBeforeUnmount(() => { if (refreshTimer) window.clearInterval(refreshTimer) })
</script>

<template>
  <div class="teacher-page generated-page">
    <header class="page-head"><div><h1>生成题记录</h1><p>学生端生成题目后直接同步到这里，教师可查看题目及作答情况。</p></div><button class="secondary-button" @click="loadRecords()">刷新记录</button></header>

    <section class="panel filter-box">
      <div class="field"><label>教学班</label><select v-model="filters.teachingClassId"><option value="">全部教学班</option><option v-for="item in classes" :key="item.teachingClassId" :value="item.teachingClassId">{{ item.className }}</option></select></div>
      <div class="field"><label>课程</label><select v-model="filters.courseId"><option value="">全部课程</option><option v-for="item in courses" :key="item.id" :value="item.id">{{ item.name }}</option></select></div>
      <div class="field"><label>作答情况</label><select v-model="filters.answerResult"><option value="">全部</option><option value="correct">回答正确</option><option value="incorrect">回答错误</option><option value="attempted">已作答</option><option value="unanswered">未作答</option></select></div>
      <div class="field"><label>生成日期从</label><input v-model="filters.dateFrom" type="date" /></div>
      <div class="field"><label>到</label><input v-model="filters.dateTo" type="date" /></div>
      <label class="typical-check"><input v-model="filters.typicalOnly" type="checkbox" /> 只看我标记的代表题</label>
      <button class="primary-button" @click="applyFilters">查询</button><button class="secondary-button" @click="resetFilters">重置</button>
    </section>

    <section v-if="filters.teachingClassId" class="panel summary-panel">
      <div class="panel-head"><div><h2>{{ selectedClassName }} · 共性题目概览</h2><p>系统按知识点聚合当前学生生成题与作答结果</p></div><span class="tag gray">实时统计</span></div>
      <div v-if="summaryLoading" class="loading-state">正在汇总…</div>
      <div v-else-if="summary?.items.length" class="summary-grid">
        <div v-for="item in summary.items.slice(0, 4)" :key="String(item.knowledgePointId)"><strong>{{ item.knowledgePointName }}</strong><span>{{ item.generatedQuestionCount }} 道题 · {{ item.studentCount }} 名学生</span><em>错误作答 {{ Math.round(item.incorrectRate * 100) }}%</em></div>
      </div>
      <div v-else class="empty-state compact">该教学班暂无可汇总的生成题。</div>
    </section>

    <section class="panel records-panel">
      <div class="panel-head"><div><h2>题目记录</h2><p>每 30 秒自动同步一次，共 {{ total }} 条</p></div></div>
      <div v-if="error" class="notice error" style="margin: 16px 20px">{{ error }}</div>
      <div v-if="loading" class="loading-state">正在加载题目…</div>
      <div v-else class="data-table-wrap">
        <table class="data-table"><thead><tr><th>题目</th><th>学生</th><th>教学班 / 课程</th><th>知识点</th><th>作答</th><th>生成时间</th><th>操作</th></tr></thead>
          <tbody><tr v-for="item in records" :key="item.generatedQuestionId">
            <td class="question-cell"><strong>{{ item.title }}</strong><span>{{ typeText(item.questionType) }} · {{ item.difficulty || '未标难度' }}</span></td>
            <td><strong>{{ item.student.studentName }}</strong><div class="subtle">{{ item.student.studentNumber || '无学号' }}</div></td>
            <td>{{ item.teachingClassName }}<div class="subtle">{{ item.courseName || '未关联课程' }}</div></td><td>{{ item.knowledgePointName || '未标注' }}</td>
            <td><span class="result-tag" :class="resultClass(item)">{{ resultText(item) }}</span><div v-if="item.latestAttempt" class="subtle">{{ item.latestAttempt.score }} 分</div></td><td>{{ formatTime(item.generatedAt) }}</td>
            <td><div class="row-actions"><button @click="selected = item">查看</button><button :class="{ active: item.isTypical }" @click="toggleTypical(item)">{{ item.isTypical ? '已标记' : '标为代表题' }}</button></div></td>
          </tr></tbody>
        </table>
        <div v-if="!records.length" class="empty-state"><strong>暂无生成题记录</strong>学生在训练中生成题目后，会同步显示在这里。</div>
      </div>
      <div v-if="total > 20" class="pagination"><button :disabled="page === 1" @click="goPage(page - 1)">上一页</button><span>第 {{ page }} 页</span><button :disabled="page * 20 >= total" @click="goPage(page + 1)">下一页</button></div>
    </section>

    <div v-if="selected" class="drawer-layer" @click.self="selected = null"><aside class="question-drawer"><div class="drawer-head"><div><span>{{ selected.teachingClassName }} · {{ selected.student.studentName }}</span><h2>{{ selected.title }}</h2></div><button @click="selected = null">×</button></div><div class="drawer-body">
      <div class="drawer-meta"><span class="tag">{{ typeText(selected.questionType) }}</span><span>{{ selected.courseName || '未关联课程' }}</span><span>{{ selected.knowledgePointName || '未标注知识点' }}</span><span>{{ formatTime(selected.generatedAt) }}</span></div>
      <section><h3>题目内容</h3><p class="stem">{{ selected.stem }}</p><ol v-if="selected.options.length"><li v-for="option in selected.options" :key="option">{{ option }}</li></ol></section>
      <section v-if="selected.generationReason"><h3>生成原因</h3><p>{{ selected.generationReason }}</p></section>
      <section v-if="selected.latestAttempt"><h3>学生最近作答</h3><p>{{ selected.latestAttempt.answer }}</p><div class="answer-score">{{ resultText(selected) }} · {{ selected.latestAttempt.score }} 分 · {{ formatTime(selected.latestAttempt.submittedAt) }}</div></section>
      <section><h3>参考信息</h3><p><strong>参考答案：</strong>{{ selected.referenceAnswer || selected.standardAnswer || '暂无' }}</p><p><strong>解析：</strong>{{ selected.explanation || '暂无' }}</p></section>
    </div><div class="drawer-actions"><button class="secondary-button" :class="{ active: selected.isTypical }" @click="toggleTypical(selected)">{{ selected.isTypical ? '取消代表题标记' : '标为代表题' }}</button></div></aside></div>
  </div>
</template>

<style scoped>
.filter-box { display: grid; grid-template-columns: 1.25fr 1.1fr .9fr .85fr .85fr auto auto auto; gap: 10px; align-items: end; padding: 15px; }.typical-check { display: flex; min-height: 39px; align-items: center; gap: 6px; color: #5f6d80; font-size: 11px; white-space: nowrap; }.summary-panel, .records-panel { margin-top: 16px; }.summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0; }.summary-grid > div { display: grid; gap: 5px; padding: 17px 20px; border-right: 1px solid #edf1f5; }.summary-grid > div:last-child { border: 0; }.summary-grid strong { font-size: 13px; }.summary-grid span { color: #7d899b; font-size: 11px; }.summary-grid em { color: #9b5b26; font-size: 11px; font-style: normal; }.question-cell { min-width: 230px; }.question-cell strong, .question-cell span { display: block; }.question-cell strong { max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.question-cell span { margin-top: 3px; color: #8490a1; font-size: 11px; }.result-tag { display: inline-flex; padding: 2px 7px; border-radius: 999px; font-size: 10px; font-weight: 700; }.result-tag.green { background: #e8f7ef; color: #237751; }.result-tag.red { background: #fff0ef; color: #b33e35; }.result-tag.gray { background: #f0f2f5; color: #788396; }.result-tag.amber { background: #fff5df; color: #8c641d; }.row-actions { display: flex; gap: 9px; white-space: nowrap; }.row-actions button { padding: 0; border: 0; background: none; color: #486888; font-size: 11px; cursor: pointer; }.row-actions button.active { color: #b06b1b; }.pagination { display: flex; align-items: center; justify-content: flex-end; gap: 12px; padding: 13px 18px; border-top: 1px solid #e8edf3; color: #718095; font-size: 11px; }.pagination button { border: 1px solid #d7dfe9; border-radius: 5px; background: #fff; color: #40516a; font-size: 11px; }.drawer-layer { position: fixed; inset: 0; z-index: 70; background: rgba(15, 23, 42, .38); }.question-drawer { position: absolute; inset: 0 0 0 auto; display: flex; width: min(620px, 92vw); flex-direction: column; background: #fff; box-shadow: -18px 0 50px rgba(15, 23, 42, .16); }.drawer-head { display: flex; align-items: flex-start; justify-content: space-between; padding: 22px 25px; border-bottom: 1px solid #e6ebf1; }.drawer-head span { color: #7b8798; font-size: 11px; }.drawer-head h2 { margin: 6px 0 0; font-size: 19px; }.drawer-head button { border: 0; background: none; color: #748094; font-size: 22px; cursor: pointer; }.drawer-body { flex: 1; padding: 22px 25px; overflow: auto; }.drawer-meta { display: flex; flex-wrap: wrap; gap: 9px; color: #788497; font-size: 11px; }.drawer-body section { padding: 18px 0; border-bottom: 1px solid #edf1f5; }.drawer-body h3 { margin: 0 0 9px; font-size: 13px; }.drawer-body p, .drawer-body li { color: #5f6d80; font-size: 12px; line-height: 1.75; }.stem { padding: 14px; border-radius: 7px; background: #f7f9fb; color: #28384f !important; }.answer-score { color: #2c65af; font-size: 11px; }.drawer-actions { padding: 15px 25px; border-top: 1px solid #e6ebf1; }.drawer-actions button.active { border-color: #d7a65c; color: #9b611c; }
@media (max-width: 1200px) { .filter-box { grid-template-columns: repeat(4, 1fr); }.summary-grid { grid-template-columns: repeat(2, 1fr); }.summary-grid > div:nth-child(2) { border-right: 0; } }
@media (max-width: 680px) { .filter-box, .summary-grid { grid-template-columns: 1fr; }.summary-grid > div { border-right: 0; border-bottom: 1px solid #edf1f5; } }
</style>
