<script setup lang="ts">
import type { TeacherCourseAnalysisDto } from '../../../../api'

defineProps<{
  data: TeacherCourseAnalysisDto | null
  analysing?: boolean
  subjectLabel: string
}>()
defineEmits<{ analyse: [] }>()
</script>

<template>
  <section class="course-analysis">
    <div class="analysis-head"><h2>{{ subjectLabel }}实验分析</h2><button class="analyse-button" :disabled="analysing" @click="$emit('analyse')">{{ analysing ? '正在分析…' : data?.analysis ? '重新分析本实验' : 'AI 分析本实验' }}</button></div>
    <div v-if="data?.analysis" class="analysis-body">
      <p class="overall">{{ data.analysis.overallComment }}</p>
      <div v-if="data.analysis.knowledgeFindings?.length" class="finding-grid"><article v-for="item in data.analysis.knowledgeFindings" :key="item.knowledgePointName"><div><strong>{{ item.knowledgePointName }}</strong><span>{{ Math.round(Number(item.accuracyRate || 0) * 100) }}% 正确率</span></div><p>{{ item.evidence }}</p><small><b>教学动作</b>{{ item.teacherAction }}</small></article></div>
      <div v-if="data.analysis.teachingSuggestions?.length" class="suggestions"><h3>建议下一步</h3><ol><li v-for="item in data.analysis.teachingSuggestions" :key="item">{{ item }}</li></ol></div>
    </div>
    <div v-else class="analysis-empty"><strong>暂无本实验分析</strong></div>
  </section>
</template>

<style scoped>
.course-analysis{padding:20px}.analysis-head{display:flex;justify-content:space-between;gap:20px;align-items:flex-start}.analysis-head h2{margin:0;color:#1c2c45;font-size:17px}.analysis-head p{margin:6px 0 0;color:#7b899d;font-size:12px}.analyse-button{padding:10px 15px;border:0;border-radius:7px;background:#2463b7;color:#fff;font-size:12px;font-weight:650;cursor:pointer}.analyse-button:disabled{opacity:.6;cursor:wait}.analysis-body{margin-top:17px}.provider-note{display:flex;gap:8px;padding:10px 12px;border:1px solid #f0d8ad;border-radius:6px;background:#fffaf0;color:#806024;font-size:11px}.provider-note strong{color:#a36a0c}.overall{margin:12px 0 0;padding:14px 16px;border-left:3px solid #2c67b5;background:#f5f8fc;color:#35455d;font-size:13px;line-height:1.75}.finding-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-top:12px}.finding-grid article{padding:14px;border:1px solid #e3e8ef;border-radius:7px}.finding-grid article>div{display:flex;justify-content:space-between;gap:10px}.finding-grid strong{color:#273850;font-size:13px}.finding-grid span{color:#a05a22;font-size:11px}.finding-grid p{margin:8px 0;color:#637187;font-size:12px;line-height:1.6}.finding-grid small{display:block;padding:9px;background:#f7f9fc;color:#4a5a70;line-height:1.55}.finding-grid b{margin-right:6px;color:#245fae}.suggestions{margin-top:14px}.suggestions h3{font-size:13px}.suggestions ol{margin:0;padding-left:22px;color:#516178;font-size:12px;line-height:1.8}.analysis-empty{display:grid;gap:6px;place-items:center;padding:35px;color:#8290a3;font-size:12px}.analysis-empty strong{color:#35445a;font-size:14px}@media(max-width:800px){.analysis-head{display:grid}.finding-grid{grid-template-columns:1fr}}
</style>
