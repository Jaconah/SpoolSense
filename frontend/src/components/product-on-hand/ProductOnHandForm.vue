<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { api, type ProductOnHand } from '@/lib/api'
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
import UiTooltip from '@/components/ui/UiTooltip.vue'
import { HelpCircle } from 'lucide-vue-next'

const props = defineProps<{
  open: boolean
  productOnHand?: ProductOnHand | null
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  saved: []
}>()

const isEdit = computed(() => !!props.productOnHand)
const saving = ref(false)
const error = ref('')

const form = ref({
  name: '',
  status: 'completed',
  location: '',
  notes: '',
})

watch(() => [props.productOnHand, props.open], () => {
  if (props.open && props.productOnHand) {
    form.value = {
      name: props.productOnHand.name,
      status: props.productOnHand.status,
      location: props.productOnHand.location || '',
      notes: props.productOnHand.notes || '',
    }
  } else {
    form.value = { name: '', status: 'completed', location: '', notes: '' }
  }
  error.value = ''
}, { immediate: true })

async function handleSubmit() {
  if (!form.value.name.trim()) {
    error.value = 'Product name is required'
    return
  }

  // If status is completed, location is required
  if (form.value.status === 'completed' && !form.value.location?.trim()) {
    error.value = 'Location is required when status is completed'
    return
  }

  saving.value = true
  error.value = ''

  try {
    const payload = {
      name: form.value.name,
      status: form.value.status,
      location: form.value.location?.trim() || null,
      notes: form.value.notes || null,
    }

    if (isEdit.value) {
      await api.put(`/products-on-hand/${props.productOnHand!.id}`, payload)
    } else {
      // Should not reach here - creation happens from PrintJobsPage
      throw new Error('Cannot create Product on Hand from this form')
    }

    emit('saved')
    emit('update:open', false)
  } catch (e: any) {
    error.value = e.message || 'Failed to save'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <UiDialog :open="open" @update:open="emit('update:open', $event)">
    <UiDialogHeader>
      <UiDialogTitle>Edit Product on Hand</UiDialogTitle>
      <UiDialogDescription>
        Update product details, status, and location
      </UiDialogDescription>
    </UiDialogHeader>

    <form @submit.prevent="handleSubmit" class="space-y-4">
      <UiAlert v-if="error" variant="error">{{ error }}</UiAlert>

      <!-- Product Info -->
      <div v-if="productOnHand" class="rounded-md bg-muted p-3 text-sm">
        <div><strong>Color:</strong> {{ productOnHand.color }}</div>
        <div v-if="productOnHand.project_name"><strong>Project:</strong> {{ productOnHand.project_name }}</div>
        <div><strong>Cost:</strong> ${{ productOnHand.total_cost.toFixed(2) }}</div>
      </div>

      <div>
        <UiLabel for="name">Product Name *</UiLabel>
        <UiInput
          id="name"
          v-model="form.name"
          placeholder="Product name"
          required
        />
      </div>

      <div>
        <UiLabel for="status">Status *</UiLabel>
        <UiSelect
          id="status"
          v-model="form.status"
          :options="[
            { value: 'printed', label: 'Printed (Needs Assembly)' },
            { value: 'completed', label: 'Completed (Ready to Sell)' }
          ]"
        />
        <p class="text-xs text-muted-foreground mt-1">
          <span v-if="form.status === 'printed'">Product needs hardware assembly</span>
          <span v-else>Product is ready to sell</span>
        </p>
      </div>

      <div>
        <div class="flex items-center gap-2 mb-2">
          <UiLabel for="location">
            Location {{ form.status === 'completed' ? '*' : '(Optional)' }}
          </UiLabel>
          <UiTooltip content="Where this finished product is stored (e.g., Car, Locker, Bag).">
            <HelpCircle class="h-4 w-4 text-muted-foreground cursor-help" />
          </UiTooltip>
        </div>
        <UiInput
          id="location"
          v-model="form.location"
          placeholder="Car, Locker, Bag, etc."
          :required="form.status === 'completed'"
        />
        <p v-if="form.status === 'printed'" class="text-xs text-muted-foreground mt-1">
          Add location when marking as completed
        </p>
      </div>

      <div>
        <UiLabel for="notes">Notes</UiLabel>
        <UiTextarea
          id="notes"
          v-model="form.notes"
          placeholder="Optional notes..."
          :rows="3"
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
        <UiButton type="submit" :disabled="saving">
          {{ saving ? 'Saving...' : 'Save Changes' }}
        </UiButton>
      </UiDialogFooter>
    </form>
  </UiDialog>
</template>
