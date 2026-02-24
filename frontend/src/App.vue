<script setup lang="ts">
import { provideTheme } from '@/composables/use-theme'

provideTheme('dark')
</script>

<template>
  <RouterView />
</template>
