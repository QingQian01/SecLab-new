<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { ArcElement, Chart, DoughnutController, Tooltip } from 'chart.js'
import type { KnowledgeRiskItemDto } from '../../../../api'
import { buildKnowledgeRiskPie, classifyKnowledgeRisk, formatRiskRatePercent } from '../analysisPresentation'

Chart.register(DoughnutController, ArcElement, Tooltip)

const props = defineProps<{
  items: KnowledgeRiskItemDto[]
  selectedCourseId: number
}>()
const emit = defineEmits<{ select: [item: KnowledgeRiskItemDto] }>()

const canvas = ref<HTMLCanvasElement | null>(null)
const model = computed(() => buildKnowledgeRiskPie(props.items, props.selectedCourseId))
let chart: Chart<'doughnut'> | null = null

function select(item: KnowledgeRiskItemDto) {
  emit('select', item)
}

function drawChart() {
  if (!canvas.value || typeof window === 'undefined') return
  chart?.destroy()
  if (!model.value.slices.length) {
    chart = null
    return
  }
  chart = new Chart(canvas.value, {
    type: 'doughnut',
    data: {
      labels: model.value.slices.map((slice) => slice.item.knowledgePointName),
      datasets: [{
        data: model.value.slices.map((slice) => Math.max(0, slice.item.incorrectCount)),
        backgroundColor: model.value.slices.map((slice) => slice.color),
        borderColor: '#ffffff',
        borderWidth: 3,
        spacing: 2,
        hoverBorderWidth: 4,
        hoverOffset: 8,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '56%',
      animation: { duration: 280 },
      onClick: (_event, elements) => {
        const index = elements[0]?.index
        if (typeof index === 'number') select(model.value.slices[index].item)
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: (context) => {
              const slice = model.value.slices[context.dataIndex]
              return `${slice.item.knowledgePointName}：错误占比 ${slice.sharePercent}%，知识点错题率 ${slice.incorrectRatePercent}%`
            },
          },
        },
      },
    },
  })
}

onMounted(() => void nextTick(drawChart))
watch(model, () => void nextTick(drawChart), { deep: true })
onBeforeUnmount(() => chart?.destroy())
</script>

<template>
  <section class="risk-pie-block">
    <div class="section-heading">
      <div>
        <h2>本实验知识点错误分布</h2>
        <p>扇区大小表示错误次数占比，颜色表示该知识点自身错题率；每个知识点都是独立扇区，同色不会合并。</p>
      </div>
      <div class="pie-summary"><strong>{{ model.slices.length + model.mastered.length }}</strong><span>个知识点</span><i></i><strong>{{ model.totalIncorrect }}</strong><span>次错误</span></div>
    </div>

    <div class="risk-legend" aria-label="知识点错题率颜色说明">
      <span v-for="rate in [0.6, 0.4, 0.2, 0]" :key="rate"><i :style="{ background: classifyKnowledgeRisk(rate).color }"></i>{{ classifyKnowledgeRisk(rate).label }}</span>
    </div>

    <div v-if="model.slices.length" class="pie-layout">
      <div class="chart-wrap">
        <canvas ref="canvas" aria-label="当前实验知识点错误占比饼图"></canvas>
        <div class="chart-center"><strong>{{ model.totalIncorrect }}</strong><span>错误记录</span></div>
      </div>
      <div class="slice-list" aria-label="可查看的知识点扇区">
        <button
          v-for="slice in model.slices"
          :key="slice.key"
          type="button"
          class="slice-button"
          :data-risk-key="slice.key"
          :data-tone="slice.tone"
          :style="{ '--risk-color': slice.color }"
          :aria-label="`${slice.item.knowledgePointName}，错误占比 ${slice.sharePercent}%，知识点错题率 ${slice.incorrectRatePercent}%，点击查看详情`"
          @click="select(slice.item)"
        >
          <i></i>
          <span><strong>{{ slice.item.knowledgePointName }}</strong><small>{{ slice.item.incorrectStudentCount }} 人出错 · {{ slice.item.incorrectCount }} 次错误</small></span>
          <em>{{ slice.sharePercent }}%</em>
        </button>
      </div>
    </div>

    <div v-else class="all-mastered"><strong>当前实验暂未发现错误知识点</strong><span>已有作答整体表现良好，可点击下方知识点查看详细证据。</span></div>

    <section v-if="model.mastered.length" class="mastered-block">
      <header><div><h3>掌握良好</h3><p>以下知识点错误次数为 0，不绘制虚假的饼图面积。</p></div><strong>{{ model.mastered.length }} 项</strong></header>
      <div class="mastered-list">
        <button
          v-for="item in model.mastered"
          :key="`${item.knowledgePointId}-${item.knowledgePointName}`"
          type="button"
          :data-mastered-key="`${item.knowledgePointId}-${item.knowledgePointName}`"
          @click="select(item)"
        ><span>{{ item.knowledgePointName }}</span><small>{{ item.attemptedStudentCount }} 人作答 · 错题率 {{ formatRiskRatePercent(item.incorrectRate) }}%</small></button>
      </div>
    </section>

    <div v-if="!model.slices.length && !model.mastered.length" class="empty-inline">本实验产生作答记录后，这里会按知识点形成错误分布。</div>
  </section>
</template>

<style scoped>
.risk-pie-block{padding:2px}.section-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:18px}.section-heading h2{margin:0;color:#1d2d47;font-size:17px}.section-heading p{max-width:720px;margin:6px 0 0;color:#75839a;font-size:12px;line-height:1.6}.pie-summary{display:flex;align-items:baseline;gap:5px;color:#7b8798;font-size:11px;white-space:nowrap}.pie-summary strong{color:#245b9c;font-size:19px}.pie-summary i{width:1px;height:16px;margin:0 7px;background:#dce4ed}.risk-legend{display:flex;justify-content:flex-end;gap:16px;margin:15px 0 12px;color:#6f7d91;font-size:11px}.risk-legend span{display:flex;align-items:center;gap:5px}.risk-legend i{width:11px;height:11px;border:2px solid #fff;border-radius:3px;box-shadow:0 0 0 1px rgba(35,53,78,.12)}.pie-layout{display:grid;grid-template-columns:minmax(300px,.8fr) minmax(360px,1.2fr);gap:24px;align-items:center}.chart-wrap{position:relative;height:330px;min-width:0}.chart-center{position:absolute;inset:50% auto auto 50%;display:grid;transform:translate(-50%,-50%);text-align:center;pointer-events:none}.chart-center strong{color:#24405f;font-size:27px}.chart-center span{color:#8390a2;font-size:11px}.slice-list{display:grid;gap:8px;max-height:340px;padding-right:5px;overflow:auto}.slice-button{--risk-color:#76869a;display:grid;width:100%;grid-template-columns:12px minmax(0,1fr) auto;gap:10px;align-items:center;padding:11px 12px;border:1px solid #e1e7ef;border-left:4px solid var(--risk-color);border-radius:8px;background:#fff;color:#27384f;text-align:left;cursor:pointer;transition:transform .15s ease,border-color .15s ease,box-shadow .15s ease}.slice-button:hover,.slice-button:focus-visible{transform:translateX(3px);border-color:var(--risk-color);box-shadow:0 5px 15px rgba(35,66,102,.09);outline:none}.slice-button>i{width:9px;height:9px;border:2px solid #fff;border-radius:50%;background:var(--risk-color);box-shadow:0 0 0 1px var(--risk-color)}.slice-button span strong,.slice-button span small{display:block}.slice-button span strong{font-size:13px}.slice-button span small{margin-top:4px;color:#8190a3;font-size:10px}.slice-button em{color:var(--risk-color);font-size:18px;font-style:normal;font-weight:750}.mastered-block{margin-top:18px;padding:15px;border:1px solid #dcece2;border-radius:9px;background:#f7fcf9}.mastered-block header{display:flex;justify-content:space-between;gap:12px}.mastered-block h3{margin:0;color:#28724c;font-size:14px}.mastered-block p{margin:4px 0 0;color:#718b7d;font-size:10px}.mastered-block header>strong{color:#31805a;font-size:13px}.mastered-list{display:flex;flex-wrap:wrap;gap:8px;margin-top:11px}.mastered-list button{display:grid;gap:3px;padding:8px 10px;border:1px solid #cfe5d8;border-radius:7px;background:#fff;color:#286a49;text-align:left;cursor:pointer}.mastered-list button:hover,.mastered-list button:focus-visible{border-color:#3e9b65;outline:none}.mastered-list span{font-size:11px;font-weight:700}.mastered-list small{color:#789184;font-size:9px}.all-mastered{display:grid;gap:5px;place-items:center;padding:34px;border-radius:9px;background:#f1faf5;color:#6f8d7c;font-size:11px}.all-mastered strong{color:#2f7852;font-size:15px}.empty-inline{padding:34px;color:#8793a5;font-size:12px;text-align:center}@media(max-width:900px){.pie-layout{grid-template-columns:1fr}.chart-wrap{height:290px}.risk-legend{justify-content:flex-start;flex-wrap:wrap}}@media(max-width:600px){.section-heading{display:grid}.pie-summary{justify-self:start}.chart-wrap{height:250px}.slice-list{max-height:none}.slice-button{grid-template-columns:10px minmax(0,1fr) auto}.risk-legend{gap:9px}}
</style>
