<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { clearStoredAuthSession, getStoredCurrentUser } from '../../auth'
import { useTheme, initThemeFromStorage } from '../../composables/useTheme'

const route = useRoute()
const router = useRouter()
const mobileOpen = ref(false)
const currentUser = computed(() => getStoredCurrentUser())
const { currentTheme, toggleTheme } = useTheme()

// 初始化主题（从 localStorage 恢复，与学生端保持一致）
onMounted(() => {
  initThemeFromStorage()
})

const navigation = [
  { label: '教学概览', to: '/teacher/overview', icon: 'home' },
  { label: '教学班', to: '/teacher/classes', icon: 'class' },
  { label: '教学分析', to: '/teacher/analysis', icon: 'analysis' },
  { label: '课程库', to: '/teacher/courses', icon: 'course' },
  { label: '生成题记录', to: '/teacher/generated-questions', icon: 'question' },
]

const active = (to: string) => route.path === to || route.path.startsWith(`${to}/`)
const logout = () => {
  clearStoredAuthSession()
  router.replace('/')
}
</script>

<template>
  <div class="teacher-shell">
    <button class="mobile-menu" type="button" aria-label="打开导航" @click="mobileOpen = true">
      <span></span><span></span><span></span>
    </button>
    <div v-if="mobileOpen" class="nav-backdrop" @click="mobileOpen = false"></div>
    <aside class="teacher-nav" :class="{ open: mobileOpen }">
      <div class="brand">
        <div class="brand-mark">S</div>
        <div>
          <strong>SecLab</strong>
          <span>网络安全教学平台</span>
        </div>
        <button
          type="button"
          class="theme-toggle"
          :title="currentTheme === 'night' ? '切换到亮色模式' : '切换到暗色模式'"
          :aria-label="currentTheme === 'night' ? '切换到亮色模式' : '切换到暗色模式'"
          @click="toggleTheme"
        >
          <i :class="['fas', currentTheme === 'night' ? 'fa-sun' : 'fa-moon']"></i>
        </button>
      </div>

      <div class="nav-caption">教师工作台</div>
      <nav>
        <RouterLink
          v-for="item in navigation"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          :class="{ active: active(item.to) }"
          @click="mobileOpen = false"
        >
          <svg v-if="item.icon === 'home'" viewBox="0 0 24 24"><path d="M3 11.5 12 4l9 7.5v8a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/></svg>
          <svg v-else-if="item.icon === 'class'" viewBox="0 0 24 24"><path d="M4 5h16v12H4zM8 21h8M12 17v4M7 9h4M7 12h7"/></svg>
          <svg v-else-if="item.icon === 'course'" viewBox="0 0 24 24"><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5a2.5 2.5 0 1 1 0-5H20M7 7h9"/></svg>
          <svg v-else-if="item.icon === 'analysis'" viewBox="0 0 24 24"><path d="M4 19V9M10 19V5M16 19v-7M3 19h18M16 7l3-3M19 4v4M19 4h-4"/></svg>
          <svg v-else viewBox="0 0 24 24"><path d="M5 4h14v16H5zM8 8h8M8 12h8M8 16h5"/></svg>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="nav-account">
        <div class="account-avatar">{{ (currentUser?.realName || currentUser?.username || '教').slice(0, 1) }}</div>
        <div class="account-copy">
          <strong>{{ currentUser?.realName || currentUser?.username || '教师' }}</strong>
          <span>教师账号</span>
        </div>
        <button type="button" title="退出登录" @click="logout">退出</button>
      </div>
    </aside>
    <main class="teacher-main">
      <RouterView />
    </main>
  </div>
</template>

<style>
/* 亮色模式变量（默认） */
:root {
  --teacher-ink: #14213d;
  --teacher-muted: #68758b;
  --teacher-line: #e5eaf1;
  --teacher-blue: #2563eb;
  --teacher-pale: #f5f7fa;
  --teacher-nav-bg: #ffffff;
  --teacher-nav-border: #eef1f5;
  --teacher-caption: #98a3b3;
  --teacher-item: #56647a;
  --teacher-item-hover-bg: #f4f7fb;
  --teacher-item-hover: #1e4fa1;
  --teacher-item-active-bg: #edf4ff;
  --teacher-item-active: #1e5fbf;
  --teacher-account-span: #8290a4;
  --teacher-account-avatar-bg: #e8eef8;
  --teacher-account-avatar-fg: #204b8f;
  --teacher-account-copy-span: #8b97a8;
  --teacher-logout: #7b8798;
  --teacher-mobile-border: #dbe1ea;
  --teacher-mobile-bg: #ffffff;
  --teacher-mobile-bar: #334155;
  --teacher-backdrop: rgba(15, 23, 42, .3);
  --teacher-theme-toggle-fg: #56647a;
  --teacher-theme-toggle-hover: #1e4fa1;
}

/* 夜间模式变量 */
[data-theme="night"] {
  --teacher-ink: #e2e8f0;
  --teacher-muted: #94a3b8;
  --teacher-line: #1e293b;
  --teacher-blue: #60a5fa;
  --teacher-pale: #0f172a;
  --teacher-nav-bg: #131417;
  --teacher-nav-border: #1e293b;
  --teacher-caption: #64748b;
  --teacher-item: #cbd5e1;
  --teacher-item-hover-bg: #1e293b;
  --teacher-item-hover: #60a5fa;
  --teacher-item-active-bg: #1e3a5f;
  --teacher-item-active: #93c5fd;
  --teacher-account-span: #64748b;
  --teacher-account-avatar-bg: #1e293b;
  --teacher-account-avatar-fg: #93c5fd;
  --teacher-account-copy-span: #64748b;
  --teacher-logout: #94a3b8;
  --teacher-mobile-border: #1e293b;
  --teacher-mobile-bg: #131417;
  --teacher-mobile-bar: #cbd5e1;
  --teacher-backdrop: rgba(0, 0, 0, .5);
  --teacher-theme-toggle-fg: #cbd5e1;
  --teacher-theme-toggle-hover: #60a5fa;
}

.teacher-shell {
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  background: var(--teacher-pale);
  color: var(--teacher-ink);
  transition: background-color .25s ease, color .25s ease;
}
.teacher-nav { position: fixed; inset: 0 auto 0 0; z-index: 40; display: flex; width: 238px; flex-direction: column; border-right: 1px solid var(--teacher-line); background: var(--teacher-nav-bg); transition: background-color .25s ease, border-color .25s ease; }
.brand { display: flex; align-items: center; gap: 11px; height: 82px; padding: 0 24px; border-bottom: 1px solid var(--teacher-nav-border); }
.brand-mark { display: grid; width: 34px; height: 34px; place-items: center; border-radius: 9px; color: #fff; background: #1e4fa1; font-size: 18px; font-weight: 800; }
.brand strong, .brand span { display: block; }
.brand strong { font-size: 17px; letter-spacing: .02em; }
.brand span { margin-top: 2px; color: var(--teacher-account-span); font-size: 11px; }
.theme-toggle { margin-left: auto; display: grid; width: 32px; height: 32px; place-items: center; border: 1px solid var(--teacher-line); border-radius: 8px; background: transparent; color: var(--teacher-theme-toggle-fg); cursor: pointer; transition: .16s ease; }
.theme-toggle:hover { color: var(--teacher-theme-toggle-hover); border-color: var(--teacher-blue); }
.nav-caption { padding: 28px 27px 10px; color: var(--teacher-caption); font-size: 11px; font-weight: 700; letter-spacing: .12em; }
.teacher-nav nav { padding: 0 14px; }
.nav-item { display: flex; align-items: center; gap: 13px; margin: 4px 0; padding: 12px 13px; border-radius: 8px; color: var(--teacher-item); font-size: 14px; font-weight: 600; transition: .16s ease; }
.nav-item:hover { background: var(--teacher-item-hover-bg); color: var(--teacher-item-hover); }
.nav-item.active { background: var(--teacher-item-active-bg); color: var(--teacher-item-active); }
.nav-item svg { width: 19px; height: 19px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.nav-account { display: flex; align-items: center; gap: 10px; margin-top: auto; padding: 18px 16px; border-top: 1px solid var(--teacher-line); }
.account-avatar { display: grid; width: 34px; height: 34px; flex: 0 0 auto; place-items: center; border-radius: 50%; background: var(--teacher-account-avatar-bg); color: var(--teacher-account-avatar-fg); font-weight: 700; }
.account-copy { min-width: 0; flex: 1; }
.account-copy strong, .account-copy span { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.account-copy strong { font-size: 13px; }
.account-copy span { color: var(--teacher-account-copy-span); font-size: 11px; }
.nav-account button { border: 0; background: none; color: var(--teacher-logout); font-size: 12px; cursor: pointer; }
.teacher-main {
  height: 100vh;
  height: 100dvh;
  min-height: 0;
  margin-left: 238px;
  overflow-x: hidden;
  overflow-y: auto;
}
.mobile-menu, .nav-backdrop { display: none; }

@media (max-width: 820px) {
  .teacher-nav { transform: translateX(-100%); transition: transform .2s ease; }
  .teacher-nav.open { transform: translateX(0); }
  .teacher-main { margin-left: 0; padding-top: 52px; }
  .mobile-menu { position: fixed; top: 10px; left: 12px; z-index: 35; display: grid; gap: 4px; width: 36px; height: 34px; place-content: center; border: 1px solid var(--teacher-mobile-border); border-radius: 8px; background: var(--teacher-mobile-bg); }
  .mobile-menu span { width: 17px; height: 1.5px; background: var(--teacher-mobile-bar); }
  .nav-backdrop { position: fixed; inset: 0; z-index: 39; display: block; background: var(--teacher-backdrop); }
}
</style>

<!-- 全局样式：夜间模式下覆盖教师端各页面的硬编码颜色，确保主题一致 -->
<style>
[data-theme="night"] .teacher-main {
  color-scheme: dark;
}
/* 夜间模式下，将教师端页面中常见的硬编码浅色背景/深色文字强制反转为夜间配色 */
[data-theme="night"] .teacher-main .page,
[data-theme="night"] .teacher-main .card,
[data-theme="night"] .teacher-main .panel,
[data-theme="night"] .teacher-main .detail-panel,
[data-theme="night"] .teacher-main .list-item,
[data-theme="night"] .teacher-main .stat-card,
[data-theme="night"] .teacher-main .overview-card,
[data-theme="night"] .teacher-main .class-card,
[data-theme="night"] .teacher-main .course-card,
[data-theme="night"] .teacher-main .student-row,
[data-theme="night"] .teacher-main table {
  background-color: #1e293b !important;
  color: #e2e8f0 !important;
  border-color: #334155 !important;
}
[data-theme="night"] .teacher-main h1,
[data-theme="night"] .teacher-main h2,
[data-theme="night"] .teacher-main h3,
[data-theme="night"] .teacher-main h4,
[data-theme="night"] .teacher-main .title,
[data-theme="night"] .teacher-main .heading,
[data-theme="night"] .teacher-main strong,
[data-theme="night"] .teacher-main .label {
  color: #f1f5f9 !important;
}
[data-theme="night"] .teacher-main .subtle,
[data-theme="night"] .teacher-main .muted,
[data-theme="night"] .teacher-main .hint,
[data-theme="night"] .teacher-main .description,
[data-theme="night"] .teacher-main .empty-state,
[data-theme="night"] .teacher-main span {
  color: #94a3b8 !important;
}
[data-theme="night"] .teacher-main input,
[data-theme="night"] .teacher-main textarea,
[data-theme="night"] .teacher-main select {
  background-color: #0f172a !important;
  color: #e2e8f0 !important;
  border-color: #334155 !important;
}
[data-theme="night"] .teacher-main input::placeholder,
[data-theme="night"] .teacher-main textarea::placeholder {
  color: #64748b !important;
}
[data-theme="night"] .teacher-main button {
  color: inherit;
}
[data-theme="night"] .teacher-main .primary-button,
[data-theme="night"] .teacher-main .btn-primary {
  background-color: #2563eb !important;
  color: #fff !important;
  border-color: #2563eb !important;
}
[data-theme="night"] .teacher-main .ghost-button,
[data-theme="night"] .teacher-main .btn-ghost {
  background-color: transparent !important;
  color: #cbd5e1 !important;
  border-color: #334155 !important;
}
[data-theme="night"] .teacher-main a {
  color: #60a5fa !important;
}
</style>
