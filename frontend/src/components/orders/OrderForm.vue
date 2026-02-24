<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import UiTextarea from '@/components/ui/UiTextarea.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiDialogHeader from '@/components/ui/UiDialogHeader.vue'
import UiDialogTitle from '@/components/ui/UiDialogTitle.vue'
import UiDialogDescription from '@/components/ui/UiDialogDescription.vue'
import UiDialogFooter from '@/components/ui/UiDialogFooter.vue'
import UiBadge from '@/components/ui/UiBadge.vue'
import UiTooltip from '@/components/ui/UiTooltip.vue'
import { HelpCircle, Plus, X, Package, Wrench } from 'lucide-vue-next'
import { useSettings } from '@/composables/use-data'
import { api, type Order, type Project, type Spool, type HardwareItem } from '@/lib/api'

const props = defineProps<{
  open: boolean
  order?: Order | null
  projects: Project[]
  spools: Spool[]
  hardwareItems: HardwareItem[]
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  saved: []
}>()

interface HwEntry {
  is_one_off: boolean
  hardware_item_id: string  // for inventory items
  quantity: string
  one_off_name: string      // for one-off items
  one_off_cost: string      // for one-off items
  deleted_name?: string     // snapshot fallback when hardware item no longer exists
}

const isEdit = computed(() => !!props.order)
const saving = ref(false)
const error = ref('')

const { data: settings } = useSettings()

const form = ref({
  project_id: '',
  spool_id: '',
  custom_name: '',
  custom_price: '',
  customer_name: '',
  customer_contact: '',
  customer_location: '',
  status: 'ordered',
  quoted_price: '',
  due_date: '',
  shipping_charge: '',
  notes: '',
})

const hwEntries = ref<HwEntry[]>([])

function newHwEntry(): HwEntry {
  return {
    is_one_off: false,
    hardware_item_id: props.hardwareItems[0] ? String(props.hardwareItems[0].id) : '',
    quantity: '1',
    one_off_name: '',
    one_off_cost: '',
  }
}

function addHwEntry() {
  hwEntries.value.push(newHwEntry())
}

function removeHwEntry(index: number) {
  hwEntries.value.splice(index, 1)
}

watch(
  () => [props.order, props.open],
  () => {
    if (props.order) {
      form.value = {
        project_id: props.order.project_id ? String(props.order.project_id) : '',
        spool_id: props.order.spool_id ? String(props.order.spool_id) : '',
        custom_name: props.order.custom_name || '',
        custom_price: props.order.custom_price ? String(props.order.custom_price) : '',
        customer_name: props.order.customer_name || '',
        customer_contact: props.order.customer_contact || '',
        customer_location: props.order.customer_location || '',
        status: props.order.status,
        quoted_price: props.order.quoted_price ? String(props.order.quoted_price) : '',
        due_date: props.order.due_date ? props.order.due_date.slice(0, 10) : '',
        shipping_charge: props.order.shipping_charge ? String(props.order.shipping_charge) : '',
        notes: props.order.notes || '',
      }
      hwEntries.value = props.order.order_hardware.map(oh => {
        const isDeletedItem = !oh.is_one_off && oh.hardware_item_id != null && oh.hardware_item == null
        return {
          is_one_off: oh.is_one_off,
          hardware_item_id: oh.hardware_item_id ? String(oh.hardware_item_id) : '',
          quantity: String(oh.quantity),
          one_off_name: oh.one_off_name || '',
          one_off_cost: oh.one_off_cost != null ? String(oh.one_off_cost) : '',
          deleted_name: isDeletedItem
            ? [oh.hardware_name_snapshot, oh.hardware_brand_snapshot].filter(Boolean).join(' — ') || 'Deleted item'
            : undefined,
        }
      })
    } else {
      form.value = {
        project_id: '',
        spool_id: '',
        custom_name: '',
        custom_price: '',
        customer_name: '',
        customer_contact: '',
        customer_location: '',
        status: 'ordered',
        quoted_price: '',
        due_date: '',
        shipping_charge: settings.value?.default_shipping_charge ? String(settings.value.default_shipping_charge) : '',
        notes: '',
      }
      hwEntries.value = []
    }
    error.value = ''
  },
  { immediate: true }
)

const projectOptions = computed(() => [
  { value: '', label: 'Custom Order' },
  ...props.projects.map((p) => ({ value: String(p.id), label: p.name })),
])

const spoolOptions = computed(() => [
  { value: '', label: 'No Spool' },
  ...props.spools.map((s) => ({
      value: String(s.id),
      label: `#${s.id} ${s.color_name} - ${s.filament_type.name} (${s.manufacturer.name})`,
    })),
])

const hardwareOptions = computed(() => [
  ...props.hardwareItems.map((h) => ({
    value: String(h.id),
    label: `${h.name}${h.brand ? ` (${h.brand})` : ''} — $${h.cost_per_item.toFixed(4)}/ea`,
  })),
])

const statusOptions = [
  { value: 'ordered', label: 'Ordered' },
  { value: 'printed', label: 'Printed' },
  { value: 'finished', label: 'Finished' },
  { value: 'sold', label: 'Sold' },
]

const selectedProject = computed(() => {
  if (!form.value.project_id) return null
  return props.projects.find((p) => p.id === Number(form.value.project_id)) || null
})

// Auto-populate quoted_price from project sell_price
watch(
  () => form.value.project_id,
  (pid) => {
    if (!pid) return
    const project = props.projects.find((p) => p.id === Number(pid))
    if (project?.sell_price != null) {
      form.value.quoted_price = String(project.sell_price)
    }
  }
)

const isCustom = computed(() => !form.value.project_id)

const missingFields = computed(() => {
  if (!selectedProject.value) return []
  const missing: string[] = []
  if (!selectedProject.value.filament_grams) missing.push('filament grams')
  if (!selectedProject.value.print_time_hours) missing.push('print time')
  if (selectedProject.value.sell_price == null) missing.push('sell price')
  return missing
})

async function handleSubmit() {
  saving.value = true
  error.value = ''
  try {
    const hardware_items = hwEntries.value.map(entry => {
      if (entry.is_one_off) {
        return {
          is_one_off: true,
          quantity: Number(entry.quantity) || 1,
          one_off_name: entry.one_off_name,
          one_off_cost: Number(entry.one_off_cost) || 0,
        }
      } else {
        return {
          is_one_off: false,
          hardware_item_id: Number(entry.hardware_item_id),
          quantity: Number(entry.quantity) || 1,
        }
      }
    })

    const payload = {
      project_id: form.value.project_id ? Number(form.value.project_id) : null,
      spool_id: form.value.spool_id ? Number(form.value.spool_id) : null,
      custom_name: form.value.custom_name || null,
      custom_price: form.value.custom_price ? Number(form.value.custom_price) : null,
      customer_name: form.value.customer_name || null,
      customer_contact: form.value.customer_contact || null,
      customer_location: form.value.customer_location || null,
      status: form.value.status,
      quoted_price: form.value.quoted_price ? Number(form.value.quoted_price) : null,
      due_date: form.value.due_date || null,
      shipping_charge: form.value.shipping_charge ? Number(form.value.shipping_charge) : null,
      notes: form.value.notes || null,
      hardware_items,
    }
    if (isEdit.value) {
      await api.put(`/orders/${props.order!.id}`, payload)
    } else {
      await api.post('/orders', payload)
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
      <UiDialogTitle>{{ isEdit ? 'Edit Order' : 'New Order' }}</UiDialogTitle>
      <UiDialogDescription>
        {{ isEdit ? 'Update order details.' : 'Create a new customer order.' }}
      </UiDialogDescription>
    </UiDialogHeader>
    <form @submit.prevent="handleSubmit" class="space-y-4">
      <!-- Project / Custom -->
      <div>
        <UiLabel>Project Template</UiLabel>
        <UiSelect v-model="form.project_id" :options="projectOptions" />
      </div>

      <!-- Show project info if selected -->
      <div v-if="selectedProject" class="rounded-md border bg-muted/30 p-3 text-sm space-y-1">
        <p v-if="selectedProject.filament_grams">Filament: {{ selectedProject.filament_grams }}g</p>
        <p v-if="selectedProject.print_time_hours">Print Time: {{ selectedProject.print_time_hours }}h</p>
        <p v-if="selectedProject.sell_price != null">Sell Price: ${{ selectedProject.sell_price.toFixed(2) }}</p>
        <div v-if="selectedProject.hardware.length" class="flex flex-wrap gap-1 pt-1">
          <UiBadge v-for="h in selectedProject.hardware" :key="h.id" variant="secondary">
            {{ h.quantity }}x {{ h.hardware_item.name }}
          </UiBadge>
        </div>
        <a
          v-if="selectedProject.model_url"
          :href="selectedProject.model_url"
          target="_blank"
          rel="noopener noreferrer"
          class="text-primary hover:underline"
        >
          View Model
        </a>
      </div>

      <!-- Missing fields warning -->
      <div v-if="selectedProject && missingFields.length" class="rounded-md border border-yellow-500/50 bg-yellow-500/10 p-3 text-sm text-yellow-700 dark:text-yellow-400">
        <p class="font-medium">This project is missing: {{ missingFields.join(', ') }}</p>
        <p class="mt-1 text-xs">Edit the project to fill in these fields for accurate cost/profit tracking.</p>
      </div>

      <!-- Custom fields -->
      <div v-if="isCustom" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <UiLabel>Custom Name</UiLabel>
          <UiInput v-model="form.custom_name" placeholder="Item name" />
        </div>
        <div>
          <UiLabel>Custom Price</UiLabel>
          <UiInput type="number" v-model="form.custom_price" min="0" step="0.01" placeholder="From estimator" />
        </div>
      </div>

      <!-- Spool (color) picker -->
      <div>
        <UiLabel>Spool (color)</UiLabel>
        <UiSelect v-model="form.spool_id" :options="spoolOptions" />
      </div>

      <!-- Customer info -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <UiLabel>Customer Name</UiLabel>
          <UiInput v-model="form.customer_name" placeholder="Name" />
        </div>
        <div>
          <UiLabel>Contact</UiLabel>
          <UiInput v-model="form.customer_contact" placeholder="Phone, email, etc." />
        </div>
      </div>

      <div>
        <UiLabel>Location</UiLabel>
        <UiInput v-model="form.customer_location" placeholder="Where they are" />
      </div>

      <!-- Pricing, Status & Due Date -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <UiLabel>Price</UiLabel>
          <UiInput type="number" v-model="form.quoted_price" min="0" step="0.01" placeholder="What they'll pay" />
        </div>
        <div>
          <div class="flex items-center gap-2 mb-2">
            <UiLabel>Status</UiLabel>
            <UiTooltip content="Workflow: ordered → printed → finished → sold. Hardware deducts when status changes to 'finished'.">
              <HelpCircle class="h-4 w-4 text-muted-foreground cursor-help" />
            </UiTooltip>
          </div>
          <UiSelect v-model="form.status" :options="statusOptions" />
        </div>
        <div>
          <UiLabel>Due Date</UiLabel>
          <UiInput type="date" v-model="form.due_date" />
        </div>
      </div>

      <!-- Shipping (conditional) -->
      <div v-if="settings?.enable_shipping">
        <div class="flex items-center gap-2 mb-2">
          <UiLabel>Shipping Charge</UiLabel>
          <UiTooltip content="Additional shipping/handling fees. Added to total revenue.">
            <HelpCircle class="h-4 w-4 text-muted-foreground cursor-help" />
          </UiTooltip>
        </div>
        <UiInput type="number" v-model="form.shipping_charge" min="0" step="0.01" placeholder="0.00" />
      </div>

      <!-- Hardware Items -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <UiLabel class="mb-0">Hardware</UiLabel>
            <UiTooltip content="Add inventory items (tracked) or one-off purchases (just name + cost, no inventory deduction).">
              <HelpCircle class="h-4 w-4 text-muted-foreground cursor-help" />
            </UiTooltip>
          </div>
          <UiButton type="button" variant="outline" size="sm" @click="addHwEntry" :disabled="hardwareItems.length === 0 && hwEntries.length === 0">
            <Plus class="h-4 w-4 mr-1" />
            Add
          </UiButton>
        </div>

        <div v-if="hwEntries.length === 0" class="text-sm text-muted-foreground py-1">
          No hardware added.
        </div>

        <div class="space-y-2">
          <div
            v-for="(entry, i) in hwEntries"
            :key="i"
            class="rounded-md border p-3 space-y-2 bg-muted/20"
          >
            <!-- Type toggle -->
            <div class="flex items-center justify-between">
              <div class="flex gap-1 rounded-md border p-0.5 bg-background text-xs">
                <button
                  type="button"
                  class="flex items-center gap-1 px-2 py-1 rounded transition-colors"
                  :class="!entry.is_one_off ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'"
                  @click="entry.is_one_off = false"
                >
                  <Package class="h-3 w-3" />
                  Inventory
                </button>
                <button
                  type="button"
                  class="flex items-center gap-1 px-2 py-1 rounded transition-colors"
                  :class="entry.is_one_off ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'"
                  @click="entry.is_one_off = true"
                >
                  <Wrench class="h-3 w-3" />
                  One-Off
                </button>
              </div>
              <button type="button" @click="removeHwEntry(i)" class="text-muted-foreground hover:text-destructive transition-colors">
                <X class="h-4 w-4" />
              </button>
            </div>

            <!-- Inventory item fields -->
            <div v-if="!entry.is_one_off" class="grid grid-cols-[1fr_80px] gap-2">
              <div>
                <UiLabel class="text-xs">Item</UiLabel>
                <!-- Deleted item: show snapshot name as warning, not a dropdown -->
                <div
                  v-if="entry.deleted_name"
                  class="flex items-center gap-1 rounded-md border border-orange-300 bg-orange-50 dark:bg-orange-950/20 px-3 py-2 text-sm text-orange-700 dark:text-orange-400"
                >
                  <span class="truncate">{{ entry.deleted_name }}</span>
                  <span class="text-xs opacity-70 shrink-0">(removed)</span>
                </div>
                <UiSelect
                  v-else
                  v-model="entry.hardware_item_id"
                  :options="hardwareOptions"
                />
              </div>
              <div>
                <UiLabel class="text-xs">Qty</UiLabel>
                <UiInput type="number" v-model="entry.quantity" min="1" step="1" />
              </div>
            </div>

            <!-- One-off item fields -->
            <div v-else class="grid grid-cols-[1fr_100px] gap-2">
              <div>
                <UiLabel class="text-xs">Name</UiLabel>
                <UiInput v-model="entry.one_off_name" placeholder="e.g. M3 screws" />
              </div>
              <div>
                <UiLabel class="text-xs">Cost ($)</UiLabel>
                <UiInput type="number" v-model="entry.one_off_cost" min="0" step="0.01" placeholder="0.00" />
              </div>
            </div>
            <!-- Qty row for one-off -->
            <div v-if="entry.is_one_off" class="w-20">
              <UiLabel class="text-xs">Qty</UiLabel>
              <UiInput type="number" v-model="entry.quantity" min="1" step="1" />
            </div>
          </div>
        </div>
      </div>

      <div>
        <UiLabel>Notes</UiLabel>
        <UiTextarea v-model="form.notes" placeholder="Optional notes..." />
      </div>

      <p v-if="error" class="text-sm text-red-500">{{ error }}</p>

      <UiDialogFooter>
        <UiButton variant="outline" @click="emit('update:open', false)">Cancel</UiButton>
        <UiButton type="submit" :disabled="saving">
          {{ saving ? 'Saving...' : isEdit ? 'Update' : 'Create Order' }}
        </UiButton>
      </UiDialogFooter>
    </form>
  </UiDialog>
</template>
