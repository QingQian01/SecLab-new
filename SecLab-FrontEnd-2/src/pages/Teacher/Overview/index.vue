<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  getApiErrorMessage,
  getGeneratedQuestionSummary,
  getTeachingClassAnalysis,
  getTeachingClassCourses,
  getTeachingClasses,
  getTeachingClassStudents,
  type TeacherGeneratedQuestionSummary,
  type TeachingClassAnalysisDto,
  type TeachingClassCourseDto,
  type TeachingClassDto,
  type TeachingClassStudentDto,
} from '../../../api'
import '../teacher-page.css'

const classes = ref<TeachingClassDto[]>([])
const selectedId = ref<number | null>(null)
const students = ref<TeachingClassStudentDto[]>([])
const courses = ref<TeachingClassCourseDto[]>([])
const summary = ref<TeacherGeneratedQuestionSummary | null>(null)
const analysis = ref<TeachingClassAnalysisDto | null>(null)
const loading = ref(true)
const detailLoading = ref(false)
const error = ref('')

const selectedClass = computed(() => classes.value.find((item) => item.teachingClassId === selectedId.value) || null)
const recentStudents = computed(() => [...students.value]
  .filter((item) => item.recentActivityAt)
  .sort((a, b) => String(b.recentActivityAt).localeCompare(String(a.recentActivityAt)))
  .slice(0, 5))
const generatedCount = computed(() => summary.value?.items.reduce((total, item) => total + item.generatedQuestionCount, 0) || 0)

const formatDateTime = (value?: string | null) => value
  ? new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(value))
  : '暂无记录'

const loadDetail = async () => {
  if (!selectedId.value) return
  detailLoading.value = true
  const classId = selectedId.value
  const [studentResult, courseResult, summaryResult, analysisResult] = await Promise.allSettled([
    getTeachingClassStudents(classId),
    getTeachingClassCourses(classId),
    getGeneratedQuestionSummary(classId),
    getTeachingClassAnalysis(classId),
  ])
  if (classId !== selectedId.value) return
  students.value = studentResult.status === 'fulfilled' ? studentResult.value : []
  courses.value = courseResult.status === 'fulfilled' ? courseResult.value : []
  summary.value = summaryResult.status === 'fulfilled' ? summaryResult.value : null
  analysis.value = analysisResult.status === 'fulfilled' ? analysisResult.value : null
  detailLoading.value = false
}

const loadClasses = async () => {
  loading.value = true
  error.value = ''
  try {
    classes.value = (await getTeachingClasses()).filter((item) => item.status !== 'ARCHIVED')
    if (!selectedId.value || !classes.value.some((item) => item.teachingClassId === selectedId.value)) {
      selectedId.value = classes.value[0]?.teachingClassId || null
    }
  } catch (err) {
    error.value = getApiErrorMessage(err, '教学班加载失败，请稍后重试。')
  } finally {
    loading.value = false
  }
}

watch(selectedId, () => void loadDetail())
onMounted(() => void loadClasses())
</script>

<template>
  <div class="teacher-page overview-page">
    <header class="page-head">
      <div>
        <h1>教学概览</h1>
        <p>查看教学班当前进度、学生学习动态和最近一次班级分析。</p>
      </div>
      <select v-model="selectedId" class="class-select" aria-label="选择教学班">
        <option v-for="item in classes" :key="item.teachingClassId" :value="item.teachingClassId">
          {{ item.academicYear }}学年 第{{ item.semester }}学期 · {{ item.className }}
        </option>
      </select>
    </header>

    <div v-if="loading" class="panel loading-state">正在加载教学数据…</div>
    <div v-else-if="error" class="panel error-state">{{ error }} <button class="secondary-button" @click="loadClasses">重新加载</button></div>
    <div v-else-if="!selectedClass" class="panel empty-state">
      <strong>还没有教学班</strong>
      创建本学期的教学班后，教学进度和学生数据会显示在这里。
      <div style="margin-top: 16px"><RouterLink class="primary-button" to="/teacher/classes">创建教学班</RouterLink></div>
    </div>

    <template v-else>
      <section class="overview-banner">
        <div>
          <span class="eyebrow">当前教学班</span>
          <h2>{{ selectedClass.className }}</h2>
          <p>{{ selectedClass.teacherName || '任课教师' }} · {{ selectedClass.academicYear }}学年 第{{ selectedClass.semester }}学期</p>
        </div>
        <div class="banner-status"><span class="status-dot"></span>授课中</div>
      </section>

      <section class="stat-row">
        <div class="stat-cell"><span>学生人数</span><strong>{{ selectedClass.studentCount }}</strong><small>已导入名单</small></div>
        <div class="stat-cell"><span>教学课程</span><strong>{{ selectedClass.courseCount }}</strong><small>按顺序安排</small></div>
        <div class="stat-cell"><span>学生生成题</span><strong>{{ generatedCount }}</strong><small>实时同步</small></div>
        <div class="stat-cell"><span>最近活动</span><strong class="date-stat">{{ formatDateTime(selectedClass.lastActiveAt) }}</strong><small>学生学习记录</small></div>
      </section>

      <div class="overview-grid" :class="{ pending: detailLoading }">
        <section class="panel ai-panel">
          <div class="panel-head">
            <div><h2>最近教学分析</h2><p>分析操作集中在“教学分析”页面</p></div>
            <RouterLink class="text-link" :to="`/teacher/analysis?classId=${selectedClass.teachingClassId}`">进入教学分析</RouterLink>
          </div>
          <div v-if="analysis?.analysis" class="analysis-summary">
            <span>分析时间 {{ formatDateTime(analysis.generatedAt) }}</span>
            <p>{{ analysis.analysis.overallComment }}</p>
            <small>共整理 {{ analysis.analysis.commonProblems?.length || 0 }} 项班级共性问题</small>
          </div>
          <div v-else class="analysis-empty compact-analysis-empty">
            <strong>尚未进行班级分析</strong>
            <p>学生数据会持续同步，需要时可前往“教学分析”手动生成结果。</p>
          </div>
        </section>

        <section class="panel progress-panel">
          <div class="panel-head"><div><h2>教学安排</h2><p>当前教学班关联的课程顺序</p></div><RouterLink to="/teacher/classes" class="text-link">调整安排</RouterLink></div>
          <div v-if="courses.length" class="course-rail">
            <div v-for="(course, index) in courses" :key="course.courseId" class="rail-item">
              <span class="rail-number">{{ index + 1 }}</span>
              <div><strong>{{ course.courseName }}</strong><small>{{ course.plannedStartDate || '未设置日期' }}<template v-if="course.plannedEndDate"> 至 {{ course.plannedEndDate }}</template></small></div>
            </div>
          </div>
          <div v-else class="empty-state compact">尚未安排课程</div>
        </section>
      </div>

      <section class="panel recent-panel">
        <div class="panel-head"><div><h2>最近学生动态</h2><p>来自学生端的学习活动时间</p></div></div>
        <div class="data-table-wrap">
          <table class="data-table">
            <thead><tr><th>学生</th><th>学号</th><th>行政班</th><th>最近活动</th></tr></thead>
            <tbody>
              <tr v-for="item in recentStudents" :key="item.studentId">
                <td><strong>{{ item.studentName || '未填写姓名' }}</strong></td><td>{{ item.studentNumber }}</td><td>{{ item.administrativeClass || '—' }}</td><td>{{ formatDateTime(item.recentActivityAt) }}</td>
              </tr>
            </tbody>
          </table>
          <div v-if="!recentStudents.length" class="empty-state compact">暂无学生学习活动</div>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.class-select { min-width: 340px; height: 40px; padding: 0 34px 0 12px; border: 1px solid #d7dfe9; border-radius: 7px; background: #fff; color: #2d3b50; font-size: 13px; }
.overview-banner { display: flex; align-items: center; justify-content: space-between; padding: 25px 28px; border: 1px solid #dce5f0; border-radius: 10px 10px 0 0; background: #fff; }
.eyebrow { color: #1e5fbf; font-size: 11px; font-weight: 750; letter-spacing: .08em; }
.overview-banner h2 { margin: 6px 0 3px; font-size: 22px; }
.overview-banner p { margin: 0; color: #7b8798; font-size: 12px; }
.banner-status { color: #486176; font-size: 12px; }
.stat-row { display: grid; grid-template-columns: repeat(4, 1fr); margin-bottom: 22px; border: solid #e2e8f0; border-width: 0 1px 1px; border-radius: 0 0 10px 10px; background: #fff; }
.stat-cell { display: grid; gap: 3px; padding: 18px 24px; border-right: 1px solid #edf1f5; }
.stat-cell:last-child { border: 0; }
.stat-cell span, .stat-cell small { color: #8290a4; font-size: 11px; }
.stat-cell strong { color: #173d78; font-size: 25px; font-weight: 720; }
.stat-cell .date-stat { margin-top: 5px; color: #263a55; font-size: 15px; }
.overview-grid { display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(310px, .85fr); gap: 20px; }
.overview-grid.pending { opacity: .6; }
.analysis-empty { display: grid; justify-items: center; min-height: 280px; place-content: center; padding: 34px; text-align: center; }
.analysis-empty strong { font-size: 15px; }
.analysis-empty p { max-width: 540px; margin: 7px 0; color: #7c899a; font-size: 12px; line-height: 1.7; }
.analysis-empty span { color: #9a6f21; font-size: 11px; }
.compact-analysis-empty { min-height: 190px; }
.analysis-summary { min-height: 190px; padding: 26px 22px; }
.analysis-summary span, .analysis-summary small { color: #8793a4; font-size: 11px; }
.analysis-summary p { margin: 12px 0 16px; padding: 14px 16px; border-left: 3px solid #346fc7; background: #f5f8fc; color: #344258; font-size: 13px; line-height: 1.75; }
.text-link { color: #2862af; font-size: 12px; }
.course-rail { padding: 18px 20px 22px; }
.rail-item { position: relative; display: flex; gap: 12px; padding-bottom: 22px; }
.rail-item:not(:last-child)::after { position: absolute; top: 25px; bottom: 2px; left: 12px; width: 1px; background: #dfe6ef; content: ''; }
.rail-number { z-index: 1; display: grid; width: 25px; height: 25px; flex: 0 0 auto; place-items: center; border-radius: 50%; background: #e9f0fa; color: #275da9; font-size: 11px; font-weight: 700; }
.rail-item strong, .rail-item small { display: block; }
.rail-item strong { padding-top: 2px; font-size: 13px; }
.rail-item small { margin-top: 4px; color: #8490a1; font-size: 11px; }
.recent-panel { margin-top: 20px; }
.compact { padding: 28px; }
@media (max-width: 1040px) { .overview-grid { grid-template-columns: 1fr; } .stat-row { grid-template-columns: repeat(2, 1fr); } .stat-cell:nth-child(2) { border-right: 0; } .stat-cell:nth-child(-n+2) { border-bottom: 1px solid #edf1f5; } }
@media (max-width: 680px) { .class-select { width: 100%; min-width: 0; } .overview-banner { align-items: flex-start; } .stat-row { grid-template-columns: 1fr 1fr; } .stat-cell { padding: 15px; } }
</style>
