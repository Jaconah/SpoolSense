<script setup lang="ts">
import { ref, computed } from 'vue'
import { useSpools, useSettings } from '@/composables/use-data'
import UiButton from '@/components/ui/UiButton.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiCardHeader from '@/components/ui/UiCardHeader.vue'
import UiCardTitle from '@/components/ui/UiCardTitle.vue'
import UiCardContent from '@/components/ui/UiCardContent.vue'
import UiTabs from '@/components/ui/UiTabs.vue'
import UiTabsList from '@/components/ui/UiTabsList.vue'
import UiTab from '@/components/ui/UiTab.vue'
import UiTabPanels from '@/components/ui/UiTabPanels.vue'
import UiTabPanel from '@/components/ui/UiTabPanel.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import { api, type CostBreakdown } from '@/lib/api'
import { Calculator, FileText } from 'lucide-vue-next'

const { data: spools } = useSpools()
const { data: settings } = useSettings()

// Spool-based estimate
const spoolId = ref('')
const grams = ref('')
const hours = ref('')

// Quick estimate
const quickCostPerKg = ref('25')
const quickGrams = ref('')
const quickHours = ref('')

const result = ref<CostBreakdown | null>(null)
const loading = ref(false)
const error = ref('')
const showQuote = ref(false)

const currency = computed(() => result.value?.currency_symbol || settings.value?.currency_symbol || '$')

const spoolOptions = computed(() =>
  spools.value?.map((s) => ({
    value: String(s.id),
    label: `#${s.id} ${s.color_name} - ${s.filament_type.name} (${currency.value}${s.cost_per_kg}/kg)`,
  })) || []
)

async function handleSpoolEstimate() {
  loading.value = true
  error.value = ''
  try {
    result.value = await api.post<CostBreakdown>('/cost-estimate', {
      spool_id: Number(spoolId.value),
      grams: Number(grams.value),
      print_time_minutes: Number(hours.value) * 60,
    })
    showQuote.value = true
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function handleQuickEstimate() {
  loading.value = true
  error.value = ''
  try {
    result.value = await api.post<CostBreakdown>('/cost-estimate/quick', {
      cost_per_kg: Number(quickCostPerKg.value),
      grams: Number(quickGrams.value),
      print_time_minutes: Number(quickHours.value) * 60,
    })
    showQuote.value = true
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-3xl font-bold">Cost Estimator</h1>

    <div class="grid gap-6 lg:grid-cols-2">
      <!-- Input Form -->
      <UiCard>
        <UiCardHeader>
          <UiCardTitle class="flex items-center gap-2">
            <Calculator class="h-5 w-5" /> Estimate Cost
          </UiCardTitle>
        </UiCardHeader>
        <UiCardContent>
          <UiTabs>
            <UiTabsList class="w-full">
              <UiTab class="flex-1">From Spool</UiTab>
              <UiTab class="flex-1">Quick Estimate</UiTab>
            </UiTabsList>

            <UiTabPanels>
              <UiTabPanel>
                <form @submit.prevent="handleSpoolEstimate" class="space-y-4 pt-4">
                  <div>
                    <UiLabel>Spool</UiLabel>
                    <UiSelect v-model="spoolId" :options="spoolOptions" placeholder="Select a spool" />
                  </div>
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <UiLabel>Filament (grams)</UiLabel>
                      <UiInput v-model="grams" type="number" min="0.1" step="0.1" required />
                    </div>
                    <div>
                      <UiLabel>Print Time (hours)</UiLabel>
                      <UiInput v-model="hours" type="number" min="0.1" step="0.1" required />
                    </div>
                  </div>
                  <UiButton type="submit" :disabled="loading" class="w-full">
                    {{ loading ? 'Calculating...' : 'Calculate' }}
                  </UiButton>
                </form>
              </UiTabPanel>

              <UiTabPanel>
                <form @submit.prevent="handleQuickEstimate" class="space-y-4 pt-4">
                  <div>
                    <UiLabel>Cost per kg ({{ currency }})</UiLabel>
                    <UiInput v-model="quickCostPerKg" type="number" min="0" step="0.01" required />
                  </div>
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <UiLabel>Filament (grams)</UiLabel>
                      <UiInput v-model="quickGrams" type="number" min="0.1" step="0.1" required />
                    </div>
                    <div>
                      <UiLabel>Print Time (hours)</UiLabel>
                      <UiInput v-model="quickHours" type="number" min="0.1" step="0.1" required />
                    </div>
                  </div>
                  <UiButton type="submit" :disabled="loading" class="w-full">
                    {{ loading ? 'Calculating...' : 'Calculate' }}
                  </UiButton>
                </form>
              </UiTabPanel>
            </UiTabPanels>
          </UiTabs>
          <p v-if="error" class="mt-4 text-sm text-red-500">{{ error }}</p>
        </UiCardContent>
      </UiCard>

      <!-- Results -->
      <div class="space-y-4">
        <UiCard v-if="result && showQuote" class="border-2 border-primary">
          <UiCardHeader class="text-center">
            <UiCardTitle class="text-2xl">Quote</UiCardTitle>
          </UiCardHeader>
          <UiCardContent class="text-center">
            <p class="text-5xl font-bold">{{ currency }}{{ result.total.toFixed(2) }}</p>
            <p class="mt-2 text-muted-foreground">Estimated print cost</p>
            <UiButton class="mt-6" variant="outline" @click="showQuote = false">
              View Breakdown
            </UiButton>
          </UiCardContent>
        </UiCard>

        <UiCard v-if="result && !showQuote">
          <UiCardHeader>
            <UiCardTitle>Cost Breakdown (Internal)</UiCardTitle>
          </UiCardHeader>
          <UiCardContent>
            <div class="space-y-3">
              <div class="flex justify-between">
                <span class="text-muted-foreground">Filament Cost</span>
                <span>{{ currency }}{{ result.filament_cost.toFixed(2) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-muted-foreground">Electricity Cost</span>
                <span>{{ currency }}{{ result.electricity_cost.toFixed(2) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-muted-foreground">Time Cost</span>
                <span>{{ currency }}{{ result.time_cost.toFixed(2) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-muted-foreground">Depreciation Cost</span>
                <span>{{ currency }}{{ result.depreciation_cost.toFixed(2) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-muted-foreground">Fixed Fee</span>
                <span>{{ currency }}{{ result.fixed_fee.toFixed(2) }}</span>
              </div>
              <hr />
              <div class="flex justify-between font-medium">
                <span>Subtotal</span>
                <span>{{ currency }}{{ result.subtotal.toFixed(2) }}</span>
              </div>
              <div class="flex justify-between text-muted-foreground">
                <span>Service Fee ({{ result.profit_margin_percent }}%)</span>
                <span>{{ currency }}{{ result.profit.toFixed(2) }}</span>
              </div>
              <hr />
              <div class="flex justify-between text-lg font-bold">
                <span>Total</span>
                <span>{{ currency }}{{ result.total.toFixed(2) }}</span>
              </div>
            </div>
            <UiButton class="mt-6 w-full" variant="secondary" @click="showQuote = true">
              <FileText class="mr-2 h-4 w-4" /> View Quote
            </UiButton>
          </UiCardContent>
        </UiCard>

        <UiCard v-if="!result">
          <UiCardContent class="p-8 text-center text-muted-foreground">
            Enter job details and click Calculate to see a cost estimate.
          </UiCardContent>
        </UiCard>
      </div>
    </div>
  </div>
</template>
