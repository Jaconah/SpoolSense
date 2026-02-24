<script setup lang="ts">
import { inject, watch } from 'vue'
import { useDashboard, useProductOnHandStats } from '@/composables/use-data'
import StatsRow from '@/components/dashboard/StatsRow.vue'
import SpoolCard from '@/components/dashboard/SpoolCard.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiCardContent from '@/components/ui/UiCardContent.vue'
import { Box, DollarSign } from 'lucide-vue-next'
import { RouterLink } from 'vue-router'

const { data, loading, error } = useDashboard()
const { data: productStats } = useProductOnHandStats()

const openOnboarding = inject<() => void>('openOnboarding')

// Auto-show wizard on first load if no spools and user hasn't dismissed it
watch(data, (d) => {
  if (d && d.spools.length === 0 && !localStorage.getItem('tour_dismissed')) {
    openOnboarding?.()
  }
}, { once: true })
</script>

<template>
  <div v-if="loading" class="p-8 text-center text-muted-foreground">Loading...</div>
  <div v-else-if="error" class="p-8 text-center text-red-500">Error: {{ error }}</div>
  <div v-else-if="data" class="space-y-6">
    <h1 class="text-3xl font-bold">Dashboard</h1>

    <StatsRow :stats="data.stats" />

    <!-- Product on Hand Stats -->
    <div v-if="productStats && productStats.total_count > 0">
      <h2 class="mb-4 text-xl font-semibold">Product on Hand</h2>
      <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <RouterLink to="/product-on-hand" class="block">
          <UiCard class="transition-colors hover:border-primary/50">
            <UiCardContent class="p-4">
              <div class="flex items-center gap-3">
                <div class="rounded-md bg-blue-500/10 p-2">
                  <Box class="h-5 w-5 text-blue-500" />
                </div>
                <div>
                  <p class="text-sm text-muted-foreground">Products Ready</p>
                  <p class="text-2xl font-bold">{{ productStats.total_count }}</p>
                  <p class="text-xs text-muted-foreground">ready to sell</p>
                </div>
              </div>
            </UiCardContent>
          </UiCard>
        </RouterLink>

        <RouterLink to="/product-on-hand" class="block">
          <UiCard class="transition-colors hover:border-primary/50">
            <UiCardContent class="p-4">
              <div class="flex items-center gap-3">
                <div class="rounded-md bg-green-500/10 p-2">
                  <DollarSign class="h-5 w-5 text-green-500" />
                </div>
                <div>
                  <p class="text-sm text-muted-foreground">Total Value</p>
                  <p class="text-2xl font-bold">${{ productStats.total_value.toFixed(2) }}</p>
                  <p class="text-xs text-muted-foreground">potential revenue</p>
                </div>
              </div>
            </UiCardContent>
          </UiCard>
        </RouterLink>

        <RouterLink to="/product-on-hand" class="block">
          <UiCard class="transition-colors hover:border-primary/50">
            <UiCardContent class="p-4">
              <div class="flex items-center gap-3">
                <div class="rounded-md bg-purple-500/10 p-2">
                  <DollarSign class="h-5 w-5 text-purple-500" />
                </div>
                <div>
                  <p class="text-sm text-muted-foreground">Potential Profit</p>
                  <p class="text-2xl font-bold">${{ productStats.total_potential_profit.toFixed(2) }}</p>
                  <p class="text-xs text-muted-foreground">if all sold</p>
                </div>
              </div>
            </UiCardContent>
          </UiCard>
        </RouterLink>
      </div>
    </div>

    <!-- Spools Grid -->
    <div>
      <h2 class="mb-4 text-xl font-semibold">Spools</h2>
      <UiCard v-if="data.spools.length === 0">
        <UiCardContent class="p-8 text-center text-muted-foreground">
          No spools yet. Add your first spool to get started!
        </UiCardContent>
      </UiCard>
      <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <SpoolCard v-for="spool in data.spools" :key="spool.id" :spool="spool" readonly />
      </div>
    </div>
  </div>
</template>
