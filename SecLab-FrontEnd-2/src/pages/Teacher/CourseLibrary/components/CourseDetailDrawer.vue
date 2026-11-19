<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  addCourseModule,
  getCourseModules,
  getTeacherLabList,
  removeCourseModule,
  updateTeacherCourse,
} from '../../../../api'
import type { Course } from '../../../../types/course'
import type { Experiment } from '../../../../types/experiment'

const props = defineProps<{
  course: Course | null
  open: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'updated', course: Course): void
}>()

// 编辑表单
const form = ref({
  name: '',
  description: '',
  difficulty: 2 as 1 | 2 | 3 | 4 | 5,
  category: '',
  tags: '',
  cover: '',
  status: 'published' as Course['status'],
})
const saving = ref(false)
const formError = ref('')

// 课程内实验
const modules = ref<Experiment[]>([])
const modulesLoading = ref(false)
const modulesError = ref('')

// 实验池（全部实验，用于添加到课程）
const labPool = ref<Experiment[]>([])
const labPoolLoading = ref(false)
const selectedModuleId = ref<number | ''>('')

// 所有课程（含共享课程）均可在抽屉中编辑：改信息、切换发布、管理实验。
const readOnly = computed(() => false)

// 可添加的实验：排除已加入本课程的
const availableLabs = computed(() => {
  const added = new Set(modules.value.map((m) => m.id))
  return labPool.value.filter((m) => !added.has(m.id))
})

const isPublished = computed(() => form.value.status === 'published')

const resetForm = () => {
  if (!props.course) return
  form.value = {
    name: props.course.name,
    description: props.course.description,
    difficulty: props.course.difficulty,
    category: props.course.category,
    tags: (props.course.tags || []).join(', '),
    cover: props.course.cover || '',
    status: props.course.status,
  }
  formError.value = ''
}

const loadModules = async () => {
  if (!props.course) return
  modulesLoading.value = true
  modulesError.value = ''
  try {
    modules.value = await getCourseModules(props.course.id)
  } catch (err) {
    modulesError.value = '课程实验加载失败'
    modules.value = []
  } finally {
    modulesLoading.value = false
  }
}

const loadLabPool = async () => {
  if (readOnly.value) return
  labPoolLoading.value = true
  try {
    labPool.value = await getTeacherLabList()
  } catch (err) {
    labPool.value = []
  } finally {
    labPoolLoading.value = false
  }
}

// 抽屉打开/课程变化时初始化
watch(
  () => [props.open, props.course?.id] as const,
  ([isOpen]) => {
    if (isOpen && props.course) {
      resetForm()
      modules.value = []
      selectedModuleId.value = ''
      void loadModules()
      void loadLabPool()
    }
  },
  { immediate: true },
)

const save = async () => {
  if (!props.course) return
  if (!form.value.name.trim() || !form.value.description.trim()) {
    formError.value = '课程名称和说明不能为空'
    return
  }
  saving.value = true
  formError.value = ''
  const payload = {
    name: form.value.name.trim(),
    description: form.value.description.trim(),
    difficulty: form.value.difficulty,
    category: form.value.category.trim() || '未分类',
    tags: form.value.tags
      .split(/[，,]/)
      .map((t) => t.trim())
      .filter(Boolean),
    cover: form.value.cover.trim() || undefined,
    status: form.value.status,
  }
  try {
    const updated = await updateTeacherCourse(props.course.id, payload)
    emit('updated', updated)
  } catch (err) {
    formError.value = '课程保存失败，请检查后重试'
  } finally {
    saving.value = false
  }
}

// 快捷发布/取消发布
const togglePublish = async () => {
  if (!props.course) return
  const next: Course['status'] = isPublished.value ? 'draft' : 'published'
  form.value.status = next
  await save()
}

const addModule = async () => {
  if (!props.course || !selectedModuleId.value) return
  try {
    modules.value = await addCourseModule(props.course.id, selectedModuleId.value as number)
    selectedModuleId.value = ''
  } catch (err) {
    modulesError.value = '添加实验失败'
  }
}

const removeModule = async (moduleId: number) => {
  if (!props.course) return
  if (!window.confirm('确定将该实验从课程中移除吗？')) return
  try {
    modules.value = await removeCourseModule(props.course.id, moduleId)
  } catch (err) {
    modulesError.value = '移除实验失败'
  }
}

const statusLabel = (status: Course['status']) =>
  status === 'published' ? '已发布' : status === 'draft' ? '草稿' : '已归档'

const difficultyStars = (d: number) => '★'.repeat(d) + '☆'.repeat(5 - d)
</script>

<template>
  <teleport to="body">
    <transition name="drawer-fade">
      <div v-if="open && course" class="drawer-layer" @click.self="emit('close')">
        <aside class="drawer-panel">
          <header class="drawer-head">
            <div>
              <h2>{{ course.name }}</h2>
              <p>{{ readOnly ? '共享课程（只读）' : '编辑课程信息与实验内容' }}</p>
            </div>
            <button class="drawer-close" @click="emit('close')" aria-label="关闭">×</button>
          </header>

          <div class="drawer-body">
            <!-- 编辑表单 -->
            <section class="drawer-section">
              <div class="section-title">课程信息</div>
              <div class="field">
                <label>课程名称</label>
                <input v-model="form.name" :disabled="readOnly" maxlength="120" placeholder="例如：SQL 注入基础" />
              </div>
              <div class="field">
                <label>课程说明</label>
                <textarea v-model="form.description" :disabled="readOnly" rows="3" placeholder="说明本课程讲什么、适合什么阶段"></textarea>
              </div>
              <div class="form-grid">
                <div class="field">
                  <label>分类</label>
                  <input v-model="form.category" :disabled="readOnly" placeholder="Web安全" />
                </div>
                <div class="field">
                  <label>难度</label>
                  <select v-model="form.difficulty" :disabled="readOnly">
                    <option v-for="level in 5" :key="level" :value="level">{{ level }} 级</option>
                  </select>
                </div>
              </div>
              <div class="field">
                <label>封面图 URL（可选）</label>
                <input v-model="form.cover" :disabled="readOnly" placeholder="https://..." />
              </div>
              <div class="field">
                <label>标签（逗号分隔）</label>
                <input v-model="form.tags" :disabled="readOnly" placeholder="SQL注入, Web安全" />
              </div>
              <div class="field">
                <label>状态</label>
                <select v-model="form.status" :disabled="readOnly">
                  <option value="published">已发布</option>
                  <option value="draft">草稿</option>
                  <option value="archived">已归档</option>
                </select>
              </div>
              <div v-if="formError" class="notice error">{{ formError }}</div>
              <div v-if="!readOnly" class="form-actions">
                <button class="primary-button" :disabled="saving" @click="save">
                  {{ saving ? '保存中…' : '保存课程' }}
                </button>
                <button class="quiet-button" :disabled="saving" @click="togglePublish">
                  {{ isPublished ? '取消发布' : '发布课程' }}
                </button>
              </div>
            </section>

            <!-- 课程内实验 -->
            <section class="drawer-section">
              <div class="section-title">
                <span>课程内实验</span>
                <span class="section-count">{{ modules.length }} 个</span>
              </div>
              <div v-if="modulesLoading" class="subtle">正在加载实验…</div>
              <div v-else-if="modulesError" class="notice error">{{ modulesError }}</div>
              <div v-else-if="!modules.length" class="subtle">本课程尚未关联实验。</div>
              <ul v-else class="module-list">
                <li v-for="m in modules" :key="m.id">
                  <div class="module-info">
                    <strong>{{ m.name }}</strong>
                    <span class="muted">{{ difficultyStars(m.difficulty) }} · {{ statusLabel(m.status) }}</span>
                  </div>
                  <button v-if="!readOnly" class="danger-button" @click="removeModule(m.id)">移除</button>
                </li>
              </ul>

              <!-- 添加实验 -->
              <div v-if="!readOnly" class="add-module">
                <select v-model="selectedModuleId" class="filter-control">
                  <option value="">选择实验加入课程…</option>
                  <option v-for="m in availableLabs" :key="m.id" :value="m.id">{{ m.name }}</option>
                </select>
                <button class="secondary-button" :disabled="!selectedModuleId || labPoolLoading" @click="addModule">
                  加入课程
                </button>
              </div>
              <div v-else-if="labPoolLoading" class="subtle"></div>
            </section>
          </div>
        </aside>
      </div>
    </transition>
  </teleport>
</template>

<style scoped>
.drawer-layer {
  position: fixed;
  inset: 0;
  z-index: 70;
  background: rgba(17, 29, 51, 0.42);
  display: flex;
  justify-content: flex-end;
}
.drawer-panel {
  width: min(520px, 100%);
  height: 100%;
  background: #fff;
  box-shadow: -20px 0 60px rgba(15, 23, 42, 0.18);
  display: flex;
  flex-direction: column;
}
.drawer-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 19px 22px;
  border-bottom: 1px solid #e8edf3;
}
.drawer-head h2 {
  margin: 0;
  font-size: 17px;
  font-weight: 720;
  color: #14213d;
}
.drawer-head p {
  margin: 5px 0 0;
  color: #8290a4;
  font-size: 12px;
}
.drawer-close {
  border: 0;
  background: none;
  color: #738096;
  font-size: 22px;
  cursor: pointer;
  line-height: 1;
}
.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 22px 32px;
  display: grid;
  gap: 26px;
}
.drawer-section {
  display: grid;
  gap: 14px;
}
.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 720;
  color: #334155;
  padding-bottom: 8px;
  border-bottom: 1px solid #eef1f5;
}
.section-count {
  color: #7c899c;
  font-size: 12px;
  font-weight: 600;
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.form-actions {
  display: flex;
  gap: 10px;
}
.module-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}
.module-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 11px 13px;
  border: 1px solid #e8edf3;
  border-radius: 8px;
  background: #f8fafc;
}
.module-info {
  display: grid;
  gap: 3px;
  min-width: 0;
}
.module-info strong {
  font-size: 13px;
  color: #25324a;
}
.module-list .danger-button {
  min-height: 30px;
  padding: 0 11px;
  font-size: 12px;
}
.add-module {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  align-items: center;
}
.muted {
  color: #7c899c;
  font-size: 11px;
}
.subtle {
  color: #8995a7;
  font-size: 12px;
}

.drawer-fade-enter-active,
.drawer-fade-leave-active {
  transition: opacity 0.2s ease;
}
.drawer-fade-enter-active .drawer-panel,
.drawer-fade-leave-active .drawer-panel {
  transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}
.drawer-fade-enter-from,
.drawer-fade-leave-to {
  opacity: 0;
}
.drawer-fade-enter-from .drawer-panel,
.drawer-fade-leave-to .drawer-panel {
  transform: translateX(100%);
}

@media (max-width: 660px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
