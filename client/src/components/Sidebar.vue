<template>
  <div class="sidebar" :class="{ collapsed: collapsed, overlay: isSmallScreen }">
    <div
      v-if="isSmallScreen && !collapsed"
      class="sidebar-backdrop"
      @click="toggleCollapsed"
    ></div>

    <div class="sidebar-inner">
      <div class="sidebar-header">
        <div v-if="!collapsed" class="brand">
          <h1>{{ t('nav.companyName') }}</h1>
          <span class="subtitle">{{ t('nav.subtitle') }}</span>
        </div>
        <div v-else class="brand-condensed" :title="t('nav.companyName')">
          {{ brandInitials }}
        </div>

        <button
          type="button"
          class="collapse-toggle"
          :aria-label="collapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
          :title="collapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
          @click="toggleCollapsed"
        >
          <PanelLeftOpen v-if="collapsed" :size="18" />
          <PanelLeftClose v-else :size="18" />
        </button>
      </div>

      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          :class="{ active: $route.path === item.to }"
          :title="collapsed ? item.label : null"
          :aria-label="item.label"
        >
          <component :is="item.icon" :size="20" />
          <span v-if="!collapsed" class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <LanguageSwitcher :collapsed="collapsed" />
        <ProfileMenu
          :collapsed="collapsed"
          @show-profile-details="$emit('show-profile-details')"
          @show-tasks="$emit('show-tasks')"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import {
  LayoutDashboard,
  Package,
  ShoppingCart,
  Wallet,
  TrendingUp,
  PackagePlus,
  FileText,
  PanelLeftClose,
  PanelLeftOpen
} from '@lucide/vue'
import { useI18n } from '../composables/useI18n'
import { useSidebar } from '../composables/useSidebar'
import LanguageSwitcher from './LanguageSwitcher.vue'
import ProfileMenu from './ProfileMenu.vue'

defineEmits(['show-profile-details', 'show-tasks'])

const { t } = useI18n()
const { collapsed, isSmallScreen, toggleCollapsed, applyBreakpoint } = useSidebar()

const SMALL_SCREEN_QUERY = '(max-width: 1024px)'
let mediaQuery = null

const handleMediaChange = (event) => applyBreakpoint(event.matches)

onMounted(() => {
  mediaQuery = window.matchMedia(SMALL_SCREEN_QUERY)
  applyBreakpoint(mediaQuery.matches)
  mediaQuery.addEventListener('change', handleMediaChange)
})

onUnmounted(() => {
  if (mediaQuery) {
    mediaQuery.removeEventListener('change', handleMediaChange)
  }
})

const brandInitials = computed(() => {
  const name = t('nav.companyName')
  return name
    .split(' ')
    .map((word) => word[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
})

const navItems = computed(() => [
  { to: '/', label: t('nav.overview'), icon: LayoutDashboard },
  { to: '/inventory', label: t('nav.inventory'), icon: Package },
  { to: '/orders', label: t('nav.orders'), icon: ShoppingCart },
  { to: '/spending', label: t('nav.finance'), icon: Wallet },
  { to: '/demand', label: t('nav.demandForecast'), icon: TrendingUp },
  { to: '/restocking', label: t('nav.restocking'), icon: PackagePlus },
  { to: '/reports', label: 'Reports', icon: FileText }
])
</script>

<style scoped>
.sidebar {
  position: sticky;
  top: 0;
  align-self: flex-start;
  width: 240px;
  height: 100vh;
  flex-shrink: 0;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  transition: width 0.2s ease;
  z-index: 100;
}

.sidebar.collapsed {
  width: 72px;
}

.sidebar.overlay {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  height: 100vh;
}

.sidebar.overlay:not(.collapsed) {
  box-shadow: 4px 0 16px rgba(0, 0, 0, 0.15);
}

.sidebar-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 23, 42, 0.35);
  z-index: -1;
}

.sidebar-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow-y: auto;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 1rem;
  height: 70px;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.sidebar.collapsed .sidebar-header {
  flex-direction: column;
  justify-content: center;
  height: auto;
  padding: 0.75rem 0.5rem;
}

.brand {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
  min-width: 0;
  overflow: hidden;
}

.brand h1 {
  font-size: 1.0625rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
  white-space: nowrap;
}

.brand .subtitle {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 400;
  white-space: nowrap;
}

.brand-condensed {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: #eff6ff;
  color: #2563eb;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.75rem;
  flex-shrink: 0;
}

.collapse-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  background: none;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s ease;
}

.collapse-toggle:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.75rem;
  flex: 1;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  color: #64748b;
  text-decoration: none;
  font-weight: 500;
  font-size: 0.938rem;
  border-radius: 6px;
  border-left: 3px solid transparent;
  transition: all 0.2s ease;
}

.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 0.625rem;
}

.nav-item svg {
  flex-shrink: 0;
}

.nav-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-item:hover {
  color: #0f172a;
  background: #f1f5f9;
}

.nav-item.active {
  color: #2563eb;
  background: #eff6ff;
  border-left-color: #2563eb;
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 0.75rem;
  border-top: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.sidebar.collapsed .sidebar-footer {
  align-items: center;
}
</style>
