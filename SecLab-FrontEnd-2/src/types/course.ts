export interface Course {
  id: number
  name: string
  description: string
  cover?: string
  difficulty: 1 | 2 | 3 | 4 | 5
  category: string
  status: 'draft' | 'published' | 'archived'
  tags?: string[]
  studentCount: number
  experimentCount: number
  createTime: string
  updateTime?: string
  createdBy?: number | null
  creatorEditable?: boolean
}
