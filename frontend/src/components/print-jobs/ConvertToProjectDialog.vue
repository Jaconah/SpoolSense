<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { api, type PrintJob, type HardwareItem } from '@/lib/api'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiDialogHeader from '@/components/ui/UiDialogHeader.vue'
import UiDialogTitle from '@/components/ui/UiDialogTitle.vue'
import UiDialogDescription from '@/components/ui/UiDialogDescription.vue'
import UiDialogFooter from '@/components/ui/UiDialogFooter.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import UiTextarea from '@/components/ui/UiTextarea.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import { Plus, Trash2 } from 'lucide-vue-next'

const props = defineProps<{
  open: boolean
  printJob?: PrintJob | null
  hardwareItems: HardwareItem[]
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  converted: []
}>()

const converting = ref(false)
const error = ref('')

interface HwEntry {
  hardware_item_id: string
  quantity: string
}

const form = ref({
  name: '',
  model_url: '',
  filament_grams: '',
  print_time_hours: '',
  sell_price: '',
  description: '',
  notes: '',
})

const hwEntries = ref<HwEntry[]>([])

const hwOptions = computed(() =>
  props.hardwareItems.map((h) => ({
    value: String(h.id),
    label: `${h.name}${h.brand ? ` (${h.brand})` : ''} - $${h.cost_per_item.toFixed(4)}/ea`,
  }))
)

function addHardware() {
  if (props.hardwareItems.length === 0) return
  hwEntries.value.push({
    hardware_item_id: String(props.hardwareItems[0].id),
    quantity: '1',
  })
}

function removeHardware(index: number) {
  hwEntries.value.splice(index, 1)
}

watch(
  () => [props.printJob, props.open],
  () => {
    if (props.open && props.printJob) {
      form.value = {
        name: props.printJob.name || '',
        model_url: '',
        filament_grams: props.printJob.filament_used_g ? String(props.printJob.filament_used_g) : '',
        print_time_hours: props.printJob.print_time_minutes
          ? String((props.printJob.print_time_minutes / 60).toFixed(2))
          : '',
        sell_price: props.printJob.quoted_price ? String(props.printJob.quoted_price) : '',
        description: props.printJob.description || '',
        notes: `Created from print job: ${props.printJob.name}`,
      }
      hwEntries.value = []
    } else {
      form.value = {
        name: '',
        model_url: '',
        filament_grams: '',
        print_time_hours: '',
        sell_price: '',
        description: '',
        notes: '',
      }
      hwEntries.value = []
    }
    error.value = ''
  },
  { immediate: true }
)

async function handleConvert() {
  if (!props.printJob) return

  converting.value = true
  error.value = ''

  try {
    const payload = {
      name: form.value.name,
      model_url: form.value.model_url || null,
      filament_grams: form.value.filament_grams ? Number(form.value.filament_grams) : null,
      print_time_hours: form.value.print_time_hours ? Number(form.value.print_time_hours) : null,
      sell_price: form.value.sell_price ? Number(form.value.sell_price) : null,
      description: form.value.description || null,
      notes: form.value.notes || null,
      is_active: true,
      hardware: hwEntries.value.map((e) => ({
        hardware_item_id: Number(e.hardware_item_id),
        quantity: Number(e.quantity),
      })),
    }

    await api.post(`/print-jobs/${props.printJob.id}/convert-to-project`, payload)

    emit('converted')
    emit('update:open', false)
  } catch (e: any) {
    error.value = e.message
  } finally {
    converting.value = false
  }
}
</script>

<template>
  <UiDialog :open="open" class="max-h-[90vh] overflow-y-auto sm:max-w-lg" @update:open="emit('update:open', $event)">
    <UiDialogHeader>
      <UiDialogTitle>Convert to Project Template</UiDialogTitle>
      <UiDialogDescription>
        Create a reusable project template from this print job. You can modify the details below.
      </UiDialogDescription>
    </UiDialogHeader>

    <form @submit.prevent="handleConvert" class="space-y-4">
      <div>
        <UiLabel>Project Name *</UiLabel>
        <UiInput v-model="form.name" placeholder="e.g. Phone Holder" required />
      </div>

      <div>
        <UiLabel>Model URL</UiLabel>
        <UiInput v-model="form.model_url" placeholder="https://..." />
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <UiLabel>Filament (grams)</UiLabel>
          <UiInput type="number" v-model="form.filament_grams" min="0" step="0.1" placeholder="e.g. 45" />
        </div>
        <div>
          <UiLabel>Print Time (hours)</UiLabel>
          <UiInput type="number" v-model="form.print_time_hours" min="0" step="0.01" placeholder="e.g. 2.5" />
        </div>
        <div>
          <UiLabel>Sell Price</UiLabel>
          <UiInput type="number" v-model="form.sell_price" min="0" step="0.01" placeholder="e.g. 15.00" />
        </div>
      </div>

      <div>
        <UiLabel>Description</UiLabel>
        <UiTextarea v-model="form.description" placeholder="Optional description..." />
      </div>

      <!-- Hardware picker -->
      <div>
        <div class="mb-2 flex items-center justify-between">
          <UiLabel>Hardware Required</UiLabel>
          <UiButton type="button" variant="outline" size="sm" @click="addHardware" :disabled="hardwareItems.length === 0">
            <Plus class="mr-1 h-3 w-3" /> Add
          </UiButton>
        </div>
        <div v-if="hwEntries.length === 0" class="rounded-md border border-dashed p-3 text-center text-sm text-muted-foreground">
          No hardware added
        </div>
        <div v-else class="space-y-2">
          <div v-for="(entry, idx) in hwEntries" :key="idx" class="flex items-end gap-2">
            <div class="flex-1">
              <UiSelect v-model="entry.hardware_item_id" :options="hwOptions" />
            </div>
            <div class="w-20">
              <UiInput type="number" v-model="entry.quantity" min="1" step="1" placeholder="Qty" />
            </div>
            <UiButton type="button" variant="ghost" size="icon" @click="removeHardware(idx)">
              <Trash2 class="h-4 w-4" />
            </UiButton>
          </div>
        </div>
      </div>

      <div>
        <UiLabel>Notes</UiLabel>
        <UiTextarea v-model="form.notes" placeholder="Optional notes..." />
      </div>

      <UiAlert v-if="error" variant="error" :title="error" />

      <UiDialogFooter>
        <UiButton type="button" variant="outline" @click="emit('update:open', false)">Cancel</UiButton>
        <UiButton type="submit" :disabled="converting">
          {{ converting ? 'Converting...' : 'Create Project' }}
        </UiButton>
      </UiDialogFooter>
    </form>
  </UiDialog>
</template>
