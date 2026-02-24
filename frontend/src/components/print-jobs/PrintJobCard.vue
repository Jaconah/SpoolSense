<script setup lang="ts">
import { Printer, Clock, DollarSign, User, Package, Pencil, Trash2, FolderPlus } from 'lucide-vue-next'
import UiBadge from '@/components/ui/UiBadge.vue'
import UiButton from '@/components/ui/UiButton.vue'
import type { PrintJob } from '@/lib/api'

defineProps<{
  job: PrintJob
}>()

const emit = defineEmits<{
  edit: [job: PrintJob]
  delete: [job: PrintJob]
  moveToProduct: [job: PrintJob]
  convertToProject: [job: PrintJob]
}>()

function formatTime(minutes: number | null) {
  if (!minutes) return '-'
  return `${Math.floor(minutes / 60)}h ${minutes % 60}m`
}
</script>

<template>
  <div class="relative overflow-hidden rounded-lg border bg-card transition-all hover:shadow-md active:scale-[0.98]">
    <!-- Status Strip (left edge accent) -->
    <div
      class="absolute left-0 top-0 bottom-0 w-1"
      :class="{
        'bg-green-500': job.status === 'completed',
        'bg-red-500': job.status === 'failed',
        'bg-gray-400': job.status === 'cancelled'
      }"
    />

    <div class="p-4 pl-5">
      <!-- Header: Name + Status Badge -->
      <div class="flex items-start justify-between gap-3 mb-3">
        <div class="flex-1 min-w-0">
          <h3 class="font-semibold text-base truncate">{{ job.name }}</h3>
          <!-- Multi-color spools -->
          <div v-if="job.print_job_spools && job.print_job_spools.length" class="flex flex-wrap gap-1 mt-1">
            <div
              v-for="pjs in job.print_job_spools"
              :key="pjs.id"
              class="inline-flex items-center gap-1 rounded border px-2 py-0.5 text-xs"
              :style="{
                backgroundColor: (pjs.spool?.color_hex || '#999') + '40',
                borderColor: pjs.spool?.color_hex || '#999',
                color: pjs.spool?.color_hex || '#999'
              }"
            >
              <span class="font-medium">{{ pjs.spool?.color_name || 'Unknown' }}</span>
              <span class="text-muted-foreground">({{ pjs.filament_used_g }}g)</span>
            </div>
          </div>
          <!-- Single spool (backward compat) -->
          <div v-else-if="job.spool" class="flex items-center gap-2 mt-1">
            <div
              class="h-3 w-3 rounded-full border shrink-0"
              :style="{ backgroundColor: job.spool.color_hex }"
            />
            <span class="text-xs text-muted-foreground truncate">{{ job.spool.color_name }}</span>
          </div>
        </div>
        <UiBadge
          :variant="
            job.status === 'completed'
              ? 'default'
              : job.status === 'failed'
                ? 'destructive'
                : 'secondary'
          "
        >
          {{ job.status }}
        </UiBadge>
      </div>

      <!-- Stats Grid -->
      <div class="grid grid-cols-2 gap-3 mb-3">
        <div class="flex items-center gap-2">
          <Package class="h-4 w-4 text-muted-foreground shrink-0" />
          <div class="min-w-0">
            <div class="text-xs text-muted-foreground">Filament Used</div>
            <div class="text-sm font-medium">
              <!-- Multi-color total -->
              <span v-if="job.print_job_spools && job.print_job_spools.length">
                {{ job.print_job_spools.reduce((sum, pjs) => sum + pjs.filament_used_g, 0).toFixed(1) }}g
              </span>
              <!-- Single spool (backward compat) -->
              <span v-else>{{ job.filament_used_g }}g</span>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <Clock class="h-4 w-4 text-muted-foreground shrink-0" />
          <div class="min-w-0">
            <div class="text-xs text-muted-foreground">Time</div>
            <div class="text-sm font-medium">{{ formatTime(job.print_time_minutes) }}</div>
          </div>
        </div>

        <div v-if="job.was_for_customer" class="flex items-center gap-2">
          <User class="h-4 w-4 text-muted-foreground shrink-0" />
          <div class="min-w-0">
            <div class="text-xs text-muted-foreground">Customer</div>
            <div class="text-sm font-medium truncate">{{ job.customer_name || 'Yes' }}</div>
          </div>
        </div>

        <div v-if="job.quoted_price" class="flex items-center gap-2">
          <DollarSign class="h-4 w-4 text-muted-foreground shrink-0" />
          <div class="min-w-0">
            <div class="text-xs text-muted-foreground">Price</div>
            <div class="text-sm font-medium">${{ job.quoted_price.toFixed(2) }}</div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-2 pt-3 border-t">
        <UiButton
          v-if="job.status === 'completed' && !job.order_id"
          variant="ghost"
          size="sm"
          class="min-h-[44px]"
          @click="emit('moveToProduct', job)"
          title="Move to Product on Hand"
        >
          <Package class="h-4 w-4" />
        </UiButton>
        <UiButton
          variant="ghost"
          size="sm"
          class="min-h-[44px]"
          @click="emit('convertToProject', job)"
          title="Convert to Project Template"
        >
          <FolderPlus class="h-4 w-4" />
        </UiButton>
        <UiButton
          variant="outline"
          size="sm"
          class="flex-1 min-h-[44px]"
          @click="emit('edit', job)"
        >
          <Pencil class="h-4 w-4 mr-2" />
          Edit
        </UiButton>
        <UiButton
          variant="ghost"
          size="sm"
          class="min-h-[44px]"
          @click="emit('delete', job)"
        >
          <Trash2 class="h-4 w-4" />
        </UiButton>
      </div>
    </div>
  </div>
</template>
