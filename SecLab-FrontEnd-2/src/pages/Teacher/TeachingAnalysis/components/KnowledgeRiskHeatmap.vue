<script setup lang="ts">
import type { KnowledgeRiskItemDto } from '../../../../api'
import { getRiskPresentation } from '../analysisPresentation'

defineProps<{ items: KnowledgeRiskItemDto[] }>()
defineEmits<{ select: [item: KnowledgeRiskItemDto] }>()
</script>

<template>
  <section class="risk-block">
    <div class="section-heading"><div><h2>知识点风险热力图</h2><p>按教学安排聚合错题风险，点击知识点可直接创建教学行动。</p></div></div>
    <div v-if="items.length" class="risk-grid">
      <button v-for="item in items" :key="`${item.knowledgePointId}-${item.knowledgePointName}`" :class="`risk-card risk-${item.riskLevel}`" @click="$emit('select', item)">
        <div class="risk-meta"><span>{{ item.courseName }}</span><strong>{{ getRiskPresentation(item.riskLevel).label }}</strong></div>
        <h3>{{ item.knowledgePointName }}</h3>
        <div class="risk-stats"><span><b>{{ item.attemptedStudentCount }}</b> 人学习</span><span><b>{{ item.incorrectStudentCount }}</b> 人出错</span><span><b>{{ Math.round(item.incorrectRate * 100) }}%</b> 错题率</span></div>
        <p v-if="item.affectedStudents.length">涉及：{{ item.affectedStudents.slice(0, 4).map((student) => student.studentName).join('、') }}{{ item.affectedStudents.length > 4 ? ' 等' : '' }}</p>
      </button>
    </div>
    <div v-else class="empty-inline">学生完成专项题后，这里会按教学安排形成风险热力图。</div>
  </section>
</template>

<style scoped>
.section-heading { margin-bottom:14px; } h2 { margin:0; color:#1d2d47; font-size:16px; }.section-heading p { margin:5px 0 0; color:#75839a; font-size:12px; }
.risk-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px; }.risk-card { padding:15px; border:1px solid #dfe6ee; border-left:4px solid #8593a5; border-radius:8px; background:#fff; text-align:left; cursor:pointer; transition:.15s ease; }
.risk-card:hover { transform:translateY(-1px); box-shadow:0 6px 18px rgba(35,63,98,.08); }.risk-high{border-left-color:#c95e49;background:#fffafa}.risk-medium{border-left-color:#d29a38;background:#fffdf8}.risk-low{border-left-color:#4d8b69;background:#f9fdfa}
.risk-meta { display:flex; justify-content:space-between; gap:10px; color:#77859a; font-size:10px; }.risk-meta strong{color:#44546a}.risk-card h3{margin:9px 0 12px;color:#25364f;font-size:14px}.risk-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}.risk-stats span{color:#7c899c;font-size:10px}.risk-stats b{display:block;margin-bottom:2px;color:#264f84;font-size:15px}.risk-card p{margin:10px 0 0;color:#758298;font-size:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.empty-inline{padding:30px;color:#8b96a6;font-size:12px;text-align:center}
@media(max-width:1000px){.risk-grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:650px){.risk-grid{grid-template-columns:1fr}}
</style>
