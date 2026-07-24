<script setup lang="ts">
import { computed } from 'vue'
import type { TeacherCourseAnalysisDto } from '../../../../api'

const props = defineProps<{
  data: TeacherCourseAnalysisDto | null
  analysing?: boolean
  subjectLabel: string
}>()
defineEmits<{ analyse: [] }>()

const summary = computed(() => props.data?.analysis?.summary || props.data?.sourceStats)
const accuracyRate = computed(() =>
  Math.round(Math.min(1, Math.max(0, Number(summary.value?.accuracyRate) || 0)) * 1000) / 10,
)
</script>

<template>
  <section class="course-analysis">
    <div class="analysis-head"><h2>{{ subjectLabel }}实验分析</h2><button class="analyse-button" :disabled="analysing" @click="$emit('analyse')">{{ analysing ? '更新中…' : '更新分析' }}</button></div>
    <div v-if="data?.analysis" class="analysis-body">
      <div class="overall">
        <strong>答题情况</strong>
        <span>本实验共 {{ summary?.questionCount || 0 }} 道题，已作答 {{ summary?.attemptCount || 0 }} 次，正确率 {{ accuracyRate }}%。</span>
      </div>
      <div v-if="data.analysis.knowledgeFindings?.length" class="finding-grid">
        <article v-for="item in data.analysis.knowledgeFindings" :key="item.knowledgePointName">
          <div>
            <strong>{{ item.knowledgePointName }}</strong>
            <span>{{ Math.round(Number(item.accuracyRate || 0) * 100) }}% 正确率</span>
          </div>
          <p>仍有 {{ item.incorrectQuestionCount || 0 }} 道题答错，涉及 {{ item.affectedStudentCount || 0 }} 名学生。</p>
        </article>
      </div>
    </div>
    <div v-else class="analysis-empty"><strong>暂无分析结果</strong></div>
  </section>
</template>

<style scoped>
.course-analysis{padding:20px}.analysis-head{display:flex;justify-content:space-between;gap:20px;align-items:flex-start}.analysis-head h2{margin:0;color:#1c2c45;font-size:17px}.analyse-button{padding:10px 15px;border:0;border-radius:7px;background:#2463b7;color:#fff;font-size:12px;font-weight:650;cursor:pointer}.analyse-button:disabled{opacity:.6;cursor:wait}.analysis-body{margin-top:17px}.overall{display:flex;gap:12px;align-items:baseline;margin:12px 0 0;padding:14px 16px;border-left:3px solid #2c67b5;background:#f5f8fc;color:#35455d;font-size:13px;line-height:1.75}.overall strong{color:#245fae;white-space:nowrap}.finding-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:12px}.finding-grid article{padding:14px;border:1px solid #e3e8ef;border-radius:7px}.finding-grid article>div{display:flex;justify-content:space-between;gap:10px}.finding-grid strong{color:#273850;font-size:13px}.finding-grid span{color:#a05a22;font-size:11px}.finding-grid p{margin:8px 0 0;color:#637187;font-size:12px;line-height:1.6}.analysis-empty{display:grid;gap:6px;place-items:center;padding:35px;color:#8290a3;font-size:12px}.analysis-empty strong{color:#35445a;font-size:14px}@media(max-width:800px){.analysis-head{display:grid}.overall{display:grid;gap:2px}.finding-grid{grid-template-columns:1fr}}
</style>
