<script setup lang="ts">
import { Tab } from '@headlessui/vue'
import { cn } from '@/lib/utils'

defineProps<{ class?: string }>()
</script>

<template>
  <Tab v-slot="{ selected }" as="template">
    <button
      :class="cn(
        'inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
        selected && 'bg-background text-foreground shadow-xs',
        $props.class
      )"
    >
      <slot />
    </button>
  </Tab>
</template>
