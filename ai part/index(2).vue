<script setup lang="ts">
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import MarkdownRenderer from "../../../components/MarkdownRenderer.vue";
import type { DisplayQuestionType } from '../../../types/Question';
import { ref, watch, computed, onMounted, onUnmounted } from 'vue';
import type {Experiment} from "../../../types/experiment.ts";
import type { Module } from './index.ts';
import { convertExperimentToModule } from './index.ts';
import axios from 'axios'
import { getModuleDetail, ingestEvents } from '../../../api';
import { findExperimentById } from '../../../data';
import { setLabRunning, clearLab, CONTAINER_NAMES, isLabRunning, getLabSessionId, addLabEvent, getLabEvents, getLabDurationSeconds, currentLabContainer } from '../../../composables/useLabState';
import { useCookie } from '../../../common'

const route = useRoute();
const router = useRouter();
const moduleId = route.params.id;
const isLoading = ref(true);
const cookie = useCookie();

const showEndExperimentModal = ref(false)
const isEndingExperiment = ref(false)

const getUserContext = () => {
  const token = cookie.get('token')
  let userId = 0
  let classId = 0
  try {
    const stored = localStorage.getItem('seclab_accounts')
    if (stored) {
      const accounts = JSON.parse(stored)
      const match = accounts.find((a: any) => a.token === token)
      if (match) {
        userId = match.userId || 0
        classId = match.classId || 0
      }
    }
  } catch (e) {
    console.warn('[getUserContext] 解析用户信息失败:', e)
  }
  return { userId, classId }
}

const buildEventsPayload = () => {
  const { userId, classId } = getUserContext()
  const sessionId = getLabSessionId()
  const events = getLabEvents()
  const durationSeconds = getLabDurationSeconds()
  const containerName = currentLabContainer.value

  const labStopEvent = {
    event_id: `evt-lab-stop-${Date.now()}`,
    request_id: `req-lab-stop-${Date.now()}`,
    event_type: 'LAB_STOP',
    event_time: new Date().toISOString(),
    user_id: userId,
    class_id: classId,
    course_id: 1,
    module_id: experiment.value.id,
    task_id: null,
    question_id: null,
    lab_session_id: sessionId,
    source: 'external-agent',
    container_name: containerName,
    extra: {
      status: 'stopped',
      stop_reason: 'user_ended',
      duration_seconds: durationSeconds,
      completed: flagSubmitStatus.value.isSuccess
    }
  }

  const allEvents = [
    ...events.map(e => ({
      event_id: e.event_id,
      request_id: `req-${e.event_id}`,
      event_type: e.event_type,
      event_time: e.event_time,
      user_id: userId,
      class_id: classId,
      course_id: 1,
      module_id: experiment.value.id,
      task_id: null,
      question_id: null,
      lab_session_id: sessionId,
      source: 'external-agent',
      container_name: containerName,
      ...e
    })),
    labStopEvent
  ]

  return {
    batch_id: `batch-${Date.now()}`,
    source_system: 'external-agent',
    generated_at: new Date().toISOString(),
    user_context: {
      user_id: userId,
      class_id: classId,
      course_id: 1,
      module_id: experiment.value.id,
      task_id: null,
      question_id: null,
      lab_session_id: sessionId
    },
    events: allEvents,
    ai_generated_questions: [],
    profile_rebuild: {
      user_id: userId,
      class_id: classId,
      rebuild_after_ingest: true
    }
  }
}

const sendEventsAndEndLab = async () => {
  isEndingExperiment.value = true
  try {
    const payload = buildEventsPayload()
    console.log('[EndExperiment] 准备发送事件数据:', payload)
    await ingestEvents(payload)
    console.log('[EndExperiment] 事件数据已发送')
  } catch (e) {
    console.error('[EndExperiment] 事件数据发送失败:', e)
  }

  try {
    const containerName = currentLabContainer.value
    if (containerName) {
      const DOCKER_API_URL = import.meta.env.VITE_DOCKER_API_URL || "http://localhost:3000"
      await axios.post(`${DOCKER_API_URL}/api/docker/stop/${containerName}`)
      console.log('[EndExperiment] 容器已停止:', containerName)
    }
  } catch (e) {
    console.error('[EndExperiment] 停止容器失败:', e)
  }

  isTargetMachineRunning.value = false
  targetMachineUrl.value = ''
  clearLab()
  showEndExperimentModal.value = false
  isEndingExperiment.value = false
}

const confirmEndExperiment = () => {
  showEndExperimentModal.value = true
}

const cancelEndExperiment = () => {
  showEndExperimentModal.value = false
}

onBeforeRouteLeave((_to, _from, next) => {
  if (isTargetMachineRunning.value) {
    showEndExperimentModal.value = true
    next(false)
  } else {
    next()
  }
})

const handleBeforeUnload = (e: BeforeUnloadEvent) => {
  if (isTargetMachineRunning.value) {
    e.preventDefault()
  }
}

onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onUnmounted(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
})

// 模拟实验数据 - 保留原有的experiment变量
const experiment = ref<Module>({
  id: 1,
  name: 'SQL注入基础实验',
  introduction: '本实验将帮助你理解SQL注入漏洞的原理和基本利用方法',
  difficulty: 3,
  taskPoints: [
    // ... 默认任务点
  ],
  targetMachine: {
    id: '550e8400-e29b-41d4-a716-446655440000'
  }
});

// 添加答案状态
const answerStatus = ref<{ [key: number]: { [key: number]: boolean | null } }>({})

// 存储答案 - 初始化为空对象
const answers = ref<{ [key: number]: { [key: number]: string | string[] } }>({})

// 添加 flag 提交状态和消息
const flagSubmitStatus = ref<{ 
  isSubmitted: boolean; 
  isSuccess: boolean; 
  message: string;
  taskId: number | null;
  questionId: number | null;
}>({
  isSubmitted: false,
  isSuccess: false,
  message: '',
  taskId: null,
  questionId: null
});

// 清除 flag 提交状态
const clearFlagStatus = () => {
  setTimeout(() => {
    flagSubmitStatus.value = {
      isSubmitted: false,
      isSuccess: false,
      message: '',
      taskId: null,
      questionId: null
    };
  }, 5000); // 5秒后自动清除状态
};

onMounted(async () => {
  try {
    // 如果没有提供模块ID，重定向到模块列表页面
    if (!moduleId) {
      console.log('未提供模块ID，重定向到模块列表');
      router.push('/user/modules');
      return;
    }
    
    // 尝试加载模块数据
    const id = Number(moduleId);
    console.log('当前请求的模块ID:', id, '类型:', typeof id);
    if (isNaN(id)) {
      console.error('无效的模块ID:', moduleId);
      throw new Error('无效的模块ID');
    }
    
    // 尝试从API获取数据，如果失败则使用本地数据
    try {
      console.log(`尝试从API获取ID为${id}的模块数据`);
      const response = await getModuleDetail(id);
      if (response.isSuccess === 1) {
        experiment.value = response.data as Module;
        console.log(`成功从API加载模块 #${id}: ${experiment.value.name}，实际ID: ${experiment.value.id}`);
      } else {
        console.warn(`API返回错误，尝试使用本地数据`);
        throw new Error('API返回错误');
      }
    } catch (error) {
      // 如果API调用失败，尝试使用本地数据
      console.log(`从本地数据查找ID为${id}的模块`);
      const localModule = findExperimentById(id);
      if (localModule) {
        // 转换为Module类型
        experiment.value = convertExperimentToModule(localModule);
        // 确保ID保持一致，不被覆盖
        const originalId = experiment.value.id;
        experiment.value.id = id;
        console.log(`使用本地数据加载模块 #${id}: ${experiment.value.name}，原始ID: ${originalId}，修正后ID: ${experiment.value.id}`);
      } else {
        console.error(`找不到ID为${id}的模块`);
        throw new Error(`找不到指定ID(${id})的模块`);
      }
    }
    
    // 在数据加载完成后再次确认ID是否正确
    console.log(`最终加载的模块: ID=${experiment.value.id}, 名称=${experiment.value.name}`);
    if (experiment.value.id !== id) {
      console.warn(`警告：模块ID不匹配！请求ID=${id}，实际ID=${experiment.value.id}`);
      experiment.value.id = id; // 强制修正ID
    }
    
    // 初始化答案状态和答案存储对象
    if (experiment.value && experiment.value.taskPoints) {
      experiment.value.taskPoints.forEach((task) => {
        if (!answerStatus.value[task.id]) {
          answerStatus.value[task.id] = {};
        }
        if (!answers.value[task.id]) {
          answers.value[task.id] = {};
        }
        if (task.questions) {
          task.questions.forEach((question) => {
            if (!answerStatus.value[task.id][question.id]) {
              answerStatus.value[task.id][question.id] = null;
            }
            // 初始化答案对象
            if (question.type === 'multiple-choice') {
              answers.value[task.id][question.id] = [];
            } else {
              answers.value[task.id][question.id] = '';
            }
          });
        }
      });
    }
  } catch (error) {
    console.error('加载模块数据失败:', error);
    // 使用内联通知替代alert
    pointsNotification.value = {
      show: true,
      message: '加载模块数据失败，将返回模块列表'
    };
    // 延迟导航，让用户有时间看到通知
    setTimeout(() => {
      router.push('/user/modules');
    }, 2000);
  } finally {
    isLoading.value = false;
  }
});

// 添加状态控制
const showNoVNC = ref(false)
const isOperationMachineRunning = ref(false)
const isTargetMachineRunning = ref(false)

// 添加加载状态
const isTargetLoading = ref(false)

// 添加操作环境加载状态
const isOperationLoading = ref(false)

// 添加环境管理变量
const activeEnvironmentTab = ref<'operation' | 'target' | null>(null);
const targetMachineUrl = ref('')

// 在experiment加载完成后初始化答案状态
watch(experiment, (newExperiment) => {
  if (newExperiment && newExperiment.taskPoints) {
    newExperiment.taskPoints.forEach((x) => {
      if (!answerStatus.value[x.id]) {
  answerStatus.value[x.id] = {}
      }
      if (!answers.value[x.id]) {
        answers.value[x.id] = {}
      }
      if (x.questions) {
  x.questions.forEach((y) => {
          if (!answerStatus.value[x.id][y.id]) {
    answerStatus.value[x.id][y.id] = null
          }
          // 初始化答案对象
          if (y.type === 'multiple-choice') {
            answers.value[x.id][y.id] = [];
          } else if (!answers.value[x.id][y.id]) {
            answers.value[x.id][y.id] = '';
          }
        })
      }
    })
  }
}, { immediate: true })

// 修改启动/关闭操作环境函数
const toggleOperationMachine = async () => {
  if (!isOperationMachineRunning.value) {
    // 启动操作环境
    isOperationLoading.value = true

    // 模拟启动延迟
    await new Promise((resolve) => setTimeout(resolve, 2000))

    isOperationMachineRunning.value = true
    activeEnvironmentTab.value = 'operation'
    isOperationLoading.value = false
  } else {
    // 关闭操作环境
    isOperationMachineRunning.value = false
    if (activeEnvironmentTab.value === 'operation') {
      activeEnvironmentTab.value = isTargetMachineRunning.value ? 'target' : null
    }
  }
}

// 添加URL清理函数，防止URL重复
const cleanUrl = (url: string): string => {
  // 检查URL是否包含重复的域名或路径
  const urlPattern = /(https?:\/\/[^\/]+)(\/.*)?/;
  const match = url.match(urlPattern);
  
  if (match) {
    const domain = match[1]; // 例如 http://localhost:8095
    let path = match[2] || ''; // 例如 /index.html 或 /http://localhost:8095/index.html
    
    // 检查路径中是否包含域名
    if (path.includes(domain)) {
      // 从路径中移除重复的域名
      path = path.replace(domain, '');
      console.log(`检测到URL重复，已清理: ${url} -> ${domain}${path}`);
      return `${domain}${path}`;
    }
  }
  
  return url;
};

// 修改启动靶机函数
const startTargetMachine = async () => {
  if (isTargetLoading.value) return; // 防止重复点击
  isTargetLoading.value = true;
  const minLoadingTime = 3000; // 最少显示3秒
  const startTime = Date.now();

  let url: string | null = null;
  try {
    // 根据模块ID确定正确的API端点
    let apiEndpoint = '/api/docker/start-sqli';
    
    // 获取当前模块的基础ID（对于101-104等变体，获取其基础类型）
    const currentId = experiment.value.id;
    console.log(`启动靶机前，当前模块ID: ${currentId}`);
    
    // 强制检查ID是否与URL参数一致
    const urlId = Number(route.params.id);
    if (currentId !== urlId) {
      console.warn(`警告：模块ID与URL不一致！URL ID=${urlId}, 当前ID=${currentId}`);
      // 如果不一致，使用URL中的ID
      experiment.value.id = urlId;
    }
    
    // 计算基础ID：对于大于100的ID，提取第一位作为基础类型
    const baseId = currentId >= 100 ? Math.floor(currentId / 100) : currentId;
    console.log(`计算得到基础ID: ${baseId}`);
                  
    // 根据基础ID选择正确的API端点
    switch(baseId) {
      case 1: // SQL注入
        apiEndpoint = '/api/docker/start-sqli';
        break;
      case 2: // XSS
        apiEndpoint = '/api/docker/start-xss';
        break;
      case 3: // CSRF
        apiEndpoint = '/api/docker/start-csrf';
        break;
      case 4: // 命令注入
        apiEndpoint = '/api/docker/start-cmd';
        break;
      case 5: // 文件上传
        apiEndpoint = '/api/docker/start-upload';
        break;
      case 6: // 目录遍历
        apiEndpoint = '/api/docker/start-dir';
        break;
      default:
        console.log(`未知的基础ID ${baseId}，默认使用SQL注入靶机`);
        apiEndpoint = '/api/docker/start-sqli';
    }
    
    console.log(`启动靶机，模块ID: ${currentId}, 基础ID: ${baseId}, 使用API: ${apiEndpoint}`);
    
    // 导入Docker API URL
    const DOCKER_API_URL = import.meta.env.VITE_DOCKER_API_URL || "http://localhost:3000";
    
    // 尝试调用API启动靶机
    async function fetchData(retryCount = 0) {
      try {
        const res = await axios.post(`${DOCKER_API_URL}${apiEndpoint}`);
        console.log('API response:', res.data);
        
        if (res.data && res.data.data && res.data.data.url) {
          // 获取API返回的URL
          let apiUrl = res.data.data.url;
          
          // 清理可能的URL重复问题
          apiUrl = cleanUrl(apiUrl);
          
          // 对于目录遍历漏洞实验，使用index.php作为入口
          if (baseId === 6) { // 目录遍历
            if (apiUrl.endsWith('/')) {
              apiUrl += 'index.php';
            } else if (apiUrl.endsWith('index.html')) {
              apiUrl = apiUrl.replace('index.html', 'index.php');
            } else if (!apiUrl.endsWith('.php')) {
              apiUrl += '/index.php';
            }
          }
          // 对于SQL注入漏洞实验，使用index.php作为入口
          else if (baseId === 1) { // SQL注入
            if (apiUrl.endsWith('/')) {
              apiUrl += 'index.php';
            } else if (apiUrl.endsWith('index.html')) {
              apiUrl = apiUrl.replace('index.html', 'index.php');
            } else if (!apiUrl.endsWith('.php')) {
              apiUrl += '/index.php';
            }
          }
          // 对于XSS漏洞实验，使用index.php作为入口
          else if (baseId === 2) { // XSS
            if (apiUrl.endsWith('/')) {
              apiUrl += 'index.php';
            } else if (apiUrl.endsWith('index.html')) {
              apiUrl = apiUrl.replace('index.html', 'index.php');
            } else if (!apiUrl.endsWith('.php')) {
              apiUrl += '/index.php';
            }
          }
          // 对于CSRF漏洞实验，使用index.php作为入口
          else if (baseId === 3) { // CSRF
            if (apiUrl.endsWith('/')) {
              apiUrl += 'index.php';
            } else if (apiUrl.endsWith('index.html')) {
              apiUrl = apiUrl.replace('index.html', 'index.php');
            } else if (!apiUrl.endsWith('.php')) {
              apiUrl += '/index.php';
            }
          }
          // 对于命令注入漏洞实验，使用index.php作为入口
          else if (baseId === 4) { // 命令注入
            if (apiUrl.endsWith('/')) {
              apiUrl += 'index.php';
            } else if (apiUrl.endsWith('index.html')) {
              apiUrl = apiUrl.replace('index.html', 'index.php');
            } else if (!apiUrl.endsWith('.php')) {
              apiUrl += '/index.php';
            }
          }
          // 对于文件上传漏洞实验，使用index.php作为入口
          else if (baseId === 5) { // 文件上传
            if (apiUrl.endsWith('/')) {
              apiUrl += 'index.php';
            } else if (apiUrl.endsWith('index.html')) {
              apiUrl = apiUrl.replace('index.html', 'index.php');
            } else if (!apiUrl.endsWith('.php')) {
              apiUrl += '/index.php';
            }
          }
          // 其他实验默认使用index.html
          else {
            if (apiUrl.endsWith('/')) {
              apiUrl += 'index.html';
            } else if (!apiUrl.endsWith('.html') && !apiUrl.endsWith('.php')) {
              apiUrl += '/index.html';
            }
          }
          
          // 再次清理URL，确保没有重复
          apiUrl = cleanUrl(apiUrl);
          console.log('处理后的URL:', apiUrl);
          return apiUrl;
        } else {
          console.log('API response not as expected:', res.data);
          throw new Error('Invalid API response');
        }
      } catch (error) {
        console.log(`API request failed (attempt ${retryCount + 1}/3):`, error);
        if (retryCount < 2) {
          // 重试最多3次
          await new Promise(resolve => setTimeout(resolve, 1000));
          return fetchData(retryCount + 1);
        } else {
          console.log('Falling back to hardcoded data after max retries');
          // 所有重试失败后使用硬编码的URL
          let fallbackUrl = '';
          switch(baseId) {
            case 1: // SQL注入
              fallbackUrl = 'http://localhost:8091/index.php';
              break;
            case 2: // XSS
              fallbackUrl = 'http://localhost:8092/index.php';
              break;
            case 3: // CSRF
              fallbackUrl = 'http://localhost:8093/index.php';
              break;
            case 4: // 命令注入
              fallbackUrl = 'http://localhost:8090/index.php';
              break;
            case 5: // 文件上传
              fallbackUrl = 'http://localhost:8094/index.php';
              break;
            case 6: // 目录遍历
              fallbackUrl = 'http://localhost:8095/index.php';
              break;
            default:
              fallbackUrl = 'http://localhost:8091/index.php';
          }
          return cleanUrl(fallbackUrl);
        }
      }
    }
    
    // 尝试获取URL，失败后使用默认值
    url = await fetchData();
  } catch (e) {
    // 如果API调用失败，使用默认URL
    const defaultUrl = 'http://localhost:8091/index.php';
    url = cleanUrl(defaultUrl);
    console.error('启动靶机失败，使用默认URL:', e);
  } finally {
    const elapsed = Date.now() - startTime;
    const finishLoading = () => {
      // 确保URL没有重复问题
      targetMachineUrl.value = url as string;
      isTargetMachineRunning.value = true;
      isTargetLoading.value = false;
      // 设置活动环境标签为靶机
      activeEnvironmentTab.value = 'target';
      
      // 确保iframe可见
      showNoVNC.value = true;

      // 打印调试信息
      console.log('靶机启动成功，URL:', targetMachineUrl.value);
      console.log('当前活动标签:', activeEnvironmentTab.value);

      // ── 通知 Agent 悬浮窗：靶机已启动 ──────────────────────
      const labId = Number(baseId) || 1
      const containerName = CONTAINER_NAMES[labId] || 'sqli-lab-web-1'
      setLabRunning(containerName)
      console.log('[AgentState] 靶机容器:', containerName);
    };
    if (elapsed < minLoadingTime) {
      setTimeout(finishLoading, minLoadingTime - elapsed);
    } else {
      finishLoading();
    }
  }
};

// 关闭靶机环境 → 改为结束实验
const closeTargetMachine = () => {
  if (isTargetMachineRunning.value) {
    confirmEndExperiment()
    return
  }
  isTargetMachineRunning.value = false
  targetMachineUrl.value = ''
  clearLab()
}

// 获取难度星级显示
const getDifficultyStars = (difficulty: number) => '★'.repeat(difficulty) + '☆'.repeat(5 - difficulty)

// 检查答案
const checkAnswer = (taskId: number, questionId: number) => {
  console.log('检查答案:', questionId, answers.value[taskId]?.[questionId])
  // 确保对象存在
  if (!answers.value[taskId]) {
    answers.value[taskId] = {};
  }
  if (!answers.value[taskId][questionId]) {
    if (experiment.value.taskPoints.find(t => t.id === taskId)?.questions.find(q => q.id === questionId)?.type === 'multiple-choice') {
      answers.value[taskId][questionId] = [];
    } else {
      answers.value[taskId][questionId] = '';
    }
  }
  
  // 模拟答案检查 - 这里应该替换为实际的答案检查逻辑
  const userAnswer = answers.value[taskId][questionId];
  const isCorrect = true; // 这里应该是实际的答案检查逻辑
  
  // 更新答案状态
  answerStatus.value[taskId][questionId] = isCorrect;
  
  // 更新 flag 提交状态
  flagSubmitStatus.value = {
    isSubmitted: true,
    isSuccess: isCorrect,
    message: isCorrect ? '恭喜！答案正确！' : '答案错误，请重试。',
    taskId: taskId,
    questionId: questionId
  };

  addLabEvent({
    event_type: 'FLAG_SUBMIT',
    container_name: currentLabContainer.value,
    flag_text: typeof userAnswer === 'string' ? userAnswer : JSON.stringify(userAnswer),
    is_correct: isCorrect,
    score: isCorrect ? (experiment.value.taskPoints.find(t => t.id === taskId)?.score || 0) : 0,
    extra: { task_id: taskId, question_id: questionId }
  })
  
  // 5秒后清除状态
  clearFlagStatus();
}

// 提交答案
const submitAnswer = (taskId: number, questionId: number) => {
  console.log('提交答案:', questionId, answers.value[taskId]?.[questionId])
  
  // 确保对象存在
  if (!answers.value[taskId]) {
    answers.value[taskId] = {};
  }
  
  // 更新 flag 提交状态
  flagSubmitStatus.value = {
    isSubmitted: true,
    isSuccess: true,
    message: '答案已提交成功！',
    taskId: taskId,
    questionId: questionId
  };
  
  // 5秒后清除状态
  clearFlagStatus();
}

// 修改计算积分的方法
const calculatePoints = computed(() => {
  // 难度基础分：每星30分（5星最高150分）
  const difficultyPoints = experiment.value.difficulty * 30

  // 时间加成：每小时10分（最长5小时，最高50分）
  const totalHours = experiment.value.taskPoints.reduce((total, task) => {
    return total + task.score / 10 // 假设每10分的任务需要1小时
  }, 0)
  // 限制最大计算时长为5小时
  const timePoints = Math.min(Math.round(totalHours * 10), 50)

  // 总分 = 难度分 + 时间分（自然限制在200分以内）
  return difficultyPoints + timePoints
})

// 添加页面状态控制，用于切换做题和题解讨论页面
const currentTab = ref('practice') // 'practice'或'discussion'

// 添加iframe显示控制
const isIframeVisible = computed(() => isOperationMachineRunning.value || isTargetMachineRunning.value)

// 计算查看题解所需积分
const getSolutionCost = (difficulty: number) => {
  const costs = {
    1: 40, // 1星40分
    2: 80, // 2星80分
    3: 140, // 3星140分
    4: 180, // 4星180分
    5: 250 // 5星250分
  }
  return costs[difficulty as keyof typeof costs]
}

// 显示积分确认弹窗
const showCostModal = ref(false)
const solutionCost = computed(() => getSolutionCost(experiment.value.difficulty))

// 模拟用户积分余额
const userPoints = ref(5000)

// 添加已付费查看标记
const hasViewedDiscussion = ref(false)

// 添加积分不足通知状态
const pointsNotification = ref({
  show: false,
  message: ''
});

// 清除积分通知
const clearPointsNotification = () => {
  setTimeout(() => {
    pointsNotification.value.show = false;
  }, 5000); // 5秒后自动清除
};

// 查看题解讨论
const viewDiscussion = () => {
  if (!hasViewedDiscussion.value) {
    // 首次查看需要支付积分
    if (userPoints.value < solutionCost.value) {
      // 使用内联通知替代alert
      pointsNotification.value = {
        show: true,
        message: `积分不足，需要${solutionCost.value}积分才能查看题解`
      };
      clearPointsNotification();
      return
    }

    // 显示确认对话框
    showCostModal.value = true
  } else {
    // 已经查看过，直接切换到讨论页面，不扣除积分
    currentTab.value = 'discussion'
  }
}

// 确认查看题解
const confirmViewDiscussion = () => {
  // 如果已查看过，不再扣费
  if (!hasViewedDiscussion.value) {
    userPoints.value -= solutionCost.value
    hasViewedDiscussion.value = true
  }
  
  // 关闭确认弹窗，切换到讨论页面
  showCostModal.value = false
  currentTab.value = 'discussion'
}

// 模拟讨论数据
const discussions = ref([
  {
    id: 1,
    author: {
      name: '安全专家',
      avatar: '/student11.png'
    },
    content: '这个实验主要考察了SQL注入的基本原理和防御技术，关键在于理解参数化查询的重要性。',
    createdAt: '2023-10-15 14:30',
    likes: 12
  },
  {
    id: 2,
    author: {
      name: '学习者',
      avatar: '/student12.png'
    },
    content: '我在做第三个任务点时遇到了一些困难，特别是构造UNION SELECT语句时。后来发现需要先确定表的列数，才能成功注入。',
    createdAt: '2023-10-16 09:15',
    likes: 8
  }
])

// 在新窗口打开环境
const openInNewWindow = (type: 'operation' | 'target') => {
  if (type === 'operation') {
    window.open('http://127.0.0.1:8443', '_blank');
  } else if (type === 'target' && targetMachineUrl.value) {
    // 确保URL有效
    if (targetMachineUrl.value) {
      console.log('在新窗口打开靶机:', targetMachineUrl.value);
      window.open(targetMachineUrl.value, '_blank');
    } else {
      console.error('靶机URL无效，无法在新窗口打开');
    }
  }
}

// 添加环境标签页的自动切换监听
watch([isOperationMachineRunning, isTargetMachineRunning], ([newOpRunning, newTargetRunning]) => {
  // 如果操作环境刚刚启动，并且没有活动的标签或靶机已关闭
  if (newOpRunning && (!activeEnvironmentTab.value || activeEnvironmentTab.value === 'target' && !newTargetRunning)) {
    activeEnvironmentTab.value = 'operation';
  }
  // 如果靶机刚刚启动，并且没有活动的标签或操作环境已关闭
  else if (newTargetRunning && (!activeEnvironmentTab.value || activeEnvironmentTab.value === 'operation' && !newOpRunning)) {
    activeEnvironmentTab.value = 'target';
  }
  // 如果两个环境都关闭了
  else if (!newOpRunning && !newTargetRunning) {
    activeEnvironmentTab.value = null;
  }
});

// 添加刷新iframe方法
const refreshIframe = () => {
  const iframe = document.querySelector('.target-iframe') as HTMLIFrameElement;
  if (iframe) {
    console.log('刷新iframe:', targetMachineUrl.value);
    iframe.src = targetMachineUrl.value;
  }
};

// 添加直接导航方法
const openDirectUrl = () => {
  if (targetMachineUrl.value) {
    console.log('直接导航到:', targetMachineUrl.value);
    window.open(targetMachineUrl.value, '_blank');
  }
};

// 添加复制到剪贴板功能
const copyToClipboard = (text: string) => {
  navigator.clipboard.writeText(text)
    .then(() => {
      console.log('URL已复制到剪贴板:', text);
      // 使用内联通知替代alert
      pointsNotification.value = {
        show: true,
        message: 'URL已复制到剪贴板'
      };
      // 5秒后自动清除通知
      setTimeout(() => {
        pointsNotification.value.show = false;
      }, 5000);
    })
    .catch(err => {
      console.error('复制失败:', err);
      // 使用内联通知替代alert
      pointsNotification.value = {
        show: true,
        message: '复制失败'
      };
      // 5秒后自动清除通知
      setTimeout(() => {
        pointsNotification.value.show = false;
      }, 5000);
    });
};
</script>

<template>
  <div class="container-fluid">
    <!-- 加载状态 -->
    <div v-if="isLoading" class="flex justify-center items-center h-screen">
      <div class="text-center">
        <div class="loading loading-spinner loading-lg"></div>
        <p class="mt-4">加载模块数据中...</p>
      </div>
    </div>
    
    <!-- 错误状态 -->
    <div v-else-if="!experiment" class="flex justify-center items-center h-screen">
      <div class="text-center">
        <div class="text-error text-5xl mb-4">
          <i class="fas fa-exclamation-circle"></i>
        </div>
        <p class="text-xl">无法加载模块数据</p>
        <button @click="router.push('/user/modules')" class="btn btn-primary mt-4">
          返回模块列表
        </button>
      </div>
    </div>
    
    <!-- 模块内容 -->
    <div v-else class="container-fluid px-4 py-6 overflow-x-hidden h-screen flex flex-col">
      <!-- 积分不足通知 -->
      <div v-if="pointsNotification.show" 
           class="alert alert-warning fixed top-4 right-4 z-50 shadow-lg animate-fade-in-down max-w-md">
        <div class="flex items-center">
          <i class="fas fa-coins mr-2"></i>
          <span>{{ pointsNotification.message }}</span>
          <button @click="pointsNotification.show = false" class="btn btn-sm btn-ghost ml-auto">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>
      
      <!-- 返回按钮 -->
      <div class="mb-4 animate-slide-down">
        <button @click="router.go(-1)" class="btn btn-sm btn-ghost gap-2 hover:bg-base-200">
          <i class="fas fa-arrow-left"></i>
          <span>返回</span>
        </button>
      </div>
      
      <div class="flex">
        <!-- 左侧内容区域 -->
        <div class="flex flex-col" :class="{ 'w-half': isIframeVisible, 'w-full': !isIframeVisible }">
          <!-- 导航栏 -->
          <div class="bg-base-100 border-b border-base-300">
            <div class="flex items-center gap-6 px-6 py-3">
              <div class="flex items-center gap-2 cursor-pointer" :class="currentTab === 'practice' ? 'text-primary font-semibold' : 'hover:text-primary transition-colors'" @click="currentTab = 'practice'">
                <i class="fas fa-code"></i>
                <span>做题</span>
              </div>
              <div class="flex items-center gap-2 cursor-pointer" :class="currentTab === 'discussion' ? 'text-primary font-semibold' : 'hover:text-primary transition-colors'" @click="viewDiscussion()">
                <i class="fas fa-comments"></i>
                <span>题解讨论</span>
                <span v-if="!hasViewedDiscussion" class="badge badge-xs badge-primary ml-1"> {{ solutionCost }}分 </span>
              </div>
            </div>
          </div>

          <!-- 做题页面 -->
          <div v-if="currentTab === 'practice'" class="flex-1 flex flex-col">
            <!-- 顶部区域 -->
            <div class="bg-base-200 p-4 shadow-lg space-y-4 animate-slide-down">
              <!-- 标题和难度行 -->
              <div class="flex justify-between items-center">
                <div class="flex items-center gap-2">
                  <i class="fas fa-flask text-primary text-2xl"></i>
                  <h1 class="text-2xl font-bold">
                    <span class="text-sm font-mono opacity-70 mr-2">#{{ experiment.id }}</span>
                    {{ experiment.name }}
                  </h1>
                </div>
                <div class="flex items-center gap-4">
                  <!-- 添加积分显示 -->
                  <div class="flex items-center gap-2 text-secondary">
                    <i class="fas fa-coins"></i>
                    <span class="font-semibold">{{ calculatePoints }}积分</span>
                  </div>
                  <!-- 原有的难度显示 -->
                  <div class="text-yellow-500">
                    <i class="fas fa-star mr-2"></i>
                    难度: {{ getDifficultyStars(experiment.difficulty) }}
                  </div>
                </div>
              </div>

              <!-- 环境控制行 -->
              <div class="flex environment-controls justify-between flex-col gap-4">
                <!-- 靶机控制 -->
                <div class="flex items-center gap-4">
                  <i class="fas fa-server text-info"></i>
                  <span>靶机环境</span>
                  <span class="badge badge-sm" :class="isTargetLoading ? 'badge-info' : isTargetMachineRunning ? 'badge-success' : 'badge-warning'">
                    {{ isTargetLoading ? '启动中' : isTargetMachineRunning ? '运行中' : '未启动' }}
                  </span>
                  <button
                    id="start-target-btn"
                    class="btn btn-sm"
                    :class="isTargetMachineRunning ? 'btn-error' : 'btn-primary'"
                    @click="isTargetMachineRunning ? closeTargetMachine() : startTargetMachine()"
                    :disabled="isTargetLoading"
                  >
                    <span class="loading loading-spinner loading-xs" v-if="isTargetLoading"></span>
                    <i :class="isTargetMachineRunning ? 'fas fa-stop' : 'fas fa-play'" class="mr-1" v-else></i>
                    {{ isTargetLoading ? '正在启动靶机...' : isTargetMachineRunning ? '结束实验' : '开始挑战' }}
                  </button>
                  <div v-if="isTargetLoading" class="text-sm text-info">靶机环境正在准备中，请稍候...</div>
                  <div v-else-if="isTargetMachineRunning" class="text-sm text-success">
                    靶机已启动，可以在右侧查看
                    <button 
                      class="btn btn-xs btn-ghost text-primary" 
                      @click="activeEnvironmentTab = 'target'"
                    >
                      <i class="fas fa-arrow-right"></i> 切换到靶机
                    </button>
                  </div>
                </div>

                <!-- 靶机URL显示和复制 -->
                <div v-if="isTargetMachineRunning && targetMachineUrl" class="flex items-center gap-2 bg-base-200 p-2 rounded">
                  <span class="text-sm font-semibold">靶机URL:</span>
                  <div class="bg-base-300 px-2 py-1 rounded text-sm font-mono flex-grow">
                    {{ targetMachineUrl }}
                  </div>
                  <button 
                    class="btn btn-xs btn-ghost" 
                    @click="copyToClipboard(targetMachineUrl)"
                    title="复制URL"
                  >
                    <i class="fas fa-copy"></i>
                  </button>
                  <button 
                    class="btn btn-xs btn-ghost" 
                    @click="openDirectUrl"
                    title="直接导航"
                  >
                    <i class="fas fa-external-link-alt"></i>
                  </button>
                </div>

                <!-- 操作环境控制 -->
                <div class="flex items-center gap-4">
                  <i class="fas fa-desktop text-info"></i>
                  <span>操作环境</span>
                  <span class="badge badge-sm" :class="isOperationLoading ? 'badge-info' : isOperationMachineRunning ? 'badge-success' : 'badge-warning'">
                    {{ isOperationLoading ? '启动中' : isOperationMachineRunning ? '运行中' : '未启动' }}
                  </span>
                  <button 
                    class="btn btn-sm" 
                    :class="isOperationMachineRunning ? 'btn-error' : 'btn-primary'" 
                    @click="toggleOperationMachine" 
                    :disabled="isOperationLoading"
                  >
                    <span class="loading loading-spinner loading-xs" v-if="isOperationLoading"></span>
                    <i :class="isOperationMachineRunning ? 'fas fa-stop' : 'fas fa-play'" class="mr-1" v-else></i>
                    {{ isOperationLoading ? '正在启动...' : isOperationMachineRunning ? '关闭操作环境' : '启动操作环境' }}
                  </button>
                  <div v-if="isOperationLoading" class="text-sm text-info">操作环境正在准备中，请稍候...</div>
                </div>
              </div>
            </div>

            <!-- 主要内容区域 -->
            <div class="transition-all duration-300 p-4 overflow-y-auto flex-1 w-full">
              <!-- 实验介绍 -->
              <div class="card bg-base-100 shadow-xl mb-6 animate-slide-up">
                <div class="card-body">
                  <h2 class="text-xl font-semibold mb-2">
                    <i class="fas fa-info-circle text-primary mr-2"></i>
                    实验介绍
                  </h2>
                  <p>{{ experiment.introduction }}</p>
                </div>
              </div>

              <!-- 任务点列表 -->
              <div class="card bg-base-100 shadow-xl animate-slide-up">
                <div class="card-body">
                  <h2 class="text-xl font-semibold mb-4">
                    <i class="fas fa-tasks text-primary mr-2"></i>
                    任务点
                  </h2>
                  <div class="space-y-4">
                    <div v-for="task in experiment.taskPoints" :key="task.id" class="collapse collapse-arrow border-base-300 bg-base-200 border">
                      <input type="checkbox" />
                      <div class="collapse-title text-xl font-semibold flex items-center gap-2">
                        <i class="fas fa-tasks"></i>
                        {{ task.name }}
                        <div class="badge badge-primary badge-lg">
                          <span class="font-bold">{{ task.score }}</span>分
                        </div>
                      </div>
                      <div class="collapse-content">
                        <p>{{ task.description }}</p>

                        <!-- 添加Markdown文档渲染 -->
                        <div class="mt-4">
                          <h4 class="font-semibold mb-2">任务说明</h4>
                          <div class="card bg-base-100 p-4 w-full max-w-full overflow-x-auto">
                            <div class="w-full prose prose-sm max-w-none break-words">
                              <div class="markdown-content">
                                <MarkdownRenderer :content="task.document" />
                              </div>
                            </div>
                          </div>
                        </div>

                        <!-- 任务问题列表 -->
                        <div class="mt-4 space-y-2">
                          <div v-for="question in task.questions" :key="question.id" class="card bg-base-300">
                            <div class="card-body">
                              <div class="flex justify-between items-center">
                                <p>{{ question.content }}</p>
                                <span class="badge">{{ question.score }}分</span>
                              </div>
                              <div class="mt-2">
                                <!-- 带答案的开放题 -->
                                <div v-if="question.type === 'open-ended-with-answer'" class="space-y-2">
                                  <textarea v-model="answers[task.id][question.id]" placeholder="请输入答案" class="textarea textarea-bordered w-full h-24" />
                                  <div class="flex items-center gap-2">
                                    <button @click="checkAnswer(task.id, question.id)" class="btn btn-primary">检查答案</button>
                                    <span v-if="answerStatus[task.id][question.id] !== null" :class="answerStatus[task.id][question.id] ? 'text-success' : 'text-error'" class="flex items-center">
                                      <i :class="answerStatus[task.id][question.id] ? 'fa-check' : 'fa-times'" class="fas mr-1"></i>
                                      {{ answerStatus[task.id][question.id] ? '答案正确' : '答案错误' }}
                                    </span>
                                  </div>
                                  
                                  <!-- Flag 提交结果显示 -->
                                  <div v-if="flagSubmitStatus.isSubmitted && flagSubmitStatus.taskId === task.id && flagSubmitStatus.questionId === question.id" 
                                      :class="flagSubmitStatus.isSuccess ? 'alert alert-success' : 'alert alert-error'"
                                      class="mt-2 animate-fade-in">
                                    <div class="flex items-center">
                                      <i :class="flagSubmitStatus.isSuccess ? 'fa-check-circle' : 'fa-times-circle'" class="fas mr-2"></i>
                                      <span>{{ flagSubmitStatus.message }}</span>
                                    </div>
                                  </div>
                                </div>

                                <!-- 无答案的开放题 -->
                                <div v-else-if="question.type === 'open-ended-without-answer'" class="space-y-2">
                                  <textarea v-model="answers[task.id][question.id]" placeholder="请输入答案" class="textarea textarea-bordered w-full h-24" />
                                  <button @click="submitAnswer(task.id, question.id)" class="btn btn-primary">提交答案</button>
                                  
                                  <!-- Flag 提交结果显示 -->
                                  <div v-if="flagSubmitStatus.isSubmitted && flagSubmitStatus.taskId === task.id && flagSubmitStatus.questionId === question.id" 
                                      class="alert alert-success mt-2 animate-fade-in">
                                    <div class="flex items-center">
                                      <i class="fas fa-check-circle mr-2"></i>
                                      <span>{{ flagSubmitStatus.message }}</span>
                                    </div>
                                  </div>
                                </div>

                                <!-- 单选题 -->
                                <div v-else-if="question.type === 'single-choice'" class="space-y-2">
                                  <div v-for="(option, index) in question.options" :key="index" class="flex items-center gap-2">
                                    <input type="radio" v-model="answers[task.id][question.id]" :name="'q' + question.id" :value="option" class="radio radio-primary" />
                                    <span>{{ option }}</span>
                                  </div>
                                  <div class="flex items-center gap-2 mt-2">
                                    <button @click="checkAnswer(task.id, question.id)" class="btn btn-primary">检查答案</button>
                                    <span v-if="answerStatus[task.id][question.id] !== null" :class="answerStatus[task.id][question.id] ? 'text-success' : 'text-error'" class="flex items-center">
                                      <i :class="answerStatus[task.id][question.id] ? 'fa-check' : 'fa-times'" class="fas mr-1"></i>
                                      {{ answerStatus[task.id][question.id] ? '答案正确' : '答案错误' }}
                                    </span>
                                  </div>
                                  
                                  <!-- Flag 提交结果显示 -->
                                  <div v-if="flagSubmitStatus.isSubmitted && flagSubmitStatus.taskId === task.id && flagSubmitStatus.questionId === question.id" 
                                      :class="flagSubmitStatus.isSuccess ? 'alert alert-success' : 'alert alert-error'"
                                      class="mt-2 animate-fade-in">
                                    <div class="flex items-center">
                                      <i :class="flagSubmitStatus.isSuccess ? 'fa-check-circle' : 'fa-times-circle'" class="fas mr-2"></i>
                                      <span>{{ flagSubmitStatus.message }}</span>
                                    </div>
                                  </div>
                                </div>

                                <!-- 多选题 -->
                                <div v-else-if="question.type === 'multiple-choice'" class="space-y-2">
                                  <div v-for="(option, index) in question.options" :key="index" class="flex items-center gap-2">
                                    <input type="checkbox" v-model="answers[task.id][question.id]" :value="option" class="checkbox checkbox-primary" />
                                    <span>{{ option }}</span>
                                  </div>
                                  <div class="flex items-center gap-2 mt-2">
                                    <button @click="checkAnswer(task.id, question.id)" class="btn btn-primary">检查答案</button>
                                    <span v-if="answerStatus[task.id][question.id] !== null" :class="answerStatus[task.id][question.id] ? 'text-success' : 'text-error'" class="flex items-center">
                                      <i :class="answerStatus[task.id][question.id] ? 'fa-check' : 'fa-times'" class="fas mr-1"></i>
                                      {{ answerStatus[task.id][question.id] ? '答案正确' : '答案错误' }}
                                    </span>
                                  </div>
                                  
                                  <!-- Flag 提交结果显示 -->
                                  <div v-if="flagSubmitStatus.isSubmitted && flagSubmitStatus.taskId === task.id && flagSubmitStatus.questionId === question.id" 
                                      :class="flagSubmitStatus.isSuccess ? 'alert alert-success' : 'alert alert-error'"
                                      class="mt-2 animate-fade-in">
                                    <div class="flex items-center">
                                      <i :class="flagSubmitStatus.isSuccess ? 'fa-check-circle' : 'fa-times-circle'" class="fas mr-2"></i>
                                      <span>{{ flagSubmitStatus.message }}</span>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 题解讨论页面 -->
          <div v-if="currentTab === 'discussion'" class="flex-1 flex flex-col relative min-h-[70vh]">
            <!-- 题解讨论内容 -->
            <div class="p-4 overflow-y-auto">
              <h2 class="text-xl font-semibold mb-4">题解与讨论</h2>
              <div class="discussion-list space-y-4">
                <div v-for="discussion in discussions" :key="discussion.id" class="card bg-base-100 shadow-md">
                  <div class="card-body p-4">
                    <div class="flex items-start gap-3">
                      <div class="avatar">
                        <div class="w-12 h-12 rounded-full">
                          <img :src="discussion.author.avatar" alt="avatar" />
                        </div>
                      </div>
                      <div class="flex-1">
                        <div class="flex justify-between items-center mb-2">
                          <h3 class="font-semibold">{{ discussion.author.name }}</h3>
                          <span class="text-xs text-base-content/60">{{ discussion.createdAt }}</span>
                        </div>
                        <p class="text-sm mb-3">{{ discussion.content }}</p>
                        <div class="flex items-center justify-end">
                          <button class="btn btn-sm btn-ghost gap-1">
                            <i class="fas fa-thumbs-up"></i>
                            <span>{{ discussion.likes }}</span>
                          </button>
                          <button class="btn btn-sm btn-ghost">
                            <i class="fas fa-reply"></i>
                            <span>回复</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 讨论输入框 -->
            <div class="discussion-input-fixed">
              <div class="discussion-input-container">
                <textarea 
                  class="textarea textarea-bordered w-full h-24" 
                  placeholder="分享你的解题思路和心得..."
                ></textarea>
                <div class="flex justify-end mt-3">
                  <button class="btn btn-primary">发表题解</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- iframe部分 -->
        <div v-if="isIframeVisible" class="w-half h-full border-l border-base-300 relative">
          <!-- 环境标签页 -->
          <div class="tabs tabs-boxed bg-base-200 p-2 border-b border-base-300">
            <a 
              class="tab flex-1 gap-2" 
              :class="{ 'tab-active': activeEnvironmentTab === 'operation' }"
              @click="isOperationMachineRunning ? activeEnvironmentTab = 'operation' : toggleOperationMachine()"
            >
              <i class="fas fa-desktop"></i>
              操作环境
              <span class="badge badge-xs" :class="isOperationMachineRunning ? 'badge-success' : 'badge-error'"></span>
            </a>
            <a 
              class="tab flex-1 gap-2" 
              :class="{ 'tab-active': activeEnvironmentTab === 'target' }"
              @click="isTargetMachineRunning ? activeEnvironmentTab = 'target' : startTargetMachine()"
            >
              <i class="fas fa-server"></i>
              靶机环境
              <span class="badge badge-xs" :class="isTargetMachineRunning ? 'badge-success' : 'badge-error'"></span>
            </a>
          </div>

          <!-- 新窗口打开按钮 -->
          <button 
            v-if="(activeEnvironmentTab === 'operation' && isOperationMachineRunning) || (activeEnvironmentTab === 'target' && isTargetMachineRunning)"
            class="btn btn-sm btn-circle absolute top-3 right-3 z-10 bg-base-100/80 hover:bg-base-100"
            @click="openInNewWindow(activeEnvironmentTab)"
            title="在新窗口打开"
          >
            <i class="fas fa-external-link-alt"></i>
          </button>

          <!-- 操作环境iframe -->
          <div v-if="activeEnvironmentTab === 'operation'" class="w-full h-[calc(100%-50px)]">
            <div v-if="isOperationMachineRunning" class="w-full h-full">
              <iframe src="http://127.0.0.1:8443" class="w-full h-full border-none"></iframe>
            </div>
            <div v-else class="flex flex-col items-center justify-center h-full p-4 text-center">
              <div class="text-6xl text-base-content/20 mb-4">
                <i class="fas fa-desktop"></i>
              </div>
              <h3 class="text-xl font-semibold mb-2">操作环境未启动</h3>
              <p class="text-base-content/70 mb-4">
                请先启动操作环境
              </p>
              <button class="btn btn-primary btn-sm" @click="toggleOperationMachine" :disabled="isOperationLoading">
                <span class="loading loading-spinner loading-xs" v-if="isOperationLoading"></span>
                <i class="fas fa-play mr-1" v-else></i>
                {{ isOperationLoading ? '正在启动...' : '启动操作环境' }}
              </button>
            </div>
          </div>

          <!-- 靶机环境iframe -->
          <div v-if="activeEnvironmentTab === 'target'" class="w-full h-[calc(100%-50px)]">
            <div v-if="isTargetMachineRunning && targetMachineUrl" class="w-full h-full">
              <!-- 添加调试信息和控制按钮 -->
              <div class="p-2 bg-info/10 text-info flex items-center justify-between">
                <div class="text-xs flex-grow flex items-center gap-2">
                  <span>当前靶机URL:</span>
                  <span class="font-mono">{{ targetMachineUrl }}</span>
                  <button 
                    class="btn btn-xs btn-ghost" 
                    @click="copyToClipboard(targetMachineUrl)"
                    title="复制URL"
                  >
                    <i class="fas fa-copy"></i>
                  </button>
                </div>
                <div class="flex gap-2">
                  <button 
                    class="btn btn-xs btn-ghost" 
                    @click="refreshIframe"
                    title="刷新靶机"
                  >
                    <i class="fas fa-sync-alt"></i>
                  </button>
                  <button 
                    class="btn btn-xs btn-ghost" 
                    @click="openInNewWindow('target')"
                    title="在新窗口打开"
                  >
                    <i class="fas fa-external-link-alt"></i>
                  </button>
                  <button 
                    class="btn btn-xs btn-ghost" 
                    @click="openDirectUrl"
                    title="直接导航"
                  >
                    <i class="fas fa-link"></i>
                  </button>
                </div>
              </div>
              <iframe 
                :src="targetMachineUrl" 
                class="w-full h-[calc(100%-32px)] border-none target-iframe"
                @load="() => console.log('靶机iframe加载完成')"
                @error="(e) => console.error('靶机iframe加载失败', e)"
              ></iframe>
            </div>
            <div v-else class="flex flex-col items-center justify-center h-full p-4 text-center">
              <div class="text-6xl text-base-content/20 mb-4">
                <i class="fas fa-server"></i>
              </div>
              <h3 class="text-xl font-semibold mb-2">靶机环境未启动</h3>
              <p class="text-base-content/70 mb-4">
                请先启动靶机环境
              </p>
              <button class="btn btn-primary btn-sm" @click="startTargetMachine" :disabled="isTargetLoading">
                <span class="loading loading-spinner loading-xs" v-if="isTargetLoading"></span>
                <i class="fas fa-play mr-1" v-else></i>
                {{ isTargetLoading ? '正在启动靶机...' : '启动靶机' }}
              </button>
            </div>
          </div>

          <!-- 未启动任何环境的提示 -->
          <div v-if="!activeEnvironmentTab" class="flex flex-col items-center justify-center h-[calc(100%-50px)] p-4 text-center">
            <div class="text-6xl text-base-content/20 mb-4">
              <i class="fas fa-desktop"></i>
            </div>
            <h3 class="text-xl font-semibold mb-2">未启动任何环境</h3>
            <p class="text-base-content/70 mb-4">
              请先启动操作环境或靶机环境
            </p>
            <div class="flex gap-2">
              <button class="btn btn-primary btn-sm" @click="toggleOperationMachine" :disabled="isOperationLoading">
                <i class="fas fa-play mr-1"></i>
                启动操作环境
              </button>
              <button class="btn btn-primary btn-sm" @click="startTargetMachine" :disabled="isTargetLoading">
                <i class="fas fa-play mr-1"></i>
                启动靶机
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 积分确认弹窗 -->
      <Transition name="modal">
        <dialog :class="{ modal: true, 'modal-open': showCostModal }">
          <div class="modal-box">
            <h3 class="font-bold text-lg">确认查看题解</h3>
            <p class="py-4">
              确认使用 {{ solutionCost }} 积分查看题解讨论吗？
              <span v-if="hasViewedDiscussion" class="text-success"> (您已经支付过，无需再次支付) </span>
            </p>
            <div class="flex justify-between items-center mb-4 border-t border-b py-2 mt-2">
              <span class="font-medium">当前积分余额:</span>
              <span class="text-success font-bold">{{ userPoints }} 积分</span>
            </div>
            <div class="modal-action">
              <button class="btn" @click="showCostModal = false">取消</button>
              <button class="btn btn-primary" @click="confirmViewDiscussion">确认</button>
            </div>
          </div>
        </dialog>
      </Transition>

      <!-- 结束实验确认弹窗 -->
      <Transition name="modal">
        <dialog :class="{ modal: true, 'modal-open': showEndExperimentModal }">
          <div class="modal-box">
            <h3 class="font-bold text-lg">
              <i class="fas fa-exclamation-triangle text-warning mr-2"></i>
              结束实验
            </h3>
            <p class="py-4">
              实验正在进行中，确定要结束实验吗？结束后系统将自动收集实验数据并关闭靶机环境。
            </p>
            <div class="bg-base-200 p-3 rounded-lg mb-4">
              <div class="flex items-center gap-2 text-sm">
                <i class="fas fa-clock text-info"></i>
                <span>实验时长: {{ getLabDurationSeconds() }}秒</span>
              </div>
              <div class="flex items-center gap-2 text-sm mt-1">
                <i class="fas fa-server text-info"></i>
                <span>靶机: {{ currentLabContainer }}</span>
              </div>
            </div>
            <div class="modal-action">
              <button class="btn" @click="cancelEndExperiment" :disabled="isEndingExperiment">继续实验</button>
              <button class="btn btn-error" @click="sendEventsAndEndLab" :disabled="isEndingExperiment">
                <span class="loading loading-spinner loading-xs" v-if="isEndingExperiment"></span>
                <i class="fas fa-stop mr-1" v-else></i>
                {{ isEndingExperiment ? '正在结束...' : '确认结束' }}
              </button>
            </div>
          </div>
        </dialog>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.container-fluid {
  width: 100%;
  max-width: 100%;
  margin: -20px auto;
  overflow-y: auto;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
}

/* 隐藏 Webkit 浏览器的滚动条 */
.container-fluid::-webkit-scrollbar {
  display: none;
}

html,
body {
  overflow-x: hidden;
  margin: 0;
  padding: 0;
  width: 100%;
}

/* 悬浮讨论输入框样式 */
.discussion-input-fixed {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 1rem;
  background-color: var(--color-base-300, #1a1a2e);
  border-top: 2px solid var(--color-primary);
  box-shadow: 0 -4px 6px -1px rgba(0, 0, 0, 0.3);
  z-index: 40;
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.discussion-input-container {
  background-color: var(--color-base-200, #222738);
  padding: 1.25rem;
  border-radius: 0.75rem;
  border: 2px solid var(--color-primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  position: relative;
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
  max-width: 100%;
  margin: 0 auto;
}

.discussion-input-container::before {
  content: '发表你的题解';
  position: absolute;
  top: -12px;
  left: 20px;
  background-color: var(--color-base-300, #1a1a2e);
  padding: 0 10px;
  font-size: 14px;
  font-weight: bold;
  color: var(--color-primary);
}

/* 讨论列表区域样式 */
.discussion-list {
  padding: 1rem;
  border-radius: 0.5rem;
  background-color: var(--color-base-100);
  margin-bottom: 100px; /* 为底部固定输入框留出更多空间 */
}

.animate-float {
  animation: float 10s ease-in-out infinite;
}

.animate-slide-down {
  animation: slideDown 1.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

.animate-slide-up {
  opacity: 0;
  animation: slideUp 1.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(10deg);
  }
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes particleFloat {
  0% {
    transform: translateY(0) translateX(0);
    opacity: 0;
  }
  20% {
    opacity: 1;
  }
  80% {
    opacity: 1;
  }
  100% {
    transform: translateY(-100vh) translateX(50px);
    opacity: 0;
  }
}

/* 页面切换动画 */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.8s cubic-bezier(0.16, 1, 0.3, 1);
  position: absolute;
  width: 100%;
}

.slide-fade-enter-from {
  opacity: 0;
  transform: scale(0.95);
  filter: blur(10px);
}

.slide-fade-leave-to {
  opacity: 0;
  transform: scale(0.95);
  filter: blur(10px);
}

.slide-fade-enter-to,
.slide-fade-leave-from {
  opacity: 1;
  transform: scale(1);
  filter: blur(0);
}

/* 添加内容动画 */
.content-enter-active,
.content-leave-active {
  transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

.content-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.content-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* 添加卡片动画 */
.card {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

/* 添加按钮动画 */
.btn {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

/* 添加讨论列表动画 */
.discussion-list > div {
  opacity: 0;
  animation: slideIn 0.5s ease-out forwards;
}

.discussion-list > div:nth-child(1) {
  animation-delay: 0.1s;
}
.discussion-list > div:nth-child(2) {
  animation-delay: 0.2s;
}
.discussion-list > div:nth-child(3) {
  animation-delay: 0.3s;
}
.discussion-list > div:nth-child(4) {
  animation-delay: 0.4s;
}
.discussion-list > div:nth-child(5) {
  animation-delay: 0.5s;
}
.discussion-list > div:nth-child(n + 6) {
  animation-delay: 0.6s;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* 添加环境切换动画 */
.environment-tab-enter-active,
.environment-tab-leave-active {
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.environment-tab-enter-from,
.environment-tab-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

/* 添加模态框动画 */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* 添加加载动画 */
.loading-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 环境控制按钮布局切换动画 */
.environment-controls {
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  width: 100%;
  padding: 1rem 0;
}

.environment-controls > div {
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 当切换为垂直布局时的动画 */
.environment-controls.flex-col > div {
  transform-origin: top;
  animation: slideDown 0.5s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

/* 当切换为水平布局时的动画 */
.environment-controls:not(.flex-col) > div {
  transform-origin: left;
  animation: slideRight 0.5s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideRight {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.markdown-content {
  width: 100%;
  overflow-wrap: break-word;
  word-wrap: break-word;
  word-break: break-word;
}

.markdown-content :deep(pre) {
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-x: auto;
  max-width: 100%;
}

.markdown-content :deep(code) {
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-x: auto;
  max-width: 100%;
}

.markdown-content :deep(p) {
  max-width: 100%;
  overflow-wrap: break-word;
}

/* 移除之前的宽度调整样式 */
.w-half {
  width: 50%;
  transition: width 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.w-full {
  width: 100%;
  transition: width 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

/* 确保环境标签页的层级正确 */
.fixed {
  z-index: 50;
}

/* 当环境标签页打开时，调整讨论输入框的位置 */
.fixed + .discussion-input-fixed {
  right: 50%;
}

.animate-fade-in {
  animation: fadeIn 0.5s ease-out;
}

.animate-fade-in-down {
  animation: fadeInDown 0.5s ease-out forwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 添加 flag 提交结果样式 */
.alert {
  padding: 0.75rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
}

.alert-success {
  background-color: rgba(var(--color-success), 0.1);
  color: var(--color-success);
  border: 1px solid var(--color-success);
}

.alert-error {
  background-color: rgba(var(--color-error), 0.1);
  color: var(--color-error);
  border: 1px solid var(--color-error);
}
</style>
