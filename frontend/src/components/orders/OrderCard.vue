<script setup lang="ts">
import { User, Calendar, DollarSign, TrendingUp, Pencil, Trash2, Play } from 'lucide-vue-next'
import UiBadge from '@/components/ui/UiBadge.vue'
import UiButton from '@/components/ui/UiButton.vue'
import type { Order } from '@/lib/api'

defineProps<{
  order: Order
  orderName: string
}>()

const emit = defineEmits<{
  edit: [order: Order]
  delete: [order: Order]
  showProfit: [order: Order]
  createPrintJob: [order: Order]
}>()

function statusVariant(status: string) {
  switch (status) {
    case 'sold': return 'default' as const
    case 'finished': return 'secondary' as const
    case 'printed': return 'secondary' as const
    default: return 'outline' as const
  }
}

function statusColor(status: string) {
  switch (status) {
    case 'sold': return 'bg-green-500'
    case 'finished': return 'bg-blue-500'
    case 'printed': return 'bg-purple-500'
    default: return 'bg-gray-400'
  }
}
</script>

<template>
  <div class="relative overflow-hidden rounded-lg border bg-card transition-all hover:shadow-md active:scale-[0.98]">
    <!-- Status Strip -->
    <div
      class="absolute left-0 top-0 bottom-0 w-1"
      :class="statusColor(order.status)"
    />

    <div class="p-4 pl-5">
      <!-- Header: Order Name + Status -->
      <div class="flex items-start justify-between gap-3 mb-3">
        <div class="flex-1 min-w-0">
          <h3 class="font-semibold text-base truncate">{{ orderName }}</h3>
          <p v-if="order.customer_name" class="text-sm text-muted-foreground flex items-center gap-1 mt-1">
            <User class="h-3 w-3" />
            {{ order.customer_name }}
          </p>
        </div>
        <UiBadge :variant="statusVariant(order.status)">
          {{ order.status.replace('_', ' ') }}
        </UiBadge>
      </div>

      <!-- Stats Grid -->
      <div class="grid grid-cols-2 gap-3 mb-3">
        <div v-if="order.quoted_price != null" class="flex items-center gap-2">
          <DollarSign class="h-4 w-4 text-muted-foreground shrink-0" />
          <div class="min-w-0">
            <div class="text-xs text-muted-foreground">Quoted</div>
            <div class="text-sm font-medium">${{ order.quoted_price.toFixed(2) }}</div>
          </div>
        </div>

        <div v-if="order.due_date" class="flex items-center gap-2">
          <Calendar class="h-4 w-4 text-muted-foreground shrink-0" />
          <div class="min-w-0">
            <div class="text-xs text-muted-foreground">Due Date</div>
            <div class="text-sm font-medium">
              {{ new Date(order.due_date).toLocaleDateString() }}
            </div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-2 pt-3 border-t">
        <UiButton
          v-if="order.project_id && order.spool_id && order.status === 'ordered'"
          variant="ghost"
          size="sm"
          class="min-h-[44px]"
          @click="emit('createPrintJob', order)"
        >
          <Play class="h-4 w-4" />
        </UiButton>
        <UiButton
          variant="ghost"
          size="sm"
          class="min-h-[44px]"
          @click="emit('showProfit', order)"
        >
          <TrendingUp class="h-4 w-4" />
        </UiButton>
        <UiButton
          variant="outline"
          size="sm"
          class="flex-1 min-h-[44px]"
          @click="emit('edit', order)"
        >
          <Pencil class="h-4 w-4 mr-2" />
          Edit
        </UiButton>
        <UiButton
          variant="ghost"
          size="sm"
          class="min-h-[44px]"
          @click="emit('delete', order)"
        >
          <Trash2 class="h-4 w-4" />
        </UiButton>
      </div>
    </div>
  </div>
</template>
