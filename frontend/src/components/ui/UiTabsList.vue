<script setup lang="ts">
import { TabList } from '@headlessui/vue'
import { cn } from '@/lib/utils'
import { computed } from 'vue'

const props = defineProps<{ class?: string }>()
const classes = computed(() => cn(
  'inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground',
  props.class
))
</script>

<template>
  <TabList :class="classes"><slot /></TabList>
</template>
