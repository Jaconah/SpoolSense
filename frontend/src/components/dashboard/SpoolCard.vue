<script setup lang="ts">
import UiCard from '@/components/ui/UiCard.vue'
import UiCardContent from '@/components/ui/UiCardContent.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiBadge from '@/components/ui/UiBadge.vue'
import { Pencil, Trash2, DollarSign, Tag } from 'lucide-vue-next'
import { cn } from '@/lib/utils'
import type { Spool } from '@/lib/api'
import { computed } from 'vue'

const props = defineProps<{ spool: Spool; readonly?: boolean }>()

const emit = defineEmits<{
  edit: [spool: Spool]
  delete: [spool: Spool]
}>()

const percent = computed(() => props.spool.remaining_percent)
const barColor = computed(() =>
  percent.value > 50
    ? 'bg-green-500'
    : percent.value > 20
      ? 'bg-yellow-500'
      : 'bg-red-500'
)
</script>

<template>
  <UiCard class="overflow-hidden">
    <div class="h-2" :style="{ backgroundColor: spool.color_hex }" />
    <UiCardContent class="p-4">
      <div class="flex items-start justify-between gap-2 mb-2">
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-2">
            <div
              class="h-4 w-4 rounded-full border shrink-0"
              :style="{ backgroundColor: spool.color_hex }"
            />
            <p class="truncate font-medium">{{ spool.color_name }}</p>
          </div>
          <p class="mt-1 text-sm text-muted-foreground">
            {{ spool.filament_type.name }} &middot; {{ spool.manufacturer.name }}
          </p>
        </div>
        <div class="flex items-center gap-1">
          <UiBadge v-if="!spool.is_active" variant="secondary" class="text-xs">Inactive</UiBadge>
          <span :class="cn('text-sm font-bold', percent <= 20 && 'text-red-500')">
            {{ percent }}%
          </span>
        </div>
      </div>

      <!-- Progress Bar -->
      <div class="mb-3">
        <div class="h-2 w-full rounded-full bg-muted">
          <div
            :class="cn('h-2 rounded-full transition-all', barColor)"
            :style="{ width: `${Math.min(percent, 100)}%` }"
          />
        </div>
        <p class="mt-1 text-xs text-muted-foreground">
          {{ spool.remaining_weight_g.toFixed(0) }}g / {{ spool.total_weight_g.toFixed(0) }}g
        </p>
      </div>

      <!-- Pricing Info -->
      <div class="grid grid-cols-2 gap-2 mb-3 text-xs">
        <div class="flex items-center gap-1">
          <DollarSign class="h-3 w-3 text-muted-foreground" />
          <div>
            <div class="text-muted-foreground">Purchase</div>
            <div class="font-medium flex items-center gap-1">
              {{ spool.normal_price != null ? `$${spool.normal_price.toFixed(2)}` : '-' }}
              <Tag v-if="spool.is_sale_price" class="h-3 w-3 text-green-600" />
            </div>
          </div>
        </div>
        <div>
          <div class="text-muted-foreground">Cost/kg</div>
          <div class="font-medium">{{ spool.cost_per_kg != null ? `$${spool.cost_per_kg.toFixed(2)}` : '-' }}</div>
        </div>
      </div>

      <!-- Actions -->
      <div v-if="!readonly" class="flex gap-2 pt-3 border-t">
        <UiButton
          variant="outline"
          size="sm"
          class="flex-1 min-h-[44px]"
          @click="emit('edit', spool)"
        >
          <Pencil class="h-4 w-4 mr-2" />
          Edit
        </UiButton>
        <UiButton
          variant="ghost"
          size="sm"
          class="min-h-[44px]"
          @click="emit('delete', spool)"
        >
          <Trash2 class="h-4 w-4" />
        </UiButton>
      </div>
    </UiCardContent>
  </UiCard>
</template>
