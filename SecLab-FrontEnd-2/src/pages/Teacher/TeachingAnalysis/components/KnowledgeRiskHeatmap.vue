<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { KnowledgeRiskItemDto } from '../../../../api'
import { buildRiskHeatmap, formatRiskRatePercent, getRiskPresentation } from '../analysisPresentation'

const props = defineProps<{ items: KnowledgeRiskItemDto[] }>()
const emit = defineEmits<{
  select: [item: KnowledgeRiskItemDto]
  action: [item: KnowledgeRiskItemDto]
}>()

const activeKey = ref('')
const rowKey = (item: KnowledgeRiskItemDto) => `${item.knowledgePointId || 'name'}-${item.knowledgePointName}`
const heatmap = computed(() => buildRiskHeatmap(props.items))
const selectedItem = computed(() => props.items.find((item) => rowKey(item) === activeKey.value) || props.items[0] || null)

watch(() => props.items, (items) => {
  if (!items.length) activeKey.value = ''
  else if (!items.some((item) => rowKey(item) === activeKey.value)) activeKey.value = rowKey(items[0])
}, { immediate: true })

function selectItem(item: KnowledgeRiskItemDto) {
  activeKey.value = rowKey(item)
  emit('select', item)
}

function startAction(item: KnowledgeRiskItemDto) {
  activeKey.value = rowKey(item)
  emit('action', item)
}
</script>

<template>
  <section class="risk-block">
    <div class="section-heading">
      <div>
        <h2>知识点风险热力图</h2>
        <p>纵轴是教学知识点，横轴是出现错误证据的学生；颜色越深，当前知识点风险越高。</p>
      </div>
      <div v-if="items.length" class="heatmap-summary">
        <strong>{{ items.length }}</strong> 个知识点
        <span></span>
        <strong>{{ heatmap.students.length }}</strong> 名风险学生
      </div>
    </div>

    <template v-if="items.length">
      <div class="heatmap-legend" aria-label="热力图图例">
        <span><i class="legend-none"></i>暂无错误证据</span>
        <span><i class="legend-low"></i>低风险错误</span>
        <span><i class="legend-medium"></i>需关注</span>
        <span><i class="legend-high"></i>高风险</span>
      </div>

      <div class="heatmap-scroll">
        <table class="heatmap-table" aria-label="知识点与学生错误证据热力矩阵">
          <thead>
            <tr>
              <th class="knowledge-column">教学知识点</th>
              <th v-for="student in heatmap.students" :key="student.studentId" class="student-column" :title="student.studentName || `学生 ${student.studentId}`">
                <span>{{ (student.studentName || `学生${student.studentId}`).slice(0, 3) }}</span>
              </th>
              <th class="rate-column">错题率</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in heatmap.rows" :key="rowKey(row.item)" :class="{ active: rowKey(row.item) === activeKey }">
              <th scope="row">
                <button type="button" class="knowledge-button" @click="selectItem(row.item)">
                  <span>{{ row.item.courseName }}</span>
                  <strong>{{ row.knowledgePointName }}</strong>
                </button>
              </th>
              <td v-for="cell in row.cells" :key="cell.studentId">
                <button
                  type="button"
                  class="heat-cell"
                  :class="cell.hasError ? `heat-${cell.tone}` : 'heat-none'"
                  :aria-label="`${row.knowledgePointName}，学生 ${heatmap.students.find((student) => student.studentId === cell.studentId)?.studentName || cell.studentId}，${cell.hasError ? getRiskPresentation(cell.tone).label : '暂无错误证据'}`"
                  :title="cell.hasError ? `${getRiskPresentation(cell.tone).label}：点击查看详情` : '暂无错误证据；点击查看该知识点'"
                  @click="selectItem(row.item)"
                ></button>
              </td>
              <td>
                <button type="button" class="rate-cell" :class="`rate-${row.item.riskLevel}`" @click="selectItem(row.item)">
                  <strong>{{ row.errorRatePercent }}%</strong>
                  <small>{{ row.item.incorrectCount }}/{{ row.item.attemptedCount }} 条</small>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <article v-if="selectedItem" class="heatmap-detail">
        <header>
          <div>
            <span>{{ selectedItem.courseName }} · {{ selectedItem.knowledgeCategory }}</span>
            <h3>{{ selectedItem.knowledgePointName }}</h3>
          </div>
          <strong :class="`risk-label risk-label-${selectedItem.riskLevel}`">{{ getRiskPresentation(selectedItem.riskLevel).label }}</strong>
        </header>
        <div class="detail-metrics">
          <div><span>参与学生</span><strong>{{ selectedItem.attemptedStudentCount }} 人</strong></div>
          <div><span>出错学生</span><strong>{{ selectedItem.incorrectStudentCount }} 人</strong></div>
          <div><span>错题率</span><strong>{{ formatRiskRatePercent(selectedItem.incorrectRate) }}%</strong></div>
        </div>
        <div class="detail-content">
          <section>
            <h4>涉及学生</h4>
            <div class="student-tags"><span v-for="student in selectedItem.affectedStudents" :key="student.studentId">{{ student.studentName || `学生 ${student.studentId}` }}</span></div>
          </section>
          <section>
            <h4>代表性错题</h4>
            <ul><li v-for="question in selectedItem.representativeQuestions" :key="question.generatedQuestionId"><span>{{ question.title }}</span><small>{{ question.generatedQuestionId }}</small></li></ul>
          </section>
        </div>
        <button type="button" class="action-button" @click="startAction(selectedItem)">用这个风险创建教学干预</button>
      </article>
    </template>
    <div v-else class="empty-inline">学生完成专项题后，这里会按教学安排形成风险热力图。</div>
  </section>
</template>

<style scoped>
.section-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;margin-bottom:12px}.section-heading h2{margin:0;color:#1d2d47;font-size:16px}.section-heading p{margin:5px 0 0;color:#75839a;font-size:12px}.heatmap-summary{display:flex;align-items:center;gap:6px;color:#718096;font-size:11px;white-space:nowrap}.heatmap-summary strong{color:#245b9c;font-size:16px}.heatmap-summary span{width:1px;height:16px;margin:0 5px;background:#dce4ed}.heatmap-legend{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:14px;margin-bottom:10px;color:#748197;font-size:10px}.heatmap-legend span{display:flex;align-items:center;gap:5px}.heatmap-legend i{width:14px;height:14px;border:1px solid rgba(40,58,82,.08);border-radius:3px}.legend-none,.heat-none{background:#edf1f5}.legend-low,.heat-low{background:#f4c66f}.legend-medium,.heat-medium{background:#e98c3d}.legend-high,.heat-high{background:#c9483c}.heatmap-scroll{overflow-x:auto;border:1px solid #dfe6ee;border-radius:9px;background:#fff}.heatmap-table{width:100%;min-width:760px;border-collapse:separate;border-spacing:0}.heatmap-table th,.heatmap-table td{padding:7px;border-right:1px solid #edf0f4;border-bottom:1px solid #edf0f4}.heatmap-table thead th{position:sticky;top:0;z-index:1;background:#f7f9fc;color:#748197;font-size:10px;font-weight:650;text-align:center}.heatmap-table tr:last-child th,.heatmap-table tr:last-child td{border-bottom:0}.heatmap-table th:last-child,.heatmap-table td:last-child{border-right:0}.knowledge-column{width:260px;min-width:260px;text-align:left!important}.student-column{width:58px;min-width:58px}.student-column span{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.rate-column{width:86px;min-width:86px}.heatmap-table tbody tr{transition:background .15s ease}.heatmap-table tbody tr:hover,.heatmap-table tbody tr.active{background:#f6f9fd}.knowledge-button{display:grid;width:100%;gap:3px;border:0;background:none;text-align:left;cursor:pointer}.knowledge-button span{color:#8995a5;font-size:9px}.knowledge-button strong{color:#2b3b52;font-size:12px;font-weight:650}.heat-cell{display:block;width:36px;height:36px;margin:auto;border:2px solid #fff;border-radius:6px;box-shadow:0 0 0 1px rgba(44,62,86,.08);cursor:pointer;transition:transform .12s ease,box-shadow .12s ease}.heat-cell:hover,.heat-cell:focus-visible{z-index:2;transform:scale(1.08);box-shadow:0 0 0 2px #245fae;outline:none}.rate-cell{display:grid;width:100%;gap:2px;padding:5px;border:0;border-radius:6px;background:#f5f7fa;color:#30435e;cursor:pointer}.rate-cell strong{font-size:14px}.rate-cell small{color:#7e8a9b;font-size:9px}.rate-high{background:#fff0ed;color:#a94238}.rate-medium{background:#fff7e9;color:#9a641b}.rate-low{background:#eff8f2;color:#2f7650}.heatmap-detail{margin-top:12px;padding:16px;border:1px solid #dce5ef;border-radius:9px;background:#fbfcfe}.heatmap-detail header{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}.heatmap-detail header span{color:#8290a3;font-size:10px}.heatmap-detail h3{margin:4px 0 0;color:#21334d;font-size:15px}.risk-label{padding:4px 8px;border-radius:999px;font-size:10px}.risk-label-high{background:#fff0ed;color:#aa4539}.risk-label-medium{background:#fff5e4;color:#9a651d}.risk-label-low{background:#edf7f1;color:#327452}.detail-metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-top:13px}.detail-metrics>div{display:grid;gap:4px;padding:10px;border:1px solid #e3e9f0;border-radius:7px;background:#fff}.detail-metrics span,.detail-content h4{margin:0;color:#7c899b;font-size:10px}.detail-metrics strong{color:#244f86;font-size:15px}.detail-content{display:grid;grid-template-columns:.8fr 1.2fr;gap:14px;margin-top:13px}.student-tags{display:flex;flex-wrap:wrap;gap:6px;margin-top:7px}.student-tags span{padding:5px 8px;border-radius:999px;background:#eaf2fc;color:#275e9e;font-size:10px}.detail-content ul{display:grid;gap:5px;margin:7px 0 0;padding:0;list-style:none}.detail-content li{display:flex;justify-content:space-between;gap:12px;padding:7px 9px;border:1px solid #e4e9ef;border-radius:6px;background:#fff;color:#415068;font-size:10px}.detail-content li small{color:#8a96a7}.action-button{margin-top:13px;padding:8px 11px;border:0;border-radius:6px;background:#245fae;color:#fff;font-size:11px;cursor:pointer}.empty-inline{padding:30px;color:#8b96a6;font-size:12px;text-align:center}
@media(max-width:760px){.section-heading{display:grid}.heatmap-summary{white-space:normal}.heatmap-legend{justify-content:flex-start}.detail-content{grid-template-columns:1fr}}
</style>
