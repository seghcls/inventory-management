import { ref } from 'vue'

// Shared sidebar state (singleton pattern, mirrors useFilters.js)
const collapsed = ref(false)
const isSmallScreen = ref(false)

// Remembers the user's manually-chosen collapsed state while at a
// large (non-forced) viewport width, so we can restore it when the
// viewport grows back past the breakpoint.
let userPreference = false

export function useSidebar() {
  // Manual toggle - always available, at any width
  const toggleCollapsed = () => {
    collapsed.value = !collapsed.value
    if (!isSmallScreen.value) {
      userPreference = collapsed.value
    }
  }

  // Called from Sidebar.vue's matchMedia listener (onMounted/onUnmounted)
  const applyBreakpoint = (matches) => {
    isSmallScreen.value = matches
    // Below the breakpoint, force icon-only collapse. Above it, restore
    // whatever the user last chose while at a large width.
    collapsed.value = matches ? true : userPreference
  }

  return {
    collapsed,
    isSmallScreen,
    toggleCollapsed,
    applyBreakpoint
  }
}
