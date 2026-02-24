<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

interface Props {
  content: string
  side?: 'top' | 'bottom' | 'left' | 'right'
  maxWidth?: string
}

const props = withDefaults(defineProps<Props>(), {
  side: 'top',
  maxWidth: 'max-w-xs'
})

const isVisible = ref(false)
const tooltipRef = ref<HTMLElement | null>(null)
const triggerRef = ref<HTMLElement | null>(null)
const timeoutId = ref<number | null>(null)
const actualSide = ref(props.side)

const tooltipStyles = ref({
  top: '0px',
  left: '0px'
})

// Calculate position based on trigger element and desired side
const calculatePosition = () => {
  if (!triggerRef.value || !tooltipRef.value) return

  const trigger = triggerRef.value.getBoundingClientRect()
  const tooltip = tooltipRef.value.getBoundingClientRect()
  const spacing = 8 // Gap between trigger and tooltip

  let top = 0
  let left = 0
  let side = props.side

  // Calculate initial position based on requested side
  switch (props.side) {
    case 'top':
      top = trigger.top - tooltip.height - spacing
      left = trigger.left + (trigger.width - tooltip.width) / 2
      break
    case 'bottom':
      top = trigger.bottom + spacing
      left = trigger.left + (trigger.width - tooltip.width) / 2
      break
    case 'left':
      top = trigger.top + (trigger.height - tooltip.height) / 2
      left = trigger.left - tooltip.width - spacing
      break
    case 'right':
      top = trigger.top + (trigger.height - tooltip.height) / 2
      left = trigger.right + spacing
      break
  }

  // Auto-adjust if near viewport edges
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight

  // Check horizontal overflow
  if (left < spacing) {
    left = spacing
  } else if (left + tooltip.width > viewportWidth - spacing) {
    left = viewportWidth - tooltip.width - spacing
  }

  // Check vertical overflow - flip if needed
  if (top < spacing && (props.side === 'top' || props.side === 'bottom')) {
    // Flip to opposite vertical side
    if (props.side === 'top') {
      top = trigger.bottom + spacing
      side = 'bottom'
    } else {
      top = trigger.top - tooltip.height - spacing
      side = 'top'
    }
  } else if (top + tooltip.height > viewportHeight - spacing && (props.side === 'top' || props.side === 'bottom')) {
    // Flip to opposite vertical side
    if (props.side === 'bottom') {
      top = trigger.top - tooltip.height - spacing
      side = 'top'
    } else {
      top = trigger.bottom + spacing
      side = 'bottom'
    }
  }

  actualSide.value = side
  tooltipStyles.value = {
    top: `${top + window.scrollY}px`,
    left: `${left + window.scrollX}px`
  }
}

const showTooltip = () => {
  if (timeoutId.value) {
    clearTimeout(timeoutId.value)
  }
  timeoutId.value = window.setTimeout(() => {
    isVisible.value = true
    // Wait for next tick to ensure tooltip is rendered before calculating position
    setTimeout(() => {
      calculatePosition()
    }, 0)
  }, 100)
}

const hideTooltip = () => {
  if (timeoutId.value) {
    clearTimeout(timeoutId.value)
    timeoutId.value = null
  }
  isVisible.value = false
}

// Touch handling (tap outside to dismiss)
const handleTouchOutside = (event: TouchEvent) => {
  if (isVisible.value &&
      tooltipRef.value &&
      !tooltipRef.value.contains(event.target as Node) &&
      triggerRef.value &&
      !triggerRef.value.contains(event.target as Node)) {
    hideTooltip()
  }
}

const handleTriggerTouch = (event: TouchEvent) => {
  event.preventDefault()
  if (isVisible.value) {
    hideTooltip()
  } else {
    showTooltip()
  }
}

// Keyboard handling
const handleTriggerFocus = () => {
  showTooltip()
}

const handleTriggerBlur = () => {
  hideTooltip()
}

// Recalculate on window resize
const handleResize = () => {
  if (isVisible.value) {
    calculatePosition()
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  document.addEventListener('touchstart', handleTouchOutside)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  document.removeEventListener('touchstart', handleTouchOutside)
  if (timeoutId.value) {
    clearTimeout(timeoutId.value)
  }
})

// Arrow position classes based on actual side after auto-positioning
const arrowClasses = computed(() => {
  const base = 'absolute w-2 h-2 bg-popover border transform rotate-45'
  switch (actualSide.value) {
    case 'top':
      return `${base} bottom-[-5px] left-1/2 -translate-x-1/2 border-r border-b border-l-0 border-t-0`
    case 'bottom':
      return `${base} top-[-5px] left-1/2 -translate-x-1/2 border-l border-t border-r-0 border-b-0`
    case 'left':
      return `${base} right-[-5px] top-1/2 -translate-y-1/2 border-t border-r border-l-0 border-b-0`
    case 'right':
      return `${base} left-[-5px] top-1/2 -translate-y-1/2 border-b border-l border-r-0 border-t-0`
    default:
      return base
  }
})
</script>

<template>
  <div class="relative inline-block">
    <!-- Trigger slot -->
    <div
      ref="triggerRef"
      @mouseenter="showTooltip"
      @mouseleave="hideTooltip"
      @focus="handleTriggerFocus"
      @blur="handleTriggerBlur"
      @touchstart="handleTriggerTouch"
      tabindex="0"
      class="cursor-help focus:outline-hidden focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded-sm"
    >
      <slot />
    </div>

    <!-- Tooltip portal -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition-all duration-200 ease-out"
        enter-from-class="opacity-0 scale-95"
        enter-to-class="opacity-100 scale-100"
        leave-active-class="transition-all duration-150 ease-in"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-95"
      >
        <div
          v-if="isVisible"
          ref="tooltipRef"
          :class="[
            'absolute z-50 px-3 py-2 text-sm bg-popover text-popover-foreground border border-border shadow-md rounded-md',
            maxWidth
          ]"
          :style="tooltipStyles"
          role="tooltip"
        >
          <!-- Arrow -->
          <div :class="arrowClasses"></div>

          <!-- Content -->
          <div class="relative z-10">
            {{ content }}
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
/* Ensure smooth animations */
.transition-all {
  transition-property: all;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}
</style>
