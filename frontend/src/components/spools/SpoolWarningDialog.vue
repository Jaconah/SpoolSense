<template>
  <UiDialog :open="open" @update:open="$emit('update:open', $event)">
    <UiDialogHeader>
      <UiDialogTitle>⚠️ {{ dialogTitle }}</UiDialogTitle>
      <UiDialogDescription>
        {{ dialogDescription }}
      </UiDialogDescription>
    </UiDialogHeader>

    <div class="space-y-4 py-4 max-h-[400px] overflow-y-auto">
      <div
        v-for="shortage in shortages"
        :key="shortage.spool_id"
        :class="[
          'border rounded-lg p-4',
          shortage.within_reserve
            ? 'bg-amber-50 dark:bg-amber-900/10 border-amber-200 dark:border-amber-700'
            : 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-800'
        ]"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1">
            <div class="font-medium text-gray-900 dark:text-gray-100">
              {{ shortage.tracking_id || `Spool #${shortage.spool_id}` }}
            </div>
            <div class="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {{ shortage.filament_type_name }}
              <span v-if="shortage.manufacturer_name"> - {{ shortage.manufacturer_name }}</span>
              - {{ shortage.color_name }}
            </div>

            <div class="mt-3 space-y-1 text-sm">
              <div class="flex items-center gap-2">
                <span class="text-gray-600 dark:text-gray-400 w-24">Current:</span>
                <span class="font-mono font-medium">{{ shortage.current_weight_g.toFixed(1) }}g</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-gray-600 dark:text-gray-400 w-24">Requested:</span>
                <span class="font-mono font-medium">{{ shortage.requested_weight_g.toFixed(1) }}g</span>
              </div>
              <div
                v-if="!shortage.within_reserve"
                class="flex items-center gap-2 text-red-600 dark:text-red-400"
              >
                <span class="font-semibold w-24">Short by:</span>
                <span class="font-mono font-bold">{{ shortage.shortage_g.toFixed(1) }}g</span>
              </div>
              <div
                v-else
                class="flex items-center gap-2 text-amber-600 dark:text-amber-400"
              >
                <span class="font-semibold w-24">Remaining:</span>
                <span class="font-mono font-bold">{{ shortage.resulting_weight_g.toFixed(1) }}g</span>
              </div>
            </div>

            <p
              v-if="shortage.within_reserve"
              class="mt-3 text-xs text-amber-700 dark:text-amber-400 leading-relaxed"
            >
              Filament is gradually lost to purging and waste throughout a spool's life —
              so your remaining weight is an estimate. This print would bring this spool below the
              minimum safety buffer, and it may run out before finishing.
            </p>
          </div>
        </div>
      </div>
    </div>

    <UiDialogFooter>
      <UiButton variant="outline" @click="handleCancel">
        Cancel
      </UiButton>
      <UiButton variant="destructive" @click="handleConfirm">
        Proceed Anyway
      </UiButton>
    </UiDialogFooter>
  </UiDialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiDialogHeader from '@/components/ui/UiDialogHeader.vue'
import UiDialogTitle from '@/components/ui/UiDialogTitle.vue'
import UiDialogDescription from '@/components/ui/UiDialogDescription.vue'
import UiDialogFooter from '@/components/ui/UiDialogFooter.vue'
import UiButton from '@/components/ui/UiButton.vue'

interface SpoolShortage {
  spool_id: number
  tracking_id: string | null
  color_name: string
  filament_type_name: string
  manufacturer_name: string | null
  current_weight_g: number
  requested_weight_g: number
  resulting_weight_g: number
  shortage_g: number
  within_reserve: boolean
}

const props = defineProps<{
  open: boolean
  shortages: SpoolShortage[]
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

const hasHardShortage = computed(() => props.shortages.some(s => !s.within_reserve))
const allWithinReserve = computed(() => props.shortages.every(s => s.within_reserve))

const dialogTitle = computed(() => {
  if (allWithinReserve.value) return 'Spool Nearly Empty'
  return 'Insufficient Spool Inventory'
})

const dialogDescription = computed(() => {
  if (allWithinReserve.value) {
    return 'These spools technically have enough filament, but this print would bring them below the minimum safety buffer. You can proceed if you\'re confident, but be ready to swap spools mid-print.'
  }
  if (hasHardShortage.value) {
    return 'One or more spools do not have enough material for this print. You can proceed if you plan to swap spools mid-print or have already accounted for the shortage.'
  }
  return 'There may not be enough material on these spools to complete this print.'
})

const handleConfirm = () => {
  emit('confirm')
  emit('update:open', false)
}

const handleCancel = () => {
  emit('cancel')
  emit('update:open', false)
}
</script>
