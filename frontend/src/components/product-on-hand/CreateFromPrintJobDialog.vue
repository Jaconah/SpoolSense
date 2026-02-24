<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { api, type PrintJob, type Project } from '@/lib/api'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiDialogHeader from '@/components/ui/UiDialogHeader.vue'
import UiDialogTitle from '@/components/ui/UiDialogTitle.vue'
import UiDialogDescription from '@/components/ui/UiDialogDescription.vue'
import UiDialogFooter from '@/components/ui/UiDialogFooter.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import UiTextarea from '@/components/ui/UiTextarea.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiAlert from '@/components/ui/UiAlert.vue'

const props = defineProps<{
  open: boolean
  printJob?: PrintJob | null
  projects: Project[]
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  created: []
}>()

const creating = ref(false)
const error = ref('')

const form = ref({
  project_id: '',
  name: '',
  location: '',
  notes: '',
})

const projectOptions = computed(() => [
  { value: '', label: 'Custom (No Project)' },
  ...props.projects.map(p => ({ value: String(p.id), label: p.name }))
])

const selectedProject = computed(() => {
  if (!form.value.project_id) return null
  return props.projects.find(p => p.id === Number(form.value.project_id))
})

const hasHardware = computed(() => {
  return selectedProject.value?.hardware && selectedProject.value.hardware.length > 0
})

watch(() => [props.printJob, props.open], () => {
  if (props.open && props.printJob) {
    const selectedProj = props.printJob.project_id
      ? props.projects.find(p => p.id === props.printJob!.project_id)
      : null
    form.value = {
      project_id: props.printJob.project_id ? String(props.printJob.project_id) : '',
      name: selectedProj?.name || props.printJob.name || '',
      location: '',
      notes: `From print job: ${props.printJob.name}`,
    }
  } else {
    form.value = { project_id: '', name: '', location: '', notes: '' }
  }
  error.value = ''
}, { immediate: true })

// Auto-fill name when project changes
watch(() => form.value.project_id, (newProjectId) => {
  if (newProjectId) {
    const project = props.projects.find(p => p.id === Number(newProjectId))
    if (project) {
      form.value.name = project.name
    }
  }
})

async function handleCreate() {
  if (!props.printJob) return

  if (!form.value.name?.trim()) {
    error.value = 'Product name is required'
    return
  }

  // If no hardware (ready immediately), location is required
  if (!hasHardware.value && !form.value.location?.trim()) {
    error.value = 'Location is required for products without hardware'
    return
  }

  creating.value = true
  error.value = ''

  try {
    const payload = {
      project_id: form.value.project_id ? Number(form.value.project_id) : null,
      print_job_id: props.printJob.id,
      name: form.value.name,
      status: hasHardware.value ? 'printed' : 'completed',
      location: form.value.location?.trim() || null,
      notes: form.value.notes || null,
    }

    await api.post('/products-on-hand', payload)

    emit('created')
    emit('update:open', false)
  } catch (e: any) {
    error.value = e.message || 'Failed to create product on hand'
  } finally {
    creating.value = false
  }
}
</script>

<template>
  <UiDialog :open="open" @update:open="emit('update:open', $event)">
    <UiDialogHeader>
      <UiDialogTitle>Move to Product on Hand</UiDialogTitle>
      <UiDialogDescription>
        Create a finished product ready to sell
      </UiDialogDescription>
    </UiDialogHeader>

    <form @submit.prevent="handleCreate" class="space-y-4">
      <UiAlert v-if="error" variant="error">{{ error }}</UiAlert>

      <!-- Print Job Info -->
      <div v-if="printJob" class="rounded-md bg-muted p-3 text-sm">
        <div><strong>Print Job:</strong> {{ printJob.name }}</div>
        <div v-if="printJob.spool"><strong>Color:</strong> {{ printJob.spool.color_name }}</div>
        <div><strong>Filament Used:</strong> {{ printJob.filament_used_g }}g</div>
      </div>

      <div v-if="printJob?.order_id" class="rounded-md bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 p-3 text-sm text-yellow-800 dark:text-yellow-200">
        ⚠️ Warning: This print job is already linked to an order
      </div>

      <div>
        <UiLabel for="project">Project (Optional)</UiLabel>
        <UiSelect
          id="project"
          v-model="form.project_id"
          :options="projectOptions"
          placeholder="Select a project or create custom..."
        />
        <p v-if="printJob?.project_id && form.project_id === String(printJob.project_id)" class="text-xs text-muted-foreground mt-1">
          ✨ Auto-selected from print job
        </p>
        <p v-if="!form.project_id" class="text-xs text-muted-foreground mt-1">
          💡 No project selected - creating custom product
        </p>
      </div>

      <div>
        <UiLabel for="name">Product Name *</UiLabel>
        <UiInput
          id="name"
          v-model="form.name"
          placeholder="e.g. Custom Widget"
          required
        />
        <p v-if="form.project_id" class="text-xs text-muted-foreground mt-1">
          ✨ Auto-filled from project (can be customized)
        </p>
      </div>

      <!-- Show status info if project selected with hardware -->
      <div v-if="hasHardware" class="rounded-md bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-3 text-sm text-blue-800 dark:text-blue-200">
        🔧 This project requires hardware assembly. Status will be set to "Printed" - you can add location later when marking as completed.
      </div>

      <div>
        <UiLabel for="location">
          Location {{ hasHardware ? '(Optional - add when assembling)' : '*' }}
        </UiLabel>
        <UiInput
          id="location"
          v-model="form.location"
          placeholder="Car, Locker, Bag, etc."
          :required="!hasHardware"
        />
        <p v-if="!hasHardware" class="text-xs text-muted-foreground mt-1">
          ✅ No hardware required - product will be marked as completed and ready to sell
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
        <UiButton type="submit" :disabled="creating">
          {{ creating ? 'Creating...' : 'Create Product on Hand' }}
        </UiButton>
      </UiDialogFooter>
    </form>
  </UiDialog>
</template>
