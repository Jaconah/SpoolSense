<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import UiTextarea from '@/components/ui/UiTextarea.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import UiSwitch from '@/components/ui/UiSwitch.vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiDialogHeader from '@/components/ui/UiDialogHeader.vue'
import UiDialogTitle from '@/components/ui/UiDialogTitle.vue'
import UiDialogDescription from '@/components/ui/UiDialogDescription.vue'
import UiDialogFooter from '@/components/ui/UiDialogFooter.vue'
import UiTooltip from '@/components/ui/UiTooltip.vue'
import { Plus, Trash2, HelpCircle } from 'lucide-vue-next'
import { api, type HardwareItem, type Project } from '@/lib/api'

const props = defineProps<{
  open: boolean
  project?: Project | null
  hardwareItems: HardwareItem[]
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  saved: []
}>()

const isEdit = computed(() => !!props.project)
const saving = ref(false)
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
  is_active: true,
})

const hwEntries = ref<HwEntry[]>([])

watch(
  () => [props.project, props.open],
  () => {
    if (props.project) {
      form.value = {
        name: props.project.name,
        model_url: props.project.model_url || '',
        filament_grams: props.project.filament_grams ? String(props.project.filament_grams) : '',
        print_time_hours: props.project.print_time_hours ? String(props.project.print_time_hours) : '',
        sell_price: props.project.sell_price ? String(props.project.sell_price) : '',
        description: props.project.description || '',
        notes: props.project.notes || '',
        is_active: props.project.is_active ?? true,
      }
      hwEntries.value = props.project.hardware.map((h) => ({
        hardware_item_id: String(h.hardware_item_id),
        quantity: String(h.quantity),
      }))
    } else {
      form.value = {
        name: '',
        model_url: '',
        filament_grams: '',
        print_time_hours: '',
  sell_price: '',
        description: '',
        notes: '',
        is_active: true,
      }
      hwEntries.value = []
    }
    error.value = ''
  },
  { immediate: true }
)

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

async function handleSubmit() {
  saving.value = true
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
      is_active: form.value.is_active,
      hardware: hwEntries.value.map((e) => ({
        hardware_item_id: Number(e.hardware_item_id),
        quantity: Number(e.quantity),
      })),
    }
    if (isEdit.value) {
      await api.put(`/projects/${props.project!.id}`, payload)
    } else {
      await api.post('/projects', payload)
    }
    emit('saved')
    emit('update:open', false)
  } catch (e: any) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <UiDialog :open="open" class="max-h-[90vh] overflow-y-auto sm:max-w-lg" @update:open="emit('update:open', $event)">
    <UiDialogHeader>
      <UiDialogTitle>{{ isEdit ? 'Edit Project' : 'Add Project' }}</UiDialogTitle>
      <UiDialogDescription>
        {{ isEdit ? 'Update project template.' : 'Create a reusable project template.' }}
      </UiDialogDescription>
    </UiDialogHeader>
    <form @submit.prevent="handleSubmit" class="space-y-4">
      <div>
        <UiLabel>Name</UiLabel>
        <UiInput v-model="form.name" placeholder="e.g. Bearing Fidget Spinner" required />
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
          <div class="flex items-center gap-2 mb-2">
            <UiLabel>Print Time (hours)</UiLabel>
            <UiTooltip content="Estimated print duration. Used for labor cost calculations.">
              <HelpCircle class="h-4 w-4 text-muted-foreground cursor-help" />
            </UiTooltip>
          </div>
          <UiInput type="number" v-model="form.print_time_hours" min="0" step="0.01" placeholder="e.g. 2.5" />
        </div>
        <div>
          <div class="flex items-center gap-2 mb-2">
            <UiLabel>Sell Price</UiLabel>
            <UiTooltip content="Final sale price. Profit = Sell Price - (Filament + Hardware).">
              <HelpCircle class="h-4 w-4 text-muted-foreground cursor-help" />
            </UiTooltip>
          </div>
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

      <div class="flex items-center gap-2">
        <UiSwitch v-model="form.is_active" id="is_active" />
        <UiLabel for="is_active" class="cursor-pointer">Active (show in dropdowns)</UiLabel>
      </div>

      <p v-if="error" class="text-sm text-red-500">{{ error }}</p>

      <UiDialogFooter>
        <UiButton variant="outline" @click="emit('update:open', false)">Cancel</UiButton>
        <UiButton type="submit" :disabled="saving">
          {{ saving ? 'Saving...' : isEdit ? 'Update' : 'Create Project' }}
        </UiButton>
      </UiDialogFooter>
    </form>
  </UiDialog>
</template>
