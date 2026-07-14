import type { CourseSummaryDto } from '../api'
import type { Course } from '../types/course'
import type { Experiment } from '../types/experiment'
import type { ModuleOverViewType } from '../pages/User/Modules/components/ModuleOverView'
import type { CourseOverViewType } from '../pages/User/Courses/components/CourseOverView'

type PresentationCourseSeed = {
  id: number
  name: string
  description: string
  difficulty: 1 | 2 | 3 | 4 | 5
  type: string
  category: string
  cover: string
  videoUrl?: string
  tags: string[]
}

type PresentationModuleSeed = {
  id: number
  name: string
  description: string
  difficulty: 1 | 2 | 3 | 4 | 5
  type: string
  estimatedTime: string
  score: number
  courseId: number
  courseName: string
}

export const PRESENTATION_TOTAL_USERS = 128
export const PRESENTATION_CLASS_SCORE = 76

export const PRESENTATION_COURSE_SEEDS: PresentationCourseSeed[] = [
  {
    id: 1,
    name: 'SQL注入攻击',
    description: '系统讲解 SQL 注入原理、利用方式与常见防护策略。',
    difficulty: 3,
    type: 'web',
    category: 'Web安全',
    cover: '/1.SQL注入攻防实战.png',
    videoUrl: '/video/1.1Sql注入攻击.mp4',
    tags: ['SQL注入', 'Web安全', '数据库安全'],
  },
  {
    id: 2,
    name: 'XSS与CSRF攻击',
    description: '围绕 XSS 与 CSRF 攻击链路，训练前端安全分析与防护能力。',
    difficulty: 2,
    type: 'web',
    category: 'Web安全',
    cover: '/2.XSS漏洞深度解析.png',
    videoUrl: '/video/1.2Xss与Csrf.mp4',
    tags: ['XSS', 'CSRF', '前端安全'],
  },
  {
    id: 3,
    name: 'IDS和IPS系统',
    description: '介绍 IDS 与 IPS 的工作机制、部署方法与流量分析思路。',
    difficulty: 3,
    type: 'network',
    category: '网络安全',
    cover: '/default-course-image.png',
    videoUrl: '/video/1.3_IDS和IPS.mp4',
    tags: ['IDS', 'IPS', '网络安全'],
  },
  {
    id: 4,
    name: 'APT攻击分析',
    description: '通过案例分析理解 APT 攻击链路、战术特征与应对方式。',
    difficulty: 4,
    type: 'advanced',
    category: '高级威胁',
    cover: '/default-course-image.png',
    videoUrl: '/video/1.4_APT攻击分析.mp4',
    tags: ['APT', '威胁分析', '安全运营'],
  },
  {
    id: 5,
    name: '防火墙技术',
    description: '学习防火墙原理、规则配置和网络边界防护方法。',
    difficulty: 3,
    type: 'network',
    category: '网络安全',
    cover: '/default-course-image.png',
    videoUrl: '/video/1.5_防火墙技术.mp4',
    tags: ['防火墙', '边界防护', '网络安全'],
  },
  {
    id: 6,
    name: '古典密码学',
    description: '掌握古典密码体制、手工破译思路与密码学基础概念。',
    difficulty: 2,
    type: 'crypto',
    category: '密码学',
    cover: '/default-course-image.png',
    videoUrl: '/video/2.1_古典密码学.mp4',
    tags: ['密码学', '古典密码', '安全基础'],
  },
  {
    id: 7,
    name: '公钥密码简介',
    description: '介绍公钥密码体系、密钥管理、证书与 PKI 基础。',
    difficulty: 3,
    type: 'crypto',
    category: '密码学',
    cover: '/default-course-image.png',
    videoUrl: '/video/2.4_公钥密码简介.mp4',
    tags: ['公钥密码', 'PKI', '证书体系'],
  },
  {
    id: 8,
    name: 'RSA公钥加密方案',
    description: '深入理解 RSA 的数学原理、密钥生成与典型应用。',
    difficulty: 4,
    type: 'crypto',
    category: '密码学',
    cover: '/default-course-image.png',
    videoUrl: '/video/2.5_RSA公钥加密方案.mp4',
    tags: ['RSA', '非对称加密', '密码学'],
  },
  {
    id: 9,
    name: '数字签名技术',
    description: '学习数字签名、身份认证和证书验证相关核心技术。',
    difficulty: 4,
    type: 'crypto',
    category: '密码学',
    cover: '/default-course-image.png',
    videoUrl: '/video/2.6_数字签名技术.mp4',
    tags: ['数字签名', '身份认证', '密码学'],
  },
  {
    id: 10,
    name: '操作系统安全概述',
    description: '建立操作系统安全机制、访问控制与系统加固的整体认知。',
    difficulty: 3,
    type: 'system',
    category: '系统安全',
    cover: '/default-course-image.png',
    videoUrl: '/video/3.2_操作系统安全概述.mp4',
    tags: ['操作系统安全', '访问控制', '系统加固'],
  },
  {
    id: 11,
    name: '可信计算技术',
    description: '学习可信计算、TPM、可信启动与远程证明等关键概念。',
    difficulty: 4,
    type: 'system',
    category: '系统安全',
    cover: '/default-course-image.png',
    videoUrl: '/video/3.4_可信计算技术.mp4',
    tags: ['可信计算', 'TPM', '系统安全'],
  },
  {
    id: 12,
    name: '网络安全概述',
    description: '梳理网络安全基础概念、威胁类型与整体防护框架。',
    difficulty: 3,
    type: 'network',
    category: '网络安全',
    cover: '/default-course-image.png',
    videoUrl: '/video/4.1.1_网络安全概述.mp4',
    tags: ['网络安全', '安全架构', '防护体系'],
  },
]

export const PRESENTATION_MODULE_SEEDS: PresentationModuleSeed[] = [
  { id: 1, name: 'SQL注入基础实验', description: '掌握 SQL 注入漏洞的基础识别与利用方式。', difficulty: 3, type: 'Web安全', estimatedTime: '2-3小时', score: 60, courseId: 1, courseName: 'SQL注入攻击' },
  { id: 2, name: 'XSS跨站脚本攻击实验', description: '训练反射型、存储型和 DOM 型 XSS 的分析能力。', difficulty: 2, type: 'Web安全', estimatedTime: '2-3小时', score: 45, courseId: 2, courseName: 'XSS与CSRF攻击' },
  { id: 3, name: 'CSRF跨站请求伪造实验', description: '理解 CSRF 利用流程与令牌防护机制。', difficulty: 3, type: 'Web安全', estimatedTime: '3-4小时', score: 65, courseId: 2, courseName: 'XSS与CSRF攻击' },
  { id: 4, name: '命令注入漏洞实验', description: '学习命令注入漏洞的利用链与输入过滤绕过方式。', difficulty: 2, type: 'Web安全', estimatedTime: '2小时', score: 40, courseId: 4, courseName: 'APT攻击分析' },
  { id: 5, name: '文件上传漏洞实验', description: '掌握文件上传绕过、校验缺陷利用与风险分析。', difficulty: 3, type: 'Web安全', estimatedTime: '2小时', score: 55, courseId: 1, courseName: 'SQL注入攻击' },
  { id: 6, name: '目录遍历', description: '训练路径遍历、敏感文件读取和绕过技巧。', difficulty: 3, type: 'Web安全', estimatedTime: '2小时', score: 55, courseId: 5, courseName: '防火墙技术' },
  { id: 7, name: '组件漏洞挖掘', description: '围绕第三方组件高危漏洞开展分析与复现。', difficulty: 4, type: '系统安全', estimatedTime: '3小时', score: 75, courseId: 11, courseName: '可信计算技术' },
  { id: 8, name: '业务逻辑漏洞实战', description: '围绕业务流程缺陷训练越权、重放与篡改攻击。', difficulty: 3, type: 'Web安全', estimatedTime: '3-4小时', score: 65, courseId: 4, courseName: 'APT攻击分析' },
  { id: 9, name: '内网渗透技术', description: '从边界突破到横向移动，训练完整内网渗透链路。', difficulty: 5, type: '网络攻防', estimatedTime: '4-5小时', score: 85, courseId: 12, courseName: '网络安全概述' },
  { id: 10, name: '代码审计进阶', description: '基于开源项目训练漏洞点追踪与代码审计能力。', difficulty: 4, type: '系统安全', estimatedTime: '3-4小时', score: 75, courseId: 10, courseName: '操作系统安全概述' },
  { id: 11, name: 'CTF综合实战', description: '综合训练 Web、逆向、密码学与取证等能力。', difficulty: 5, type: 'CTF', estimatedTime: '5小时', score: 100, courseId: 9, courseName: '数字签名技术' },
  { id: 12, name: '红队武器库', description: '学习红队武器使用、免杀、钓鱼与渗透技巧。', difficulty: 5, type: '网络攻防', estimatedTime: '4-5小时', score: 100, courseId: 3, courseName: 'IDS和IPS系统' },
  { id: 13, name: '漏洞挖掘方法论', description: '掌握漏洞发现、验证、利用和复现的方法论。', difficulty: 5, type: '系统安全', estimatedTime: '5小时', score: 100, courseId: 10, courseName: '操作系统安全概述' },
  { id: 14, name: '第三方框架漏洞', description: '聚焦 ThinkPHP、Struts2、Spring 等框架漏洞实战。', difficulty: 5, type: '系统安全', estimatedTime: '5小时', score: 100, courseId: 11, courseName: '可信计算技术' },
]

const buildPresentationAdminCourse = (course: PresentationCourseSeed, index: number): Course => ({
  id: course.id,
  name: course.name,
  description: course.description,
  cover: course.cover,
  difficulty: course.difficulty,
  category: course.category,
  status: 'published',
  studentCount: 48 + index * 3,
  experimentCount: PRESENTATION_MODULE_SEEDS.filter((module) => module.courseId === course.id).length,
  createTime: `2024-03-${String(index + 1).padStart(2, '0')} 10:00:00`,
})

const buildPresentationCourseSummary = (course: PresentationCourseSeed): CourseSummaryDto => ({
  id: course.id,
  name: course.name,
  description: course.description,
  difficulty: course.difficulty,
  imageUrl: course.cover.replace(/^\//, ''),
  type: course.type,
  tags: course.tags,
  status: 'published',
})

const buildPresentationModuleOverview = (module: PresentationModuleSeed): ModuleOverViewType => ({
  id: module.id,
  name: module.name,
  description: module.description,
  difficulty: module.difficulty,
  type: module.type,
  status: 'available',
  estimatedTime: module.estimatedTime,
  score: module.score,
})

const buildPresentationAdminLab = (module: PresentationModuleSeed, index: number): Experiment => ({
  id: module.id,
  name: module.name,
  description: module.description,
  difficulty: module.difficulty,
  courseId: module.courseId,
  courseName: module.courseName,
  status: 'published',
  taskPoints: [
    {
      id: module.id * 10 + 1,
      name: `${module.name}任务点`,
      score: 50,
      description: `围绕 ${module.name} 的核心知识点展开训练`,
    },
  ],
  environment: {
    targetMachine: {
      image: `module-${module.id}:latest`,
      port: 80,
      memory: module.difficulty >= 4 ? '1GB' : '512MB',
    },
    operationMachine: {
      image: 'kali-tools:latest',
      port: 6080,
      memory: '1GB',
    },
  },
  studentCount: 32 + (index % 6) * 8,
  completionRate: 58 + (index % 5) * 6,
  averageScore: 70 + (index % 4) * 5,
  createTime: `2024-03-${String(index + 1).padStart(2, '0')} 09:00:00`,
})

export const buildPresentationCourseSummaries = (): CourseSummaryDto[] =>
  PRESENTATION_COURSE_SEEDS.map(buildPresentationCourseSummary)

export const buildPresentationAdminCourses = (): Course[] =>
  PRESENTATION_COURSE_SEEDS.map(buildPresentationAdminCourse)

export const buildPresentationUserCourses = (): CourseOverViewType[] =>
  PRESENTATION_COURSE_SEEDS.map((course, index) => ({
    id: course.id,
    name: course.name,
    image: course.cover,
    description: course.description,
    status: 'available',
    category: course.type,
    difficulty: course.difficulty,
    estimatedHours: 6 + (index % 5),
    tags: course.tags,
    totalStudents: 800 + index * 35,
    videoUrl: course.videoUrl,
  }))

export const buildPresentationModuleOverviews = (): ModuleOverViewType[] =>
  PRESENTATION_MODULE_SEEDS.map(buildPresentationModuleOverview)

export const buildPresentationAdminLabs = (): Experiment[] =>
  PRESENTATION_MODULE_SEEDS.map(buildPresentationAdminLab)

const courseSummaryMap = new Map(buildPresentationCourseSummaries().map((item) => [item.name, item]))
const adminCourseMap = new Map(buildPresentationAdminCourses().map((item) => [item.name, item]))
const moduleOverviewMap = new Map(buildPresentationModuleOverviews().map((item) => [item.name, item]))
const adminLabMap = new Map(buildPresentationAdminLabs().map((item) => [item.name, item]))

export const mergeCourseSummariesWithPresentation = (remoteCourses: CourseSummaryDto[] = []) =>
  PRESENTATION_COURSE_SEEDS.map((seed) => {
    const base = courseSummaryMap.get(seed.name)!
    const remote = remoteCourses.find((item) => item.name === seed.name)
    return remote
      ? {
          ...base,
          ...remote,
          description: remote.description || base.description,
          imageUrl: remote.imageUrl || base.imageUrl,
          type: remote.type || base.type,
          tags: remote.tags?.length ? remote.tags : base.tags,
        }
      : base
  })

export const mergeAdminCoursesWithPresentation = (remoteCourses: Course[] = []) =>
  PRESENTATION_COURSE_SEEDS.map((seed) => {
    const base = adminCourseMap.get(seed.name)!
    const remote = remoteCourses.find((item) => item.name === seed.name)
    return remote
      ? {
          ...base,
          ...remote,
          description: remote.description || base.description,
          cover: remote.cover || base.cover,
          category: remote.category || base.category,
          studentCount: remote.studentCount || base.studentCount,
          experimentCount: base.experimentCount,
          createTime: remote.createTime || base.createTime,
        }
      : base
  })

export const mergeModuleOverviewsWithPresentation = (remoteModules: ModuleOverViewType[] = []) =>
  PRESENTATION_MODULE_SEEDS.map((seed) => {
    const base = moduleOverviewMap.get(seed.name)!
    const remote = remoteModules.find((item) => item.name === seed.name)
    return remote
      ? {
          ...base,
          ...remote,
          description: remote.description || base.description,
          type: remote.type || base.type,
          estimatedTime: remote.estimatedTime || base.estimatedTime,
          score: remote.score || base.score,
        }
      : base
  })

export const mergeAdminLabsWithPresentation = (remoteLabs: Experiment[] = []) =>
  PRESENTATION_MODULE_SEEDS.map((seed) => {
    const base = adminLabMap.get(seed.name)!
    const remote = remoteLabs.find((item) => item.name === seed.name)
    return remote
      ? {
          ...base,
          ...remote,
          description: remote.description || base.description,
          courseId: remote.courseId ?? base.courseId,
          courseName: remote.courseName || base.courseName,
          taskPoints: remote.taskPoints?.length ? remote.taskPoints : base.taskPoints,
          environment: Object.keys(remote.environment || {}).length ? remote.environment : base.environment,
          studentCount: remote.studentCount || base.studentCount,
          completionRate: remote.completionRate || base.completionRate,
          averageScore: remote.averageScore || base.averageScore,
          createTime: remote.createTime || base.createTime,
        }
      : base
  })
