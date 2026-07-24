import type { ModuleOverViewType } from './components/ModuleOverView'

interface ModuleCatalogResult {
  isSuccess?: number
  status: number
  message: string
  data?: ModuleOverViewType[] | null
}

export function readModuleCatalog(result: ModuleCatalogResult): ModuleOverViewType[] {
  if (result.status !== 200 || result.isSuccess === 0 || !Array.isArray(result.data)) {
    throw new Error(result.message || '实验目录加载失败')
  }
  return result.data
}

export function moduleRoute(moduleId: number, courseId?: number | null): string {
  const base = `/user/module/${moduleId}`
  return courseId ? `${base}?courseId=${encodeURIComponent(String(courseId))}` : base
}
