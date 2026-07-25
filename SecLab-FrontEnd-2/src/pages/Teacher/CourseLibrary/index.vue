<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { createTeacherCourse, deleteTeacherCourse, getApiErrorMessage, getTeacherCourseList, updateTeacherCourse } from '../../../api'
import { getStoredCurrentUser } from '../../../auth'
import type { Course } from '../../../types/course'
import '../teacher-page.css'

const courses = ref<Course[]>([])
const loading = ref(true)
const error = ref('')
const search = ref('')
const category = ref('')
const showModal = ref(false)
const editing = ref<Course | null>(null)
const saving = ref(false)
const form = ref({ name: '', description: '', difficulty: 2 as 1 | 2 | 3 | 4 | 5, category: 'Web安全', tags: '', status: 'published' as Course['status'] })
const currentUserId = getStoredCurrentUser()?.userId || 0

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
const openCreate = () => { editing.value = null; form.value = { name: '', description: '', difficulty: 2, category: 'Web安全', tags: '', status: 'published' }; showModal.value = true }
const openEdit = (course: Course) => { if (!canEdit(course)) return; editing.value = course; form.value = { name: course.name, description: course.description, difficulty: course.difficulty, category: course.category, tags: '', status: course.status }; showModal.value = true }
const save = async () => {
  if (!form.value.name.trim() || !form.value.description.trim()) return
  saving.value = true
  const payload = { ...form.value, name: form.value.name.trim(), description: form.value.description.trim(), tags: form.value.tags.split(/[，,]/).map((item) => item.trim()).filter(Boolean) }
  try { if (editing.value) await updateTeacherCourse(editing.value.id, payload); else await createTeacherCourse(payload); showModal.value = false; await load() }
  catch (err) { error.value = getApiErrorMessage(err, '课程保存失败，请检查后重试。') }
  finally { saving.value = false }
}
const remove = async (course: Course) => {
  if (!canEdit(course) || !window.confirm(`确定删除课程“${course.name}”吗？`)) return
  try { await deleteTeacherCourse(course.id); await load() }
  catch (err) { error.value = getApiErrorMessage(err, '课程删除失败，可能仍被教学班使用。') }
}
onMounted(() => void load())
</script>

<template>
  <div class="teacher-page course-library-page">
    <header class="page-head"><div><h1>课程库</h1><p>课程跨学期共享复用。每位教师只能维护自己创建的课程。</p></div><button class="primary-button" @click="openCreate">＋ 创建课程</button></header>
    <div class="panel filter-panel"><input v-model="search" class="filter-control" placeholder="搜索课程名称或内容" /><select v-model="category" class="filter-control"><option value="">全部分类</option><option v-for="item in categories" :key="item">{{ item }}</option></select><span>共 {{ filtered.length }} 门课程</span></div>
    <div v-if="error" class="notice error" style="margin: 16px 0">{{ error }}</div>
    <div v-if="loading" class="panel loading-state" style="margin-top: 16px">正在加载课程库…</div>
    <div v-else-if="!filtered.length" class="panel empty-state" style="margin-top: 16px"><strong>没有符合条件的课程</strong>可以创建一门新课程，供所有教师安排到教学班。</div>
    <div v-else class="course-grid">
      <article v-for="course in filtered" :key="course.id" class="panel course-card">
        <div class="course-accent"></div>
        <div class="course-card-head"><span class="tag">{{ course.category || '未分类' }}</span><span class="owner-label" :class="{ mine: canEdit(course) }">{{ canEdit(course) ? '我创建' : '共享课程' }}</span></div>
        <h2>{{ course.name }}</h2><p>{{ course.description || '暂无课程说明' }}</p>
        <div class="course-meta"><span>难度 {{ course.difficulty }}/5</span><span>{{ course.status === 'published' ? '已发布' : course.status === 'draft' ? '草稿' : '已归档' }}</span></div>
        <div class="course-actions" v-if="canEdit(course)"><button class="secondary-button" @click="openEdit(course)">编辑</button><button class="danger-button" @click="remove(course)">删除</button></div>
        <div v-else class="shared-note">可用于教学班安排，不可修改</div>
      </article>
    </div>

    <div v-if="showModal" class="modal-layer" @click.self="showModal = false"><div class="modal-card"><div class="modal-head"><h2>{{ editing ? '编辑课程' : '创建课程' }}</h2><button @click="showModal = false">×</button></div>
      <form @submit.prevent="save"><div class="modal-body"><div class="field"><label>课程名称</label><input v-model="form.name" required maxlength="120" placeholder="例如：SQL 注入基础" /></div><div class="field"><label>课程说明</label><textarea v-model="form.description" required rows="4" placeholder="说明本课程讲什么、适合什么阶段"></textarea></div><div class="form-grid"><div class="field"><label>分类</label><input v-model="form.category" required placeholder="Web安全" /></div><div class="field"><label>难度</label><select v-model="form.difficulty"><option v-for="level in 5" :key="level" :value="level">{{ level }} 级</option></select></div></div><div class="field"><label>标签（逗号分隔）</label><input v-model="form.tags" placeholder="SQL注入, Web安全" /></div><div class="field"><label>状态</label><select v-model="form.status"><option value="published">已发布</option><option value="draft">草稿</option><option value="archived">已归档</option></select></div></div><div class="modal-actions"><button type="button" class="secondary-button" @click="showModal = false">取消</button><button class="primary-button" :disabled="saving">{{ saving ? '保存中…' : '保存课程' }}</button></div></form>
    </div></div>
  </div>
</template>

<style scoped>
.filter-panel { display: grid; grid-template-columns: minmax(240px, 1fr) 190px auto; gap: 12px; align-items: center; padding: 14px; }.filter-panel span { color: #7c899a; font-size: 12px; text-align: right; }
.course-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin-top: 16px; }.course-card { position: relative; overflow: hidden; padding: 20px; }.course-accent { position: absolute; inset: 0 auto 0 0; width: 3px; background: #2c65b5; }.course-card-head { display: flex; align-items: center; justify-content: space-between; }.owner-label { color: #8894a4; font-size: 10px; }.owner-label.mine { color: #2360ae; }.course-card h2 { margin: 19px 0 8px; font-size: 17px; }.course-card > p { height: 61px; margin: 0; overflow: hidden; color: #758196; font-size: 12px; line-height: 1.7; }.course-meta { display: flex; gap: 18px; margin-top: 16px; padding-top: 13px; border-top: 1px solid #edf1f5; color: #7c899a; font-size: 11px; }.course-actions { display: flex; gap: 8px; margin-top: 15px; }.course-actions button { min-height: 32px; }.shared-note { margin-top: 15px; color: #8a95a4; font-size: 11px; }.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
@media (max-width: 1100px) { .course-grid { grid-template-columns: repeat(2, 1fr); } } @media (max-width: 660px) { .filter-panel, .course-grid, .form-grid { grid-template-columns: 1fr; }.filter-panel span { text-align: left; } }
</style>
