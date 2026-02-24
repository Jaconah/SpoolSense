<script setup lang="ts">
import { Package, DollarSign, AlertTriangle, ExternalLink, Pencil, Trash2 } from 'lucide-vue-next'
import UiButton from '@/components/ui/UiButton.vue'
import type { HardwareItem } from '@/lib/api'

defineProps<{
  item: HardwareItem
}>()

const emit = defineEmits<{
  edit: [item: HardwareItem]
  delete: [item: HardwareItem]
}>()
</script>

<template>
  <div
    class="relative overflow-hidden rounded-lg border bg-card transition-all hover:shadow-md active:scale-[0.98]"
    :class="{ 'ring-2 ring-yellow-500/20': item.is_low_stock }"
  >
    <!-- Low Stock Indicator -->
    <div
      v-if="item.is_low_stock"
      class="absolute right-0 top-0 w-0 h-0 border-t-[40px] border-l-[40px] border-t-yellow-500 border-l-transparent"
    >
      <AlertTriangle class="absolute -top-8 -right-1 h-4 w-4 text-white" />
    </div>

    <div class="p-4">
      <!-- Header -->
      <div class="flex items-start justify-between gap-3 mb-3">
        <div class="flex-1 min-w-0">
          <h3 class="font-semibold text-base truncate">{{ item.name }}</h3>
          <p v-if="item.brand" class="text-sm text-muted-foreground truncate">{{ item.brand }}</p>
        </div>
        <a
          v-if="item.purchase_url"
          :href="item.purchase_url"
          target="_blank"
          rel="noopener noreferrer"
          class="shrink-0 p-2 hover:bg-muted rounded-md transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
        >
          <ExternalLink class="h-4 w-4 text-primary" />
        </a>
      </div>

      <!-- Stats Grid -->
      <div class="grid grid-cols-2 gap-3 mb-3">
        <div>
          <div class="text-xs text-muted-foreground">Purchase Price</div>
          <div class="text-sm font-medium">${{ item.purchase_price.toFixed(2) }}</div>
        </div>

        <div>
          <div class="text-xs text-muted-foreground">Cost per Item</div>
          <div class="text-sm font-medium">${{ item.cost_per_item.toFixed(4) }}</div>
        </div>

        <div>
          <div class="text-xs text-muted-foreground">Purchased</div>
          <div class="text-sm font-medium">{{ item.quantity_purchased }}</div>
        </div>

        <div>
          <div class="text-xs text-muted-foreground">In Stock</div>
          <div
            class="text-sm font-medium"
            :class="{ 'text-yellow-600 dark:text-yellow-500 font-semibold': item.is_low_stock }"
          >
            {{ item.quantity_in_stock }}
          </div>
        </div>
      </div>

      <!-- Stock Progress Bar -->
      <div class="mb-3">
        <div class="flex justify-between text-xs text-muted-foreground mb-1">
          <span>Stock Level</span>
          <span>{{ Math.round((item.quantity_in_stock / item.quantity_purchased) * 100) }}%</span>
        </div>
        <div class="h-2 rounded-full bg-muted overflow-hidden">
          <div
            class="h-full transition-all"
            :class="{
              'bg-green-500': !item.is_low_stock,
              'bg-yellow-500': item.is_low_stock
            }"
            :style="{
              width: `${Math.min((item.quantity_in_stock / item.quantity_purchased) * 100, 100)}%`
            }"
          />
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-2 pt-3 border-t">
        <UiButton
          variant="outline"
          size="sm"
          class="flex-1 min-h-[44px]"
          @click="emit('edit', item)"
        >
          <Pencil class="h-4 w-4 mr-2" />
          Edit
        </UiButton>
        <UiButton
          variant="ghost"
          size="sm"
          class="min-h-[44px]"
          @click="emit('delete', item)"
        >
          <Trash2 class="h-4 w-4" />
        </UiButton>
      </div>
    </div>
  </div>
</template>
