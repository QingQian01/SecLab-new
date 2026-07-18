<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import {
  createTeachingClassIntervention,
  getApiErrorMessage,
  refreshTeachingClassIntervention,
  type KnowledgeRiskItemDto,
  type TeacherInterventionActionType,
  type TeacherInterventionDto,
  type TeachingClassStudentDto,
} from '../../../../api'

const props = defineProps<{
  classId: number
  students: TeachingClassStudentDto[]
  selectedRisk: KnowledgeRiskItemDto | null
  interventions: TeacherInterventionDto[]
}>()
const emit = defineEmits<{ changed: [] }>()

const actionType = ref<TeacherInterventionActionType>('FOCUS_GROUP')
const title = ref('')
const description = ref('')
const selectedStudentIds = ref<number[]>([])
const creating = ref(false)
const refreshingId = ref<number | null>(null)
const message = ref('')
const error = ref('')

watch(() => props.selectedRisk, (risk) => {
  if (!risk) return
  title.value = `${risk.knowledgePointName}专项辅导`
  description.value = `${risk.incorrectStudentCount}名学生在${risk.knowledgePointName}上出现错误，安排专项练习并在一周后复盘。`
  selectedStudentIds.value = risk.affectedStudents.map((item) => Number(item.studentId)).filter(Boolean)
}, { immediate: true })

const selectedCount = computed(() => selectedStudentIds.value.length)

async function createAction() {
  if (!title.value.trim() || !selectedStudentIds.value.length) {
    error.value = '请填写行动名称并至少选择一名学生。'
    return
  }
  creating.value = true
  error.value = ''
  message.value = ''
  try {
    await createTeachingClassIntervention(props.classId, {
      title: title.value.trim(),
      actionType: actionType.value,
      studentIds: selectedStudentIds.value,
      knowledgePointId: props.selectedRisk?.knowledgePointId,
      description: description.value.trim(),
      questionIds: props.selectedRisk?.representativeQuestions.map((item) => item.generatedQuestionId) || [],
    })
    message.value = '教学行动已创建，并已同步到相关学生的画像页。'
    emit('changed')
  } catch (cause) {
    error.value = getApiErrorMessage(cause, '教学行动创建失败，请稍后重试。')
  } finally {
    creating.value = false
  }
}

async function refreshAction(item: TeacherInterventionDto) {
  refreshingId.value = item.interventionId
  error.value = ''
  try {
    await refreshTeachingClassIntervention(props.classId, item.interventionId)
    message.value = '已更新训练完成情况和干预前后变化。'
    emit('changed')
  } catch (cause) {
    error.value = getApiErrorMessage(cause, '教学行动进度更新失败。')
  } finally {
    refreshingId.value = null
  }
}
</script>

<template>
  <section class="action-block">
    <div class="section-heading"><div><h2>从分析进入教学行动</h2><p>创建重点辅导小组或沉淀为下节课案例，并保留后续效果对照。专项练习请在知识点详情中审核例题后下发。</p></div></div>
    <div class="action-layout">
      <form class="action-form" @submit.prevent="createAction">
        <label>行动类型<select v-model="actionType"><option value="FOCUS_GROUP">创建重点辅导小组</option><option value="LESSON_EXAMPLE">加入下节课典型案例</option></select></label>
        <label>行动名称<input v-model="title" placeholder="例如：SQL盲注专项辅导" /></label>
        <label>教学说明<textarea v-model="description" rows="3" placeholder="说明需要关注的问题和预期结果"></textarea></label>
        <fieldset><legend>参与学生（已选 {{ selectedCount }} 人）</legend><div class="student-checks"><label v-for="student in students" :key="student.studentId"><input v-model="selectedStudentIds" type="checkbox" :value="student.studentId" /><span>{{ student.studentName || student.studentNumber }}</span></label></div></fieldset>
        <div v-if="error" class="form-message error">{{ error }}</div><div v-if="message" class="form-message success">{{ message }}</div>
        <button class="primary-button" type="submit" :disabled="creating">{{ creating ? '正在创建…' : '创建教学行动' }}</button>
      </form>
      <div class="action-history">
        <h3>行动追踪</h3>
        <article v-for="item in interventions" :key="item.interventionId">
          <div><strong>{{ item.title }}</strong><span>{{ item.status === 'ACTIVE' ? '进行中' : item.status === 'COMPLETED' ? '已完成' : '已取消' }}</span></div>
          <p>{{ item.description || '未填写教学说明' }}</p>
          <div class="progress-row"><span>{{ item.progress.completedCount }}/{{ item.progress.studentCount }} 人完成</span><progress :value="item.progress.completionRate" max="1"></progress><button type="button" :disabled="refreshingId === item.interventionId" @click="refreshAction(item)">{{ refreshingId === item.interventionId ? '更新中…' : '更新对照' }}</button></div>
          <small>对照时间：{{ new Date(item.dueAt).toLocaleDateString('zh-CN') }}；届时自动比较能力分数和错题表现。</small>
        </article>
        <div v-if="!interventions.length" class="empty-inline">还没有教学行动。点击上方饼图中的知识点，可查看证据并带入相关学生。</div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.section-heading{margin-bottom:14px}h2,h3{margin:0;color:#1d2d47;font-size:16px}.section-heading p{margin:5px 0 0;color:#75839a;font-size:12px}.action-layout{display:grid;grid-template-columns:minmax(320px,.9fr) minmax(360px,1.1fr);gap:16px}.action-form,.action-history{padding:16px;border:1px solid #e3e9f0;border-radius:8px;background:#fbfcfe}.action-form{display:grid;gap:12px}.action-form>label{display:grid;gap:5px;color:#526177;font-size:11px}.action-form input,.action-form select,.action-form textarea{width:100%;padding:9px 10px;border:1px solid #d7e0ea;border-radius:6px;background:#fff;color:#26364d;font-size:12px}.action-form textarea{resize:vertical}.action-form fieldset{margin:0;padding:10px;border:1px solid #dde5ee;border-radius:6px}.action-form legend{padding:0 5px;color:#526177;font-size:11px}.student-checks{display:grid;grid-template-columns:repeat(3,1fr);gap:7px;max-height:128px;overflow:auto}.student-checks label{display:flex;align-items:center;gap:5px;color:#536278;font-size:10px}.student-checks input{width:auto}.primary-button{justify-self:start}.action-history{display:grid;align-content:start;gap:10px}.action-history>h3{margin-bottom:2px}.action-history article{padding:12px;border:1px solid #e2e8ef;border-radius:7px;background:#fff}.action-history article>div:first-child{display:flex;justify-content:space-between;gap:10px}.action-history strong{color:#2c3c53;font-size:12px}.action-history article>div:first-child span{padding:2px 6px;border-radius:999px;background:#edf4fd;color:#32639f;font-size:9px}.action-history p{margin:6px 0;color:#6b788c;font-size:10px;line-height:1.5}.action-history small{display:block;margin-top:7px;color:#8a96a6;font-size:9px}.progress-row{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:8px;color:#66748a;font-size:10px}.progress-row progress{width:100%;height:6px}.progress-row button{border:0;background:none;color:#2362ad;font-size:10px;cursor:pointer}.form-message{padding:8px;border-radius:5px;font-size:10px}.form-message.error{background:#fff0ed;color:#a94838}.form-message.success{background:#edf8f2;color:#2f7552}.empty-inline{padding:28px;color:#8b96a6;font-size:11px;text-align:center}
@media(max-width:1000px){.action-layout{grid-template-columns:1fr}}@media(max-width:650px){.student-checks{grid-template-columns:repeat(2,1fr)}}
</style>
