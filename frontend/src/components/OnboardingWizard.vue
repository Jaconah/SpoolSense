<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  X, ChevronRight, ChevronLeft, Check,
  Cylinder, Printer, ShoppingCart, Wrench,
  FolderOpen, Calculator, Box,
} from 'lucide-vue-next'
import UiButton from '@/components/ui/UiButton.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import { api } from '@/lib/api'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ 'update:open': [value: boolean] }>()

const router = useRouter()
const step = ref(1)
const TOTAL_STEPS = 5

// Step 1 form
const rates = ref({ currency_symbol: '$', electricity_rate_kwh: 0.12, hourly_rate: 25 })
const ratesSaving = ref(false)

// Step 2 form
const ftName = ref('')
const ftAbbr = ref('')
const ftSaving = ref(false)
const ftSaved = ref(false)
const ftError = ref('')

// Step 3 form
const mfgName = ref('')
const mfgSaving = ref(false)
const mfgSaved = ref(false)
const mfgError = ref('')

// Load current settings when wizard opens
watch(() => props.open, async (val) => {
  if (!val) return
  step.value = 1
  ftName.value = ''
  ftAbbr.value = ''
  ftSaved.value = false
  ftError.value = ''
  mfgName.value = ''
  mfgSaved.value = false
  mfgError.value = ''
  try {
    const s = await api.get('/settings') as { currency_symbol: string; electricity_rate_kwh: number; hourly_rate: number }
    rates.value.currency_symbol = s.currency_symbol ?? '$'
    rates.value.electricity_rate_kwh = s.electricity_rate_kwh ?? 0.12
    rates.value.hourly_rate = s.hourly_rate ?? 25
  } catch {
    // use defaults
  }
})

function dismiss() {
  localStorage.setItem('tour_dismissed', 'true')
  emit('update:open', false)
}

async function nextStep() {
  if (step.value === 1) {
    ratesSaving.value = true
    try {
      await api.patch('/settings', {
        currency_symbol: rates.value.currency_symbol,
        electricity_rate_kwh: Number(rates.value.electricity_rate_kwh),
        hourly_rate: Number(rates.value.hourly_rate),
      })
    } catch {
      // non-critical — continue anyway
    } finally {
      ratesSaving.value = false
    }
  }
  step.value++
}

function prevStep() {
  if (step.value > 1) step.value--
}

async function addFilamentType() {
  if (!ftName.value.trim() || !ftAbbr.value.trim()) return
  ftError.value = ''
  ftSaving.value = true
  try {
    await api.post('/filament-types', {
      name: ftName.value.trim(),
      abbreviation: ftAbbr.value.trim().toUpperCase(),
    })
    ftSaved.value = true
    ftName.value = ''
    ftAbbr.value = ''
  } catch (e: any) {
    ftError.value = e.message ?? 'Failed to add filament type'
  } finally {
    ftSaving.value = false
  }
}

async function addManufacturer() {
  if (!mfgName.value.trim()) return
  mfgError.value = ''
  mfgSaving.value = true
  try {
    await api.post('/manufacturers', { name: mfgName.value.trim() })
    mfgSaved.value = true
    mfgName.value = ''
  } catch (e: any) {
    mfgError.value = e.message ?? 'Failed to add manufacturer'
  } finally {
    mfgSaving.value = false
  }
}

function goToSpools() {
  dismiss()
  router.push('/spools')
}

function finish() {
  dismiss()
}

const sections = [
  { icon: Cylinder,     label: 'Spools',          desc: 'Track filament rolls, weight remaining, and cost per gram.' },
  { icon: Printer,      label: 'Print Jobs',       desc: 'Log prints, filament used, and time for cost analysis.' },
  { icon: ShoppingCart, label: 'Orders',           desc: 'Manage customer requests from quote to completion.' },
  { icon: Wrench,       label: 'Hardware',         desc: 'Track components, quantities, and unit costs.' },
  { icon: FolderOpen,   label: 'Projects',         desc: 'Reusable templates with material and time estimates.' },
  { icon: Calculator,   label: 'Cost Estimator',   desc: 'Price any job without creating a full order.' },
  { icon: Box,          label: 'Product on Hand',  desc: 'Inventory of finished goods ready to sell.' },
]
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-150"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="open"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60"
        @click.self="dismiss"
      >
        <Transition
          enter-active-class="transition-all duration-200"
          enter-from-class="opacity-0 scale-95"
          enter-to-class="opacity-100 scale-100"
          leave-active-class="transition-all duration-150"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-0 scale-95"
        >
          <div
            v-if="open"
            class="relative w-full max-w-xl max-h-[90vh] flex flex-col rounded-xl border bg-background shadow-2xl overflow-hidden"
          >
            <!-- Header -->
            <div class="flex items-center justify-between px-6 py-4 border-b">
              <h2 class="text-lg font-semibold">Setup Tour</h2>
              <button
                @click="dismiss"
                class="rounded-md p-1 text-muted-foreground hover:text-foreground transition-colors"
                title="Close"
              >
                <X class="h-5 w-5" />
              </button>
            </div>

            <!-- Step indicator -->
            <div class="px-6 pt-4 pb-2">
              <div class="flex items-center gap-0">
                <template v-for="n in TOTAL_STEPS" :key="n">
                  <div
                    :class="[
                      'flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold transition-colors',
                      step > n
                        ? 'bg-primary text-primary-foreground'
                        : step === n
                          ? 'bg-primary text-primary-foreground ring-2 ring-primary/30'
                          : 'border bg-muted text-muted-foreground'
                    ]"
                  >
                    <Check v-if="step > n" class="h-3.5 w-3.5" />
                    <span v-else>{{ n }}</span>
                  </div>
                  <div
                    v-if="n < TOTAL_STEPS"
                    :class="[
                      'flex-1 h-0.5 transition-colors',
                      step > n ? 'bg-primary' : 'bg-muted'
                    ]"
                  />
                </template>
              </div>
            </div>

            <!-- Step content -->
            <div class="flex-1 overflow-y-auto px-6 py-4">

              <!-- Step 1: Currency & Rates -->
              <div v-if="step === 1" class="space-y-4">
                <div>
                  <h3 class="text-base font-semibold mb-1">Currency &amp; Rates</h3>
                  <p class="text-sm text-muted-foreground">These drive all cost calculations across the app. You can change them anytime in Settings.</p>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <UiLabel>Currency Symbol</UiLabel>
                    <UiInput v-model="rates.currency_symbol" placeholder="$" maxlength="10" />
                  </div>
                  <div>
                    <UiLabel>Electricity (per kWh)</UiLabel>
                    <UiInput type="number" v-model="rates.electricity_rate_kwh" min="0" step="0.01" />
                  </div>
                  <div>
                    <UiLabel>Hourly Rate</UiLabel>
                    <UiInput type="number" v-model="rates.hourly_rate" min="0" step="0.50" />
                  </div>
                </div>
              </div>

              <!-- Step 2: Filament Types -->
              <div v-else-if="step === 2" class="space-y-4">
                <div>
                  <h3 class="text-base font-semibold mb-1">Filament Types</h3>
                  <p class="text-sm text-muted-foreground">6 common types are already set up: PLA, PETG, ABS, TPU, Nylon, ASA. Want to add a custom one?</p>
                </div>
                <div v-if="ftSaved" class="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
                  <Check class="h-4 w-4" /> Added! You can add more anytime in Settings → Filament Types.
                </div>
                <div v-if="!ftSaved" class="space-y-3">
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <UiLabel>Name</UiLabel>
                      <UiInput v-model="ftName" placeholder="e.g. ASA-CF" />
                    </div>
                    <div>
                      <UiLabel>Abbreviation</UiLabel>
                      <UiInput v-model="ftAbbr" placeholder="e.g. ASACF" />
                    </div>
                  </div>
                  <p v-if="ftError" class="text-sm text-red-500">{{ ftError }}</p>
                  <UiButton
                    variant="outline"
                    size="sm"
                    :disabled="!ftName.trim() || !ftAbbr.trim() || ftSaving"
                    :loading="ftSaving"
                    @click="addFilamentType"
                  >
                    Add Filament Type
                  </UiButton>
                </div>
              </div>

              <!-- Step 3: Manufacturers -->
              <div v-else-if="step === 3" class="space-y-4">
                <div>
                  <h3 class="text-base font-semibold mb-1">Manufacturers</h3>
                  <p class="text-sm text-muted-foreground">A "Generic" manufacturer is already set up. Want to add your own (e.g. Bambu, Polymaker)?</p>
                </div>
                <div v-if="mfgSaved" class="flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
                  <Check class="h-4 w-4" /> Added! You can add more anytime in Settings → Manufacturers.
                </div>
                <div v-if="!mfgSaved" class="space-y-3">
                  <div>
                    <UiLabel>Manufacturer Name</UiLabel>
                    <UiInput v-model="mfgName" placeholder="e.g. Bambu Lab" />
                  </div>
                  <p v-if="mfgError" class="text-sm text-red-500">{{ mfgError }}</p>
                  <UiButton
                    variant="outline"
                    size="sm"
                    :disabled="!mfgName.trim() || mfgSaving"
                    :loading="mfgSaving"
                    @click="addManufacturer"
                  >
                    Add Manufacturer
                  </UiButton>
                </div>
              </div>

              <!-- Step 4: First spool -->
              <div v-else-if="step === 4" class="space-y-4">
                <div>
                  <h3 class="text-base font-semibold mb-1">Add Your First Spool</h3>
                  <p class="text-sm text-muted-foreground">
                    Spools are the heart of SpoolSense. Each spool tracks filament type,
                    colour, weight, and cost — and everything else (print jobs, orders, cost
                    estimates) links back to them.
                  </p>
                </div>
                <div class="rounded-lg border bg-muted/40 p-4 text-sm space-y-2">
                  <p class="font-medium">When you add a spool you'll enter:</p>
                  <ul class="space-y-1 text-muted-foreground list-disc list-inside">
                    <li>Filament type &amp; manufacturer</li>
                    <li>Colour and total weight</li>
                    <li>Purchase cost (for accurate job costing)</li>
                    <li>Optionally: location, brand, notes</li>
                  </ul>
                </div>
                <UiButton @click="goToSpools" class="w-full sm:w-auto">
                  Go to Spools &amp; Add First Spool
                  <ChevronRight class="h-4 w-4 ml-1" />
                </UiButton>
              </div>

              <!-- Step 5: Done -->
              <div v-else-if="step === 5" class="space-y-4">
                <div>
                  <h3 class="text-base font-semibold mb-1">You're all set!</h3>
                  <p class="text-sm text-muted-foreground">Here's a quick overview of what each section does.</p>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  <div
                    v-for="s in sections"
                    :key="s.label"
                    class="flex items-start gap-3 rounded-lg border p-3"
                  >
                    <div class="rounded-md bg-primary/10 p-1.5 shrink-0">
                      <component :is="s.icon" class="h-4 w-4 text-primary" />
                    </div>
                    <div>
                      <p class="text-sm font-medium">{{ s.label }}</p>
                      <p class="text-xs text-muted-foreground">{{ s.desc }}</p>
                    </div>
                  </div>
                </div>
                <p class="text-xs text-muted-foreground">
                  You can reopen this tour anytime from the sidebar or Settings.
                </p>
              </div>

            </div>

            <!-- Footer -->
            <div class="border-t px-6 py-4 flex items-center justify-between gap-3">
              <UiButton
                v-if="step > 1"
                variant="ghost"
                size="sm"
                @click="prevStep"
              >
                <ChevronLeft class="h-4 w-4 mr-1" /> Back
              </UiButton>
              <span v-else />

              <div class="flex items-center gap-2">
                <!-- Skip (steps 2 & 3 only) -->
                <UiButton
                  v-if="step === 2 || step === 3"
                  variant="ghost"
                  size="sm"
                  @click="step++"
                >
                  Skip
                </UiButton>
                <!-- Skip to overview (step 4) -->
                <UiButton
                  v-if="step === 4"
                  variant="ghost"
                  size="sm"
                  @click="step++"
                >
                  Skip for now
                </UiButton>

                <!-- Next (steps 1–4) -->
                <UiButton
                  v-if="step < 5"
                  @click="nextStep"
                  :loading="ratesSaving"
                >
                  Next <ChevronRight class="h-4 w-4 ml-1" />
                </UiButton>

                <!-- Finish (step 5) -->
                <UiButton v-if="step === 5" @click="finish">
                  <Check class="h-4 w-4 mr-1" /> Done
                </UiButton>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
