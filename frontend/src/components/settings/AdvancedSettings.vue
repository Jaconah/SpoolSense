<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import UiSwitch from '@/components/ui/UiSwitch.vue'
import UiTooltip from '@/components/ui/UiTooltip.vue'
import { HelpCircle } from 'lucide-vue-next'
import { api, type Settings } from '@/lib/api'

const props = defineProps<{ settings: Settings }>()
const emit = defineEmits<{ saved: [] }>()

function parseEvents(raw: string): string[] {
  try { return JSON.parse(raw) } catch { return [] }
}

const fee = ref(String(props.settings.profit_margin_percent))
const webhookUrl = ref(props.settings.webhook_url || '')
const webhookEnabled = ref(props.settings.webhook_enabled)
const webhookEvents = ref<string[]>(parseEvents(props.settings.webhook_events))
const webhookOrderDueDays = ref(String(props.settings.webhook_order_due_days ?? 2))
const lowSpoolThreshold = ref(String(props.settings.low_spool_threshold_g || 50))
const showSpoolLocation = ref(props.settings.show_spool_location ?? true)

// Feature Toggles
const enableHardware = ref(props.settings.enable_hardware ?? true)
const enableProjects = ref(props.settings.enable_projects ?? true)
const enableOrders = ref(props.settings.enable_orders ?? true)
const enableProductsOnHand = ref(props.settings.enable_products_on_hand ?? true)

// Spool Validation
const enableSpoolPrevention = ref(props.settings.enable_spool_negative_prevention ?? true)
const minimumReserve = ref(String(props.settings.minimum_spool_reserve_g || 5))
const enableLowSpoolAlerts = ref(props.settings.enable_low_spool_alerts ?? true)
const enableTrackingIdAuto = ref(props.settings.enable_tracking_id_auto_generation ?? true)

const saving = ref(false)
const testing = ref(false)
const message = ref('')

const eventOrderDue = computed({
  get: () => webhookEvents.value.includes('order_due'),
  set: (v) => toggleEvent('order_due', v),
})
const eventOrderStatus = computed({
  get: () => webhookEvents.value.includes('order_status_change'),
  set: (v) => toggleEvent('order_status_change', v),
})
const eventLowStock = computed({
  get: () => webhookEvents.value.includes('low_stock'),
  set: (v) => toggleEvent('low_stock', v),
})

function toggleEvent(event: string, enabled: boolean) {
  if (enabled) {
    if (!webhookEvents.value.includes(event)) webhookEvents.value.push(event)
  } else {
    webhookEvents.value = webhookEvents.value.filter(e => e !== event)
  }
}

watch(() => props.settings, (s) => {
  fee.value = String(s.profit_margin_percent)
  webhookUrl.value = s.webhook_url || ''
  webhookEnabled.value = s.webhook_enabled
  webhookEvents.value = parseEvents(s.webhook_events)
  webhookOrderDueDays.value = String(s.webhook_order_due_days ?? 2)
  lowSpoolThreshold.value = String(s.low_spool_threshold_g || 50)
  showSpoolLocation.value = s.show_spool_location ?? true

  // Feature Toggles
  enableHardware.value = s.enable_hardware ?? true
  enableProjects.value = s.enable_projects ?? true
  enableOrders.value = s.enable_orders ?? true
  enableProductsOnHand.value = s.enable_products_on_hand ?? true

  // Spool Validation
  enableSpoolPrevention.value = s.enable_spool_negative_prevention ?? true
  minimumReserve.value = String(s.minimum_spool_reserve_g || 5)
  enableLowSpoolAlerts.value = s.enable_low_spool_alerts ?? true
  enableTrackingIdAuto.value = s.enable_tracking_id_auto_generation ?? true
})

async function handleSubmit() {
  saving.value = true
  message.value = ''
  try {
    await api.patch('/settings', {
      profit_margin_percent: Number(fee.value),
      webhook_url: webhookUrl.value || null,
      webhook_enabled: webhookEnabled.value,
      webhook_events: JSON.stringify(webhookEvents.value),
      webhook_order_due_days: Number(webhookOrderDueDays.value),
      low_spool_threshold_g: Number(lowSpoolThreshold.value),
      show_spool_location: showSpoolLocation.value,

      // Feature Toggles
      enable_hardware: enableHardware.value,
      enable_projects: enableProjects.value,
      enable_orders: enableOrders.value,
      enable_products_on_hand: enableProductsOnHand.value,

      // Spool Validation
      enable_spool_negative_prevention: enableSpoolPrevention.value,
      minimum_spool_reserve_g: Number(minimumReserve.value),
      enable_low_spool_alerts: enableLowSpoolAlerts.value,
      enable_tracking_id_auto_generation: enableTrackingIdAuto.value,
    })
    message.value = 'Settings saved!'
    emit('saved')
  } catch (e: any) {
    message.value = `Error: ${e.message}`
  } finally {
    saving.value = false
  }
}

async function testNotifications() {
  testing.value = true
  message.value = ''
  try {
    const result = await api.post<{ notifications_sent: number }>('/orders/check-notifications', {})
    message.value = `Test completed. Sent ${result.notifications_sent} notification(s).`
  } catch (e: any) {
    message.value = `Test failed: ${e.message}`
  } finally {
    testing.value = false
  }
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="space-y-6">
    <div class="max-w-sm">
      <UiLabel>Service Fee %</UiLabel>
      <UiInput type="number" v-model="fee" min="0" max="100" step="0.1" />
      <p class="mt-1 text-xs text-muted-foreground">
        Applied to cost estimates to cover overhead. This is added on top of the
        calculated subtotal.
      </p>
    </div>

    <div class="space-y-4 rounded-lg border p-4">
      <h3 class="font-medium">Webhook Notifications</h3>
      <div class="flex items-center justify-between">
        <div>
          <UiLabel>Enable Webhooks</UiLabel>
          <p class="mt-1 text-xs text-muted-foreground">
            Send HTTP POST notifications to any HTTPS URL
          </p>
        </div>
        <UiSwitch v-model="webhookEnabled" />
      </div>

      <div v-if="webhookEnabled" class="space-y-4">
        <div>
          <UiLabel>Webhook URL</UiLabel>
          <UiInput v-model="webhookUrl" type="url" placeholder="https://your-service.example.com/webhook" />
          <p class="mt-1 text-xs text-muted-foreground">
            Any HTTPS endpoint — compatible with Discord, Slack, Make.com, n8n, or custom services.
          </p>
        </div>

        <div class="space-y-3">
          <UiLabel>Events to send</UiLabel>

          <div class="space-y-2 pl-1">
            <div class="flex items-center gap-3">
              <input
                type="checkbox"
                id="evt-order-due"
                v-model="eventOrderDue"
                class="h-4 w-4 rounded border-border accent-primary"
              />
              <div>
                <label for="evt-order-due" class="text-sm font-medium cursor-pointer">Order due soon</label>
                <p class="text-xs text-muted-foreground">Daily check for orders approaching their due date</p>
              </div>
            </div>

            <div v-if="eventOrderDue" class="ml-7 max-w-[160px]">
              <div class="flex items-center gap-2 mb-1">
                <UiLabel>Days before due date</UiLabel>
                <UiTooltip content="Alert this many days before an order's due date (1–7)">
                  <HelpCircle class="h-4 w-4 text-muted-foreground cursor-help" />
                </UiTooltip>
              </div>
              <UiInput type="number" v-model="webhookOrderDueDays" min="1" max="7" step="1" />
            </div>

            <div class="flex items-center gap-3">
              <input
                type="checkbox"
                id="evt-order-status"
                v-model="eventOrderStatus"
                class="h-4 w-4 rounded border-border accent-primary"
              />
              <div>
                <label for="evt-order-status" class="text-sm font-medium cursor-pointer">Order status changed</label>
                <p class="text-xs text-muted-foreground">Fires whenever an order moves to a new status</p>
              </div>
            </div>

            <div class="flex items-center gap-3">
              <input
                type="checkbox"
                id="evt-low-stock"
                v-model="eventLowStock"
                class="h-4 w-4 rounded border-border accent-primary"
              />
              <div>
                <label for="evt-low-stock" class="text-sm font-medium cursor-pointer">Low stock alert</label>
                <p class="text-xs text-muted-foreground">Fires when a spool drops below the alert threshold</p>
              </div>
            </div>
          </div>
        </div>

        <UiButton
          type="button"
          variant="outline"
          size="sm"
          :disabled="testing || !webhookUrl"
          @click="testNotifications"
        >
          {{ testing ? 'Testing...' : 'Test Webhook' }}
        </UiButton>
      </div>
    </div>

    <div class="space-y-4 rounded-lg border p-4">
      <h3 class="font-medium">Feature Modules</h3>
      <p class="text-xs text-muted-foreground">Enable or disable features you don't need</p>
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <div>
            <UiLabel>Hardware Management</UiLabel>
            <p class="mt-1 text-xs text-muted-foreground">Track hardware parts inventory</p>
          </div>
          <UiSwitch v-model="enableHardware" />
        </div>
        <div class="flex items-center justify-between">
          <div>
            <UiLabel>Projects (Templates)</UiLabel>
            <p class="mt-1 text-xs text-muted-foreground">Reusable product templates</p>
          </div>
          <UiSwitch v-model="enableProjects" />
        </div>
        <div class="flex items-center justify-between">
          <div>
            <UiLabel>Customer Orders</UiLabel>
            <p class="mt-1 text-xs text-muted-foreground">Track customer orders and fulfillment</p>
          </div>
          <UiSwitch v-model="enableOrders" />
        </div>
        <div class="flex items-center justify-between">
          <div>
            <UiLabel>Products on Hand</UiLabel>
            <p class="mt-1 text-xs text-muted-foreground">Manage finished product inventory</p>
          </div>
          <UiSwitch v-model="enableProductsOnHand" />
        </div>
      </div>
    </div>

    <div class="space-y-4 rounded-lg border p-4">
      <h3 class="font-medium">Spool Validation</h3>
      <div class="flex items-center justify-between">
        <div>
          <div class="flex items-center gap-2">
            <UiLabel>Prevent Negative Weight</UiLabel>
            <UiTooltip content="Hard block operations that would cause spool weight to go below reserve amount">
              <HelpCircle class="h-4 w-4 text-muted-foreground cursor-help" />
            </UiTooltip>
          </div>
          <p class="mt-1 text-xs text-muted-foreground">
            Block print jobs/orders that would overdraw spools
          </p>
        </div>
        <UiSwitch v-model="enableSpoolPrevention" />
      </div>
      <div v-if="enableSpoolPrevention" class="max-w-sm pl-4 border-l-2">
        <div class="flex items-center gap-2 mb-2">
          <UiLabel>Minimum Reserve (grams)</UiLabel>
          <UiTooltip content="Minimum grams to keep in reserve. Accounts for waste/purge. Default: 5g.">
            <HelpCircle class="h-4 w-4 text-muted-foreground cursor-help" />
          </UiTooltip>
        </div>
        <UiInput type="number" v-model="minimumReserve" min="0" max="100" step="0.1" />
        <p class="mt-1 text-xs text-muted-foreground">
          Protects against filament loss during purge/failures
        </p>
      </div>
    </div>

    <div class="space-y-4 rounded-lg border p-4">
      <h3 class="font-medium">Spool Tracking</h3>
      <div class="flex items-center justify-between">
        <div>
          <UiLabel>Low Spool Alerts</UiLabel>
          <p class="mt-1 text-xs text-muted-foreground">
            Show alerts when spools drop below threshold
          </p>
        </div>
        <UiSwitch v-model="enableLowSpoolAlerts" />
      </div>
      <div v-if="enableLowSpoolAlerts" class="max-w-sm pl-4 border-l-2">
        <div class="flex items-center gap-2 mb-2">
          <UiLabel>Alert Threshold (grams)</UiLabel>
          <UiTooltip content="Alert when spool weight drops below this amount in grams. Default: 50g.">
            <HelpCircle class="h-4 w-4 text-muted-foreground cursor-help" />
          </UiTooltip>
        </div>
        <UiInput type="number" v-model="lowSpoolThreshold" min="0" step="1" />
      </div>
      <div class="flex items-center justify-between">
        <div>
          <UiLabel>Auto-Generate Tracking IDs</UiLabel>
          <p class="mt-1 text-xs text-muted-foreground">
            Automatically generate PLA01, ABS02, etc.
          </p>
        </div>
        <UiSwitch v-model="enableTrackingIdAuto" />
      </div>
      <div class="flex items-center justify-between">
        <div>
          <UiLabel>Show Location Field</UiLabel>
          <p class="mt-1 text-xs text-muted-foreground">
            Display physical location field for spools
          </p>
        </div>
        <UiSwitch v-model="showSpoolLocation" />
      </div>
    </div>

    <p
      v-if="message"
      :class="['text-sm', message.startsWith('Error') || message.startsWith('Test failed') ? 'text-red-500' : 'text-green-600']"
    >
      {{ message }}
    </p>
    <UiButton type="submit" :disabled="saving">
      {{ saving ? 'Saving...' : 'Save' }}
    </UiButton>
  </form>
</template>
