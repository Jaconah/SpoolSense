<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import UiTextarea from '@/components/ui/UiTextarea.vue'
import UiSwitch from '@/components/ui/UiSwitch.vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiDialogHeader from '@/components/ui/UiDialogHeader.vue'
import UiDialogTitle from '@/components/ui/UiDialogTitle.vue'
import UiDialogDescription from '@/components/ui/UiDialogDescription.vue'
import UiDialogFooter from '@/components/ui/UiDialogFooter.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiAlertTitle from '@/components/ui/UiAlertTitle.vue'
import UiAlertDescription from '@/components/ui/UiAlertDescription.vue'
import UiTooltip from '@/components/ui/UiTooltip.vue'
import { AlertTriangle, HelpCircle } from 'lucide-vue-next'
import { api, type FilamentType, type Manufacturer, type Spool } from '@/lib/api'

const props = defineProps<{
  open: boolean
  spool?: Spool | null
  filamentTypes: FilamentType[]
  manufacturers: Manufacturer[]
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  saved: []
}>()

const isEdit = computed(() => !!props.spool)
const saving = ref(false)
const error = ref('')
const duplicateInfo = ref<any>(null)
const showDuplicateDialog = ref(false)

const form = ref({
  filament_type_id: '',
  manufacturer_id: '',
  color_name: '',
  color_hex: '#000000',
  total_weight_g: '1000',
  remaining_weight_g: '1000',
  cost_per_kg: '0',
  msrp: '',  // Customer pricing reference
  purchase_price: '',  // What you paid
  boughtOnSale: false,  // Toggle for showing purchase_price field
  // Legacy fields (for backwards compat during migration)
  normal_price: '',
  is_sale_price: false,
  tracking_id: '',
  location: '',
  notes: '',
  is_active: true,
})

// Calculate savings when on sale
const savedAmount = computed(() => {
  const msrp = Number(form.value.msrp) || 0
  const purchase = Number(form.value.purchase_price) || 0
  if (form.value.boughtOnSale && purchase > 0 && purchase < msrp) {
    return msrp - purchase
  }
  return 0
})

watch(
  () => [props.spool, props.open],
  () => {
    if (props.spool) {
      const msrp = props.spool.msrp || props.spool.normal_price || 0
      const purchasePrice = props.spool.purchase_price || props.spool.normal_price || 0
      const onSale = msrp > 0 && purchasePrice > 0 && purchasePrice < msrp

      form.value = {
        filament_type_id: String(props.spool.filament_type_id),
        manufacturer_id: String(props.spool.manufacturer_id),
        color_name: props.spool.color_name,
        color_hex: props.spool.color_hex,
        total_weight_g: String(props.spool.total_weight_g),
        remaining_weight_g: String(props.spool.remaining_weight_g),
        cost_per_kg: String(props.spool.cost_per_kg),
        msrp: String(msrp),
        purchase_price: String(purchasePrice),
        boughtOnSale: onSale,
        // Legacy fields
        normal_price: props.spool.normal_price ? String(props.spool.normal_price) : '',
        is_sale_price: props.spool.is_sale_price,
        tracking_id: props.spool.tracking_id || '',
        location: props.spool.location || '',
        notes: props.spool.notes || '',
        is_active: props.spool.is_active,
      }
    } else {
      form.value = {
        filament_type_id: props.filamentTypes[0]?.id ? String(props.filamentTypes[0].id) : '',
        manufacturer_id: props.manufacturers[0]?.id ? String(props.manufacturers[0].id) : '',
        color_name: '',
        color_hex: '#000000',
        total_weight_g: '1000',
        remaining_weight_g: '1000',
        cost_per_kg: '0',
        msrp: '',
        purchase_price: '',
        boughtOnSale: false,
        // Legacy fields
        normal_price: '',
        is_sale_price: false,
        tracking_id: '',
        location: '',
        notes: '',
        is_active: true,
      }
    }
    error.value = ''
  },
  { immediate: true }
)

// Auto-calculate cost_per_kg from purchase_price and total_weight_g (what you paid)
watch(
  () => [form.value.purchase_price, form.value.total_weight_g, form.value.boughtOnSale],
  ([pp, tw, onSale]) => {
    const purchasePrice = Number(pp)
    const totalWeight = Number(tw)
    if (purchasePrice > 0 && totalWeight > 0) {
      form.value.cost_per_kg = String(Math.round((purchasePrice / (totalWeight / 1000)) * 100) / 100)
    }
  }
)

// Auto-copy MSRP to purchase_price when not on sale or when MSRP changes
watch(
  () => [form.value.boughtOnSale, form.value.msrp],
  ([onSale, msrp]) => {
    if (!onSale && msrp) {
      form.value.purchase_price = form.value.msrp  // Use direct value to avoid type issues
    }
  }
)

// Track if user has manually edited the tracking ID
const trackingIdManuallyEdited = ref(false)
const isUpdatingProgrammatically = ref(false)

// Auto-generate tracking ID when filament type changes
watch(
  () => form.value.filament_type_id,
  async (newTypeId, oldTypeId) => {
    // Skip if editing existing spool or user manually edited tracking ID
    if (isEdit.value) {
      return
    }

    if (trackingIdManuallyEdited.value) {
      return
    }

    // Skip if no type selected
    if (!newTypeId) {
      return
    }

    try {
      const response = await api.get<{ tracking_id: string }>(`/spools/suggest-tracking-id?filament_type_id=${newTypeId}`)
      isUpdatingProgrammatically.value = true
      form.value.tracking_id = response.tracking_id
      // Keep flag true for next tick to ensure watcher sees it
      await new Promise(resolve => setTimeout(resolve, 0))
    } catch (e: any) {
      console.error('Failed to generate tracking ID:', e)
      console.error('Error details:', e.detail || e.message)
    } finally {
      isUpdatingProgrammatically.value = false
    }
  },
  { immediate: true }
)

// Track manual edits to tracking ID
watch(
  () => form.value.tracking_id,
  (newVal, oldVal) => {
    // Only mark as manually edited if user typed it (not programmatic update)
    if (oldVal !== undefined && newVal !== oldVal && !isEdit.value && !isUpdatingProgrammatically.value) {
      trackingIdManuallyEdited.value = true
    }
  }
)

// Reset manual edit flag when dialog opens/closes
watch(
  () => props.open,
  async (isOpen) => {
    if (isOpen && !props.spool) {
      trackingIdManuallyEdited.value = false
      // Auto-generate tracking ID for new spools
      if (form.value.filament_type_id) {
        try {
          const response = await api.get<{ tracking_id: string }>(`/spools/suggest-tracking-id?filament_type_id=${form.value.filament_type_id}`)
          isUpdatingProgrammatically.value = true
          form.value.tracking_id = response.tracking_id
          await new Promise(resolve => setTimeout(resolve, 0))
        } catch (e: any) {
          console.error('Failed to generate tracking ID:', e)
          console.error('Error details:', e.detail || e.message)
        } finally {
          isUpdatingProgrammatically.value = false
        }
      }
    }
  }
)

// Common filament color mappings (name -> hex code)
const colorMap: Record<string, string> = {
  // Reds
  'red': '#FF0000',
  'light red': '#FF6666',
  'dark red': '#8B0000',
  'crimson': '#DC143C',
  'maroon': '#800000',

  // Blues
  'blue': '#0000FF',
  'light blue': '#87CEEB',
  'dark blue': '#00008B',
  'navy': '#000080',
  'sky blue': '#87CEEB',
  'royal blue': '#4169E1',
  'cobalt': '#0047AB',

  // Greens
  'green': '#00FF00',
  'light green': '#90EE90',
  'dark green': '#006400',
  'lime': '#00FF00',
  'forest green': '#228B22',
  'olive': '#808000',
  'mint': '#98FF98',

  // Yellows
  'yellow': '#FFFF00',
  'light yellow': '#FFFFE0',
  'dark yellow': '#CCCC00',
  'gold': '#FFD700',
  'lemon': '#FFF44F',

  // Oranges
  'orange': '#FFA500',
  'light orange': '#FFB347',
  'dark orange': '#FF8C00',
  'coral': '#FF7F50',
  'peach': '#FFDAB9',

  // Purples
  'purple': '#800080',
  'light purple': '#DDA0DD',
  'dark purple': '#4B0082',
  'violet': '#8B00FF',
  'lavender': '#E6E6FA',
  'magenta': '#FF00FF',

  // Pinks
  'pink': '#FFC0CB',
  'light pink': '#FFB6C1',
  'dark pink': '#FF1493',
  'hot pink': '#FF69B4',
  'rose': '#FF007F',

  // Browns
  'brown': '#A52A2A',
  'light brown': '#D2691E',
  'dark brown': '#654321',
  'tan': '#D2B48C',
  'beige': '#F5F5DC',
  'copper': '#B87333',

  // Grays
  'gray': '#808080',
  'grey': '#808080',
  'light gray': '#D3D3D3',
  'light grey': '#D3D3D3',
  'dark gray': '#404040',
  'dark grey': '#404040',
  'silver': '#C0C0C0',
  'charcoal': '#36454F',

  // Black & White
  'black': '#000000',
  'white': '#FFFFFF',
  'off white': '#FAF9F6',
  'ivory': '#FFFFF0',

  // Cyans & Teals
  'cyan': '#00FFFF',
  'light cyan': '#E0FFFF',
  'dark cyan': '#008B8B',
  'teal': '#008080',
  'turquoise': '#40E0D0',
  'aqua': '#00FFFF',

  // Special filament colors
  'natural': '#F5F5DC',
  'transparent': '#FFFFFF',
  'clear': '#FFFFFF',
  'translucent': '#F0F0F0',
  'glow in the dark': '#E0FFE0',
  'neon green': '#39FF14',
  'neon pink': '#FF10F0',
  'neon yellow': '#FFFF33',
  'neon orange': '#FF6600',
}

const typeOptions = computed(() =>
  [...props.filamentTypes]
    .sort((a, b) => (b.usage_count || 0) - (a.usage_count || 0))
    .map((ft) => ({ value: String(ft.id), label: ft.name }))
)

const mfgOptions = computed(() =>
  [...props.manufacturers]
    .sort((a, b) => (b.usage_count || 0) - (a.usage_count || 0))
    .map((m) => ({ value: String(m.id), label: m.name }))
)

// Auto-fill color hex based on color name
watch(
  () => form.value.color_name,
  (colorName) => {
    if (!colorName) return

    // Check if user is editing an existing spool - don't override their color
    if (isEdit.value) return

    // Check if color hex has been manually changed from default
    if (form.value.color_hex !== '#000000') return

    // Try to find a matching color (case-insensitive)
    const normalizedName = colorName.toLowerCase().trim()
    const hexCode = colorMap[normalizedName]

    if (hexCode) {
      form.value.color_hex = hexCode
    }
  }
)

async function handleSubmit(forceDuplicate = false) {
  saving.value = true
  error.value = ''
  duplicateInfo.value = null
  try {
    const payload = {
      filament_type_id: Number(form.value.filament_type_id),
      manufacturer_id: Number(form.value.manufacturer_id),
      color_name: form.value.color_name,
      color_hex: form.value.color_hex,
      total_weight_g: Number(form.value.total_weight_g),
      remaining_weight_g: Number(form.value.remaining_weight_g),
      cost_per_kg: Number(form.value.cost_per_kg),

      // New pricing schema
      msrp: Number(form.value.msrp) || 0,
      purchase_price: Number(form.value.purchase_price) || 0,

      // Legacy fields (for backwards compatibility)
      normal_price: form.value.normal_price ? Number(form.value.normal_price) : null,
      is_sale_price: form.value.is_sale_price,

      tracking_id: form.value.tracking_id || null,
      location: form.value.location || null,
      notes: form.value.notes || null,
      is_active: form.value.is_active,
    }

    const url = isEdit.value ? `/spools/${props.spool!.id}` : '/spools'
    const queryParam = forceDuplicate ? '?force_duplicate=true' : ''

    if (isEdit.value) {
      await api.put(`${url}${queryParam}`, payload)
    } else {
      await api.post(`${url}${queryParam}`, payload)
    }
    emit('saved')
    emit('update:open', false)
  } catch (e: any) {
    // Check if it's a 409 duplicate error
    if (e.status === 409 && e.detail?.existing_spool) {
      duplicateInfo.value = e.detail.existing_spool
      showDuplicateDialog.value = true
    } else {
      error.value = e.message
    }
  } finally {
    saving.value = false
  }
}

async function handleMakeInactive() {
  if (!duplicateInfo.value) return
  try {
    // Make the existing spool inactive
    await api.put(`/spools/${duplicateInfo.value.id}`, { is_active: false })
    // Then submit with force flag
    await handleSubmit(true)
    showDuplicateDialog.value = false
  } catch (e: any) {
    error.value = e.message
  }
}

function handleChangeId() {
  showDuplicateDialog.value = false
  // Focus back on the tracking_id field
}
</script>

<template>
  <UiDialog :open="open" class="max-h-[90vh] overflow-y-auto sm:max-w-lg" @update:open="emit('update:open', $event)">
    <UiDialogHeader>
      <UiDialogTitle>{{ isEdit ? 'Edit Spool' : 'Add Spool' }}</UiDialogTitle>
      <UiDialogDescription>
        {{ isEdit ? 'Update spool details.' : 'Add a new filament spool to your inventory.' }}
      </UiDialogDescription>
    </UiDialogHeader>
    <form @submit.prevent="() => handleSubmit()" class="space-y-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <UiLabel>Filament Type</UiLabel>
          <UiSelect v-model="form.filament_type_id" :options="typeOptions" />
        </div>
        <div>
          <UiLabel>Manufacturer</UiLabel>
          <UiSelect v-model="form.manufacturer_id" :options="mfgOptions" />
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <UiLabel>Color Name</UiLabel>
          <UiInput v-model="form.color_name" placeholder="e.g. Matte Black" required />
        </div>
        <div>
          <UiLabel>Color</UiLabel>
          <div class="flex gap-2">
            <UiInput type="color" v-model="form.color_hex" class="h-10 w-14 p-1" />
            <UiInput v-model="form.color_hex" placeholder="#000000" class="flex-1" />
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <UiLabel>Total Weight (g)</UiLabel>
          <UiInput type="number" v-model="form.total_weight_g" min="0" step="1" />
        </div>
        <div>
          <UiLabel>Remaining (g)</UiLabel>
          <UiInput type="number" v-model="form.remaining_weight_g" min="0" step="1" />
        </div>
        <div>
          <div class="flex items-center gap-2 mb-2">
            <UiLabel>Cost/kg</UiLabel>
            <UiTooltip content="What you paid per kilogram. Auto-calculated from purchase price, or enter manually. Used for P&L calculations.">
              <HelpCircle class="h-4 w-4 text-muted-foreground cursor-help" />
            </UiTooltip>
          </div>
          <UiInput type="number" v-model="form.cost_per_kg" min="0" step="0.01" />
        </div>
      </div>

      <!-- Pricing Section (New Schema) -->
      <div class="space-y-4 p-4 border rounded-lg bg-muted/50">
        <div>
          <div class="flex items-center gap-2 mb-2">
            <UiLabel>MSRP / Regular Price</UiLabel>
            <UiTooltip content="Standard retail price. Used for customer pricing calculations.">
              <HelpCircle class="h-4 w-4 text-muted-foreground cursor-help" />
            </UiTooltip>
          </div>
          <UiInput type="number" v-model="form.msrp" min="0" step="0.01" placeholder="25.00" required />
        </div>

        <div class="flex items-center gap-2">
          <UiSwitch v-model="form.boughtOnSale" />
          <div class="flex items-center gap-2">
            <UiLabel>Bought on sale</UiLabel>
            <UiTooltip content="Enable if you purchased this spool at a discounted price.">
              <HelpCircle class="h-4 w-4 text-muted-foreground cursor-help" />
            </UiTooltip>
          </div>
        </div>

        <div v-if="form.boughtOnSale">
          <div class="flex items-center gap-2 mb-2">
            <UiLabel>Purchase Price (what you paid)</UiLabel>
            <UiTooltip content="The actual amount you paid. Used for P&L calculations.">
              <HelpCircle class="h-4 w-4 text-muted-foreground cursor-help" />
            </UiTooltip>
          </div>
          <UiInput type="number" v-model="form.purchase_price" min="0" step="0.01" placeholder="18.00" />
          <p v-if="savedAmount > 0" class="text-sm text-green-600 mt-1 flex items-center gap-1">
            ✓ Saved ${{ savedAmount.toFixed(2) }}
          </p>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <div class="flex items-center gap-2 mb-2">
            <UiLabel>Tracking ID</UiLabel>
            <UiTooltip content="Auto-generated ID like PLA01, ABS02, CF100. You can override manually if needed.">
              <HelpCircle class="h-4 w-4 text-muted-foreground cursor-help" />
            </UiTooltip>
          </div>
          <UiInput v-model="form.tracking_id" placeholder="Auto-generated (e.g., PLA01)" />
        </div>
        <div>
          <UiLabel>Location</UiLabel>
          <UiInput v-model="form.location" placeholder="Physical location (optional)" />
        </div>
      </div>

      <div class="flex items-center gap-2">
        <UiSwitch v-model="form.is_active" />
        <UiLabel>Active</UiLabel>
      </div>

      <div>
        <UiLabel>Notes</UiLabel>
        <UiTextarea v-model="form.notes" placeholder="Optional notes..." />
      </div>

      <p v-if="error" class="text-sm text-red-500">{{ error }}</p>

      <UiDialogFooter>
        <UiButton variant="outline" @click="emit('update:open', false)">Cancel</UiButton>
        <UiButton type="submit" :disabled="saving">
          {{ saving ? 'Saving...' : isEdit ? 'Update' : 'Add Spool' }}
        </UiButton>
      </UiDialogFooter>
    </form>
  </UiDialog>

  <!-- Duplicate Tracking ID Dialog -->
  <UiDialog :open="showDuplicateDialog" @update:open="showDuplicateDialog = $event">
    <UiDialogHeader>
      <UiDialogTitle>Duplicate Tracking ID</UiDialogTitle>
      <UiDialogDescription>
        This tracking ID is already in use by another spool.
      </UiDialogDescription>
    </UiDialogHeader>

    <UiAlert variant="warning" v-if="duplicateInfo">
      <AlertTriangle class="h-4 w-4" />
      <UiAlertTitle>Existing Spool</UiAlertTitle>
      <UiAlertDescription>
        <div class="mt-2 space-y-1 text-sm">
          <p><strong>Tracking ID:</strong> {{ duplicateInfo.tracking_id }}</p>
          <p><strong>Color:</strong> {{ duplicateInfo.color_name }}</p>
          <p><strong>Type:</strong> {{ duplicateInfo.filament_type }}</p>
          <p><strong>Manufacturer:</strong> {{ duplicateInfo.manufacturer }}</p>
          <p><strong>Remaining:</strong> {{ duplicateInfo.remaining_weight_g }}g</p>
          <p><strong>Status:</strong> {{ duplicateInfo.is_active ? 'Active' : 'Inactive' }}</p>
        </div>
      </UiAlertDescription>
    </UiAlert>

    <UiDialogFooter class="flex-col gap-2 sm:flex-row">
      <UiButton variant="outline" @click="handleChangeId">
        Change Tracking ID
      </UiButton>
      <UiButton variant="destructive" @click="handleMakeInactive">
        Make Old Spool Inactive & Continue
      </UiButton>
    </UiDialogFooter>
  </UiDialog>
</template>
