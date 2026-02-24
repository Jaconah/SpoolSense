<script setup lang="ts">
import { cn } from '@/lib/utils'
import { computed } from 'vue'

const props = defineProps<{ class?: string }>()
const classes = computed(() => cn('rounded-lg border bg-card text-card-foreground shadow-xs', props.class))
</script>

<template>
  <div :class="classes"><slot /></div>
</template>
