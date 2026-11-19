<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { TeacherCourseQuestionsDto, TeacherGeneratedQuestionRecord } from '../../../../api'

const props = defineProps<{
  data: TeacherCourseQuestionsDto | null
  loading?: boolean
  scopeLabel: string
}>()

const answerFilter = ref<'all' | 'incorrect' | 'correct' | 'unanswered'>('all')
const expandedId = ref<string | null>(null)
const showAll = ref(false)
const PAGE_SIZE = 20

const visibleItems = computed(() => (props.data?.items || []).filter((item) => {
  const latest = item.attemptHistory?.at(-1)
  if (answerFilter.value === 'incorrect') return latest?.isCorrect === false
  if (answerFilter.value === 'correct') return latest?.isCorrect === true
  if (answerFilter.value === 'unanswered') return !latest
  return true
}))

// 默认只展示前 20 条，点击"展开全部"后再展示其余记录
const displayItems = computed(() => showAll.value ? visibleItems.value : visibleItems.value.slice(0, PAGE_SIZE))

watch(() => props.data, (data) => {
  const firstIncorrect = data?.items.find((item) => item.attemptHistory?.at(-1)?.isCorrect === false)
  expandedId.value = firstIncorrect?.generatedQuestionId || data?.items[0]?.generatedQuestionId || null
}, { immediate: true })

function latest(item: TeacherGeneratedQuestionRecord) {
  return item.attemptHistory?.at(-1) || null
}

function formatAnswer(value: unknown) {
  if (value === null || value === undefined || value === '') return '未作答'
  if (typeof value === 'string') return value
  try { return JSON.stringify(value, null, 2) } catch { return String(value) }
}

function formatTime(value?: string | null) {
  return value ? new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(value)) : '时间未知'
}
</script>

<template>
  <section class="course-records">
    <div class="records-head">
      <h2>{{ scopeLabel }}本实验全部做题情况</h2>
      <div class="filter-tabs" aria-label="作答结果筛选">
        <button v-for="item in [['all','全部'],['incorrect','错题'],['correct','答对'],['unanswered','未作答']]" :key="item[0]" :class="{ active: answerFilter === item[0] }" @click="answerFilter = item[0] as typeof answerFilter">{{ item[1] }}</button>
      </div>
    </div>
    <div v-if="loading" class="records-empty">正在读取实验作答记录…</div>
    <div v-else-if="!data?.items.length" class="records-empty"><strong>本实验暂无做题记录</strong></div>
    <div v-else-if="!visibleItems.length" class="records-empty">当前筛选条件下没有题目。</div>
    <div v-else class="question-list">
      <article v-for="(item,index) in displayItems" :key="item.generatedQuestionId" class="question-card" :class="{ open: expandedId === item.generatedQuestionId }">
        <button class="question-summary" @click="expandedId = expandedId === item.generatedQuestionId ? null : item.generatedQuestionId">
          <span class="question-no">{{ index + 1 }}</span>
          <span class="question-main"><strong>{{ item.title }}</strong><small>{{ item.student.studentName }} · {{ item.knowledgePointName || '未标注知识点' }} · 共 {{ item.attemptHistory?.length || 0 }} 次作答</small></span>
          <span class="question-score">{{ latest(item) ? `${latest(item)?.score ?? 0} 分` : '未作答' }}</span>
          <span class="result-badge" :class="latest(item)?.isCorrect === true ? 'correct' : latest(item)?.isCorrect === false ? 'incorrect' : 'empty'">{{ latest(item)?.isCorrect === true ? '最终答对' : latest(item)?.isCorrect === false ? '最终答错' : '未作答' }}</span>
          <span class="chevron">{{ expandedId === item.generatedQuestionId ? '收起' : '详情' }}</span>
        </button>
        <div v-if="expandedId === item.generatedQuestionId" class="question-detail">
          <div class="question-copy"><h4>题目</h4><p>{{ item.stem || item.title }}</p><div v-if="item.options?.length" class="options"><span v-for="(option,optionIndex) in item.options" :key="optionIndex">{{ option }}</span></div></div>
          <div class="answer-grid"><div><h4>标准答案</h4><pre>{{ formatAnswer(item.standardAnswer || item.referenceAnswer) }}</pre></div><div><h4>题目解析</h4><p>{{ item.explanation || '暂无解析' }}</p></div></div>
          <div class="attempt-block"><h4>完整作答轨迹</h4><div v-if="!item.attemptHistory?.length" class="attempt-empty">学生尚未作答。</div><ol v-else class="attempt-list"><li v-for="(attempt,attemptIndex) in item.attemptHistory" :key="attempt.attemptId"><span class="attempt-index">{{ attemptIndex + 1 }}</span><div><div class="attempt-meta"><strong :class="attempt.isCorrect ? 'text-correct' : 'text-incorrect'">{{ attempt.isCorrect ? '回答正确' : '回答错误' }} · {{ attempt.score }} 分</strong><small>{{ formatTime(attempt.submittedAt) }}<template v-if="attempt.costTime"> · 用时 {{ attempt.costTime }} 秒</template></small></div><pre>{{ formatAnswer(attempt.answer) }}</pre></div></li></ol></div>
        </div>
      </article>
    </div>
    <div v-if="visibleItems.length > PAGE_SIZE" class="expand-bar">
      <button v-if="showAll" @click="showAll = false">收起（仅显示前 {{ PAGE_SIZE }} 条）</button>
      <button v-else @click="showAll = true">展开全部（共 {{ visibleItems.length }} 条，已显示前 {{ PAGE_SIZE }} 条）</button>
    </div>
  </section>
</template>

<style scoped>
.course-records{padding:20px}.records-head{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin-bottom:16px}.records-head h2{margin:0;color:#1c2c45;font-size:17px}.records-head p{margin:6px 0 0;color:#7b899d;font-size:12px}.filter-tabs{display:flex;padding:3px;border:1px solid #dce4ee;border-radius:7px;background:#f7f9fc}.filter-tabs button{padding:6px 11px;border:0;border-radius:5px;background:transparent;color:#6d7b8f;font-size:12px;cursor:pointer}.filter-tabs button.active{background:#fff;color:#1f5ca9;box-shadow:0 1px 4px rgba(30,65,105,.12)}.records-empty{display:grid;gap:7px;place-items:center;padding:48px;color:#8793a5;font-size:13px}.records-empty strong{color:#35445a;font-size:15px}.question-list{display:grid;gap:10px}.question-card{border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;background:#fff}.question-card.open{border-color:#9cb9df;box-shadow:0 4px 14px rgba(36,94,174,.07)}.question-summary{display:grid;width:100%;grid-template-columns:28px minmax(0,1fr) 72px 76px 44px;gap:11px;align-items:center;padding:13px 14px;border:0;background:#fff;color:#35445a;text-align:left;cursor:pointer}.question-summary:hover{background:#f8fafd}.question-no{display:grid;width:25px;height:25px;place-items:center;border-radius:6px;background:#edf3fb;color:#245fae;font-size:11px;font-weight:700}.question-main strong,.question-main small{display:block}.question-main strong{color:#24354d;font-size:13px}.question-main small{margin-top:5px;color:#8390a2;font-size:11px}.question-score{text-align:right;color:#40516a;font-size:12px;font-weight:650}.result-badge{padding:4px 7px;border-radius:999px;text-align:center;font-size:10px}.result-badge.correct{background:#e9f7ef;color:#28794a}.result-badge.incorrect{background:#fff0ed;color:#b24838}.result-badge.empty{background:#f0f2f5;color:#7e8997}.chevron{color:#2762aa;font-size:11px}.question-detail{padding:18px 20px;border-top:1px solid #e6ebf1;background:#fbfcfe}.question-detail h4{margin:0 0 8px;color:#6d7b8e;font-size:11px}.question-copy p,.answer-grid p{margin:0;color:#34445b;font-size:13px;line-height:1.7}.options{display:grid;gap:6px;margin-top:10px}.options span{padding:7px 9px;border:1px solid #e1e7ef;border-radius:5px;background:#fff;color:#46566c;font-size:12px}.answer-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:16px}.answer-grid>div{padding:13px;border:1px solid #e2e8ef;border-radius:7px;background:#fff}.question-detail pre{margin:0;white-space:pre-wrap;word-break:break-word;color:#25364d;font:12px/1.6 ui-monospace,SFMono-Regular,Consolas,monospace}.attempt-block{margin-top:17px}.attempt-list{display:grid;gap:0;margin:0;padding:0;list-style:none}.attempt-list li{display:grid;grid-template-columns:26px 1fr;gap:10px;padding:12px 0;border-top:1px solid #e6ebf1}.attempt-index{display:grid;width:23px;height:23px;place-items:center;border-radius:50%;background:#eaf1fb;color:#245fae;font-size:10px;font-weight:700}.attempt-meta{display:flex;justify-content:space-between;margin-bottom:7px}.attempt-meta strong,.attempt-meta small{font-size:11px}.attempt-meta small{color:#8a96a7}.text-correct{color:#28794a}.text-incorrect{color:#b24838}.attempt-empty{color:#8793a5;font-size:12px}.expand-bar{display:grid;place-items:center;padding-top:14px}.expand-bar button{padding:8px 16px;border:1px solid #c9d8ec;border-radius:6px;background:#f4f8fd;color:#245fae;font-size:12px;cursor:pointer}.expand-bar button:hover{background:#e8f0fb}@media(max-width:800px){.records-head{display:grid}.filter-tabs{overflow:auto}.question-summary{grid-template-columns:28px 1fr 70px}.question-score,.chevron{display:none}.answer-grid{grid-template-columns:1fr}}
</style>
