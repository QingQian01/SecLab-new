<script setup lang="ts">
// 定义课程接口

import {useRoute, useRouter} from "vue-router";
import { ref, onMounted, computed, type Ref } from 'vue'
import { CourseStatus } from "./index";
import type { Course } from "./index";
import {getCourseDetail} from "../../../api.ts";
import { getUserInfo } from '../../../api.ts'

const route = useRoute();
const router = useRouter();
const courseId = route.params.id;

// 添加错误提示状态
const errorMessage = ref<string | null>(null);

// 模拟课程数据
let course:Ref<Course> = ref({
  id: null,
  name: "",
  description: null,
  difficulty: null,
  type: null,
  tags: null,
  imageUrl: null,
  costTime: null,
  schedule: null,
  status: null,
  instructor: null,
  modules: []
})

// 用于模块依赖图的数据
const moduleItems = ref<any[]>([]);

// 添加学习进度（基于实际完成的模块数动态计算）
const learningProgress = ref(0);

// 动态计算学习进度：根据课程模块总数和实际完成数计算
function updateLearningProgress() {
  if (!course.value.modules || course.value.modules.length === 0) {
    learningProgress.value = 0;
    return;
  }
  // 默认初始化为0，后端接入后应从API获取实际完成数
  learningProgress.value = 0;
}

// 添加课程资源
const courseResources = ref([
  { name: '课程PPT', type: 'pdf', icon: 'file-pdf', size: '2.5MB' },
  { name: '实验手册', type: 'doc', icon: 'file-word', size: '1.8MB' },
  { name: '参考资料', type: 'link', icon: 'link', url: '#' },
  { name: '课程视频', type: 'video', icon: 'video', size: '108MB' }
]);

// 添加相关课程
const relatedCourses = ref([
  { id: 1, name: '网络安全基础', similarity: 95, students: 1280 },
  { id: 2, name: '密码学原理', similarity: 82, students: 865 },
  { id: 3, name: '数据加密与解密', similarity: 78, students: 742 }
]);

// 添加推荐实验数据，使用实际实验ID
const recommendedExperiments = ref([
  { id: 1, name: 'SQL注入基础实验', type: '实战演练', difficulty: 3, tags: ['Web安全', 'SQL注入'], estimatedTime: '2小时' },
  { id: 2, name: 'XSS攻击防御实验', type: '实战演练', difficulty: 2, tags: ['Web安全', 'XSS'], estimatedTime: '1.5小时' },
  { id: 3, name: 'CSRF漏洞利用实验', type: '实战演练', difficulty: 3, tags: ['Web安全', 'CSRF'], estimatedTime: '2.5小时' },
  { id: 4, name: '文件上传漏洞实验', type: '实战演练', difficulty: 4, tags: ['Web安全', '文件上传'], estimatedTime: '3小时' }
]);

// 跳转到实验模块
const goToExperiment = (experimentId: number) => {
  console.log(`跳转到实验模块: ${experimentId}`);
  router.push(`/user/module/${experimentId}`);
};

onMounted( async ()=>{
  try {
    // 直接使用本地数据，提高加载速度
    console.log('Using local fallback data for course detail');
    
    // 从本地课程列表中获取对应ID的课程数据
    const courseIdNum = Number(courseId);
    const allCourses = [
      {
        id: 1,
        name: 'SQL注入攻击',
        description: '本课程详细讲解SQL注入攻击的原理、分类和防御技术。通过实际案例讲解如何发现和利用SQL注入漏洞，以及如何通过参数化查询、输入验证和最小权限原则等方法防止SQL注入攻击，保障Web应用的数据安全。',
        difficulty: 3,
        type: 'web',
        tags: ['SQL注入', 'Web安全', '数据库安全'],
        imageUrl: '/1.png',
        costTime: 8,
        schedule: '每周一 14:00-16:00',
        status: 'active',
        instructor: '张教授',
        modules: [
          {
            moduleId: 1,
            moduleName: 'SQL注入基础',
            introduction: '学习SQL注入的基本原理和常见攻击方法',
            type: ['Web安全', 'SQL注入'],
            difficulty: 3
          },
          {
            moduleId: 2,
            moduleName: 'SQL注入防御',
            introduction: '掌握SQL注入的防御技术和最佳实践',
            type: ['Web安全', 'SQL注入'],
            difficulty: 4
          }
        ]
      },
      {
        id: 2,
        name: 'XSS与CSRF攻击',
        description: '本课程深入剖析跨站脚本(XSS)和跨站请求伪造(CSRF)攻击的原理和防御方法。通过实例讲解反射型XSS、存储型XSS和DOM型XSS攻击，以及CSRF攻击的实施过程，帮助学习者掌握Web前端安全防护的关键技术。',
        difficulty: 2,
        type: 'web',
        tags: ['XSS', 'CSRF', 'Web安全'],
        imageUrl: '/2.png',
        costTime: 6,
        schedule: '每周二 10:00-12:00',
        status: 'active',
        instructor: '李教授',
        modules: [
          {
            moduleId: 3,
            moduleName: 'XSS攻击原理',
            introduction: '了解XSS攻击的基本原理和分类',
            type: ['Web安全', 'XSS'],
            difficulty: 2
          },
          {
            moduleId: 4,
            moduleName: 'CSRF攻击防御',
            introduction: '学习CSRF攻击的防御方法',
            type: ['Web安全', 'CSRF'],
            difficulty: 3
          }
        ]
      },
      {
        id: 3,
        name: 'IDS和IPS系统',
        description: '本课程介绍入侵检测系统(IDS)和入侵防御系统(IPS)的工作原理和部署策略。通过分析网络流量和系统行为，识别和防御各类网络攻击，包括异常检测、特征匹配和行为分析等技术，帮助学习者构建有效的网络安全防护体系。',
        difficulty: 3,
        type: 'network',
        tags: ['IDS', 'IPS', '网络安全'],
        imageUrl: '/3.png',
        costTime: 7,
        schedule: '每周三 14:00-16:00',
        status: 'active',
        instructor: '王教授',
        modules: [
          {
            moduleId: 5,
            moduleName: 'IDS系统原理',
            introduction: '了解IDS系统的工作原理和部署方法',
            type: ['网络安全', 'IDS'],
            difficulty: 3
          },
          {
            moduleId: 6,
            moduleName: 'IPS系统配置',
            introduction: '学习IPS系统的配置和管理',
            type: ['网络安全', 'IPS'],
            difficulty: 4
          }
        ]
      },
      {
        id: 4,
        name: 'APT攻击分析',
        description: '本课程深入分析高级持续性威胁(APT)攻击的特点和防御策略。通过实际APT攻击案例分析，介绍攻击者的战术、技术和程序(TTP)，以及如何建立有效的威胁情报和安全防御体系，提升组织抵御高级威胁的能力。',
        difficulty: 4,
        type: 'advanced',
        tags: ['APT', '高级威胁', '网络安全'],
        imageUrl: '/4.png',
        costTime: 10,
        schedule: '每周四 10:00-12:00',
        status: 'active',
        instructor: '赵教授',
        modules: [
          {
            moduleId: 7,
            moduleName: 'APT攻击特征',
            introduction: '识别APT攻击的特征和行为模式',
            type: ['高级威胁', 'APT'],
            difficulty: 4
          },
          {
            moduleId: 8,
            moduleName: 'APT防御策略',
            introduction: '学习APT攻击的防御策略和最佳实践',
            type: ['高级威胁', 'APT'],
            difficulty: 5
          }
        ]
      },
      {
        id: 5,
        name: '防火墙技术',
        description: '本课程详细讲解网络防火墙的原理、类型和配置方法。包括包过滤防火墙、状态检测防火墙、应用层防火墙和下一代防火墙的特点与部署策略，以及访问控制列表(ACL)、NAT配置、VPN集成等实用技术，帮助学习者掌握网络边界防护的核心技能。',
        difficulty: 3,
        type: 'network',
        tags: ['防火墙', '网络安全', '边界防护'],
        imageUrl: '/5.png',
        costTime: 8,
        schedule: '每周五 14:00-16:00',
        status: 'active',
        instructor: '钱教授',
        modules: [
          {
            moduleId: 9,
            moduleName: '防火墙基础',
            introduction: '了解防火墙的基本原理和类型',
            type: ['网络安全', '防火墙'],
            difficulty: 3
          },
          {
            moduleId: 10,
            moduleName: '防火墙配置',
            introduction: '学习防火墙的配置和管理',
            type: ['网络安全', '防火墙'],
            difficulty: 4
          }
        ]
      },
      {
        id: 13,
        name: '栈溢出攻击实战',
        description: '本课程从栈结构原理出发，系统讲解栈溢出漏洞的成因与利用方法。通过在 Linux 操作环境中编写含后门的漏洞程序、使用 pwndbg 定位溢出偏移、用 pwntools 编写 exp 劫持函数返回地址，完成从理论到 getshell 的完整栈溢出学习闭环，掌握二进制安全基础与 PWN 核心技能。',
        difficulty: 3,
        type: 'system',
        tags: ['栈溢出', '二进制安全', 'PWN'],
        imageUrl: '/13.png',
        costTime: 8,
        schedule: '每周一 14:00-16:00',
        status: 'active',
        instructor: 'SecLab 教研组',
        modules: [
          {
            moduleId: 15,
            moduleName: '栈溢出实验',
            introduction: '编写漏洞程序、定位溢出偏移、用 pwntools 编写 exp 劫持返回地址',
            type: ['系统安全', '栈溢出'],
            difficulty: 3
          }
        ]
      },
      {
        id: 14,
        name: '协议分析实战',
        description: '本课程围绕网络协议分析展开，使用 Wireshark 对 HTTP、TCP、UDP 等常见协议进行深度抓包与解析。通过分析三次握手、HTTP 请求响应、明文传输风险与 HTTPS/TLS 加密防护，帮助学习者掌握网络流量分析方法，理解协议级安全风险与防护手段。',
        difficulty: 3,
        type: 'network',
        tags: ['协议分析', 'Wireshark', '网络安全'],
        imageUrl: '/14.png',
        costTime: 8,
        schedule: '每周二 14:00-16:00',
        status: 'active',
        instructor: 'SecLab 教研组',
        modules: [
          {
            moduleId: 16,
            moduleName: '协议分析实验',
            introduction: '使用 Wireshark 抓包分析 HTTP/TCP 协议，理解明文传输与加密防护',
            type: ['网络安全', '协议分析'],
            difficulty: 3
          }
        ]
      },
      {
        id: 15,
        name: '堆溢出攻击实战',
        description: '本课程深入讲解 glibc 堆管理机制与堆溢出利用技术。涵盖 chunk 结构、fastbin/smallbin 组织、unlink 利用、fastbin attack 等核心攻击手法，通过实战 exp 编写完成堆溢出利用与控制流劫持，提升二进制漏洞利用进阶能力。',
        difficulty: 4,
        type: 'system',
        tags: ['堆溢出', '二进制安全', 'PWN'],
        imageUrl: '/15.png',
        costTime: 10,
        schedule: '每周三 14:00-16:00',
        status: 'active',
        instructor: 'SecLab 教研组',
        modules: [
          {
            moduleId: 17,
            moduleName: '堆溢出实验',
            introduction: '理解 glibc 堆管理，利用 unlink 与 fastbin attack 完成堆溢出利用',
            type: ['系统安全', '堆溢出'],
            difficulty: 5
          }
        ]
      },
      {
        id: 16,
        name: '格式化字符串漏洞实战',
        description: '本课程系统讲解格式化字符串漏洞原理与利用。从 printf 函数机制出发，覆盖栈上任意地址泄露、利用 %n 完成任意地址写入、结合 GOT 表劫持与控制流转移等进阶技术，帮助学习者掌握这一经典且威力巨大的漏洞利用手法。',
        difficulty: 4,
        type: 'system',
        tags: ['格式化字符串', '二进制安全', 'PWN'],
        imageUrl: '/16.png',
        costTime: 10,
        schedule: '每周四 14:00-16:00',
        status: 'active',
        instructor: 'SecLab 教研组',
        modules: [
          {
            moduleId: 18,
            moduleName: '格式化字符串实验',
            introduction: '利用 printf 格式化字符串漏洞完成栈泄露与任意地址写入',
            type: ['系统安全', '格式化字符串'],
            difficulty: 4
          }
        ]
      }
    ];
    
    // 查找对应ID的课程
    const foundCourse = allCourses.find(c => c.id === courseIdNum);
    if (foundCourse) {
      course.value = foundCourse;
      // 更新模块依赖图数据
      moduleItems.value = course.value.modules.map(module => ({
        id: module.moduleId,
        name: module.moduleName,
        description: module.introduction,
        difficulty: module.difficulty,
        type: module.type ? module.type.join(', ') : "",
        status: 'available' as 'available' | 'completed' | 'locked',
        prerequisites: [], // 假设模块没有prerequisites属性
        estimatedTime: "2-3小时"
      }));
    } else {
      console.warn('Course not found, using default data');
      // 使用默认数据
      course.value = {
        id: courseIdNum,
        name: '课程名称',
        description: '课程描述',
        difficulty: 3,
        type: 'web',
        tags: [],
        imageUrl: '',
        costTime: 8,
        schedule: '',
        status: 'active',
        instructor: '教授',
        modules: []
      };
    }
  } catch (error) {
    console.error('Failed to load course data:', error);
    // 使用默认数据
    course.value = {
      id: Number(courseId),
      name: '课程名称',
      description: '课程描述',
      difficulty: 3,
      type: 'web',
      tags: [],
      imageUrl: '',
      costTime: 8,
      schedule: '',
      status: 'active',
      instructor: '教授',
      modules: []
    };
  }
})

// 选择模块时的跳转处理
const handleSelectModule = (moduleId: number) => {
  router.push(`/user/module/${moduleId}`);
};

// 获取课程状态对应的标签样式
const getStatusBadgeClass = (status: CourseStatus | null) => {
  if (!status) return 'badge-neutral';
  const classes = {
    [CourseStatus.ACTIVE]: 'badge-success',
    [CourseStatus.UPCOMING]: 'badge-warning',
    [CourseStatus.COMPLETED]: 'badge-neutral'
  }
  return classes[status];
}

// 获取状态的中文描述
const getStatusText = (status: CourseStatus | null) => {
  if (!status) return '未知';
  const text = {
    [CourseStatus.ACTIVE]: '进行中',
    [CourseStatus.UPCOMING]: '即将开始',
    [CourseStatus.COMPLETED]: '已结束'
  }
  return text[status];
}

// Add a helper function to render stars
const getDifficultyStars = (difficulty: number | null) => {
  if (difficulty === null) return '未知';
  return '★'.repeat(difficulty) + '☆'.repeat(5 - difficulty);
}

// 添加难度等级描述
const getDifficultyText = (difficulty: number | null) => {
  if (difficulty === null) return '未知';
  const levels = {
    1: '入门',
    2: '基础',
    3: '进阶',
    4: '困难',
    5: '专家'
  }
  return levels[difficulty as keyof typeof levels];
}

// 添加动画控制状态
const isPageLoaded = ref(false)
const isContentVisible = ref(false)

function onButtonClick(id:number | null){
  if (id === null) return;
  router.push(`/user/module/${id}`);
}

onMounted(() => {
  isPageLoaded.value = true
  setTimeout(() => {
    isContentVisible.value = true
  }, 100)
})

// 用户信息
const userInfo = ref({
  userName: '',
  userStudentNumber: '',
  userImage: ''
  // ...其他字段
})

// 获取token（假设保存在localStorage）
const token = localStorage.getItem('token') || ''

onMounted(async () => {
  if (token) {
    const res = await getUserInfo(token)
    if (res.isSuccess === 1 && res.data) {
      // 确保userImage不为undefined
      userInfo.value = {
        userName: res.data.userName || '',
        userStudentNumber: res.data.userStudentNumber || '',
        userImage: res.data.userImage || ''
      }
    }
  }
})

// 获取推荐实验
const getRecommendedExperiments = (courseId: number | null) => {
  if (!courseId) return [];
  
  // 根据课程ID返回相关实验
  // 为每个课程返回1-2个相关实验
  switch (courseId) {
    case 1: // SQL注入攻防实战
      return recommendedExperiments.value.filter(exp => exp.id === 1);
    case 2: // XSS与CSRF攻防详解
      return recommendedExperiments.value.filter(exp => [2, 3].includes(exp.id));
    case 3: // IDS和IPS安全防护
      return recommendedExperiments.value.filter(exp => exp.id === 1);
    case 4: // APT攻击分析与防御
      return recommendedExperiments.value.filter(exp => exp.id === 4);
    case 5: // 防火墙技术与配置
      return recommendedExperiments.value.filter(exp => exp.id === 1);
    case 6: // 古典密码学基础
      return recommendedExperiments.value.filter(exp => exp.id === 2);
    case 7: // 公钥密码简介
      return recommendedExperiments.value.filter(exp => exp.id === 2);
    case 8: // RSA公钥加密方案
      return recommendedExperiments.value.filter(exp => exp.id === 2);
    case 9: // 数字签名技术
      return recommendedExperiments.value.filter(exp => exp.id === 2);
    case 10: // 操作系统安全概述
      return recommendedExperiments.value.filter(exp => exp.id === 4);
    case 11: // 可信计算技术
      return recommendedExperiments.value.filter(exp => exp.id === 3);
    case 12: // 网络安全概述
      return recommendedExperiments.value.filter(exp => exp.id === 1);
    default:
      // 默认返回所有实验
      return recommendedExperiments.value.slice(0, 2);
  }
};

// 开始实验
const startExperiment = (experimentId: number) => {
  console.log(`开始实验: ${experimentId}`);
  router.push(`/user/module/${experimentId}`);
};

// 获取视频标题
const getVideoTitle = (courseId: number | null, videoIndex: number) => {
  if (!courseId) return '未知视频';
  switch (courseId) {
    case 1:
      return videoIndex === 1 ? 'SQL注入攻击' : (videoIndex === 2 ? 'XSS与CSRF' : 'IDS和IPS');
    case 2:
      return videoIndex === 1 ? 'XSS攻击防御' : (videoIndex === 2 ? 'CSRF漏洞利用' : '文件上传漏洞');
    case 3:
      return videoIndex === 1 ? 'IDS和IPS' : (videoIndex === 2 ? 'APT攻击分析' : '防火墙技术');
    case 4:
      return videoIndex === 1 ? 'APT攻击分析' : (videoIndex === 2 ? '操作系统安全' : '可信计算');
    case 5:
      return videoIndex === 1 ? '防火墙技术' : (videoIndex === 2 ? '古典密码学' : '公钥密码');
    case 6:
      return videoIndex === 1 ? '古典密码学' : (videoIndex === 2 ? '公钥密码' : 'RSA公钥加密');
    case 7:
      return videoIndex === 1 ? '公钥密码' : (videoIndex === 2 ? 'RSA公钥加密' : '数字签名');
    case 8:
      return videoIndex === 1 ? 'RSA公钥加密' : (videoIndex === 2 ? '数字签名' : '操作系统安全');
    case 9:
      return videoIndex === 1 ? '数字签名' : (videoIndex === 2 ? '操作系统安全' : '网络安全概述');
    case 10:
      return videoIndex === 1 ? '操作系统安全' : (videoIndex === 2 ? '可信计算' : '网络安全概述');
    case 11:
      return videoIndex === 1 ? '可信计算' : (videoIndex === 2 ? '网络安全概述' : '实战实验推荐');
    case 12:
      return videoIndex === 1 ? '网络安全概述' : (videoIndex === 2 ? '实战实验推荐' : '课程结束');
    default:
      return '未知视频';
  }
};

// 获取视频描述
const getVideoDescription = (courseId: number | null, videoIndex: number) => {
  if (!courseId) return '暂无描述';
  switch (courseId) {
    case 1:
      return videoIndex === 1 ? '介绍SQL注入攻击的基本原理和常见类型' : (videoIndex === 2 ? '讲解XSS和CSRF的防御方法' : '介绍IDS和IPS的工作原理和区别');
    case 2:
      return videoIndex === 1 ? '讲解XSS攻击的防御措施' : (videoIndex === 2 ? '介绍CSRF漏洞的利用和防御' : '讲解文件上传漏洞的防御方法');
    case 3:
      return videoIndex === 1 ? '介绍IDS和IPS的工作原理' : (videoIndex === 2 ? '讲解APT攻击的分析方法' : '介绍防火墙技术的配置和作用');
    case 4:
      return videoIndex === 1 ? '讲解APT攻击的分析方法' : (videoIndex === 2 ? '介绍操作系统安全的概念' : '讲解可信计算技术的应用');
    case 5:
      return videoIndex === 1 ? '介绍防火墙技术的配置方法' : (videoIndex === 2 ? '讲解古典密码学的基本原理' : '介绍公钥密码的加密过程');
    case 6:
      return videoIndex === 1 ? '介绍古典密码学的基本原理' : (videoIndex === 2 ? '介绍公钥密码的加密过程' : '介绍RSA公钥加密的原理和应用');
    case 7:
      return videoIndex === 1 ? '介绍公钥密码的加密过程' : (videoIndex === 2 ? '介绍RSA公钥加密的原理和应用' : '介绍数字签名的作用');
    case 8:
      return videoIndex === 1 ? '介绍RSA公钥加密的原理和应用' : (videoIndex === 2 ? '介绍数字签名的作用' : '介绍操作系统安全的概念');
    case 9:
      return videoIndex === 1 ? '介绍数字签名的作用' : (videoIndex === 2 ? '介绍操作系统安全的概念' : '介绍网络安全概述');
    case 10:
      return videoIndex === 1 ? '介绍操作系统安全的概念' : (videoIndex === 2 ? '介绍可信计算技术的应用' : '介绍网络安全概述');
    case 11:
      return videoIndex === 1 ? '介绍可信计算技术的应用' : (videoIndex === 2 ? '介绍网络安全概述' : '介绍实战实验推荐');
    case 12:
      return videoIndex === 1 ? '介绍网络安全概述' : (videoIndex === 2 ? '介绍实战实验推荐' : '课程结束');
    default:
      return '暂无描述';
  }
};

const allCourses = ref([
  { id: 1, name: 'SQL注入攻击' },
  { id: 2, name: 'XSS与CSRF攻防详解' },
  { id: 3, name: 'IDS和IPS安全防护' },
  { id: 4, name: 'APT攻击分析与防御' },
  { id: 5, name: '防火墙技术与配置' },
  { id: 6, name: '古典密码学基础' },
  { id: 7, name: '公钥密码简介' },
  { id: 8, name: 'RSA公钥加密方案' },
  { id: 9, name: '数字签名技术' },
  { id: 10, name: '操作系统安全概述' },
  { id: 11, name: '可信计算技术' },
  { id: 12, name: '网络安全概述' },
  { id: 13, name: '栈溢出攻击实战' },
  { id: 14, name: '协议分析实战' },
  { id: 15, name: '堆溢出攻击实战' },
  { id: 16, name: '格式化字符串漏洞实战' }
]);

// ── 教学视频（阿里云 OSS 公共读）──────────────────────────
// OSS bucket: seclab2026，地域: cn-hangzhou，权限: public-read
// 前端直接拼接 URL 播放，无需后端签名。文件名含中文/空格需 encodeURIComponent。
const OSS_BASE_URL =
  import.meta.env.VITE_OSS_BASE_URL ||
  'https://seclab2026.oss-cn-hangzhou.aliyuncs.com';

// 课程 ID -> OSS 视频文件名映射（文件名与 bucket 内实际对象 key 一致）
// 注：课程 2 的视频未在 OSS 中找到（已尝试多种文件名变体均 404），暂留空，
//     页面会显示「该课程暂无视频」。上传后在此补充文件名即可。
const COURSE_VIDEOS: Record<number, string> = {
  1: '1.1Sql注入攻击.mp4',
  2: '1.2Xss与csrf-.mp4',
  3: '1.3 IDS和IPS.mp4',
  4: '1.4Apt攻击.mp4',
  5: '1.5防火墙.mp4',
  6: '2.2 古典密码.mp4',
  7: '2.4公钥密码简介.mp4',
  8: '2.5 Rsa公钥加密方案.mp4',
  9: '2.6数字签名.mp4',
  10: '3.2 操作系统安全概述.mp4',
  11: '3.4 可信计算.mp4',
  12: '4.1.1 网络安全概述.mp4',
};

// 当前课程的视频 URL，无映射则返回空串（模板显示「暂无视频」占位）
const videoUrl = computed(() => {
  const filename = COURSE_VIDEOS[course.value.id as number];
  if (!filename) return '';
  return `${OSS_BASE_URL}/${encodeURIComponent(filename)}`;
});
</script>

<template>
  <div class="container-fluid px-4 py-6 overflow-x-hidden" :class="{ 'fade-in': isPageLoaded }">
    <!-- 错误提示 -->
    <div v-if="errorMessage" class="alert alert-error mb-4">
      <i class="fas fa-exclamation-circle"></i>
      <span>{{ errorMessage }}</span>
    </div>
    
    <!-- 返回按钮 -->
    <div class="mb-4 slide-in-top">
      <button @click="router.go(-1)" class="btn btn-sm btn-ghost gap-2 hover:bg-base-200">
        <i class="fas fa-arrow-left"></i>
        <span>返回</span>
      </button>
    </div>
    
    <!-- 页面顶部：课程标题和状态 -->
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8 slide-in-top">
      <div class="flex items-center gap-4">
        <div class="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
          <i class="fas fa-graduation-cap text-2xl text-primary"></i>
        </div>
        <div>
          <h1 class="text-3xl font-bold hover:scale-[1.02] transition-transform">{{ course.name }}</h1>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <div :class="[
          'badge badge-lg py-3 px-4 gap-2 transition-all animate-pulse', 
          getStatusBadgeClass(course.status)
        ]">
          <span class="w-2 h-2 rounded-full bg-current"></span>
          <span class="font-medium">{{ getStatusText(course.status) }}</span>
        </div>
        <button class="btn btn-primary btn-sm gap-2 hidden md:flex">
          <i class="fas fa-bookmark"></i>
          收藏课程
        </button>
      </div>
    </div>

    <!-- 课程信息卡片 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
      <!-- 左侧：课程简介 -->
      <div class="lg:col-span-1">
        <div class="card bg-base-100 shadow-xl hover:shadow-2xl transition-all duration-300 h-full"
            :class="{ 'slide-in-left': isContentVisible }">
          <div class="card-body">
            <!-- 课程简介 -->
            <div class="mb-4">
              <div class="flex items-center gap-3 mb-3">
                <div class="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <i class="fas fa-info-circle text-xl text-primary"></i>
                </div>
                <h2 class="text-xl font-semibold">课程简介</h2>
              </div>
              <div class="pl-2 space-y-2 text-base-content/80 text-sm">
                <p class="whitespace-pre-line">{{ course.description }}</p>
              </div>
            </div>
            
            <!-- 课程标签 -->
            <div v-if="course.tags && course.tags.length > 0" class="mb-4">
              <div class="flex items-center gap-2 mb-3">
                <i class="fas fa-tags text-primary"></i>
                <h3 class="font-medium">课程标签</h3>
              </div>
              <div class="flex flex-wrap gap-2 pl-2">
                <span v-for="tag in course.tags" :key="tag" class="badge badge-outline">{{ tag }}</span>
              </div>
            </div>
            
            <!-- 课程信息 -->
            <div class="grid grid-cols-1 gap-2 mb-4">
              <div v-if="course.instructor" class="flex items-center gap-2">
                <i class="fas fa-chalkboard-teacher w-5 text-center text-primary"></i>
                <span class="text-sm">讲师：{{ course.instructor }}</span>
              </div>
              <div v-if="course.difficulty" class="flex items-center gap-2">
                <i class="fas fa-signal w-5 text-center text-primary"></i>
                <span class="text-sm">
                  难度：
                  <span class="text-yellow-500">{{ getDifficultyStars(course.difficulty) }}</span>
                  ({{ getDifficultyText(course.difficulty) }})
                </span>
              </div>
              <div v-if="course.costTime" class="flex items-center gap-2">
                <i class="fas fa-clock w-5 text-center text-primary"></i>
                <span class="text-sm">课时：{{ course.costTime }}</span>
              </div>
              <div v-if="course.type" class="flex items-center gap-2">
                <i class="fas fa-bookmark w-5 text-center text-primary"></i>
                <span class="text-sm">类型：{{ course.type }}</span>
              </div>
              <div v-if="course.schedule" class="flex items-center gap-2">
                <i class="fas fa-calendar-alt w-5 text-center text-primary"></i>
                <span class="text-sm">课程安排：{{ course.schedule }}</span>
              </div>
            </div>
            
            <!-- 课程资源 -->
            <div v-if="courseResources.length > 0" class="mb-4">
              <div class="flex items-center gap-2 mb-3">
                <i class="fas fa-download text-primary"></i>
                <h3 class="font-medium">课程资源</h3>
              </div>
              <div class="space-y-2 pl-2">
                <div v-for="resource in courseResources" :key="resource.name"
                    class="bg-base-200 p-2 rounded-lg flex justify-between items-center hover:bg-base-300 transition-colors">
                  <div class="flex items-center gap-2">
                    <i :class="`fas fa-${resource.icon} text-primary`"></i>
                    <span class="text-sm">{{ resource.name }}</span>
                  </div>
                  <div class="flex items-center">
                    <span v-if="resource.size" class="text-xs text-base-content/60 mr-2">{{ resource.size }}</span>
                    <button class="btn btn-xs btn-ghost btn-circle">
                      <i class="fas fa-download"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 进度 -->
            <div class="mt-auto">
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium">学习进度</span>
                <span class="text-sm font-bold text-primary">{{ learningProgress }}%</span>
              </div>
              <div class="w-full bg-base-200 rounded-full h-2.5">
                <div class="bg-primary h-2.5 rounded-full" :style="{ width: `${learningProgress}%` }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：视频区域（占据2/3宽度） -->
      <div class="lg:col-span-2">
        <!-- 课程视频卡片 -->
        <div class="card bg-base-100 shadow-xl hover:shadow-2xl transition-all duration-300 h-full"
             :class="{ 'slide-in-right': isContentVisible }">
          <div class="card-body p-4">
            <div class="flex items-center gap-2 mb-3">
              <i class="fas fa-video text-xl text-primary"></i>
              <h2 class="text-xl font-semibold">课程视频</h2>
              <span class="badge badge-primary badge-sm ml-2">视频教程</span>
            </div>
            
            <!-- 视频区域 -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <!-- 主视频区域 -->
              <div class="lg:col-span-3">
                <div class="bg-base-200 rounded-xl overflow-hidden shadow-lg">
                  <!-- 视频播放器区域 -->
                  <div class="aspect-video w-full">
                    <video
                      v-if="videoUrl"
                      class="w-full"
                      controls
                      :key="videoUrl"
                    >
                      <source :src="videoUrl" type="video/mp4" />
                      您的浏览器不支持 HTML5 视频播放。
                    </video>
                    <div v-else class="w-full h-full flex items-center justify-center bg-base-300">
                      <div class="text-center p-6">
                        <i class="fas fa-video-slash text-4xl text-base-content/50 mb-3"></i>
                        <p class="text-base-content/70">该课程暂无视频</p>
                      </div>
                    </div>
                  </div>
                  <!-- 视频信息 -->
                  <div class="p-4">
                    <h3 class="font-medium text-lg mb-2">{{ course.name }} - 课程介绍</h3>
                    <div class="flex items-center justify-between text-sm text-base-content/80 mb-3">
                      <div class="flex items-center gap-3">
                        <span><i class="fas fa-clock mr-1"></i> 10:28</span>
                        <span><i class="fas fa-eye mr-1"></i> 3,254 次观看</span>
                      </div>
                      <div class="flex items-center gap-2">
                        <button class="btn btn-xs btn-outline btn-circle">
                          <i class="fas fa-thumbs-up"></i>
                        </button>
                        <button class="btn btn-xs btn-outline btn-circle">
                          <i class="fas fa-share"></i>
                        </button>
                      </div>
                    </div>
                    <p class="text-sm text-base-content/70">
                      本视频介绍了课程的主要内容、学习目标和实验环境。通过观看，您将了解到如何高效地完成课程学习，以及获取相关的实践经验。
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 视频选集 -->
            <div class="mt-5 mb-3">
              <div class="flex items-center justify-between mb-3">
                <div class="flex items-center gap-2">
                  <i class="fas fa-list text-primary"></i>
                  <h3 class="font-medium text-lg">{{ course.name }} 视频选集</h3>
                </div>
                <span class="badge badge-sm">{{ course.id && course.id <= 12 ? '3个视频' : '暂无视频' }}</span>
              </div>
              
              <!-- 视频列表 -->
              <div v-if="course.id && course.id <= 12" class="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div class="bg-base-200 p-3 rounded-lg cursor-pointer hover:bg-base-300 transition-colors border-l-4 border-primary">
                  <div class="flex items-center gap-2 mb-2">
                    <div class="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
                      <i class="fas fa-play-circle text-primary"></i>
                    </div>
                    <div>
                      <h4 class="font-medium">{{ getVideoTitle(course.id, 1) }}</h4>
                      <span class="text-xs text-base-content/60">{{ course.costTime ? `${Math.floor(course.costTime * 5)}:${Math.floor(Math.random() * 60).toString().padStart(2, '0')}` : '10:28' }}</span>
                    </div>
                  </div>
                  <p class="text-xs text-base-content/70 line-clamp-2">{{ getVideoDescription(course.id, 1) }}</p>
                </div>
                <div class="bg-base-200 p-3 rounded-lg cursor-pointer hover:bg-base-300 transition-colors">
                  <div class="flex items-center gap-2 mb-2">
                    <div class="w-10 h-10 rounded-lg bg-base-300 flex items-center justify-center">
                      <i class="fas fa-play-circle text-base-content/60"></i>
                    </div>
                    <div>
                      <h4 class="font-medium">{{ getVideoTitle(course.id, 2) }}</h4>
                      <span class="text-xs text-base-content/60">{{ course.costTime ? `${Math.floor(course.costTime * 4)}:${Math.floor(Math.random() * 60).toString().padStart(2, '0')}` : '8:15' }}</span>
                    </div>
                  </div>
                  <p class="text-xs text-base-content/70 line-clamp-2">{{ getVideoDescription(course.id, 2) }}</p>
                </div>
                <div class="bg-base-200 p-3 rounded-lg cursor-pointer hover:bg-base-300 transition-colors">
                  <div class="flex items-center gap-2 mb-2">
                    <div class="w-10 h-10 rounded-lg bg-base-300 flex items-center justify-center">
                      <i class="fas fa-play-circle text-base-content/60"></i>
                    </div>
                    <div>
                      <h4 class="font-medium">{{ getVideoTitle(course.id, 3) }}</h4>
                      <span class="text-xs text-base-content/60">{{ course.costTime ? `${Math.floor(course.costTime * 6)}:${Math.floor(Math.random() * 60).toString().padStart(2, '0')}` : '12:42' }}</span>
                    </div>
                  </div>
                  <p class="text-xs text-base-content/70 line-clamp-2">{{ getVideoDescription(course.id, 3) }}</p>
                </div>
              </div>
              <div v-else class="bg-base-200 p-6 rounded-lg text-center">
                <i class="fas fa-film text-4xl text-base-content/30 mb-3"></i>
                <p class="text-base-content/70">该课程暂无视频选集</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 模块列表 -->
    <div class="card bg-base-100 shadow-xl hover:shadow-2xl transition-shadow duration-300"
         :class="{ 'slide-in-right': isContentVisible }">
      <div class="card-body">
        <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
          <div class="flex items-center gap-2">
            <i class="fas fa-flask text-xl text-primary"></i>
            <h2 class="text-xl font-semibold">课程模块</h2>
            <span class="badge badge-primary">{{ course.modules.length }}个</span>
          </div>
          
          <!-- 筛选和搜索 -->
          <div class="flex flex-wrap gap-2">
            <div class="join">
              <button class="btn btn-sm join-item btn-active">全部</button>
              <button class="btn btn-sm join-item">实验</button>
              <button class="btn btn-sm join-item">理论</button>
            </div>
            <div class="form-control">
              <div class="input-group input-group-sm">
                <input type="text" placeholder="搜索模块..." class="input input-sm input-bordered" />
                <button class="btn btn-sm btn-square">
                  <i class="fas fa-search"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <div class="grid gap-4">
          <div v-for="(module, index) in course.modules" 
               :key="module.moduleId || index"
               class="card bg-base-200 hover:bg-base-300 transition-all duration-200 fade-in-row"
               :style="{ animationDelay: `${index * 0.1}s` }">
            <div class="card-body p-4">
              <div class="flex justify-between items-start">
                <div class="space-y-2">
                  <h3 class="text-lg font-medium flex items-center gap-2">
                    <i class="fas fa-terminal text-primary"></i>
                    {{ module.moduleName }}
                    <span class="badge badge-sm" :class="index === 0 ? 'badge-accent' : ''">
                      {{ index === 0 ? '推荐开始' : `模块 ${index + 1}` }}
                    </span>
                  </h3>
                  <p class="text-sm text-gray-500">{{ module.introduction }}</p>
                  <div class="flex items-center gap-4 text-sm flex-wrap">
                    <div v-if="module.type && module.type.length > 0" class="flex items-center gap-1">
                      <i class="fas fa-bookmark text-primary"></i>
                      <span>{{ module.type.join(', ') }}</span>
                    </div>
                    <div class="flex items-center gap-1" :title="getDifficultyText(module.difficulty)">
                      <i class="fas fa-signal text-primary"></i>
                      <span class="text-yellow-500">{{ getDifficultyStars(module.difficulty) }}</span>
                    </div>
                    <div class="flex items-center gap-1">
                      <i class="fas fa-clock text-primary"></i>
                      <span>预计 {{ module.difficulty ? `${module.difficulty}-${module.difficulty + 1}小时` : '未知' }}</span>
                    </div>
                  </div>
                </div>
                <div class="flex flex-col gap-2 items-end">
                  <div class="badge" :class="index < Math.ceil(course.modules.length * learningProgress / 100) ? 'badge-success' : 'badge-outline'">
                    {{ index < Math.ceil(course.modules.length * learningProgress / 100) ? '已完成' : '待完成' }}
                  </div>
                  <button @click="onButtonClick(module.moduleId)" class="btn btn-primary btn-sm gap-2 hover:scale-105 transition-transform duration-200 mt-2">
                    <i class="fas fa-arrow-right text-sm"></i>
                    进入模块
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 添加分隔线 -->
        <div class="divider my-8">
          <div class="flex items-center gap-2">
            <i class="fas fa-fire-alt text-warning"></i>
            <span class="text-lg">实战实验推荐</span>
          </div>
        </div>
        
        <!-- 推荐实验 -->
        <div class="bg-gradient-to-r from-primary/5 to-secondary/5 p-4 rounded-lg mb-6 border border-primary/20">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2">
              <i class="fas fa-flask text-primary"></i>
              <h3 class="font-medium text-lg">{{ course.name }} 相关实验</h3>
              <span class="badge badge-sm badge-primary">可直接跳转</span>
            </div>
            <button class="btn btn-sm btn-outline btn-primary">
              <i class="fas fa-th-list mr-1"></i>
              查看全部
            </button>
          </div>
          <p class="text-sm text-base-content/70 mb-3">以下是与《{{ course.name }}》相关的实战实验，点击即可直接开始</p>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
            <div v-for="experiment in getRecommendedExperiments(course.id)" :key="experiment.id" 
                class="card bg-base-200/90 hover:bg-base-200 transition-all duration-300 hover:shadow-md border-l-4"
                :class="{
                  'border-error': experiment.difficulty >= 4,
                  'border-warning': experiment.difficulty === 3,
                  'border-success': experiment.difficulty <= 2
                }">
              <div class="card-body p-3">
                <div class="flex items-center justify-between">
                  <div>
                    <h4 class="font-medium">{{ experiment.name }}</h4>
                    <div class="flex items-center gap-2 mt-1">
                      <span class="text-xs text-base-content/60">
                        <i class="fas fa-signal mr-1"></i> 
                        {{ getDifficultyText(experiment.difficulty) }}
                      </span>
                      <span class="text-xs text-base-content/60">
                        <i class="fas fa-clock mr-1"></i> 
                        {{ experiment.estimatedTime }}
                      </span>
                    </div>
                  </div>
                  <button @click="startExperiment(experiment.id)" class="btn btn-xs btn-primary">
                    开始实验
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
</div>
</template>

<style scoped>
.container-fluid {
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
}

html, body {
  overflow-x: hidden;
  margin: 0;
  padding: 0;
  width: 100%;
}

/* 基础淡入动画 */
.fade-in {
  animation: fadeIn 0.5s ease-out;
}

/* 从上滑入动画 */
.slide-in-top {
  animation: slideInTop 0.5s ease-out;
}

/* 从左滑入动画 */
.slide-in-left {
  animation: slideInLeft 0.5s ease-out;
}

/* 从右滑入动画 */
.slide-in-right {
  animation: slideInRight 0.5s ease-out;
}

/* 表格行淡入动画 */
.fade-in-row {
  opacity: 0;
  animation: fadeIn 0.5s ease-out forwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* 从顶部滑入 */
.slide-in-top {
  animation: slideInTop 0.7s ease-out;
}

@keyframes slideInTop {
  from {
    transform: translateY(-20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes slideInLeft {
  from {
    transform: translateX(-20px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slideInRight {
  from {
    transform: translateX(20px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* 添加图标悬停效果 */
.fas {
  transition: transform 0.2s ease;
}

.fas:hover {
  transform: scale(1.1);
}

/* 调整卡片过渡效果 */
.card {
  transition: all 0.3s ease;
}

.card:hover {
  transform: translateY(-2px);
}
</style>
