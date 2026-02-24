<script setup lang="ts">
import { ref, watch } from 'vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import UiSwitch from '@/components/ui/UiSwitch.vue'
import { api, type Settings } from '@/lib/api'

const props = defineProps<{ settings: Settings }>()
const emit = defineEmits<{ saved: [] }>()

const form = ref({
  currency_symbol: props.settings.currency_symbol,
  electricity_rate_kwh: String(props.settings.electricity_rate_kwh),
  printer_wattage: String(props.settings.printer_wattage),
  hourly_rate: String(props.settings.hourly_rate),
  machine_depreciation_rate: String(props.settings.machine_depreciation_rate),
  fixed_fee_per_order: String(props.settings.fixed_fee_per_order),
  enable_shipping: props.settings.enable_shipping,
  default_shipping_charge: String(props.settings.default_shipping_charge),
})
const saving = ref(false)
const message = ref('')

watch(() => props.settings, (s) => {
  form.value = {
    currency_symbol: s.currency_symbol,
    electricity_rate_kwh: String(s.electricity_rate_kwh),
    printer_wattage: String(s.printer_wattage),
    hourly_rate: String(s.hourly_rate),
    machine_depreciation_rate: String(s.machine_depreciation_rate),
    fixed_fee_per_order: String(s.fixed_fee_per_order),
    enable_shipping: s.enable_shipping,
    default_shipping_charge: String(s.default_shipping_charge),
  }
})

async function handleSubmit() {
  saving.value = true
  message.value = ''
  try {
    await api.patch('/settings', {
      currency_symbol: form.value.currency_symbol,
      electricity_rate_kwh: Number(form.value.electricity_rate_kwh),
      printer_wattage: Number(form.value.printer_wattage),
      hourly_rate: Number(form.value.hourly_rate),
      machine_depreciation_rate: Number(form.value.machine_depreciation_rate),
      fixed_fee_per_order: Number(form.value.fixed_fee_per_order),
      enable_shipping: form.value.enable_shipping,
      default_shipping_charge: Number(form.value.default_shipping_charge),
    })
    message.value = 'Settings saved!'
    emit('saved')
  } catch (e: any) {
    message.value = `Error: ${e.message}`
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="space-y-4">
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div>
        <UiLabel>Currency Symbol</UiLabel>
        <UiInput v-model="form.currency_symbol" :max-length="10" />
      </div>
      <div>
        <UiLabel>Electricity Rate (per kWh)</UiLabel>
        <UiInput type="number" v-model="form.electricity_rate_kwh" min="0" step="0.01" />
      </div>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <div>
        <UiLabel>Printer Wattage</UiLabel>
        <UiInput type="number" v-model="form.printer_wattage" min="0" step="1" />
      </div>
      <div>
        <UiLabel>Hourly Rate ({{ form.currency_symbol }}/hr)</UiLabel>
        <UiInput type="number" v-model="form.hourly_rate" min="0" step="0.01" />
      </div>
    </div>
    <div>
      <UiLabel>Machine Depreciation Rate ({{ form.currency_symbol }}/hr)</UiLabel>
      <UiInput type="number" v-model="form.machine_depreciation_rate" min="0" step="0.01" />
    </div>
    <div>
      <UiLabel>Fixed Fee Per Order ({{ form.currency_symbol }})</UiLabel>
      <UiInput type="number" v-model="form.fixed_fee_per_order" min="0" step="0.01" />
      <p class="mt-1 text-xs text-muted-foreground">Applied to cost estimator only, not orders</p>
    </div>
    <div class="space-y-4 rounded-lg border p-4">
      <h3 class="font-medium">Shipping</h3>
      <div class="flex items-center justify-between">
        <UiLabel>Enable Shipping</UiLabel>
        <UiSwitch v-model="form.enable_shipping" />
      </div>
      <div v-if="form.enable_shipping">
        <UiLabel>Default Shipping Charge ({{ form.currency_symbol }})</UiLabel>
        <UiInput type="number" v-model="form.default_shipping_charge" min="0" step="0.01" />
      </div>
    </div>
    <p
      v-if="message"
      :class="['text-sm', message.startsWith('Error') ? 'text-red-500' : 'text-green-600']"
    >
      {{ message }}
    </p>
    <UiButton type="submit" :disabled="saving">
      {{ saving ? 'Saving...' : 'Save Settings' }}
    </UiButton>
  </form>
</template>
