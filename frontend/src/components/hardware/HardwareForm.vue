<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import UiTextarea from '@/components/ui/UiTextarea.vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiDialogHeader from '@/components/ui/UiDialogHeader.vue'
import UiDialogTitle from '@/components/ui/UiDialogTitle.vue'
import UiDialogDescription from '@/components/ui/UiDialogDescription.vue'
import UiDialogFooter from '@/components/ui/UiDialogFooter.vue'
import UiTooltip from '@/components/ui/UiTooltip.vue'
import { HelpCircle } from 'lucide-vue-next'
import { api, type HardwareItem } from '@/lib/api'

const props = defineProps<{
  open: boolean
  item?: HardwareItem | null
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  saved: []
}>()

const isEdit = computed(() => !!props.item)
const saving = ref(false)
const error = ref('')

const form = ref({
  name: '',
  brand: '',
  purchase_url: '',
  purchase_price: '0',
  quantity_purchased: '1',
  quantity_in_stock: '0',
  low_stock_threshold: '',
  notes: '',
})

watch(
  () => [props.item, props.open],
  () => {
    if (props.item) {
      form.value = {
        name: props.item.name,
        brand: props.item.brand || '',
        purchase_url: props.item.purchase_url || '',
        purchase_price: String(props.item.purchase_price),
        quantity_purchased: String(props.item.quantity_purchased),
        quantity_in_stock: String(props.item.quantity_in_stock),
        low_stock_threshold: props.item.low_stock_threshold ? String(props.item.low_stock_threshold) : '',
        notes: props.item.notes || '',
      }
    } else {
      form.value = {
        name: '',
        brand: '',
        purchase_url: '',
        purchase_price: '0',
        quantity_purchased: '1',
        quantity_in_stock: '0',
        low_stock_threshold: '',
        notes: '',
      }
    }
    error.value = ''
  },
  { immediate: true }
)

const costPerItem = computed(() => {
  const price = Number(form.value.purchase_price)
  const qty = Number(form.value.quantity_purchased)
  if (qty <= 0 || price <= 0) return 0
  return Math.round((price / qty) * 10000) / 10000
})

async function handleSubmit() {
  saving.value = true
  error.value = ''
  try {
    const payload = {
      name: form.value.name,
      brand: form.value.brand || null,
      purchase_url: form.value.purchase_url || null,
      purchase_price: Number(form.value.purchase_price),
      quantity_purchased: Number(form.value.quantity_purchased),
      quantity_in_stock: Number(form.value.quantity_in_stock),
      low_stock_threshold: form.value.low_stock_threshold ? Number(form.value.low_stock_threshold) : null,
      notes: form.value.notes || null,
    }
    if (isEdit.value) {
      await api.put(`/hardware/${props.item!.id}`, payload)
    } else {
      await api.post('/hardware', payload)
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
  <UiDialog :open="open" class="sm:max-w-lg" @update:open="emit('update:open', $event)">
    <UiDialogHeader>
      <UiDialogTitle>{{ isEdit ? 'Edit Hardware' : 'Add Hardware' }}</UiDialogTitle>
      <UiDialogDescription>
        {{ isEdit ? 'Update hardware item details.' : 'Add a new hardware item to your inventory.' }}
      </UiDialogDescription>
    </UiDialogHeader>
    <form @submit.prevent="handleSubmit" class="space-y-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <UiLabel>Name</UiLabel>
          <UiInput v-model="form.name" placeholder="e.g. 608ZZ Bearing" required />
        </div>
        <div>
          <UiLabel>Brand</UiLabel>
          <UiInput v-model="form.brand" placeholder="Optional" />
        </div>
      </div>

      <div>
        <UiLabel>Purchase URL</UiLabel>
        <UiInput v-model="form.purchase_url" placeholder="https://..." />
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <div class="flex items-center gap-2 mb-2">
            <UiLabel>Total Price</UiLabel>
            <UiTooltip content="Total price paid for all items in this purchase.">
              <HelpCircle class="h-4 w-4 text-muted-foreground cursor-help" />
            </UiTooltip>
          </div>
          <UiInput type="number" v-model="form.purchase_price" min="0" step="0.01" />
        </div>
        <div>
          <div class="flex items-center gap-2 mb-2">
            <UiLabel>Qty Purchased</UiLabel>
            <UiTooltip content="Total items bought in this order.">
              <HelpCircle class="h-4 w-4 text-muted-foreground cursor-help" />
            </UiTooltip>
          </div>
          <UiInput type="number" v-model="form.quantity_purchased" min="1" step="1" />
        </div>
        <div>
          <UiLabel>Cost/Item</UiLabel>
          <div class="flex h-10 items-center rounded-md border bg-muted/50 px-3 text-sm">
            ${{ costPerItem.toFixed(4) }}
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <div class="flex items-center gap-2 mb-2">
            <UiLabel>Qty In Stock</UiLabel>
            <UiTooltip content="Items remaining. Updates when used in orders marked 'finished'.">
              <HelpCircle class="h-4 w-4 text-muted-foreground cursor-help" />
            </UiTooltip>
          </div>
          <UiInput type="number" v-model="form.quantity_in_stock" min="0" step="1" />
        </div>
        <div>
          <UiLabel>Low Stock Alert</UiLabel>
          <UiInput type="number" v-model="form.low_stock_threshold" min="0" step="1" placeholder="Optional" />
          <p class="mt-1 text-xs text-muted-foreground">
            Alert when stock reaches this level
          </p>
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
          {{ saving ? 'Saving...' : isEdit ? 'Update' : 'Add Item' }}
        </UiButton>
      </UiDialogFooter>
    </form>
  </UiDialog>
</template>
