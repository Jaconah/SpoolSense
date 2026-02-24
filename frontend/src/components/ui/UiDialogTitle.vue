<script setup lang="ts">
import { DialogTitle } from '@headlessui/vue'
import { cn } from '@/lib/utils'
import { computed } from 'vue'

const props = defineProps<{ class?: string }>()
const classes = computed(() => cn('text-lg font-semibold leading-none tracking-tight', props.class))
</script>

<template>
  <DialogTitle :class="classes"><slot /></DialogTitle>
</template>
