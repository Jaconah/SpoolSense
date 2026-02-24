<script setup lang="ts">
import { Package, Clock, DollarSign, ExternalLink, Pencil, Trash2 } from 'lucide-vue-next'
import UiBadge from '@/components/ui/UiBadge.vue'
import UiButton from '@/components/ui/UiButton.vue'
import type { Project } from '@/lib/api'

defineProps<{
  project: Project
}>()

const emit = defineEmits<{
  edit: [project: Project]
  delete: [project: Project]
}>()
</script>

<template>
  <div class="overflow-hidden rounded-lg border bg-card transition-all hover:shadow-md active:scale-[0.98]">
    <div class="p-4">
      <!-- Header -->
      <div class="flex items-start justify-between gap-3 mb-3">
        <div class="flex-1 min-w-0">
          <h3 class="font-semibold text-base truncate">{{ project.name }}</h3>
        </div>
        <a
          v-if="project.model_url"
          :href="project.model_url"
          target="_blank"
          rel="noopener noreferrer"
          class="shrink-0 p-2 hover:bg-muted rounded-md transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
        >
          <ExternalLink class="h-4 w-4 text-primary" />
        </a>
      </div>

      <!-- Stats Grid -->
      <div class="grid grid-cols-2 gap-3 mb-3">
        <div class="flex items-center gap-2">
          <Package class="h-4 w-4 text-muted-foreground shrink-0" />
          <div class="min-w-0">
            <div class="text-xs text-muted-foreground">Filament</div>
            <div class="text-sm font-medium">
              {{ project.filament_grams ? `${project.filament_grams}g` : '-' }}
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <Clock class="h-4 w-4 text-muted-foreground shrink-0" />
          <div class="min-w-0">
            <div class="text-xs text-muted-foreground">Print Time</div>
            <div class="text-sm font-medium">
              {{ project.print_time_hours ? `${project.print_time_hours}h` : '-' }}
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2 col-span-2">
          <DollarSign class="h-4 w-4 text-muted-foreground shrink-0" />
          <div class="min-w-0">
            <div class="text-xs text-muted-foreground">Sell Price</div>
            <div class="text-sm font-medium">
              {{ project.sell_price != null ? `$${project.sell_price.toFixed(2)}` : '-' }}
            </div>
          </div>
        </div>
      </div>

      <!-- Hardware Badges -->
      <div v-if="project.hardware.length" class="mb-3">
        <div class="text-xs text-muted-foreground mb-2">Hardware</div>
        <div class="flex flex-wrap gap-1">
          <UiBadge v-for="h in project.hardware" :key="h.id" variant="secondary" class="text-xs">
            {{ h.quantity }}x {{ h.hardware_item.name }}
          </UiBadge>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-2 pt-3 border-t">
        <UiButton
          variant="outline"
          size="sm"
          class="flex-1 min-h-[44px]"
          @click="emit('edit', project)"
        >
          <Pencil class="h-4 w-4 mr-2" />
          Edit
        </UiButton>
        <UiButton
          variant="ghost"
          size="sm"
          class="min-h-[44px]"
          @click="emit('delete', project)"
        >
          <Trash2 class="h-4 w-4" />
        </UiButton>
      </div>
    </div>
  </div>
</template>
