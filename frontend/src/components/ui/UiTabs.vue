<script setup lang="ts">
import { TabGroup, TabList, Tab, TabPanels, TabPanel } from '@headlessui/vue'
import { cn } from '@/lib/utils'

defineProps<{
  defaultIndex?: number
  class?: string
}>()
</script>

<template>
  <TabGroup :default-index="defaultIndex || 0">
    <slot />
  </TabGroup>
</template>
