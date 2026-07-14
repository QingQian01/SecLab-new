<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { uploadImageFile } from '../../../api'
import type { RegisterForm } from '../../../types/auth'

defineProps<{
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'register', form: RegisterForm): void
}>()

const academyClassMap: Record<string, string[]> = {
  '网络空间安全学院': ['网安231班', '网安232班', '网安233班'],
  '计算机科学与技术学院': ['计科231班', '计科232班', '计科233班'],
  '软件工程学院': ['软件231班', '软件232班', '软件233班'],
  '人工智能学院': ['人工智能231班', '人工智能232班', '人工智能233班'],
}

const defaultAcademy = '网络空间安全学院'
const defaultClass = academyClassMap[defaultAcademy][1]

const registerForm = ref<RegisterForm>({
  userStudentNumber: '',
  userPassword: '',
  userName: '',
  userEmail: '',
  userTel: '',
  userGender: 1,
  userAcademy: defaultAcademy,
  userClass: defaultClass,
  userImage: '',
})

const confirmPassword = ref('')
const avatarFile = ref<File | null>(null)
const avatarPreview = ref('')
const avatarError = ref('')
const isUploadingAvatar = ref(false)

const errors = reactive({
  userStudentNumber: '',
  userPassword: '',
  confirmPassword: '',
  userName: '',
  userEmail: '',
  userTel: '',
})

const academyOptions = Object.keys(academyClassMap)
const availableClasses = computed(() => academyClassMap[registerForm.value.userAcademy || defaultAcademy] || academyClassMap[defaultAcademy])

watch(
  () => registerForm.value.userAcademy,
  (academy) => {
    const classes = academyClassMap[academy || defaultAcademy] || academyClassMap[defaultAcademy]
    if (!classes.includes(registerForm.value.userClass || '')) {
      registerForm.value.userClass = classes[0]
    }
  },
  { immediate: true },
)

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const handleAvatarChange = (event: Event) => {
  avatarError.value = ''
  const input = event.target as HTMLInputElement
  const file = input.files?.[0] || null

  if (!file) {
    avatarFile.value = null
    avatarPreview.value = ''
    registerForm.value.userImage = ''
    return
  }

  if (!file.type.startsWith('image/')) {
    avatarError.value = '请选择图片文件。'
    input.value = ''
    return
  }

  if (file.size > 2 * 1024 * 1024) {
    avatarError.value = '头像图片不能超过 2MB。'
    input.value = ''
    return
  }

  avatarFile.value = file
  avatarPreview.value = URL.createObjectURL(file)
  registerForm.value.userImage = ''
}

const clearAvatar = () => {
  avatarFile.value = null
  avatarPreview.value = ''
  avatarError.value = ''
  registerForm.value.userImage = ''
}

const handleSubmit = async () => {
  errors.userStudentNumber = ''
  errors.userPassword = ''
  errors.confirmPassword = ''
  errors.userName = ''
  errors.userEmail = ''
  errors.userTel = ''

  const studentNumber = registerForm.value.userStudentNumber.trim()
  const userName = registerForm.value.userName.trim()
  const userEmail = registerForm.value.userEmail.trim()
  const userTel = registerForm.value.userTel?.trim() || ''

  if (!userName) {
    errors.userName = '请输入姓名。'
  }
  if (!studentNumber) {
    errors.userStudentNumber = '请输入学号。'
  } else if (studentNumber.length > 13) {
    errors.userStudentNumber = '学号不能超过 13 个字符。'
  }
  if (!userEmail) {
    errors.userEmail = '请输入邮箱。'
  } else if (!emailPattern.test(userEmail)) {
    errors.userEmail = '请输入有效的邮箱地址。'
  }
  if (userTel && (!/^\d+$/.test(userTel) || userTel.length > 11)) {
    errors.userTel = '手机号需为不超过 11 位的数字。'
  }
  if (!registerForm.value.userPassword) {
    errors.userPassword = '请输入密码。'
  } else if (registerForm.value.userPassword.length < 6) {
    errors.userPassword = '密码至少需要 6 个字符。'
  }
  if (confirmPassword.value !== registerForm.value.userPassword) {
    errors.confirmPassword = '两次输入的密码不一致。'
  }

  if (Object.values(errors).some(Boolean)) {
    return
  }

  if (avatarFile.value) {
    try {
      isUploadingAvatar.value = true
      const uploadResult = await uploadImageFile(avatarFile.value)
      const uploadedUrl = uploadResult.url || uploadResult.filename || ''
      if (!uploadedUrl) {
        avatarError.value = '头像上传失败，请重新选择图片。'
        return
      }
      registerForm.value.userImage = uploadedUrl
    } catch (error) {
      console.error('头像上传失败:', error)
      avatarError.value = '头像上传失败，请稍后重试。'
      return
    } finally {
      isUploadingAvatar.value = false
    }
  }

  emit('register', {
    ...registerForm.value,
    userStudentNumber: studentNumber,
    userName,
    userEmail,
    userTel,
  })
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="space-y-5">
    <div class="form-control">
      <label class="label">
        <span class="label-text font-medium">头像</span>
        <span class="label-text-alt text-base-content/50">可选</span>
      </label>
      <div class="flex items-center gap-4">
        <div class="w-16 h-16 rounded-full border border-base-300 bg-base-200 flex items-center justify-center overflow-hidden">
          <img
            v-if="avatarPreview"
            :src="avatarPreview"
            alt="头像预览"
            class="w-full h-full object-cover"
          />
          <i v-else class="fas fa-user text-2xl text-base-content/30"></i>
        </div>
        <div class="flex-1">
          <input
            type="file"
            accept="image/*"
            class="file-input file-input-bordered file-input-sm w-full"
            @change="handleAvatarChange"
          />
          <div class="mt-2 flex items-center gap-2">
            <button
              v-if="avatarPreview"
              type="button"
              class="btn btn-xs btn-ghost"
              @click="clearAvatar"
            >
              清除头像
            </button>
            <span class="text-xs text-base-content/50">未上传时头像保持空白</span>
          </div>
        </div>
      </div>
      <label v-if="avatarError" class="label">
        <span class="label-text-alt text-error">{{ avatarError }}</span>
      </label>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="form-control">
        <label class="label">
          <span class="label-text font-medium">姓名</span>
        </label>
        <input
          v-model="registerForm.userName"
          type="text"
          placeholder="请输入姓名"
          class="input input-bordered bg-base-200/60 focus:bg-base-100"
          :class="{ 'input-error': errors.userName }"
        />
        <label v-if="errors.userName" class="label">
          <span class="label-text-alt text-error">{{ errors.userName }}</span>
        </label>
      </div>

      <div class="form-control">
        <label class="label">
          <span class="label-text font-medium">学号</span>
        </label>
        <input
          v-model="registerForm.userStudentNumber"
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
          <span class="label-text font-medium">邮箱</span>
        </label>
        <input
          v-model="registerForm.userEmail"
          type="email"
          placeholder="请输入邮箱"
          class="input input-bordered bg-base-200/60 focus:bg-base-100"
          :class="{ 'input-error': errors.userEmail }"
        />
        <label v-if="errors.userEmail" class="label">
          <span class="label-text-alt text-error">{{ errors.userEmail }}</span>
        </label>
      </div>

      <div class="form-control">
        <label class="label">
          <span class="label-text font-medium">手机号</span>
        </label>
        <input
          v-model="registerForm.userTel"
          type="tel"
          maxlength="11"
          placeholder="可选，请输入手机号"
          class="input input-bordered bg-base-200/60 focus:bg-base-100"
          :class="{ 'input-error': errors.userTel }"
        />
        <label v-if="errors.userTel" class="label">
          <span class="label-text-alt text-error">{{ errors.userTel }}</span>
        </label>
      </div>

      <div class="form-control">
        <label class="label">
          <span class="label-text font-medium">学院</span>
        </label>
        <select
          v-model="registerForm.userAcademy"
          class="select select-bordered bg-base-200/60 focus:bg-base-100"
        >
          <option
            v-for="academy in academyOptions"
            :key="academy"
            :value="academy"
          >
            {{ academy }}
          </option>
        </select>
      </div>

      <div class="form-control">
        <label class="label">
          <span class="label-text font-medium">班级</span>
        </label>
        <select
          v-model="registerForm.userClass"
          class="select select-bordered bg-base-200/60 focus:bg-base-100"
        >
          <option
            v-for="className in availableClasses"
            :key="className"
            :value="className"
          >
            {{ className }}
          </option>
        </select>
      </div>

      <div class="form-control">
        <label class="label">
          <span class="label-text font-medium">性别</span>
        </label>
        <select
          v-model="registerForm.userGender"
          class="select select-bordered bg-base-200/60 focus:bg-base-100"
        >
          <option :value="1">男</option>
          <option :value="0">女</option>
          <option :value="2">暂不填写</option>
        </select>
      </div>

      <div class="form-control">
        <label class="label">
          <span class="label-text font-medium">密码</span>
        </label>
        <input
          v-model="registerForm.userPassword"
          type="password"
          placeholder="至少 6 个字符"
          class="input input-bordered bg-base-200/60 focus:bg-base-100"
          :class="{ 'input-error': errors.userPassword }"
        />
        <label v-if="errors.userPassword" class="label">
          <span class="label-text-alt text-error">{{ errors.userPassword }}</span>
        </label>
      </div>

      <div class="form-control">
        <label class="label">
          <span class="label-text font-medium">确认密码</span>
        </label>
        <input
          v-model="confirmPassword"
          type="password"
          placeholder="请再次输入密码"
          class="input input-bordered bg-base-200/60 focus:bg-base-100"
          :class="{ 'input-error': errors.confirmPassword }"
        />
        <label v-if="errors.confirmPassword" class="label">
          <span class="label-text-alt text-error">{{ errors.confirmPassword }}</span>
        </label>
      </div>
    </div>

    <button
      type="submit"
      class="btn btn-primary w-full"
      :disabled="loading || isUploadingAvatar"
    >
      <span v-if="loading || isUploadingAvatar" class="loading loading-spinner loading-sm"></span>
      <i v-else class="fas fa-user-plus mr-2"></i>
      {{ isUploadingAvatar ? '上传头像中...' : loading ? '注册中...' : '注册' }}
    </button>
  </form>
</template>
