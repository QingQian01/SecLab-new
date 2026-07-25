<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import Chart from 'chart.js/auto'

import type {
  CapabilityGrowthDimensionDto,
  CapabilityGrowthHistoryDto,
  CapabilityGrowthResponseDto,
} from '../api'
import {
  confidenceLabel,
  formatGrowthDelta,
  formatMetricValue,
  metricDirectionLabel,
} from './capabilityGrowthPresentation'

const props = withDefaults(defineProps<{
  data?: CapabilityGrowthResponseDto | null
  loading?: boolean
  error?: string
  teacherMode?: boolean
}>(), {
  data: null,
  loading: false,
  error: '',
  teacherMode: false,
})

defineEmits<{ retry: [] }>()

const selectedKey = ref<string>('knowledge_mastery')
const chartCanvas = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null

const hasGrowthData = computed(() => {
  const data = props.data
  if (!data) return false
  if (typeof data.overall.baselineScore === 'number' || typeof data.overall.currentScore === 'number') {
    return true
  }
  if (data.history.length) return true
  return data.dimensions.some((dimension) =>
    typeof dimension.baselineScore === 'number'
    || typeof dimension.currentScore === 'number'
    || dimension.metrics.length > 0
    || dimension.evidence.length > 0,
  )
})

const selectedDimension = computed<CapabilityGrowthDimensionDto | null>(() =>
  props.data?.dimensions.find((item) => item.key === selectedKey.value)
  ?? props.data?.dimensions[0]
  ?? null,
)

const overallTone = computed(() => {
  const delta = props.data?.overall.delta
  if (delta == null) return 'neutral'
  if (delta > 0) return 'improved'
  if (delta < 0) return 'declined'
  return 'stable'
})

function formatScore(value: number | null | undefined): string {
  return value == null ? '—' : value.toFixed(1)
}

function formatDate(value: string | null | undefined): string {
  if (!value) return '日期待积累'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  }).format(date)
}

function historyValue(row: CapabilityGrowthHistoryDto): number | null | undefined {
  if (selectedKey.value === 'knowledge_mastery') return row.knowledge_masteryScore
  if (selectedKey.value === 'troubleshooting') return row.troubleshootingScore
  if (selectedKey.value === 'autonomy') return row.autonomyScore
  if (selectedKey.value === 'ai_collaboration') return row.ai_collaborationScore
  if (selectedKey.value === 'engagement') return row.engagementScore
  return row.overallScore
}

function renderChart(): void {
  if (!chartCanvas.value) return
  chart?.destroy()
  chart = null
  const history = props.data?.history ?? []
  const points = history
    .map((row) => ({ row, value: historyValue(row) }))
    .filter((item): item is { row: CapabilityGrowthHistoryDto; value: number } =>
      typeof item.value === 'number',
    )
  if (points.length < 2) return
  chart = new Chart(chartCanvas.value, {
    type: 'line',
    data: {
      labels: points.map(({ row }) => formatDate(row.computedAt)),
      datasets: [{
        data: points.map(({ value }) => value),
        borderColor: '#2563eb',
        backgroundColor: 'rgba(37, 99, 235, 0.10)',
        pointBackgroundColor: '#ffffff',
        pointBorderColor: '#2563eb',
        pointBorderWidth: 2,
        pointRadius: 4,
        tension: 0.32,
        fill: true,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#64748b', maxRotation: 0, font: { size: 11 } },
          border: { display: false },
        },
        y: {
          suggestedMin: 0,
          suggestedMax: 100,
          ticks: { color: '#94a3b8', font: { size: 11 } },
          grid: { color: 'rgba(148, 163, 184, 0.14)' },
          border: { display: false },
        },
      },
    },
  })
}

watch(
  () => [props.data?.history, selectedKey.value],
  () => nextTick(renderChart),
  { deep: true },
)

watch(
  () => props.data?.dimensions,
  (dimensions) => {
    if (dimensions?.length && !dimensions.some((item) => item.key === selectedKey.value)) {
      selectedKey.value = dimensions[0].key
    }
  },
)

onMounted(() => nextTick(renderChart))
onBeforeUnmount(() => chart?.destroy())
</script>

<template>
  <section class="growth-panel" aria-labelledby="capability-growth-title">
    <header class="growth-header">
      <div>
        <h2 id="capability-growth-title">能力成长</h2>
        <p>
          {{ teacherMode ? '基于学生真实学习行为的可比成长证据' : '用真实学习记录，看见你在哪些方面正在进步' }}
        </p>
      </div>
      <div v-if="data?.dataProvenance.mode === 'production_events'" class="source-status">
        <span class="status-dot" aria-hidden="true"></span>
        真实记录计算
      </div>
    </header>

    <div v-if="loading" class="state-view" role="status">
      <span class="loading-ring" aria-hidden="true"></span>
      <strong>正在汇总成长证据</strong>
      <p>系统正在核对可比任务与原始记录。</p>
    </div>

    <div v-else-if="error" class="state-view error-view" role="alert">
      <strong>成长数据暂时无法读取</strong>
      <p>{{ error }}</p>
      <button type="button" @click="$emit('retry')">重新加载</button>
    </div>

    <div v-else-if="!data || !hasGrowthData" class="state-view empty-view">
      <span class="empty-symbol" aria-hidden="true">↗</span>
      <strong>{{ data?.message || '暂无真实成长数据' }}</strong>
      <p>完成真实实验和练习后，这里会形成可追溯的成长证据。</p>
    </div>

    <div v-else class="growth-content">
      <div class="overall-strip">
        <div class="overall-title">
          <span>综合能力</span>
          <strong :class="`tone-${overallTone}`">{{ formatGrowthDelta(data.overall.delta) }}</strong>
        </div>
        <div class="score-journey">
          <div>
            <span>早期基线</span>
            <strong>{{ formatScore(data.overall.baselineScore) }}</strong>
            <small>{{ formatDate(data.baselineComputedAt) }}</small>
          </div>
          <div class="journey-line" aria-hidden="true">
            <span></span>
          </div>
          <div class="current-score">
            <span>当前表现</span>
            <strong>{{ formatScore(data.overall.currentScore) }}</strong>
            <small>{{ formatDate(data.currentComputedAt) }}</small>
          </div>
        </div>
      </div>

      <nav class="dimension-tabs" aria-label="能力维度">
        <button
          v-for="dimension in data.dimensions"
          :key="dimension.key"
          type="button"
          :class="{ active: selectedDimension?.key === dimension.key }"
          :aria-current="selectedDimension?.key === dimension.key ? 'true' : undefined"
          @click="selectedKey = dimension.key"
        >
          <span>{{ dimension.label }}</span>
          <strong>{{ formatGrowthDelta(dimension.delta) }}</strong>
        </button>
      </nav>

      <article v-if="selectedDimension" class="dimension-detail">
        <div class="dimension-summary">
          <div>
            <span class="confidence">{{ confidenceLabel(selectedDimension.confidence) }}</span>
            <h3>{{ selectedDimension.label }}</h3>
            <p>{{ selectedDimension.summary }}</p>
          </div>
          <div v-if="data.history.length >= 2" class="trend-chart">
            <canvas ref="chartCanvas" :aria-label="`${selectedDimension.label}历史趋势`"></canvas>
          </div>
        </div>

        <div v-if="selectedDimension.metrics.length" class="metrics-list">
          <section
            v-for="metric in selectedDimension.metrics"
            :key="metric.key"
            class="metric-row"
          >
            <div class="metric-name">
              <span :class="`direction direction-${metric.direction}`">
                {{ metricDirectionLabel(metric.direction) }}
              </span>
              <h4>{{ metric.label }}</h4>
            </div>
            <div class="metric-comparison">
              <div>
                <span>早期</span>
                <strong>{{ formatMetricValue(metric.baselineValue, metric.unit) }}</strong>
              </div>
              <span class="comparison-arrow" aria-hidden="true">→</span>
              <div class="metric-current">
                <span>近期</span>
                <strong>{{ formatMetricValue(metric.currentValue, metric.unit) }}</strong>
              </div>
            </div>
            <div class="metric-explanation">
              <p>{{ metric.explanation }}</p>
              <small>
                早期 {{ metric.baselineSampleCount }} 条 · 近期 {{ metric.currentSampleCount }} 条
                · {{ confidenceLabel(metric.confidence) }}
              </small>
              <small v-if="teacherMode && metric.sourceRecordIds.length" class="trace">
                来源记录 {{ metric.sourceRecordIds.join('、') }}
              </small>
            </div>
          </section>
        </div>

        <div v-else class="metric-empty">
          该维度已有当前能力结果，但还没有足够的同类任务形成前后对比。
        </div>

        <div v-if="selectedDimension.evidence.length" class="evidence-list">
          <h4>最近证据</h4>
          <div
            v-for="item in selectedDimension.evidence"
            :key="`${item.sourceType}-${item.sourceId}`"
            class="evidence-row"
          >
            <span class="evidence-mark" aria-hidden="true"></span>
            <div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.detail || '已记录真实学习行为' }}</p>
            </div>
            <time>{{ formatDate(item.occurredAt) }}</time>
          </div>
        </div>
      </article>

      <footer class="provenance-bar">
        <span>计算版本 {{ data.calculationVersion }}</span>
        <span>纳入 {{ data.dataProvenance.eligibleRecordCount ?? 0 }} 条生产记录</span>
        <span v-if="data.dataProvenance.excludedRecordCount">
          已排除 {{ data.dataProvenance.excludedRecordCount }} 条非生产数据
        </span>
        <span v-if="data.dataProvenance.unverifiableRecordCount">
          {{ data.dataProvenance.unverifiableRecordCount }} 条来源不明记录未参与
        </span>
      </footer>
    </div>
  </section>
</template>

<style scoped>
.growth-panel {
  overflow: hidden;
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 12px 34px rgba(15, 23, 42, 0.06);
  color: #0f172a;
}

.growth-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  padding: 28px 30px 22px;
  border-bottom: 1px solid #eef2f7;
}

.growth-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.growth-header p,
.dimension-summary p,
.metric-explanation p,
.evidence-row p,
.state-view p {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 14px;
  line-height: 1.65;
}

.source-status {
  display: inline-flex;
  flex: none;
  align-items: center;
  gap: 8px;
  color: #166534;
  font-size: 13px;
  font-weight: 600;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 0 4px #dcfce7;
}

.overall-strip {
  display: grid;
  grid-template-columns: minmax(150px, .6fr) minmax(360px, 1.4fr);
  align-items: center;
  gap: 32px;
  padding: 26px 30px;
  background: #f8fafc;
}

.overall-title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
}

.overall-title > span {
  color: #475569;
  font-size: 14px;
  font-weight: 600;
}

.overall-title strong {
  font-size: 24px;
  font-weight: 750;
}

.tone-improved,
.direction-improved {
  color: #047857 !important;
}

.tone-declined,
.direction-declined {
  color: #b45309 !important;
}

.tone-stable,
.tone-neutral {
  color: #475569;
}

.score-journey {
  display: grid;
  grid-template-columns: auto minmax(80px, 1fr) auto;
  align-items: center;
  gap: 18px;
}

.score-journey > div:not(.journey-line) {
  display: grid;
  gap: 2px;
}

.score-journey span,
.metric-comparison span,
.metric-explanation small,
.score-journey small {
  color: #64748b;
  font-size: 12px;
}

.score-journey strong {
  font-size: 30px;
  font-weight: 750;
  letter-spacing: -0.03em;
}

.current-score {
  text-align: right;
}

.current-score strong {
  color: #1d4ed8;
}

.journey-line {
  position: relative;
  height: 2px;
  background: #cbd5e1;
}

.journey-line::before,
.journey-line::after {
  position: absolute;
  top: 50%;
  width: 8px;
  height: 8px;
  border: 2px solid #94a3b8;
  border-radius: 50%;
  background: #fff;
  content: "";
  transform: translateY(-50%);
}

.journey-line::before { left: -1px; }
.journey-line::after {
  right: -1px;
  border-color: #2563eb;
  background: #2563eb;
}

.dimension-tabs {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  border-top: 1px solid #eef2f7;
  border-bottom: 1px solid #eef2f7;
}

.dimension-tabs button {
  display: grid;
  gap: 5px;
  min-width: 0;
  padding: 17px 14px 15px;
  border: 0;
  border-right: 1px solid #eef2f7;
  border-bottom: 3px solid transparent;
  background: #fff;
  color: #64748b;
  font-family: inherit;
  text-align: left;
  cursor: pointer;
  transition: background .18s ease, border-color .18s ease, color .18s ease;
}

.dimension-tabs button:last-child { border-right: 0; }
.dimension-tabs button:hover { background: #f8fafc; }
.dimension-tabs button.active {
  border-bottom-color: #2563eb;
  color: #0f172a;
  background: #f8fbff;
}

.dimension-tabs span {
  overflow: hidden;
  font-size: 13px;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dimension-tabs strong {
  color: inherit;
  font-size: 12px;
  font-weight: 600;
}

.dimension-detail {
  padding: 28px 30px;
}

.dimension-summary {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(250px, .8fr);
  align-items: center;
  gap: 36px;
  margin-bottom: 22px;
}

.confidence,
.direction {
  display: inline-flex;
  align-items: center;
  color: #475569;
  font-size: 12px;
  font-weight: 650;
}

.dimension-summary h3 {
  margin: 8px 0 0;
  font-size: 20px;
}

.trend-chart {
  height: 130px;
}

.metrics-list {
  border-top: 1px solid #e2e8f0;
}

.metric-row {
  display: grid;
  grid-template-columns: minmax(145px, .7fr) minmax(220px, 1fr) minmax(260px, 1.25fr);
  align-items: center;
  gap: 24px;
  padding: 22px 0;
  border-bottom: 1px solid #eef2f7;
}

.metric-name h4,
.evidence-list h4 {
  margin: 6px 0 0;
  font-size: 15px;
}

.metric-comparison {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 12px;
}

.metric-comparison > div {
  display: grid;
  gap: 3px;
}

.metric-comparison strong {
  font-size: 22px;
  letter-spacing: -0.02em;
}

.metric-current { text-align: right; }
.metric-current strong { color: #1d4ed8; }
.comparison-arrow { color: #94a3b8 !important; }

.metric-explanation p { margin: 0; }
.metric-explanation small {
  display: block;
  margin-top: 6px;
}

.metric-explanation .trace {
  overflow-wrap: anywhere;
  color: #475569;
}

.metric-empty {
  padding: 24px;
  border: 1px dashed #cbd5e1;
  border-radius: 12px;
  background: #f8fafc;
  color: #64748b;
  font-size: 14px;
}

.evidence-list {
  margin-top: 26px;
}

.evidence-row {
  display: grid;
  grid-template-columns: 10px minmax(0, 1fr) auto;
  align-items: start;
  gap: 12px;
  padding: 14px 0;
  border-bottom: 1px solid #f1f5f9;
}

.evidence-row strong { font-size: 14px; }
.evidence-row p { margin-top: 2px; }
.evidence-row time {
  color: #94a3b8;
  font-size: 12px;
}

.evidence-mark {
  width: 8px;
  height: 8px;
  margin-top: 5px;
  border-radius: 50%;
  background: #60a5fa;
}

.provenance-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 20px;
  padding: 14px 30px;
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
  color: #64748b;
  font-size: 12px;
}

.state-view {
  display: grid;
  justify-items: center;
  padding: 58px 30px;
  text-align: center;
}

.state-view strong { font-size: 16px; }
.state-view button {
  margin-top: 18px;
  padding: 9px 16px;
  border: 0;
  border-radius: 8px;
  background: #1d4ed8;
  color: #fff;
  font-family: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.loading-ring {
  width: 24px;
  height: 24px;
  margin-bottom: 16px;
  border: 3px solid #dbeafe;
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin .8s linear infinite;
}

.empty-symbol {
  display: grid;
  width: 42px;
  height: 42px;
  margin-bottom: 16px;
  place-items: center;
  border-radius: 50%;
  background: #eff6ff;
  color: #2563eb;
  font-size: 21px;
}

@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 900px) {
  .overall-strip,
  .dimension-summary {
    grid-template-columns: 1fr;
  }

  .dimension-tabs {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .dimension-tabs button { border-bottom-width: 1px; }
  .dimension-tabs button.active { box-shadow: inset 3px 0 #2563eb; }

  .metric-row {
    grid-template-columns: minmax(130px, .7fr) minmax(210px, 1fr);
  }

  .metric-explanation { grid-column: 1 / -1; }
}

@media (max-width: 600px) {
  .growth-header,
  .overall-strip,
  .dimension-detail {
    padding-right: 20px;
    padding-left: 20px;
  }

  .growth-header { flex-direction: column; }
  .score-journey { grid-template-columns: auto 1fr auto; }
  .score-journey strong { font-size: 25px; }
  .dimension-tabs { grid-template-columns: 1fr; }
  .dimension-tabs button {
    grid-template-columns: 1fr auto;
    border-right: 0;
  }

  .metric-row { grid-template-columns: 1fr; }
  .metric-explanation { grid-column: auto; }
  .evidence-row { grid-template-columns: 10px 1fr; }
  .evidence-row time { grid-column: 2; }
}

@media (prefers-reduced-motion: reduce) {
  .loading-ring { animation: none; }
  .dimension-tabs button { transition: none; }
}
</style>
