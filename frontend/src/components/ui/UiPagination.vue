<script setup lang="ts">
import { computed } from 'vue'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { cn } from '@/lib/utils'

const props = defineProps<{
  modelValue: number
  total: number
  perPage: number
}>()

const emit = defineEmits<{
  'update:modelValue': [page: number]
}>()

const pages = computed(() => Math.max(1, Math.ceil(props.total / props.perPage)))

const startItem = computed(() => props.total === 0 ? 0 : (props.modelValue - 1) * props.perPage + 1)
const endItem = computed(() => Math.min(props.modelValue * props.perPage, props.total))

// Generate visible page numbers (max 5, with ellipsis markers)
const visiblePages = computed<(number | '...')[]>(() => {
  const total = pages.value
  const current = props.modelValue
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }
  const result: (number | '...')[] = [1]
  if (current > 3) result.push('...')
  const start = Math.max(2, current - 1)
  const end = Math.min(total - 1, current + 1)
  for (let i = start; i <= end; i++) result.push(i)
  if (current < total - 2) result.push('...')
  result.push(total)
  return result
})

function goTo(page: number) {
  if (page < 1 || page > pages.value || page === props.modelValue) return
  emit('update:modelValue', page)
}

const btnBase = 'inline-flex items-center justify-center h-8 w-8 rounded-md text-sm font-medium transition-colors focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50'
</script>

<template>
  <div v-if="total > 0" class="flex flex-col items-center gap-2 sm:flex-row sm:items-center sm:justify-between">
    <p class="text-sm text-muted-foreground">
      Showing <span class="font-medium">{{ startItem }}</span>–<span class="font-medium">{{ endItem }}</span>
      of <span class="font-medium">{{ total }}</span>
    </p>
    <div class="flex items-center gap-1">
      <button
        :class="cn(btnBase, 'border border-input bg-background hover:bg-accent hover:text-accent-foreground')"
        :disabled="modelValue <= 1"
        @click="goTo(modelValue - 1)"
        aria-label="Previous page"
      >
        <ChevronLeft class="h-4 w-4" />
      </button>

      <template v-for="(p, idx) in visiblePages" :key="idx">
        <span
          v-if="p === '...'"
          class="inline-flex h-8 w-8 items-center justify-center text-sm text-muted-foreground"
        >…</span>
        <button
          v-else
          :class="cn(
            btnBase,
            p === modelValue
              ? 'bg-primary text-primary-foreground hover:bg-primary/90'
              : 'border border-input bg-background hover:bg-accent hover:text-accent-foreground'
          )"
          @click="goTo(p)"
          :aria-label="`Page ${p}`"
          :aria-current="p === modelValue ? 'page' : undefined"
        >
          {{ p }}
        </button>
      </template>

      <button
        :class="cn(btnBase, 'border border-input bg-background hover:bg-accent hover:text-accent-foreground')"
        :disabled="modelValue >= pages"
        @click="goTo(modelValue + 1)"
        aria-label="Next page"
      >
        <ChevronRight class="h-4 w-4" />
      </button>
    </div>
  </div>
</template>
