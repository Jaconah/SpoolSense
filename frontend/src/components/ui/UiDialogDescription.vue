<script setup lang="ts">
import { DialogDescription } from '@headlessui/vue'
import { cn } from '@/lib/utils'
import { computed } from 'vue'

const props = defineProps<{ class?: string }>()
const classes = computed(() => cn('text-sm text-muted-foreground', props.class))
</script>

<template>
  <DialogDescription :class="classes"><slot /></DialogDescription>
</template>
