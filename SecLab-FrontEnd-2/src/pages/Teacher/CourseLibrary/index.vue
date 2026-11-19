<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  addCourseModule,
  createTeacherCourse,
  deleteTeacherCourse,
  getApiErrorMessage,
  getTeacherCourseList,
  uploadLabPackage,
} from '../../../api'
import { getStoredCurrentUser } from '../../../auth'
import type { Course } from '../../../types/course'
import CourseDetailDrawer from './components/CourseDetailDrawer.vue'
import '../teacher-page.css'

const courses = ref<Course[]>([])
const loading = ref(true)
const error = ref('')
const search = ref('')
const category = ref('')
const showModal = ref(false)
const saving = ref(false)
const form = ref({ name: '', description: '', difficulty: 2 as 1 | 2 | 3 | 4 | 5, category: 'Web安全', tags: '', status: 'published' as Course['status'] })
const currentUserId = getStoredCurrentUser()?.userId || 0

// 详情/编辑抽屉
const selectedCourse = ref<Course | null>(null)
const drawerOpen = ref(false)

// 实验包上传（创建课程时可选附带）
const attachLab = ref(false)
const labForm = ref({
  file: null as File | null,
  labKey: '',
  imageName: '',
  hostPort: null as number | null,
  flag: '',
  moduleName: '',
  moduleDescription: '',
  moduleDifficulty: 3 as 1 | 2 | 3 | 4 | 5,
  moduleType: '',
})
const labFileName = ref('')
const labUploadHint = ref('')
const onLabFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0] ?? null
  labForm.value.file = file
  labFileName.value = file ? file.name : ''
  labUploadHint.value = ''
  if (file && !file.name.toLowerCase().endsWith('.zip')) {
    labUploadHint.value = '仅支持 .zip 文件'
  }
}
const resetLabForm = () => {
  attachLab.value = false
  labForm.value = {
    file: null,
    labKey: '',
    imageName: '',
    hostPort: null,
    flag: '',
    moduleName: '',
    moduleDescription: '',
    moduleDifficulty: 3,
    moduleType: '',
  }
  labFileName.value = ''
  labUploadHint.value = ''
}

const categories = computed(() => [...new Set(courses.value.map((item) => item.category).filter(Boolean))])
const filtered = computed(() => courses.value.filter((item) => {
  const keyword = search.value.trim().toLowerCase()
  return (!keyword || `${item.name} ${item.description}`.toLowerCase().includes(keyword)) && (!category.value || item.category === category.value)
}))
const canEdit = (course: Course) => course.createdBy != null && course.createdBy === currentUserId

const load = async () => {
  loading.value = true; error.value = ''
  try { courses.value = await getTeacherCourseList() }
  catch (err) { error.value = getApiErrorMessage(err, '课程库加载失败，请稍后重试。') }
  finally { loading.value = false }
}
const openCreate = () => {
  form.value = { name: '', description: '', difficulty: 2, category: 'Web安全', tags: '', status: 'published' }
  resetLabForm()
  showModal.value = true
}

const save = async () => {
  if (!form.value.name.trim() || !form.value.description.trim()) return
  // 若勾选了上传实验包，做本地校验
  if (attachLab.value) {
    if (!labForm.value.labKey.trim()) { labUploadHint.value = '请填写实验标识'; return }
    if (!labForm.value.file) { labUploadHint.value = '请选择 zip 文件'; return }
    if (!labForm.value.file.name.toLowerCase().endsWith('.zip')) { labUploadHint.value = '仅支持 .zip 文件'; return }
  }

  saving.value = true
  const coursePayload = {
    ...form.value,
    name: form.value.name.trim(),
    description: form.value.description.trim(),
    tags: form.value.tags.split(/[，,]/).map((item) => item.trim()).filter(Boolean),
  }
  let createdCourse: Course | null = null
  try {
    createdCourse = await createTeacherCourse(coursePayload)
  } catch (err) {
    error.value = getApiErrorMessage(err, '课程保存失败，请检查后重试。')
    saving.value = false
    return
  }

  // 课程创建成功后，若勾选了上传实验包则继续上传；上传失败不回滚课程，仅提示
  if (attachLab.value && labForm.value.file && createdCourse) {
    try {
      const labDto = await uploadLabPackage({
        file: labForm.value.file,
        labKey: labForm.value.labKey.trim(),
        imageName: labForm.value.imageName.trim() || null,
        hostPort: labForm.value.hostPort,
        flag: labForm.value.flag.trim() || null,
        moduleName: labForm.value.moduleName.trim() || null,
        moduleDescription: labForm.value.moduleDescription.trim() || null,
        moduleDifficulty: labForm.value.moduleDifficulty,
        moduleType: labForm.value.moduleType.trim() || null,
      })
      // 若上传时指定了 moduleName，后端会建 module；自动把它加入刚创建的课程
      if (labDto.moduleId) {
        try { await addCourseModule(createdCourse.id, labDto.moduleId) }
        catch (err) { labUploadHint.value = `${getApiErrorMessage(err, '实验加入课程失败，请到课程详情手动添加。')}（实验包已上传：${labDto.labKey}）` }
      }
    } catch (err) {
      labUploadHint.value = `课程已创建，但实验包上传失败：${getApiErrorMessage(err, '请到课程详情重试或单独上传。')}`
    }
  }

  saving.value = false
  showModal.value = false
  await load()
}
const remove = async (course: Course) => {
  if (!canEdit(course) || !window.confirm(`确定删除课程“${course.name}”吗？`)) return
  try { await deleteTeacherCourse(course.id); await load() }
  catch (err) { error.value = getApiErrorMessage(err, '课程删除失败，可能仍被教学班使用。') }
}

// 点击课程卡片 → 打开详情/编辑抽屉
const openDetail = (course: Course) => {
  selectedCourse.value = course
  drawerOpen.value = true
}
// 抽屉保存后同步列表
const onDrawerUpdated = (updated: Course) => {
  const idx = courses.value.findIndex((c) => c.id === updated.id)
  if (idx >= 0) courses.value[idx] = updated
  selectedCourse.value = updated
}

const statusLabel = (status: Course['status']) => status === 'published' ? '已发布' : status === 'draft' ? '草稿' : '已归档'

onMounted(() => void load())
</script>

<template>
  <div class="teacher-page course-library-page">
    <header class="page-head"><div><h1>课程库</h1><p>课程跨学期共享复用。点击课程可编辑信息、切换发布与管理实验。每位教师只能维护自己创建的课程。</p></div><button class="primary-button" @click="openCreate">＋ 创建课程</button></header>
    <div class="panel filter-panel"><input v-model="search" class="filter-control" placeholder="搜索课程名称或内容" /><select v-model="category" class="filter-control"><option value="">全部分类</option><option v-for="item in categories" :key="item">{{ item }}</option></select><span>共 {{ filtered.length }} 门课程</span></div>
    <div v-if="error" class="notice error" style="margin: 16px 0">{{ error }}</div>
    <div v-if="loading" class="panel loading-state" style="margin-top: 16px">正在加载课程库…</div>
    <div v-else-if="!filtered.length" class="panel empty-state" style="margin-top: 16px"><strong>没有符合条件的课程</strong>可以创建一门新课程，供所有教师安排到教学班。</div>
    <div v-else class="course-grid">
      <article v-for="course in filtered" :key="course.id" class="panel course-card" :class="{ clickable: true }" @click="openDetail(course)">
        <div class="course-accent"></div>
        <div class="course-card-head"><span class="tag">{{ course.category || '未分类' }}</span><span class="owner-label" :class="{ mine: canEdit(course) }">{{ canEdit(course) ? '我创建' : '共享课程' }}</span></div>
        <h2>{{ course.name }}</h2><p>{{ course.description || '暂无课程说明' }}</p>
        <div v-if="course.tags && course.tags.length" class="course-tags">
          <span v-for="tag in course.tags" :key="tag" class="tag gray">{{ tag }}</span>
        </div>
        <div class="course-meta"><span>难度 {{ course.difficulty }}/5</span><span>{{ statusLabel(course.status) }}</span></div>
        <div class="course-actions">
          <button class="secondary-button" @click.stop="openDetail(course)">编辑 / 实验</button>
          <button v-if="canEdit(course)" class="danger-button" @click.stop="remove(course)">删除</button>
        </div>
      </article>
    </div>

    <!-- 创建课程弹窗 -->
    <div v-if="showModal" class="modal-layer" @click.self="showModal = false"><div class="modal-card"><div class="modal-head"><h2>创建课程</h2><button @click="showModal = false">×</button></div>
      <form @submit.prevent="save"><div class="modal-body">
        <div class="field"><label>课程名称</label><input v-model="form.name" required maxlength="120" placeholder="例如：SQL 注入基础" /></div>
        <div class="field"><label>课程说明</label><textarea v-model="form.description" required rows="4" placeholder="说明本课程讲什么、适合什么阶段"></textarea></div>
        <div class="form-grid"><div class="field"><label>分类</label><input v-model="form.category" required placeholder="Web安全" /></div><div class="field"><label>难度</label><select v-model="form.difficulty"><option v-for="level in 5" :key="level" :value="level">{{ level }} 级</option></select></div></div>
        <div class="field"><label>标签（逗号分隔）</label><input v-model="form.tags" placeholder="SQL注入, Web安全" /></div>
        <div class="field"><label>状态</label><select v-model="form.status"><option value="published">已发布</option><option value="draft">草稿</option><option value="archived">已归档</option></select></div>

        <!-- 上传实验包（可选） -->
        <div class="lab-attach-block">
          <label class="lab-attach-toggle">
            <input type="checkbox" v-model="attachLab" />
            <span>同时上传实验包（zip）</span>
            <span class="muted">可选，用于登记一个新实验容器</span>
          </label>
          <div v-if="attachLab" class="lab-attach-form">
            <div class="notice">本期仅上传 zip 与元数据登记，不会自动构建镜像或启动容器。上传后可在课程详情里把生成的实验加入课程。</div>
            <div class="form-grid">
              <div class="field"><label>实验标识 lab_key *</label><input v-model="labForm.labKey" required maxlength="64" placeholder="如 stack-overflow（小写字母/数字/连字符）" /></div>
              <div class="field"><label>实验包 zip 文件 *</label>
                <div class="file-pick">
                  <label class="secondary-button file-pick-btn">
                    选择 zip
                    <input type="file" accept=".zip,application/zip" @change="onLabFileChange" hidden />
                  </label>
                  <span class="file-name" :class="{ placeholder: !labFileName }">{{ labFileName || '未选择文件' }}</span>
                </div>
              </div>
            </div>
            <div class="form-grid">
              <div class="field"><label>预期镜像名</label><input v-model="labForm.imageName" maxlength="255" placeholder="如 stack-overflow-lab-web:latest" /></div>
              <div class="field"><label>宿主端口</label><input v-model.number="labForm.hostPort" type="number" min="1" max="65535" placeholder="如 8096" /></div>
            </div>
            <div class="field"><label>Flag</label><input v-model="labForm.flag" maxlength="255" placeholder="如 flag{...}，用于后续启动注入与校验" /></div>
            <div class="lab-section-title">自动创建实验模块（可选）</div>
            <div class="field"><label>实验名称</label><input v-model="labForm.moduleName" maxlength="120" placeholder="填写后会在实验池新建一个 module 并自动加入本课程" /></div>
            <div class="field"><label>实验说明</label><textarea v-model="labForm.moduleDescription" rows="3" placeholder="实验目标与简要说明"></textarea></div>
            <div class="form-grid">
              <div class="field"><label>实验难度</label><select v-model="labForm.moduleDifficulty"><option v-for="level in 5" :key="level" :value="level">{{ level }} 级</option></select></div>
              <div class="field"><label>实验类型</label><input v-model="labForm.moduleType" maxlength="64" placeholder="如 栈溢出" /></div>
            </div>
            <div v-if="labUploadHint" class="notice error">{{ labUploadHint }}</div>
          </div>
        </div>
      </div>
      <div class="modal-actions"><button type="button" class="secondary-button" @click="showModal = false">取消</button><button class="primary-button" :disabled="saving">{{ saving ? '保存中…' : '保存课程' }}</button></div></form>
    </div></div>

    <!-- 详情/编辑抽屉 -->
    <CourseDetailDrawer :course="selectedCourse" :open="drawerOpen" @close="drawerOpen = false" @updated="onDrawerUpdated" />
  </div>
</template>

<style scoped>
.filter-panel { display: grid; grid-template-columns: minmax(240px, 1fr) 190px auto; gap: 12px; align-items: center; padding: 14px; }
.filter-panel span { color: #7c899a; font-size: 12px; text-align: right; }
.course-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-top: 16px; }
.course-card { position: relative; overflow: hidden; padding: 18px; }
.course-card.clickable { cursor: pointer; transition: box-shadow .15s ease, transform .15s ease; }
.course-card.clickable:hover { box-shadow: 0 8px 24px rgba(15, 23, 42, .08); transform: translateY(-2px); }
.course-accent { position: absolute; inset: 0 auto 0 0; width: 3px; background: #2c65b5; }
.course-card-head { display: flex; align-items: center; justify-content: space-between; }
.owner-label { color: #8894a4; font-size: 10px; }
.owner-label.mine { color: #2360ae; }
.course-card h2 { margin: 14px 0 7px; font-size: 15px; line-height: 1.4; }
.course-card > p { height: 58px; margin: 0; overflow: hidden; color: #758196; font-size: 12px; line-height: 1.6; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; }
.course-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 10px; }
.course-meta { display: flex; gap: 14px; margin-top: 14px; padding-top: 12px; border-top: 1px solid #edf1f5; color: #7c899a; font-size: 11px; }
.course-actions { display: flex; gap: 8px; margin-top: 13px; }
.course-actions button { min-height: 32px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }

/* 实验包上传区块 */
.lab-attach-block { margin-top: 8px; border: 1px dashed #cfd8e5; border-radius: 8px; padding: 14px; background: #f9fbfd; }
.lab-attach-toggle { display: flex; align-items: center; gap: 8px; cursor: pointer; font-size: 13px; font-weight: 650; color: #2c3c55; }
.lab-attach-toggle input { width: 16px; height: 16px; cursor: pointer; }
.lab-attach-toggle .muted { color: #8995a7; font-size: 11px; font-weight: 400; }
.lab-attach-form { display: grid; gap: 12px; margin-top: 12px; }
.lab-attach-form .form-grid { gap: 12px; }
.lab-section-title { margin-top: 4px; padding-top: 10px; border-top: 1px solid #e8edf3; color: #526176; font-size: 12px; font-weight: 700; }
.file-pick { display: flex; align-items: center; gap: 10px; }
.file-pick-btn { min-height: 39px; cursor: pointer; }
.file-name { font-size: 12px; color: #2d3b50; word-break: break-all; }
.file-name.placeholder { color: #98abc4; }

@media (max-width: 1280px) { .course-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 980px) { .course-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 660px) {
  .filter-panel, .course-grid, .form-grid { grid-template-columns: 1fr; }
  .filter-panel span { text-align: left; }
}
</style>
