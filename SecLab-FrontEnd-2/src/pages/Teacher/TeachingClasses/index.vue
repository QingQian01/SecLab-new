<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  archiveTeachingClass,
  confirmTeachingClassImport,
  createTeachingClass,
  getApiErrorMessage,
  getTeacherCourseList,
  getTeachingClassCourses,
  getTeachingClasses,
  getTeachingClassStudents,
  previewTeachingClassImport,
  removeTeachingClassStudent,
  replaceTeachingClassCourses,
  updateTeachingClass,
  type TeachingClassCourseDto,
  type TeachingClassDto,
  type TeachingClassImportPreviewDto,
  type TeachingClassSavePayload,
  type TeachingClassStudentDto,
} from '../../../api'
import type { Course } from '../../../types/course'
import '../teacher-page.css'

type CoursePlan = { courseId: number; teachingOrder: number; plannedStartDate: string; plannedEndDate: string }

const classes = ref<TeachingClassDto[]>([])
const selected = ref<TeachingClassDto | null>(null)
const students = ref<TeachingClassStudentDto[]>([])
const arrangedCourses = ref<TeachingClassCourseDto[]>([])
const courseLibrary = ref<Course[]>([])
const tab = ref<'students' | 'courses'>('students')
const loading = ref(true)
const detailLoading = ref(false)
const error = ref('')
const notice = ref('')
const showClassModal = ref(false)
const editingClass = ref<TeachingClassDto | null>(null)
const savingClass = ref(false)
const classForm = ref<TeachingClassSavePayload>({ className: '', academicYear: '2026-2027', semester: 1, startDate: null, endDate: null })
const showImportModal = ref(false)
const importPreview = ref<TeachingClassImportPreviewDto | null>(null)
const importFile = ref<File | null>(null)
const importing = ref(false)
const showCourseModal = ref(false)
const coursePlans = ref<CoursePlan[]>([])
const savingCourses = ref(false)

const activeClasses = computed(() => classes.value.filter((item) => item.status !== 'ARCHIVED'))
const selectedCourseIds = computed(() => new Set(coursePlans.value.map((item) => item.courseId)))
const availableCourses = computed(() => courseLibrary.value.filter((item) => !selectedCourseIds.value.has(item.id)))
const courseName = (courseId: number) => courseLibrary.value.find((item) => item.id === courseId)?.name || `课程 ${courseId}`
const semesterLabel = (item: TeachingClassDto) => `${item.academicYear}学年 · 第${item.semester}学期`
const formatDateTime = (value?: string | null) => value ? new Date(value).toLocaleString('zh-CN', { hour12: false }) : '暂无记录'

const loadClassDetail = async (item: TeachingClassDto) => {
  selected.value = item
  detailLoading.value = true
  notice.value = ''
  const [studentResult, courseResult] = await Promise.allSettled([
    getTeachingClassStudents(item.teachingClassId),
    getTeachingClassCourses(item.teachingClassId),
  ])
  if (selected.value?.teachingClassId !== item.teachingClassId) return
  students.value = studentResult.status === 'fulfilled' ? studentResult.value : []
  arrangedCourses.value = courseResult.status === 'fulfilled' ? courseResult.value : []
  if (studentResult.status === 'rejected' || courseResult.status === 'rejected') notice.value = '部分教学班数据暂时未能加载，请稍后重试。'
  detailLoading.value = false
}

const load = async () => {
  loading.value = true
  error.value = ''
  try {
    const [classData, courses] = await Promise.all([getTeachingClasses(), getTeacherCourseList()])
    classes.value = classData
    courseLibrary.value = courses
    const current = selected.value
      ? classData.find((item) => item.teachingClassId === selected.value?.teachingClassId)
      : activeClasses.value[0]
    if (current) await loadClassDetail(current)
  } catch (err) {
    error.value = getApiErrorMessage(err, '教学班加载失败，请稍后重试。')
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editingClass.value = null
  classForm.value = { className: '', academicYear: '2026-2027', semester: 1, startDate: null, endDate: null }
  showClassModal.value = true
}

const openEdit = () => {
  if (!selected.value?.canManage) return
  editingClass.value = selected.value
  classForm.value = {
    className: selected.value.className,
    academicYear: selected.value.academicYear,
    semester: selected.value.semester,
    startDate: selected.value.startDate || null,
    endDate: selected.value.endDate || null,
  }
  showClassModal.value = true
}

const saveClass = async () => {
  if (!classForm.value.className.trim() || !/^\d{4}-\d{4}$/.test(classForm.value.academicYear)) return
  savingClass.value = true
  try {
    const payload = { ...classForm.value, className: classForm.value.className.trim() }
    const saved = editingClass.value
      ? await updateTeachingClass(editingClass.value.teachingClassId, payload)
      : await createTeachingClass(payload)
    showClassModal.value = false
    await load()
    const refreshed = classes.value.find((item) => item.teachingClassId === saved.teachingClassId)
    if (refreshed) await loadClassDetail(refreshed)
  } catch (err) {
    notice.value = getApiErrorMessage(err, '教学班保存失败，请检查填写内容。')
  } finally {
    savingClass.value = false
  }
}

const archiveCurrent = async () => {
  if (!selected.value?.canManage || !window.confirm(`确定归档“${selected.value.className}”吗？学生账号和学习记录会保留。`)) return
  await archiveTeachingClass(selected.value.teachingClassId)
  selected.value = null
  await load()
}

const openImport = () => {
  importFile.value = null
  importPreview.value = null
  showImportModal.value = true
}

const chooseFile = (event: Event) => {
  importFile.value = (event.target as HTMLInputElement).files?.[0] || null
  importPreview.value = null
}

const previewImport = async () => {
  if (!selected.value || !importFile.value) return
  importing.value = true
  try { importPreview.value = await previewTeachingClassImport(selected.value.teachingClassId, importFile.value) }
  catch (err) { notice.value = getApiErrorMessage(err, '名单校验失败，请检查 Excel 格式。') }
  finally { importing.value = false }
}

const confirmImport = async () => {
  if (!selected.value || !importPreview.value || importPreview.value.errorRows.length) return
  importing.value = true
  try {
    const result = await confirmTeachingClassImport(selected.value.teachingClassId, importPreview.value.batchId)
    notice.value = `导入完成：新增账号 ${result.createdAccountCount} 个，加入教学班 ${result.addedMemberCount} 人。`
    showImportModal.value = false
    await loadClassDetail(selected.value)
    await load()
  } catch (err) { notice.value = getApiErrorMessage(err, '名单导入失败，请重新校验。') }
  finally { importing.value = false }
}

const removeStudent = async (student: TeachingClassStudentDto) => {
  if (!selected.value?.canManage || !window.confirm(`将“${student.studentName || student.studentNumber}”移出该教学班？账号和学习记录不会删除。`)) return
  await removeTeachingClassStudent(selected.value.teachingClassId, student.studentId)
  await loadClassDetail(selected.value)
  await load()
}

const openCoursePlan = () => {
  if (!selected.value?.canManage) return
  coursePlans.value = arrangedCourses.value.map((item) => ({
    courseId: item.courseId,
    teachingOrder: item.teachingOrder,
    plannedStartDate: item.plannedStartDate || '',
    plannedEndDate: item.plannedEndDate || '',
  }))
  showCourseModal.value = true
}

const addCourse = (event: Event) => {
  const courseId = Number((event.target as HTMLSelectElement).value)
  if (!courseId) return
  coursePlans.value.push({ courseId, teachingOrder: coursePlans.value.length + 1, plannedStartDate: '', plannedEndDate: '' })
  ;(event.target as HTMLSelectElement).value = ''
}

const moveCourse = (index: number, direction: -1 | 1) => {
  const target = index + direction
  if (target < 0 || target >= coursePlans.value.length) return
  const next = [...coursePlans.value]
  ;[next[index], next[target]] = [next[target], next[index]]
  coursePlans.value = next.map((item, order) => ({ ...item, teachingOrder: order + 1 }))
}

const removeCourse = (index: number) => { coursePlans.value.splice(index, 1); coursePlans.value = coursePlans.value.map((item, order) => ({ ...item, teachingOrder: order + 1 })) }

const saveCoursePlan = async () => {
  if (!selected.value) return
  savingCourses.value = true
  try {
    arrangedCourses.value = await replaceTeachingClassCourses(selected.value.teachingClassId, coursePlans.value.map((item, order) => ({
      ...item,
      teachingOrder: order + 1,
      plannedStartDate: item.plannedStartDate || null,
      plannedEndDate: item.plannedEndDate || null,
    })))
    showCourseModal.value = false
    await load()
  } catch (err) { notice.value = getApiErrorMessage(err, '教学安排保存失败。') }
  finally { savingCourses.value = false }
}

onMounted(() => void load())
</script>

<template>
  <div class="teacher-page classes-page">
    <header class="page-head">
      <div><h1>教学班</h1><p>按学期组织学生和课程。所有教师可查看，创建人负责维护。</p></div>
      <button class="primary-button" @click="openCreate">＋ 创建教学班</button>
    </header>
    <div v-if="notice" class="notice" style="margin-bottom: 16px">{{ notice }}</div>
    <div v-if="loading" class="panel loading-state">正在加载教学班…</div>
    <div v-else-if="error" class="panel error-state">{{ error }} <button class="secondary-button" @click="load">重新加载</button></div>
    <div v-else class="classes-layout">
      <aside class="panel class-list">
        <div class="list-caption">当前教学班 <span>{{ activeClasses.length }}</span></div>
        <button
          v-for="item in activeClasses" :key="item.teachingClassId" type="button" class="class-row"
          :class="{ selected: selected?.teachingClassId === item.teachingClassId }" @click="loadClassDetail(item)"
        >
          <span class="class-title"><strong>{{ item.className }}</strong><i v-if="item.canManage">我创建</i></span>
          <span>{{ semesterLabel(item) }}</span>
          <small>{{ item.studentCount }} 名学生 · {{ item.courseCount }} 门课程</small>
        </button>
        <div v-if="!activeClasses.length" class="empty-state compact">暂无教学班</div>
      </aside>

      <section v-if="selected" class="panel class-detail">
        <div class="detail-title">
          <div><span class="subtle">{{ semesterLabel(selected) }}</span><h2>{{ selected.className }}</h2><p>任课教师：{{ selected.teacherName || '未填写' }} · 最近活动：{{ formatDateTime(selected.lastActiveAt) }}</p></div>
          <div v-if="selected.canManage" class="toolbar"><button class="secondary-button" @click="openEdit">编辑信息</button><button class="danger-button" @click="archiveCurrent">归档</button></div>
          <span v-else class="tag gray">只读</span>
        </div>
        <div class="detail-tabs">
          <button :class="{ active: tab === 'students' }" @click="tab = 'students'">学生名单 <span>{{ students.length }}</span></button>
          <button :class="{ active: tab === 'courses' }" @click="tab = 'courses'">教学安排 <span>{{ arrangedCourses.length }}</span></button>
        </div>
        <div v-if="detailLoading" class="loading-state">正在加载…</div>
        <template v-else-if="tab === 'students'">
          <div class="detail-toolbar">
            <div><strong>学生名单</strong><span>账号不存在时将自动创建，初始密码为 123456</span></div>
            <div class="toolbar" v-if="selected.canManage"><a class="secondary-button" href="/templates/教学班学生导入模板.xlsx">下载模板</a><button class="primary-button" @click="openImport">导入 Excel</button></div>
          </div>
          <div class="data-table-wrap">
            <table class="data-table"><thead><tr><th>学号</th><th>姓名</th><th>行政班</th><th>加入时间</th><th>最近活动</th><th v-if="selected.canManage">操作</th></tr></thead>
              <tbody><tr v-for="student in students" :key="student.studentId"><td>{{ student.studentNumber }}</td><td><strong>{{ student.studentName || '未填写' }}</strong></td><td>{{ student.administrativeClass || '—' }}</td><td>{{ formatDateTime(student.joinedAt) }}</td><td>{{ formatDateTime(student.recentActivityAt) }}</td><td v-if="selected.canManage"><button class="row-action danger" @click="removeStudent(student)">移出教学班</button></td></tr></tbody>
            </table>
            <div v-if="!students.length" class="empty-state"><strong>还没有学生</strong>下载模板填写名单后导入即可。</div>
          </div>
        </template>
        <template v-else>
          <div class="detail-toolbar"><div><strong>教学安排</strong><span>课程可跨学期复用，这里只安排本教学班的授课顺序</span></div><button v-if="selected.canManage" class="primary-button" @click="openCoursePlan">调整课程</button></div>
          <div v-if="arrangedCourses.length" class="course-list">
            <div v-for="(course, index) in arrangedCourses" :key="course.courseId" class="course-row">
              <span class="course-order">{{ index + 1 }}</span><div><strong>{{ course.courseName }}</strong><p>{{ course.courseDescription || '暂无课程说明' }}</p><small>{{ course.plannedStartDate || '未设置开始日期' }}<template v-if="course.plannedEndDate"> 至 {{ course.plannedEndDate }}</template></small></div>
            </div>
          </div>
          <div v-else class="empty-state"><strong>还没有安排课程</strong>从课程库中选择本学期要讲授的课程。</div>
        </template>
      </section>
      <section v-else class="panel empty-state"><strong>选择一个教学班</strong>查看学生名单和教学安排。</section>
    </div>

    <div v-if="showClassModal" class="modal-layer" @click.self="showClassModal = false"><div class="modal-card">
      <div class="modal-head"><h2>{{ editingClass ? '编辑教学班' : '创建教学班' }}</h2><button @click="showClassModal = false">×</button></div>
      <form @submit.prevent="saveClass"><div class="modal-body">
        <div class="field"><label>教学班名称</label><input v-model="classForm.className" maxlength="120" required placeholder="例如：网络安全232班" /></div>
        <div class="form-grid"><div class="field"><label>学年</label><input v-model="classForm.academicYear" required pattern="\d{4}-\d{4}" placeholder="2026-2027" /></div><div class="field"><label>学期</label><select v-model="classForm.semester"><option :value="1">第1学期</option><option :value="2">第2学期</option></select></div></div>
        <div class="form-grid"><div class="field"><label>开始日期（可选）</label><input v-model="classForm.startDate" type="date" /></div><div class="field"><label>结束日期（可选）</label><input v-model="classForm.endDate" type="date" /></div></div>
      </div><div class="modal-actions"><button type="button" class="secondary-button" @click="showClassModal = false">取消</button><button class="primary-button" :disabled="savingClass">{{ savingClass ? '保存中…' : '保存' }}</button></div></form>
    </div></div>

    <div v-if="showImportModal" class="modal-layer" @click.self="showImportModal = false"><div class="modal-card import-card">
      <div class="modal-head"><h2>导入学生名单</h2><button @click="showImportModal = false">×</button></div>
      <div class="modal-body">
        <div class="notice">Excel 表头须为“学号、姓名、行政班”。系统先校验，不会直接写入数据。</div>
        <div class="field"><label>选择 .xlsx 文件</label><input type="file" accept=".xlsx" @change="chooseFile" /></div>
        <button v-if="!importPreview" class="secondary-button" :disabled="!importFile || importing" @click="previewImport">{{ importing ? '正在校验…' : '校验名单' }}</button>
        <template v-if="importPreview">
          <div class="preview-stats"><div><strong>{{ importPreview.newAccounts.length }}</strong><span>新建账号</span></div><div><strong>{{ importPreview.existingAccounts.length }}</strong><span>已有账号</span></div><div><strong>{{ importPreview.duplicateRows.length }}</strong><span>重复行</span></div><div :class="{ bad: importPreview.errorRows.length }"><strong>{{ importPreview.errorRows.length }}</strong><span>错误行</span></div></div>
          <div v-if="importPreview.errorRows.length" class="notice error"><div v-for="item in importPreview.errorRows" :key="item.rowNumber">第 {{ item.rowNumber }} 行：{{ item.message }}</div></div>
          <div class="subtle">确认后，新账号初始密码为 123456；不会强制学生首次登录修改密码。</div>
        </template>
      </div><div class="modal-actions"><button class="secondary-button" @click="showImportModal = false">取消</button><button class="primary-button" :disabled="!importPreview || !!importPreview.errorRows.length || importing" @click="confirmImport">{{ importing ? '导入中…' : '确认导入' }}</button></div>
    </div></div>

    <div v-if="showCourseModal" class="modal-layer" @click.self="showCourseModal = false"><div class="modal-card course-modal">
      <div class="modal-head"><h2>安排教学课程</h2><button @click="showCourseModal = false">×</button></div>
      <div class="modal-body"><div class="notice">课程来自共享课程库；调整只影响当前教学班。</div>
        <select class="filter-control" @change="addCourse"><option value="">＋ 选择课程加入安排</option><option v-for="course in availableCourses" :key="course.id" :value="course.id">{{ course.name }}</option></select>
        <div v-for="(plan, index) in coursePlans" :key="plan.courseId" class="plan-row"><div class="plan-top"><span>{{ index + 1 }}</span><strong>{{ courseName(plan.courseId) }}</strong><div><button :disabled="index === 0" @click="moveCourse(index, -1)">↑</button><button :disabled="index === coursePlans.length - 1" @click="moveCourse(index, 1)">↓</button><button class="remove" @click="removeCourse(index)">移除</button></div></div><div class="form-grid"><div class="field"><label>计划开始</label><input v-model="plan.plannedStartDate" type="date" /></div><div class="field"><label>计划结束</label><input v-model="plan.plannedEndDate" type="date" /></div></div></div>
        <div v-if="!coursePlans.length" class="empty-state compact">从上方选择课程</div>
      </div><div class="modal-actions"><button class="secondary-button" @click="showCourseModal = false">取消</button><button class="primary-button" :disabled="savingCourses" @click="saveCoursePlan">{{ savingCourses ? '保存中…' : '保存安排' }}</button></div>
    </div></div>
  </div>
</template>

<style scoped>
.classes-layout { display: grid; grid-template-columns: 292px minmax(0, 1fr); gap: 18px; align-items: start; }
.class-list { overflow: hidden; }
.list-caption { display: flex; justify-content: space-between; padding: 15px 17px; border-bottom: 1px solid #e7ecf2; color: #69768a; font-size: 12px; font-weight: 700; }
.class-list button.class-row { display: grid; width: 100%; gap: 5px; padding: 15px 17px; border: 0; border-bottom: 1px solid #edf1f5; background: #fff; color: #6d798b; text-align: left; cursor: pointer; }
.class-list button.class-row:hover, .class-list button.class-row.selected { background: #f3f7fc; }
.class-list button.class-row.selected { box-shadow: inset 3px 0 #2864b8; }
.class-title { display: flex; align-items: center; justify-content: space-between; color: #25344b; }
.class-title i { padding: 2px 6px; border-radius: 999px; background: #eaf2fd; color: #275da9; font-size: 10px; font-style: normal; }
.class-row > span:not(.class-title), .class-row small { font-size: 11px; }
.detail-title { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; padding: 22px 24px; }
.detail-title h2 { margin: 4px 0; font-size: 21px; }
.detail-title p { margin: 0; color: #7e8a9b; font-size: 12px; }
.detail-tabs { display: flex; padding: 0 22px; border-top: 1px solid #edf1f5; border-bottom: 1px solid #e5eaf0; }
.detail-tabs button { padding: 13px 3px; margin-right: 25px; border: 0; border-bottom: 2px solid transparent; background: none; color: #748095; font-size: 13px; cursor: pointer; }
.detail-tabs button.active { border-color: #2864b8; color: #1d4f92; font-weight: 700; }
.detail-tabs span { margin-left: 4px; color: #9ba5b3; font-size: 11px; }
.detail-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 18px 22px; }
.detail-toolbar strong, .detail-toolbar span { display: block; }
.detail-toolbar span { margin-top: 3px; color: #8692a3; font-size: 11px; }
.row-action { padding: 0; border: 0; background: none; color: #4f6e96; font-size: 11px; cursor: pointer; }
.row-action.danger { color: #b54942; }
.course-list { padding: 0 22px 12px; }
.course-row { display: flex; gap: 14px; padding: 16px 0; border-top: 1px solid #edf1f5; }
.course-order { display: grid; width: 27px; height: 27px; flex: 0 0 auto; place-items: center; border-radius: 50%; background: #edf3fb; color: #285da7; font-size: 11px; font-weight: 700; }
.course-row p { max-width: 700px; margin: 4px 0; color: #7c899a; font-size: 12px; line-height: 1.5; }
.course-row small { color: #55779f; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.preview-stats { display: grid; grid-template-columns: repeat(4, 1fr); border: 1px solid #e2e8f0; border-radius: 8px; }
.preview-stats div { display: grid; gap: 3px; padding: 12px; border-right: 1px solid #e7ecf2; text-align: center; }
.preview-stats div:last-child { border: 0; }.preview-stats strong { color: #1e579e; font-size: 19px; }.preview-stats span { color: #8290a4; font-size: 10px; }.preview-stats .bad strong { color: #b42318; }
.course-modal { width: min(720px, 100%); }.plan-row { padding: 14px; border: 1px solid #e2e8f0; border-radius: 8px; }.plan-top { display: flex; align-items: center; gap: 9px; margin-bottom: 11px; }.plan-top > span { color: #2862ad; font-size: 11px; font-weight: 700; }.plan-top strong { flex: 1; font-size: 13px; }.plan-top button { border: 0; background: #f0f3f7; color: #5b687b; cursor: pointer; }.plan-top button.remove { background: none; color: #ad443d; font-size: 11px; }
@media (max-width: 980px) { .classes-layout { grid-template-columns: 1fr; } .class-list { display: grid; grid-template-columns: repeat(2, 1fr); } .list-caption { grid-column: 1 / -1; } }
@media (max-width: 620px) { .class-list { grid-template-columns: 1fr; } .detail-title, .detail-toolbar { align-items: flex-start; flex-direction: column; } .form-grid, .preview-stats { grid-template-columns: 1fr; } .preview-stats div { border-right: 0; border-bottom: 1px solid #e7ecf2; } }
</style>
