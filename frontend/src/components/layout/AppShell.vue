<script setup lang="ts">
import { ref, onMounted, provide } from 'vue'
import SideBar from './SideBar.vue'
import WhatsNewDialog from '@/components/WhatsNewDialog.vue'
import OnboardingWizard from '@/components/OnboardingWizard.vue'
import { useSettings } from '@/composables/use-data'
import { api } from '@/lib/api'
import { APP_VERSION } from '@/lib/changelog'

const whatsNewOpen = ref(false)
const onboardingOpen = ref(false)
const { data: settings, refresh: refreshSettings } = useSettings()

onMounted(async () => {
  await new Promise(r => setTimeout(r, 500))
  if (settings.value && settings.value.last_seen_version !== APP_VERSION) {
    whatsNewOpen.value = true
  }
})

async function handleWhatsNewClose() {
  whatsNewOpen.value = false
  try {
    await api.patch('/settings', { last_seen_version: APP_VERSION })
    refreshSettings()
  } catch {
    // Non-critical
  }
}

provide('openWhatsNew', () => { whatsNewOpen.value = true })
provide('openOnboarding', () => { onboardingOpen.value = true })
</script>

<template>
  <div class="flex h-screen overflow-hidden">
    <SideBar />
    <main class="flex-1 overflow-y-auto pt-14 md:pt-0">
      <div class="container mx-auto max-w-7xl px-3 py-4 sm:px-4 sm:py-5 md:px-6 md:py-6">
        <RouterView />
      </div>
    </main>
    <WhatsNewDialog :open="whatsNewOpen" @update:open="!$event && handleWhatsNewClose()" />
    <OnboardingWizard :open="onboardingOpen" @update:open="onboardingOpen = $event" />
  </div>
</template>
