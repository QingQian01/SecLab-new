<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import type { ModuleOverViewType } from './components/ModuleOverView.ts'
import ModuleOverView from './components/ModuleOverView.vue'

// 修改模块数据，添加分数计算
const calculateScore = (difficulty: number, time: string): number => {
  // 解析预计用时，提取小时数
  const hours = parseFloat(time.split('-')[1]?.split('小时')[0] || time.split('小时')[0])
  // 计算总分：难度基础分 + 时间加成，上限100分
  const score = Math.min(difficulty * 15 + hours * 5, 100)
  return Math.round(score)
}

// 模拟模块数据
const modules = ref<ModuleOverViewType[]>([
  {
    id: 1,
    name: 'SQL注入基础实验',
    description: '学习Web安全的基本概念和常见漏洞类型，包括SQL注入、XSS等。适合安全学习的入门者。',
    difficulty: 3,
    type: 'Web安全',
    status: 'available',
    estimatedTime: '2-3小时',
    score: calculateScore(3, '2-3小时'), // 65分：难度3×15 + 3小时×5
    image: '/1.SQL注入攻防实战.png'
  },
  {
    id: 2,
    name: 'XSS跨站脚本攻击实验',
    description: '学习XSS跨站脚本攻击的原理、分类和防御方法，包括反射型、存储型和DOM型XSS。',
    difficulty: 2,
    type: 'Web安全',
    status: 'available',
    estimatedTime: '2-3小时',
    score: calculateScore(2, '2-3小时'), // 45分：难度2×15 + 3小时×5
    image: '/2.XSS漏洞深度解析.png'
  },
  {
    id: 3,
    name: 'CSRF跨站请求伪造实验',
    description: '学习CSRF攻击的原理和防御方法，包括Token验证、同源检查等安全措施。',
    difficulty: 3,
    type: 'Web安全',
    status: 'available',
    estimatedTime: '3-4小时',
    score: calculateScore(3, '3-4小时'), // 65分：难度3×15 + 4小时×5
    image: '/2.XSS漏洞深度解析.png'
  },
  {
    id: 4,
    name: '命令注入漏洞实验',
    description: '学习命令注入漏洞的原理、危害和防御方法，实践各种命令注入攻击技术。',
    difficulty: 2,
    type: 'Web安全',
    status: 'available',
    estimatedTime: '2小时',
    score: calculateScore(2, '2小时'), // 40分：难度2×15 + 2小时×5
    image: '/1.SQL注入攻防实战.png'
  },
  {
    id: 5,
    name: '文件上传漏洞实验',
    description: '学习文件上传漏洞的原理和利用方法，包括绕过客户端验证、服务器端验证等技术。',
    difficulty: 3,
    type: 'Web安全',
    status: 'available',
    estimatedTime: '2小时',
    score: calculateScore(3, '2小时'), // 55分：难度3×15 + 2小时×5
    image: '/3.文件上传漏洞突破 .png'
  },
  {
    id: 6,
    name: '目录遍历',
    description: '学习目录遍历漏洞的原理和利用方法，包括路径遍历、敏感文件读取、目录遍历绕过等技术。通过实战演练掌握目录遍历漏洞的发现、利用和防护方法。',
    difficulty: 3,
    type: 'Web安全',
    status: 'available',
    estimatedTime: '2小时',
    score: calculateScore(3, '2小时'), // 55分：难度3×15 + 2小时×5
    image: '/3.文件上传漏洞突破 .png'
  },
  {
    id: 15,
    name: '栈溢出实验',
    description: '在操作环境中自己编写栈溢出程序，用 pwndbg 定位溢出点、pwntools 编写 exp 劫持返回地址拿到本地 shell，再连接真实远程靶机完成 getshell 拿 flag。',
    difficulty: 3,
    type: '二进制安全',
    status: 'available',
    estimatedTime: '2-3小时',
    score: calculateScore(3, '2-3小时'), // 65分：难度3×15 + 3小时×5
    image: '/cover-stack-overflow.png'
  },
  {
    id: 7,
    name: '组件漏洞挖掘',
    description: '通过静态代码分析和动态测试发现第三方组件安全隐患，深入解析Shiro RememberMe反序列化、Fastjson JNDI注入、Log4j2远程代码执行等高危组件漏洞',
    difficulty: 4,
    type: 'Web安全',
    status: 'locked',
    estimatedTime: '3小时',
    score: calculateScore(4, '3小时'), // 70分：难度4×15 + 3小时×5
    image: '/5.组件漏洞挖掘.png'
  },
  {
    id: 8,
    name: '业务逻辑漏洞实战',
    description: '基于真实电商平台业务流程，系统训练水平越权、垂直越权、支付金额篡改、订单重放攻击等典型业务逻辑漏洞的发现与利用方法',
    difficulty: 3,
    type: 'Web安全',
    status: 'locked',
    prerequisites: [1, 2, 3],
    estimatedTime: '3-4小时',
    score: calculateScore(3, '3-4小时'), // 65分：难度3×15 + 4小时×5
    image: '/7.业务逻辑漏洞实战.png'
  },
  {
    id: 9,
    name: '内网渗透技术',
    description: '从外网突破到内网控制的完整渗透链路实践，包括边界突破、域环境信息收集、横向移动、域控提权等高级内网渗透技术',
    difficulty: 5,
    type: '网络攻防',
    status: 'locked',
    prerequisites: [4, 6, 7],
    estimatedTime: '4-5小时',
    score: calculateScore(5, '4-5小时'), // 85分：难度5×15 + 5小时×5
    image: '/8.内网渗透技术.png'
  },
  {
    id: 10,
    name: '代码审计进阶',
    description: '使用静态分析与动态调试相结合的方法，基于真实开源CMS项目源码，系统训练漏洞点定位、参数流追踪、调用链分析等代码审计核心技能',
    difficulty: 4,
    type: '系统安全',
    status: 'locked',
    prerequisites: [6, 7],
    estimatedTime: '3-4小时',
    score: calculateScore(4, '3-4小时'), // 75分：难度4×15 + 4小时×5
    image: '/9.代码审计进阶.png'
  },
  {
    id: 11,
    name: 'CTF综合实战',
    description: '通过实战演练最新CTF赛题，全面提升Web渗透、二进制逆向、密码学、隐写分析等多领域安全技能，掌握高效解题思路与自动化工具开发方法',
    difficulty: 5,
    type: 'CTF',
    status: 'locked',
    prerequisites: [1, 2, 3, 4, 5],
    estimatedTime: '5小时',
    score: calculateScore(5, '5小时'), // 100分：难度5×15 + 5小时×5
    image: '/10.CTF攻防实战.png'
  },
  {
    id: 12,
    name: '红队武器库',
    description: '系统学习红队实战武器装备的使用与定制，包括Cobalt Strike高级功能应用、木马免杀技术、社会工程学钓鱼攻击、网络侦查等红队核心战术与技术',
    difficulty: 5,
    type: '网络攻防',
    status: 'locked',
    prerequisites: [9],
    estimatedTime: '4-5小时',
    score: calculateScore(5, '4-5小时'), // 100分：难度5×15 + 5小时×5
    image: '/11.红队武器库.png'
  },
  {
    id: 13,
    name: '漏洞挖掘方法论',
    description: '系统讲解从发现到利用的完整漏洞挖掘流程，包括模糊测试技术应用、静态代码分析方法、动态调试技巧、漏洞验证与利用开发以及CVE申请全过程',
    difficulty: 5,
    type: '系统安全',
    status: 'locked',
    prerequisites: [10],
    estimatedTime: '5小时',
    score: calculateScore(5, '5小时'), // 100分：难度5×15 + 5小时×5
    image: '/12.漏洞挖掘方法论.png'
  },
  {
    id: 14,
    name: '第三方框架漏洞',
    description: '整漏洞挖掘流程，包包括Thinkphp多种典型漏洞利用、Struts2多种典型漏洞利用、Spring框架典型漏洞利用、若依框架典型漏洞利用等实验内容',
    difficulty: 5,
    type: '系统安全',
    status: 'locked',
    prerequisites: [10],
    estimatedTime: '5小时',
    score: calculateScore(5, '5小时'), // 100分：难度5×15 + 5小时×5
    image: '/6.框架漏洞利用.png'
  }

])



onMounted(()=>{
  // getModuleList().then((res)=>{
  //   modules.value = res.data;
  // })
})

// 筛选条件
const filters = ref({
  type: '',
  difficulty: '',
  status: ''
})

// 类型列表 
const types = ['Web安全', '系统安全', '密码学', '网络攻击与防御', '二进制安全']

// 添加搜索关键词
const searchQuery = ref('')

// 更新筛选逻辑
// 更新筛选逻辑
const filteredModules = computed(() => {
  // 首先进行筛选
  const filtered = modules.value.filter(module => {
    // 搜索过滤
    if (searchQuery.value && !module.name.toLowerCase().includes(searchQuery.value.toLowerCase()) &&
        !module.description.toLowerCase().includes(searchQuery.value.toLowerCase())) {
      return false
    }
    // 现有的筛选条件
    if (filters.value.type && module.type !== filters.value.type) return false
    if (filters.value.status && module.status !== filters.value.status) return false
    if (filters.value.difficulty && module.difficulty !== parseInt(filters.value.difficulty)) return false
    return true
  })

  // 然后按照状态排序
  return filtered.sort((a, b) => {
    const statusOrder = {
      'available': 0,  // 可开始 排第一
      'locked': 1,     // 未解锁 排第二
      'completed': 2   // 可进行 排第三
    }
    return statusOrder[a.status] - statusOrder[b.status]
  })
})

// 重置筛选器
const resetFilters = () => {
  filters.value = {
    type: '',
    difficulty: '',
    status: ''
  }
  searchQuery.value = ''
}

// 获取统计信息
const stats = computed(() => ({
  total: modules.value.length,
  completed: modules.value.filter(m => m.status === 'completed').length,
  available: modules.value.filter(m => m.status === 'available').length,
  locked: modules.value.filter(m => m.status === 'locked').length
}))
</script>

<template>
  <div class="container-fluid px-4 py-6 overflow-x-hidden">
    <!-- 统计信息 -->
    <div class="stats shadow w-full mb-6">
      <div class="stat">
        <div class="stat-figure text-primary">
          <i class="fas fa-cube text-3xl"></i>
        </div>
        <div class="stat-title">总实验数</div>
        <div class="stat-value text-primary">{{ stats.total }}</div>
      </div>
      
      <div class="stat">
        <div class="stat-figure text-success">
          <i class="fas fa-check-circle text-3xl"></i>
        </div>
        <div class="stat-title">已完成</div>
        <div class="stat-value text-success">{{ stats.completed }}</div>
      </div>
      
      <div class="stat">
        <div class="stat-figure text-warning">
          <i class="fas fa-unlock text-3xl"></i>
        </div>
        <div class="stat-title">可开始</div>
        <div class="stat-value text-warning">{{ stats.available }}</div>
      </div>
      
      <div class="stat">
        <div class="stat-figure text-error">
          <i class="fas fa-lock text-3xl"></i>
        </div>
        <div class="stat-title">未解锁</div>
        <div class="stat-value text-error">{{ stats.locked }}</div>
      </div>
    </div>
    
    <!-- 筛选器 -->
    <div class="card bg-base-100 shadow-xl mb-6 overflow-hidden">
      <!-- 搜索区域 -->

      <div class="card-body pt-4">

        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <!-- 类型筛选 -->
          <div class="form-control">
            <label class="label cursor-pointer gap-2 pb-2">
              <i class="fas fa-tags text-primary"></i>
              <span class="label-text">类型</span>
            </label>
            <select 
              class="select select-bordered w-full bg-base-100/70 hover:bg-base-100 transition-colors"
              v-model="filters.type"
            >
              <option value="">全部类型</option>
              <option v-for="type in types" :key="type" :value="type">
                {{ type }}
              </option>
            </select>
          </div>
          
          <!-- 难度筛选 -->
          <div class="form-control">
            <label class="label cursor-pointer gap-2 pb-2">
              <i class="fas fa-signal text-primary"></i>
              <span class="label-text">难度</span>
            </label>
            <select 
              class="select select-bordered w-full bg-base-100/70 hover:bg-base-100 transition-colors"
              v-model="filters.difficulty"
            >
              <option value="">全部难度</option>
              <option v-for="n in 5" :key="n" :value="n" class="py-1">
                {{ '★'.repeat(n) }}{{ '☆'.repeat(5-n) }}
              </option>
            </select>
          </div>
          
          <!-- 状态筛选 -->
          <div class="form-control">
            <label class="label cursor-pointer gap-2 pb-2">
              <i class="fas fa-circle-check text-primary"></i>
              <span class="label-text">状态</span>
            </label>
            <select 
              class="select select-bordered w-full bg-base-100/70 hover:bg-base-100 transition-colors"
              v-model="filters.status"
            >
              <option value="">全部状态</option>
              <option value="available" class="text-warning">可开始</option>
              <option value="locked" class="text-error">未解锁</option>
              <option value="completed" class="text-success">已完成</option>
            </select>
          </div>
          <div class="form-control">
            <label class="label cursor-pointer gap-2 pb-2">
              <i class="fas fa-circle-check text-primary"></i>
              <span class="label-text">搜索</span>
            </label>
            <input
              type="text" 
              placeholder="搜索实验名称或描述..." 
              class="input input-bordered w-full pl-11 pr-4 bg-base-100/70 focus:bg-base-100
                     transition-all duration-300 shadow-sm hover:shadow focus:shadow-md"
              v-model="searchQuery"
            > 
          </div>
        </div>
      </div>
    </div>
    
    <!-- 实验列表 -->
    <div v-if="filteredModules.length" 
         class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-fade-in">
      <ModuleOverView 
        v-for="module in filteredModules" 
        :key="module.id" 
        :module="module"
      />
    </div>
    
    <!-- 无结果提示 -->
    <div v-else class="text-center py-12">
      <div class="text-6xl mb-4 text-base-content/30">
        <i class="fas fa-search"></i>
      </div>
      <h3 class="text-xl font-semibold mb-2">未找到匹配的实验</h3>
      <p class="text-base-content/70">
        试试调整筛选条件或重置筛选器
      </p>
      <button 
        class="btn btn-primary btn-sm mt-4"
        @click="resetFilters"
      >
        重置筛选器
      </button>
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

.input-group > span {
  padding: 0 1rem;
  display: flex;
  align-items: center;
  color: var(--color-base-content/50);
}

.animate-fade-in {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 统计卡片动画 */
.stat {
  transition: all 0.3s ease;
}

.stat:hover {
  transform: translateY(-2px);
}

.stat-figure {
  transition: transform 0.3s ease;
}

.stat:hover .stat-figure {
  transform: scale(1.1);
}

/* 搜索框样式 */
.input {
  transition: all 0.3s ease;
}

.input:focus {
  outline: none;
  border-color: var(--color-primary);
}

/* 下拉框样式 */
.select {
  transition: all 0.3s ease;
}

.select:focus {
  outline: none;
  border-color: var(--color-primary);
}

/* 选项悬停效果 */
.select option {
  padding: 0.5rem;
}

.select option:hover {
  background-color: var(--color-primary);
  color: white;
}

/* 卡片内部边框 */
.border-b {
  border-bottom-width: 1px;
  border-color: rgba(var(--color-base-content), 0.1);
}

/* 磨砂玻璃效果 */
.backdrop-blur-sm {
  backdrop-filter: blur(8px);
}
</style>