<script setup lang="ts">
import { reactive, ref } from 'vue'
import type { LoginForm } from '../../../types/auth'

defineProps<{
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'login', form: LoginForm): void
}>()

const loginForm = ref<LoginForm>({
  userStudentNumber: '',
  userPassword: '',
  remember: false,
})

const errors = reactive({
  userStudentNumber: '',
  userPassword: '',
})

const handleSubmit = () => {
  errors.userStudentNumber = ''
  errors.userPassword = ''

  if (!loginForm.value.userStudentNumber.trim()) {
    errors.userStudentNumber = '请输入学号。'
  }
  if (!loginForm.value.userPassword) {
    errors.userPassword = '请输入密码。'
  }

  if (errors.userStudentNumber || errors.userPassword) {
    return
  }

  emit('login', {
    ...loginForm.value,
    userStudentNumber: loginForm.value.userStudentNumber.trim(),
  })
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="space-y-5">
    <div class="form-control">
      <label class="label">
        <span class="label-text font-medium">学号</span>
      </label>
      <input
        v-model="loginForm.userStudentNumber"
        type="text"
        maxlength="13"
        placeholder="请输入学号"
        class="input input-bordered bg-base-200/60 focus:bg-base-100"
        :class="{ 'input-error': errors.userStudentNumber }"
      />
      <label v-if="errors.userStudentNumber" class="label">
        <span class="label-text-alt text-error">{{ errors.userStudentNumber }}</span>
      </label>
    </div>

    <div class="form-control">
      <label class="label">
        <span class="label-text font-medium">密码</span>
      </label>
      <input
        v-model="loginForm.userPassword"
        type="password"
        placeholder="请输入密码"
        class="input input-bordered bg-base-200/60 focus:bg-base-100"
        :class="{ 'input-error': errors.userPassword }"
      />
      <label v-if="errors.userPassword" class="label">
        <span class="label-text-alt text-error">{{ errors.userPassword }}</span>
      </label>
    </div>

    <label class="label cursor-pointer justify-start gap-3">
      <input
        v-model="loginForm.remember"
        type="checkbox"
        class="checkbox checkbox-primary checkbox-sm"
      />
      <span class="label-text">在此设备上记住我</span>
    </label>

    <button
      type="submit"
      class="btn btn-primary w-full"
      :disabled="loading"
    >
      <span v-if="loading" class="loading loading-spinner loading-sm"></span>
      <i v-else class="fas fa-sign-in-alt mr-2"></i>
      {{ loading ? '登录中...' : '登录' }}
    </button>
  </form>
</template>
