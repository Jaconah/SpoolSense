<script setup lang="ts">
import { computed } from 'vue'
import { Edit, Trash2, Package } from 'lucide-vue-next'
import UiButton from '@/components/ui/UiButton.vue'
import UiBadge from '@/components/ui/UiBadge.vue'
import type { Spool } from '@/lib/api'

interface Props {
  spool: Spool
}

const props = defineProps<Props>()
const emit = defineEmits<{
  edit: [spool: Spool]
  delete: [spool: Spool]
}>()

// Calculate remaining percentage
const remainingPercentage = computed(() => {
  if (!props.spool.total_weight_g || props.spool.total_weight_g === 0) return 0
  return Math.round((props.spool.remaining_weight_g / props.spool.total_weight_g) * 100)
})

// Progress bar color based on percentage
const progressColor = computed(() => {
  const pct = remainingPercentage.value
  if (pct > 50) return 'bg-green-500'
  if (pct > 20) return 'bg-yellow-500'
  return 'bg-red-500'
})

// Status badge variant
const statusVariant = computed(() => {
  return props.spool.is_active ? 'default' : 'secondary'
})
</script>

<template>
  <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 shadow-xs hover:shadow-md transition-shadow">
    <!-- Header Row: Tracking ID + Color Swatch + Actions -->
    <div class="flex items-start justify-between mb-3">
      <div class="flex items-center gap-3 flex-1 min-w-0">
        <!-- Color Swatch -->
        <div
          class="w-10 h-10 rounded-md border-2 border-gray-300 dark:border-gray-600 shrink-0"
          :style="{ backgroundColor: spool.color_hex }"
          :title="spool.color_name"
        />

        <!-- Tracking ID + Type -->
        <div class="min-w-0 flex-1">
          <div class="font-semibold text-gray-900 dark:text-white text-lg flex items-center gap-2">
            <Package class="w-4 h-4 text-gray-500 shrink-0" />
            <span class="truncate">{{ spool.tracking_id || `#${spool.id}` }}</span>
          </div>
          <div class="text-sm text-gray-600 dark:text-gray-400 truncate">
            {{ spool.filament_type?.name || 'Unknown' }}
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex items-center gap-1 shrink-0 ml-2">
        <UiButton variant="ghost" size="sm" @click="emit('edit', spool)" class="min-w-[44px] min-h-[44px]">
          <Edit class="w-4 h-4" />
        </UiButton>
        <UiButton variant="ghost" size="sm" @click="emit('delete', spool)" class="min-w-[44px] min-h-[44px]">
          <Trash2 class="w-4 h-4 text-red-600 dark:text-red-400" />
        </UiButton>
      </div>
    </div>

    <!-- Manufacturer + Color Name -->
    <div class="mb-3 space-y-1">
      <div class="text-sm">
        <span class="text-gray-500 dark:text-gray-400">Brand:</span>
        <span class="ml-2 text-gray-900 dark:text-white font-medium">
          {{ spool.manufacturer?.name || 'Unknown' }}
        </span>
      </div>
      <div class="text-sm">
        <span class="text-gray-500 dark:text-gray-400">Color:</span>
        <span class="ml-2 text-gray-900 dark:text-white">{{ spool.color_name }}</span>
      </div>
      <div v-if="spool.location" class="text-sm">
        <span class="text-gray-500 dark:text-gray-400">Location:</span>
        <span class="ml-2 text-gray-900 dark:text-white">{{ spool.location }}</span>
      </div>
    </div>

    <!-- Progress Bar -->
    <div class="mb-3">
      <div class="flex items-center justify-between text-sm mb-1">
        <span class="text-gray-600 dark:text-gray-400">Remaining</span>
        <span class="font-semibold text-gray-900 dark:text-white">{{ remainingPercentage }}%</span>
      </div>
      <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
        <div
          :class="progressColor"
          class="h-full rounded-full transition-all duration-300"
          :style="{ width: `${remainingPercentage}%` }"
        />
      </div>
      <div class="flex items-center justify-between text-xs mt-1 text-gray-500 dark:text-gray-400">
        <span>{{ spool.remaining_weight_g }}g</span>
        <span>{{ spool.total_weight_g }}g total</span>
      </div>
    </div>

    <!-- Status Badge + Price -->
    <div class="flex items-center justify-between pt-3 border-t border-gray-200 dark:border-gray-700">
      <UiBadge :variant="statusVariant">
        {{ spool.is_active ? 'Active' : 'Inactive' }}
      </UiBadge>

      <div class="text-right">
        <div v-if="spool.is_sale_price && spool.normal_price" class="text-xs text-gray-500 line-through">
          ${{ spool.normal_price.toFixed(2) }}
        </div>
        <div class="font-semibold text-gray-900 dark:text-white">
          ${{ (spool.purchase_price || 0).toFixed(2) }}
          <span v-if="spool.is_sale_price" class="text-xs text-green-600 dark:text-green-400 ml-1">SALE</span>
        </div>
      </div>
    </div>
  </div>
</template>
