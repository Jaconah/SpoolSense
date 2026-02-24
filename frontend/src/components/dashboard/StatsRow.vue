<script setup lang="ts">
import UiCard from '@/components/ui/UiCard.vue'
import UiCardContent from '@/components/ui/UiCardContent.vue'
import { Cylinder, DollarSign, ShoppingCart } from 'lucide-vue-next'
import type { DashboardStats } from '@/lib/api'
import { computed } from 'vue'
import { RouterLink } from 'vue-router'

const props = defineProps<{ stats: DashboardStats }>()

const items = computed(() => [
  {
    label: 'Spools',
    value: props.stats.total_spools,
    icon: Cylinder,
    sub: 'in inventory',
    to: '/spools',
  },
  {
    label: 'Revenue',
    value: `${props.stats.currency_symbol}${props.stats.order_revenue.toFixed(2)}`,
    icon: DollarSign,
    sub: `from ${props.stats.sold_orders} sold orders`,
    to: '/orders',
  },
  {
    label: 'Orders',
    value: props.stats.total_orders,
    icon: ShoppingCart,
    sub: `${props.stats.sold_orders} sold`,
    to: '/orders',
  },
])
</script>

<template>
  <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
    <RouterLink v-for="item in items" :key="item.label" :to="item.to" class="block">
      <UiCard class="transition-colors hover:border-primary/50">
        <UiCardContent class="p-4">
          <div class="flex items-center gap-3">
            <div class="rounded-md bg-primary/10 p-2">
              <component :is="item.icon" class="h-5 w-5 text-primary" />
            </div>
            <div>
              <p class="text-sm text-muted-foreground">{{ item.label }}</p>
              <p class="text-2xl font-bold">{{ item.value }}</p>
              <p class="text-xs text-muted-foreground">{{ item.sub }}</p>
            </div>
          </div>
        </UiCardContent>
      </UiCard>
    </RouterLink>
  </div>
</template>
