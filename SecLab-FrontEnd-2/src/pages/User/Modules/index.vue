<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCourseList, getModuleList } from '../../../api'
import ModuleOverView from './components/ModuleOverView.vue'
import type { ModuleOverViewType } from './components/ModuleOverView'
import { moduleRoute, readModuleCatalog } from './moduleCatalog'

const router = useRouter()
const route = useRoute()
const modules = ref<ModuleOverViewType[]>([])
const loading = ref(true)
const loadError = ref('')
const startError = ref('')
const pendingModule = ref<ModuleOverViewType | null>(null)
const courseNames = ref<Record<number, string>>({})
const searchQuery = ref('')
const filters = ref({ type: '', difficulty: '', status: '' })

const types = computed(() =>
  Array.from(new Set(modules.value.map((module) => module.type).filter(Boolean))).sort(),
)

const filteredModules = computed(() => {
  const keyword = searchQuery.value.trim().toLowerCase()
  const statusOrder = { available: 0, locked: 1, completed: 2 }
  return modules.value
    .filter((module) => {
      if (keyword && !`${module.name} ${module.description}`.toLowerCase().includes(keyword)) return false
      if (filters.value.type && module.type !== filters.value.type) return false
      if (filters.value.status && module.status !== filters.value.status) return false
      if (filters.value.difficulty && module.difficulty !== Number(filters.value.difficulty)) return false
      return true
    })
    .slice()
    .sort((a, b) => statusOrder[a.status] - statusOrder[b.status])
})

const stats = computed(() => ({
  total: modules.value.length,
  completed: modules.value.filter((module) => module.status === 'completed').length,
  available: modules.value.filter((module) => module.status === 'available').length,
  locked: modules.value.filter((module) => module.status === 'locked').length,
}))

async function loadModules() {
  loading.value = true
  loadError.value = ''
  try {
    const [moduleResult, courseResult] = await Promise.all([
      getModuleList(),
      getCourseList(),
    ])
    modules.value = readModuleCatalog(moduleResult)
    courseNames.value = Object.fromEntries(
      (courseResult.data || []).map((course) => [course.id, course.name]),
    )
  } catch (error) {
    modules.value = []
    loadError.value = error instanceof Error ? error.message : '实验目录加载失败'
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.value = { type: '', difficulty: '', status: '' }
  searchQuery.value = ''
}

function startModule(module: ModuleOverViewType) {
  if (module.status === 'locked') return
  const requestedCourseId = Number(route.query.courseId)
  const selectedCourseId = Number.isInteger(requestedCourseId)
    && module.courseIds?.includes(requestedCourseId)
    ? requestedCourseId
    : module.courseId
  if (!selectedCourseId && (module.courseIds?.length || 0) > 1) {
    pendingModule.value = module
    return
  }
  startError.value = ''
  void router.push(moduleRoute(module.id, selectedCourseId))
}

function chooseModuleCourse(courseId: number) {
  const module = pendingModule.value
  if (!module || !module.courseIds?.includes(courseId)) return
  pendingModule.value = null
  startError.value = ''
  void router.push(moduleRoute(module.id, courseId))
}

onMounted(loadModules)
</script>

<template>
  <div class="container-fluid px-4 py-6 overflow-x-hidden">
    <div class="stats shadow w-full mb-6">
      <div class="stat">
        <div class="stat-title">实验总数</div>
        <div class="stat-value text-primary">{{ stats.total }}</div>
      </div>
      <div class="stat">
        <div class="stat-title">已完成</div>
        <div class="stat-value text-success">{{ stats.completed }}</div>
      </div>
      <div class="stat">
        <div class="stat-title">可开始</div>
        <div class="stat-value text-warning">{{ stats.available }}</div>
      </div>
      <div class="stat">
        <div class="stat-title">未解锁</div>
        <div class="stat-value text-error">{{ stats.locked }}</div>
      </div>
    </div>

    <div class="card bg-base-100 shadow-xl mb-6">
      <div class="card-body">
        <div class="grid grid-cols-1 gap-4 md:grid-cols-4">
          <label class="form-control md:col-span-2">
            <span class="label-text mb-2">搜索实验</span>
            <input v-model="searchQuery" class="input input-bordered" placeholder="输入实验名称或内容" />
          </label>
          <label class="form-control">
            <span class="label-text mb-2">类型</span>
            <select v-model="filters.type" class="select select-bordered">
              <option value="">全部类型</option>
              <option v-for="type in types" :key="type" :value="type">{{ type }}</option>
            </select>
          </label>
          <label class="form-control">
            <span class="label-text mb-2">状态</span>
            <select v-model="filters.status" class="select select-bordered">
              <option value="">全部状态</option>
              <option value="available">可开始</option>
              <option value="completed">已完成</option>
              <option value="locked">未解锁</option>
            </select>
          </label>
          <label class="form-control">
            <span class="label-text mb-2">难度</span>
            <select v-model="filters.difficulty" class="select select-bordered">
              <option value="">全部难度</option>
              <option v-for="level in 5" :key="level" :value="String(level)">{{ level }} 星</option>
            </select>
          </label>
        </div>
        <div class="card-actions justify-end mt-4">
          <button class="btn btn-ghost btn-sm" type="button" @click="resetFilters">清空筛选</button>
        </div>
      </div>
    </div>

    <div v-if="startError" class="alert alert-warning mb-4">{{ startError }}</div>

    <div v-if="loading" class="flex min-h-64 items-center justify-center" aria-live="polite">
      <span class="loading loading-spinner loading-lg text-primary"></span>
    </div>

    <div v-else-if="loadError" class="alert alert-error">
      <span>{{ loadError }}</span>
      <button class="btn btn-sm" type="button" @click="loadModules">重新加载</button>
    </div>
    <div v-else-if="filteredModules.length" class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      <ModuleOverView
        v-for="module in filteredModules"
        :key="module.id"
        :module="module"
        @start="startModule"
      />
    </div>

    <div v-else class="py-12 text-center">
      <h3 class="text-xl font-semibold mb-2">没有符合条件的实验</h3>
      <button class="btn btn-primary btn-sm" type="button" @click="resetFilters">查看全部实验</button>
    </div>

    <div v-if="pendingModule" class="modal modal-open" role="dialog" aria-modal="true">
      <div class="modal-box">
        <h3 class="text-lg font-bold">选择实验所属课程</h3>
        <p class="py-3 text-sm text-base-content/70">{{ pendingModule.name }}</p>
        <div class="grid gap-2">
          <button
            v-for="courseId in pendingModule.courseIds"
            :key="courseId"
            class="btn btn-outline justify-start"
            type="button"
            @click="chooseModuleCourse(courseId)"
          >
            {{ courseNames[courseId] || `课程 ${courseId}` }}
          </button>
        </div>
        <div class="modal-action">
          <button class="btn btn-ghost" type="button" @click="pendingModule = null">取消</button>
        </div>
      </div>
      <button class="modal-backdrop" type="button" aria-label="关闭" @click="pendingModule = null"></button>
    </div>
  </div>
</template>
