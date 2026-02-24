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
import UiTooltip from '@/components/ui/UiTooltip.vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import { HelpCircle, Plus, Trash2, AlertTriangle } from 'lucide-vue-next'
import { api, type PrintJob, type Spool, type Project, type SpoolShortage } from '@/lib/api'
import SpoolWarningDialog from '@/components/spools/SpoolWarningDialog.vue'

const props = defineProps<{
  open: boolean
  job?: PrintJob | null
  spools: Spool[]
  projects: Project[]
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  saved: []
}>()

interface SpoolEntry {
  spool_id: string
  filament_used_g: string
  position: number
}

const isEdit = computed(() => !!props.job)
const saving = ref(false)
const error = ref('')

// Spool shortage warning dialog (Issue #17)
const showSpoolWarning = ref(false)
const spoolShortages = ref<SpoolShortage[]>([])

const spoolEntries = ref<SpoolEntry[]>([{
  spool_id: '',
  filament_used_g: '',
  position: 1
}])

const form = ref({
  project_id: '',
  name: '',
  description: '',
  print_time_minutes: '',
  status: 'completed',
  was_for_customer: false,
  customer_name: '',
  quoted_price: '',
  notes: '',
})

// Check if a project is selected (spools should be locked to project requirements)
const isProjectSelected = computed(() => {
  return !!form.value.project_id && form.value.project_id !== ''
})

// Filament type compatibility warning
const hasIncompatibleTypes = computed(() => {
  if (spoolEntries.value.length <= 1) return false

  const selectedSpools = spoolEntries.value
    .filter(e => e.spool_id)
    .map(e => props.spools.find(s => s.id === Number(e.spool_id)))
    .filter(Boolean)

  if (selectedSpools.length <= 1) return false

  // Check if all spools have same filament type
  const firstType = selectedSpools[0]?.filament_type_id
  return !selectedSpools.every(s => s!.filament_type_id === firstType)
})

watch(
  () => [props.job, props.open],
  () => {
    if (props.job) {
      // Load existing job (multi-color or single-spool)
      if (props.job.print_job_spools && props.job.print_job_spools.length > 0) {
        // Multi-color job
        spoolEntries.value = props.job.print_job_spools
          .sort((a, b) => a.position - b.position)
          .map(pjs => ({
            spool_id: String(pjs.spool_id),
            filament_used_g: String(pjs.filament_used_g),
            position: pjs.position
          }))
      } else if (props.job.spool_id) {
        // Old single-spool format (backward compatibility)
        spoolEntries.value = [{
          spool_id: String(props.job.spool_id),
          filament_used_g: String(props.job.filament_used_g || 0),
          position: 1
        }]
      }

      form.value = {
        project_id: props.job.project_id ? String(props.job.project_id) : '',
        name: props.job.name,
        description: props.job.description || '',
        print_time_minutes: props.job.print_time_minutes ? String(props.job.print_time_minutes) : '',
        status: props.job.status,
        was_for_customer: props.job.was_for_customer,
        customer_name: props.job.customer_name || '',
        quoted_price: props.job.quoted_price ? String(props.job.quoted_price) : '',
        notes: props.job.notes || '',
      }
    } else {
      // New job - start with one spool entry
      spoolEntries.value = [{
        spool_id: props.spools[0]?.id ? String(props.spools[0].id) : '',
        filament_used_g: '',
        position: 1
      }]
      form.value = {
        project_id: '',
        name: '',
        description: '',
        print_time_minutes: '',
        status: 'completed',
        was_for_customer: false,
        customer_name: '',
        quoted_price: '',
        notes: '',
      }
    }
    error.value = ''
  },
  { immediate: true }
)

// Auto-fill form when project is selected
watch(() => form.value.project_id, (newProjectId) => {
  if (!newProjectId || isEdit.value) return

  const project = props.projects.find(p => p.id === Number(newProjectId))
  if (!project) return

  // Auto-fill from project template
  form.value.name = project.name
  form.value.print_time_minutes = project.print_time_hours ? String(Math.round(project.print_time_hours * 60)) : ''

  // If project has multi-filament requirements, auto-populate spool entries
  if (project.project_filaments && project.project_filaments.length > 0) {
    spoolEntries.value = project.project_filaments
      .sort((a, b) => a.position - b.position)
      .map((pf, idx) => ({
        spool_id: '', // User must select matching spool
        filament_used_g: String(pf.grams),
        position: idx + 1
      }))
  } else if (project.filament_grams) {
    // Old single-filament project
    spoolEntries.value = [{
      spool_id: spoolEntries.value[0]?.spool_id || '',
      filament_used_g: String(project.filament_grams),
      position: 1
    }]
  }
})

function addSpool() {
  if (spoolEntries.value.length >= 6) return

  spoolEntries.value.push({
    spool_id: '',
    filament_used_g: '',
    position: spoolEntries.value.length + 1
  })
}

function removeSpool(index: number) {
  if (spoolEntries.value.length === 1) return
  spoolEntries.value.splice(index, 1)

  // Reindex positions
  spoolEntries.value.forEach((entry, idx) => {
    entry.position = idx + 1
  })
}

const spoolOptions = computed(() =>
  props.spools.map((s) => ({
    value: String(s.id),
    label: `#${s.id} ${s.color_name} - ${s.filament_type.name} (${s.remaining_weight_g.toFixed(0)}g left)`,
  }))
)

const projectOptions = computed(() => [
  { value: '', label: 'None (manual entry)' },
  ...props.projects.map(p => ({
    value: String(p.id),
    label: p.name
  }))
])

const statusOptions = [
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
  { value: 'cancelled', label: 'Cancelled' },
]

async function submitWithForce(force: boolean) {
  saving.value = true
  error.value = ''
  try {
    // Filter out incomplete spool entries (must have both spool_id and filament_used_g > 0)
    const validSpoolEntries = spoolEntries.value.filter(entry => {
      const spoolId = Number(entry.spool_id)
      const filamentUsed = Number(entry.filament_used_g)
      return spoolId > 0 && filamentUsed > 0
    })

    // Validate at least one valid spool entry
    if (validSpoolEntries.length === 0) {
      error.value = 'Please add at least one spool with filament amount greater than 0'
      saving.value = false
      return
    }

    const payload = {
      spools: validSpoolEntries.map(entry => ({
        spool_id: Number(entry.spool_id),
        filament_used_g: Number(entry.filament_used_g),
        position: entry.position
      })),
      project_id: form.value.project_id ? Number(form.value.project_id) : null,
      name: form.value.name,
      description: form.value.description || null,
      print_time_minutes: form.value.print_time_minutes
        ? Number(form.value.print_time_minutes)
        : null,
      status: form.value.status,
      was_for_customer: form.value.was_for_customer,
      customer_name: form.value.customer_name || null,
      quoted_price: form.value.quoted_price ? Number(form.value.quoted_price) : null,
      notes: form.value.notes || null,
      printed_at: new Date().toISOString(),
      force: force  // Issue #17: Allow bypassing spool shortage warnings
    }
    if (isEdit.value) {
      await api.put(`/print-jobs/${props.job!.id}`, payload)
    } else {
      await api.post('/print-jobs', payload)
    }
    emit('saved')
    emit('update:open', false)
  } catch (e: any) {
    console.error('Print job submission error:', e)

    // Check if it's a spool shortage validation error (Issue #17)
    if (e.response?.status === 422 && e.response?.data?.detail?.type === 'spool_shortage') {
      const validation = e.response.data.detail.validation
      spoolShortages.value = validation.shortages
      showSpoolWarning.value = true
      saving.value = false
      return
    }

    // Handle other errors normally
    error.value = e.response?.data?.detail || e.message || 'Failed to save print job. Check console for details.'
  } finally {
    saving.value = false
  }
}

async function handleSubmit() {
  await submitWithForce(false)
}

function handleWarningConfirm() {
  // User confirmed they want to proceed despite shortage
  showSpoolWarning.value = false
  submitWithForce(true)
}

function handleWarningCancel() {
  // User canceled, clear pending data
  showSpoolWarning.value = false
  spoolShortages.value = []
}
</script>

<template>
  <UiDialog :open="open" @update:open="emit('update:open', $event)">
    <template #header>
      <UiDialogHeader>
        <UiDialogTitle>{{ isEdit ? 'Edit Print Job' : 'Log Print Job' }}</UiDialogTitle>
        <UiDialogDescription>
          {{ isEdit ? 'Update print job details.' : 'Log a new print job. Filament will be auto-subtracted from the spool(s).' }}
        </UiDialogDescription>
      </UiDialogHeader>
    </template>

    <form @submit.prevent="handleSubmit" class="space-y-5 md:space-y-6">
      <!-- Project Template -->
      <div class="space-y-2">
        <UiLabel class="text-sm font-medium">Project Template (Optional)</UiLabel>
        <UiSelect v-model="form.project_id" :options="projectOptions" placeholder="Select a project to auto-fill" />
        <p v-if="form.project_id" class="text-xs text-muted-foreground flex items-start gap-1.5">
          <span class="text-primary">✨</span>
          <span>Auto-filled from project template. You can still adjust values below.</span>
        </p>
      </div>

      <!-- Filament Spools -->
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <UiLabel class="text-sm font-medium">Filament Spools</UiLabel>
          <span class="text-xs text-muted-foreground">{{ spoolEntries.length }} of 6</span>
        </div>

        <!-- Compatibility Warning -->
        <UiAlert v-if="hasIncompatibleTypes" variant="warning" class="text-xs md:text-sm">
          <AlertTriangle class="h-4 w-4 shrink-0" />
          <div>
            <strong class="block mb-0.5">Mixed filament types detected</strong>
            <span class="text-xs opacity-90">
              Printing with different materials may fail due to temperature differences.
              Ensure your printer supports multi-material prints.
            </span>
          </div>
        </UiAlert>

        <!-- Spool Entries - Improved mobile layout -->
        <div class="space-y-2.5">
          <div
            v-for="(entry, idx) in spoolEntries"
            :key="idx"
            class="group relative rounded-lg border border-border bg-card/30 p-3 transition-colors hover:border-primary/30"
          >
            <!-- Mobile: Stacked layout -->
            <div class="space-y-2.5 md:hidden">
              <div class="flex items-center justify-between">
                <span class="text-xs font-medium text-muted-foreground">Color {{ idx + 1 }}</span>
                <div class="flex items-center gap-1">
                  <UiButton
                    type="button"
                    variant="ghost"
                    size="icon"
                    class="h-8 w-8"
                    @click="removeSpool(idx)"
                    :disabled="spoolEntries.length === 1 || isProjectSelected"
                    :title="isProjectSelected ? 'Cannot remove spools when using a project' : 'Remove spool'"
                  >
                    <Trash2 class="h-3.5 w-3.5" />
                  </UiButton>
                  <UiButton
                    v-if="idx === spoolEntries.length - 1"
                    type="button"
                    variant="outline"
                    size="icon"
                    class="h-8 w-8"
                    @click="addSpool"
                    :disabled="spoolEntries.length >= 6 || isProjectSelected"
                    :title="isProjectSelected ? 'Cannot add spools when using a project' : 'Add another color'"
                  >
                    <Plus class="h-3.5 w-3.5" />
                  </UiButton>
                </div>
              </div>
              <UiSelect v-model="entry.spool_id" :options="spoolOptions" placeholder="Select spool" />
              <div>
                <UiLabel class="text-xs text-muted-foreground mb-1">Filament Amount (grams)</UiLabel>
                <UiInput
                  type="number"
                  v-model="entry.filament_used_g"
                  min="0.1"
                  step="0.1"
                  placeholder="0.0"
                  class="text-base"
                />
              </div>
            </div>

            <!-- Desktop: Side-by-side layout -->
            <div class="hidden md:grid md:grid-cols-[1fr_140px_auto] md:gap-3 md:items-end">
              <div class="space-y-1.5">
                <UiLabel class="text-xs text-muted-foreground">Color {{ idx + 1 }}</UiLabel>
                <UiSelect v-model="entry.spool_id" :options="spoolOptions" placeholder="Select spool" />
              </div>

              <div class="space-y-1.5">
                <UiLabel class="text-xs text-muted-foreground">Grams</UiLabel>
                <UiInput
                  type="number"
                  v-model="entry.filament_used_g"
                  min="0.1"
                  step="0.1"
                  placeholder="0.0"
                />
              </div>

              <div class="flex items-center gap-1">
                <UiButton
                  type="button"
                  variant="ghost"
                  size="icon"
                  @click="removeSpool(idx)"
                  :disabled="spoolEntries.length === 1 || isProjectSelected"
                  :title="isProjectSelected ? 'Cannot remove spools when using a project' : 'Remove spool'"
                >
                  <Trash2 class="h-4 w-4" />
                </UiButton>
                <UiButton
                  v-if="idx === spoolEntries.length - 1"
                  type="button"
                  variant="outline"
                  size="icon"
                  @click="addSpool"
                  :disabled="spoolEntries.length >= 6 || isProjectSelected"
                  :title="isProjectSelected ? 'Cannot add spools when using a project' : 'Add another color'"
                >
                  <Plus class="h-4 w-4" />
                </UiButton>
              </div>
            </div>
          </div>
        </div>

        <!-- Help text -->
        <div class="flex items-start gap-2 text-xs text-muted-foreground bg-muted/30 rounded-md p-2.5">
          <HelpCircle class="h-3.5 w-3.5 shrink-0 mt-0.5" />
          <p>
            <template v-if="isProjectSelected">
              Spools are locked to project requirements. Deselect the project to customize.
            </template>
            <template v-else>
              Add up to 6 colors for multi-material prints. Click <Plus class="inline h-3 w-3 mx-0.5" /> to add another spool.
            </template>
          </p>
        </div>
      </div>

      <!-- Job Name -->
      <div class="space-y-2">
        <UiLabel class="text-sm font-medium">Job Name</UiLabel>
        <UiInput v-model="form.name" placeholder="e.g. Phone Stand v2" required class="text-base" />
      </div>

      <!-- Print Time & Status -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-5">
        <div class="space-y-2">
          <div class="flex items-center gap-2">
            <UiLabel class="text-sm font-medium">Print Time (min)</UiLabel>
            <UiTooltip content="Total print duration in minutes (e.g., 150 for 2h 30m). Optional.">
              <HelpCircle class="h-3.5 w-3.5 text-muted-foreground cursor-help" />
            </UiTooltip>
          </div>
          <UiInput type="number" v-model="form.print_time_minutes" min="0" placeholder="Optional" class="text-base" />
        </div>
        <div class="space-y-2">
          <UiLabel class="text-sm font-medium">Status</UiLabel>
          <UiSelect v-model="form.status" :options="statusOptions" />
        </div>
      </div>

      <!-- Customer Job Section -->
      <div class="space-y-3 rounded-lg border border-dashed border-border/60 p-3 md:p-4">
        <div class="flex items-center gap-2.5">
          <UiSwitch v-model="form.was_for_customer" />
          <UiLabel class="text-sm font-medium cursor-pointer">Customer Job</UiLabel>
        </div>

        <div v-if="form.was_for_customer" class="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4 pt-1">
          <div class="space-y-2">
            <UiLabel class="text-sm">Customer Name</UiLabel>
            <UiInput v-model="form.customer_name" placeholder="Customer name" class="text-base" />
          </div>
          <div class="space-y-2">
            <UiLabel class="text-sm">Quoted Price</UiLabel>
            <UiInput type="number" v-model="form.quoted_price" min="0" step="0.01" placeholder="0.00" class="text-base" />
          </div>
        </div>
      </div>

      <!-- Notes -->
      <div class="space-y-2">
        <UiLabel class="text-sm font-medium">Notes (Optional)</UiLabel>
        <UiTextarea v-model="form.notes" placeholder="Add any additional notes about this print..." rows="3" />
      </div>

      <!-- Error Display -->
      <UiAlert v-if="error" variant="error" class="text-sm">
        <AlertTriangle class="h-4 w-4" />
        <div>{{ error }}</div>
      </UiAlert>
    </form>

    <template #footer>
      <UiDialogFooter>
        <UiButton variant="outline" @click="emit('update:open', false)" type="button" class="flex-1 sm:flex-initial">
          Cancel
        </UiButton>
        <UiButton type="submit" :disabled="saving" @click="handleSubmit" class="flex-1 sm:flex-initial">
          {{ saving ? 'Saving...' : isEdit ? 'Update' : 'Log Print' }}
        </UiButton>
      </UiDialogFooter>
    </template>
  </UiDialog>

  <!-- Spool Shortage Warning Dialog (Issue #17) -->
  <SpoolWarningDialog
    :open="showSpoolWarning"
    :shortages="spoolShortages"
    @update:open="showSpoolWarning = $event"
    @confirm="handleWarningConfirm"
    @cancel="handleWarningCancel"
  />
</template>
