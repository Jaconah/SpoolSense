<script setup lang="ts">
import { cn } from '@/lib/utils'
import { computed } from 'vue'

const props = defineProps<{ class?: string }>()
const classes = computed(() => cn('flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2', props.class))
</script>

<template>
  <div :class="classes"><slot /></div>
</template>
