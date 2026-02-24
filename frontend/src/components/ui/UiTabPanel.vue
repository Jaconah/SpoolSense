<script setup lang="ts">
import { TabPanel } from '@headlessui/vue'
import { cn } from '@/lib/utils'
import { computed } from 'vue'

const props = defineProps<{ class?: string }>()
const classes = computed(() => cn(
  'ring-offset-background focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
  props.class
))
</script>

<template>
  <TabPanel :class="classes"><slot /></TabPanel>
</template>
