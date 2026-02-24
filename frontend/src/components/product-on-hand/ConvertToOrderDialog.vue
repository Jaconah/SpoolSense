<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { api, type ProductOnHand } from '@/lib/api'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiDialogHeader from '@/components/ui/UiDialogHeader.vue'
import UiDialogTitle from '@/components/ui/UiDialogTitle.vue'
import UiDialogDescription from '@/components/ui/UiDialogDescription.vue'
import UiDialogFooter from '@/components/ui/UiDialogFooter.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiAlert from '@/components/ui/UiAlert.vue'

const props = defineProps<{
  open: boolean
  product?: ProductOnHand | null
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  converted: [orderId: number]
}>()

const converting = ref(false)
const error = ref('')

const form = ref({
  customer_name: '',
  customer_contact: '',
  customer_location: '',
  quoted_price: '',
})

const isGift = computed(() => form.value.quoted_price === '0' || form.value.quoted_price === '0.00')

watch(() => [props.product, props.open], () => {
  if (props.open && props.product) {
    form.value = {
      customer_name: '',
      customer_contact: '',
      customer_location: '',
      quoted_price: String(props.product.sell_price || 0),
    }
  } else {
    form.value = {
      customer_name: '',
      customer_contact: '',
      customer_location: '',
      quoted_price: '',
    }
  }
  error.value = ''
}, { immediate: true })

async function handleConvert() {
  if (!props.product) return

  converting.value = true
  error.value = ''

  try {
    const payload = {
      customer_name: form.value.customer_name || null,
      customer_contact: form.value.customer_contact || null,
      customer_location: form.value.customer_location || null,
      quoted_price: parseFloat(form.value.quoted_price) || 0,
    }

    const result = await api.post<{ order_id: number }>(`/products-on-hand/${props.product.id}/convert-to-order`, payload)

    emit('converted', result.order_id)
    emit('update:open', false)
  } catch (e: any) {
    error.value = e.message || 'Failed to convert to order'
  } finally {
    converting.value = false
  }
}
</script>

<template>
  <UiDialog :open="open" @update:open="emit('update:open', $event)">
    <UiDialogHeader>
      <UiDialogTitle>
        {{ isGift ? 'Mark as Gifted' : 'Convert to Order' }}
      </UiDialogTitle>
      <UiDialogDescription>
        {{ isGift
          ? 'Create a $0 order to track this gifted product'
          : 'Create an order from this finished product'
        }}
      </UiDialogDescription>
    </UiDialogHeader>

    <form @submit.prevent="handleConvert" class="space-y-4">
      <UiAlert v-if="error" variant="error">{{ error }}</UiAlert>

      <!-- Product Info -->
      <div v-if="product" class="rounded-md bg-muted p-3 text-sm">
        <div><strong>Product:</strong> {{ product.project_name }}</div>
        <div><strong>Color:</strong> {{ product.color }}</div>
        <div><strong>Location:</strong> {{ product.location }}</div>
        <div><strong>Cost:</strong> ${{ product.total_cost.toFixed(2) }}</div>
      </div>

      <div>
        <UiLabel for="quoted_price">Sale Price *</UiLabel>
        <UiInput
          id="quoted_price"
          v-model="form.quoted_price"
          type="number"
          step="0.01"
          required
        />
        <p class="text-xs text-muted-foreground mt-1">
          Enter 0 to mark as gifted
        </p>
      </div>

      <div>
        <UiLabel for="customer_name">Customer Name</UiLabel>
        <UiInput
          id="customer_name"
          v-model="form.customer_name"
          placeholder="Optional"
        />
      </div>

      <div>
        <UiLabel for="customer_contact">Contact Info</UiLabel>
        <UiInput
          id="customer_contact"
          v-model="form.customer_contact"
          placeholder="Email or phone (optional)"
        />
      </div>

      <div>
        <UiLabel for="customer_location">Customer Location</UiLabel>
        <UiInput
          id="customer_location"
          v-model="form.customer_location"
          placeholder="Optional"
        />
      </div>

      <UiDialogFooter>
        <UiButton
          type="button"
          variant="outline"
          @click="emit('update:open', false)"
        >
          Cancel
        </UiButton>
        <UiButton type="submit" :disabled="converting">
          {{ converting ? 'Converting...' : (isGift ? 'Mark as Gifted' : 'Create Order') }}
        </UiButton>
      </UiDialogFooter>
    </form>
  </UiDialog>
</template>
