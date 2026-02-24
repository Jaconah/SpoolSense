<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePaginatedPrintJobs, useSpools, useProjects, useHardware, useDebounce } from '@/composables/use-data'
import UiButton from '@/components/ui/UiButton.vue'
import UiBadge from '@/components/ui/UiBadge.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiCardContent from '@/components/ui/UiCardContent.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiPagination from '@/components/ui/UiPagination.vue'
import PrintJobForm from '@/components/print-jobs/PrintJobForm.vue'
import PrintJobCard from '@/components/print-jobs/PrintJobCard.vue'
import CreateFromPrintJobDialog from '@/components/product-on-hand/CreateFromPrintJobDialog.vue'
import ConvertToProjectDialog from '@/components/print-jobs/ConvertToProjectDialog.vue'
import { Plus, Pencil, Trash2, Package, FolderPlus, Search } from 'lucide-vue-next'
import { api, type PrintJob } from '@/lib/api'

const route = useRoute()
const router = useRouter()

const filterStatus = ref(String(route.query.status || 'all'))
const filterCustomer = ref(String(route.query.customer || 'all'))
const formOpen = ref(false)
const editingJob = ref<PrintJob | null>(null)
const createProductDialogOpen = ref(false)
const convertToProjectDialogOpen = ref(false)
const selectedPrintJob = ref<PrintJob | null>(null)
const page = ref(Number(route.query.page) || 1)
const perPage = ref(Number(route.query.per_page) || 25)
const searchInput = ref(String(route.query.search || ''))
const debouncedSearch = useDebounce(searchInput)

const params = computed(() => {
  const p: Record<string, any> = {}
  if (filterStatus.value !== 'all') p.status = filterStatus.value
  if (filterCustomer.value !== 'all') p.was_for_customer = filterCustomer.value === 'true'
  if (debouncedSearch.value) p.search = debouncedSearch.value
  p.page = page.value
  p.per_page = perPage.value
  return p
})

const { data: pageData, loading, refresh } = usePaginatedPrintJobs(params)
const jobs = computed(() => pageData.value?.items ?? [])
const { data: spools, refresh: refreshSpools } = useSpools()
const { data: projects } = useProjects()
const { data: hardwareItems } = useHardware()

// Reset page on filter/search change
watch([debouncedSearch, filterStatus, filterCustomer], () => { page.value = 1 })

// Sync URL
watch([page, perPage, debouncedSearch, filterStatus, filterCustomer], () => {
  const query: Record<string, string> = {}
  if (page.value !== 1) query.page = String(page.value)
  if (perPage.value !== 25) query.per_page = String(perPage.value)
  if (searchInput.value) query.search = searchInput.value
  if (filterStatus.value !== 'all') query.status = filterStatus.value
  if (filterCustomer.value !== 'all') query.customer = filterCustomer.value
  router.replace({ query })
})

const statusOptions = [
  { value: 'all', label: 'All Status' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
  { value: 'cancelled', label: 'Cancelled' },
]

const customerOptions = [
  { value: 'all', label: 'All Jobs' },
  { value: 'true', label: 'Customer Jobs' },
  { value: 'false', label: 'Personal Jobs' },
]

async function handleDelete(job: PrintJob) {
  if (!confirm(`Delete print job "${job.name}"?`)) return
  try {
    await api.delete(`/print-jobs/${job.id}`)
    refresh()
    refreshSpools()
  } catch (e: any) {
    alert(e.message)
  }
}

function handleMoveToProductOnHand(job: PrintJob) {
  selectedPrintJob.value = job
  createProductDialogOpen.value = true
}

function handleConvertToProject(job: PrintJob) {
  selectedPrintJob.value = job
  convertToProjectDialogOpen.value = true
}

function handleProductCreated() {
  refresh()
}

function handleProjectConverted() {
  refresh()
}

function handleSaved() {
  refresh()
  refreshSpools()
}

function openCreate() {
  editingJob.value = null
  formOpen.value = true
}

function openEdit(job: PrintJob) {
  editingJob.value = job
  formOpen.value = true
}

function formatTime(minutes: number | null) {
  if (!minutes) return '-'
  return `${Math.floor(minutes / 60)}h ${minutes % 60}m`
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">Print Jobs</h1>
      <div class="flex gap-2">
        <UiButton @click="openCreate">
          <Plus class="mr-2 h-4 w-4" /> Log Print
        </UiButton>
      </div>
    </div>

    <!-- Search + Filters -->
    <div class="flex flex-wrap gap-2">
      <div class="relative flex-1 min-w-[180px] max-w-xs">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <UiInput v-model="searchInput" placeholder="Search print jobs..." class="pl-9" />
      </div>
      <UiSelect v-model="filterStatus" :options="statusOptions" class="w-full sm:w-[140px]" />
      <UiSelect v-model="filterCustomer" :options="customerOptions" class="w-full sm:w-[160px]" />
      <select
        v-model="perPage"
        class="w-full sm:w-auto h-10 rounded-md border border-input bg-background px-3 text-sm"
      >
        <option :value="10">10 / page</option>
        <option :value="25">25 / page</option>
        <option :value="50">50 / page</option>
        <option :value="100">100 / page</option>
      </select>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center text-muted-foreground">Loading...</div>

    <!-- Empty State -->
    <UiCard v-else-if="!jobs.length && !pageData?.total">
      <UiCardContent class="p-8 text-center text-muted-foreground">
        No print jobs found. Log your first print!
      </UiCardContent>
    </UiCard>

    <!-- Mobile: Cards -->
    <div v-else class="grid gap-3 md:hidden">
      <PrintJobCard
        v-for="job in jobs"
        :key="job.id"
        :job="job"
        @edit="openEdit"
        @delete="handleDelete"
        @move-to-product="handleMoveToProductOnHand"
        @convert-to-project="handleConvertToProject"
      />
    </div>

    <!-- Desktop: Table -->
    <div v-if="!loading && jobs.length" class="hidden md:block rounded-lg border bg-card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b bg-muted/50">
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Name</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Spool</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Filament</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Time</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Status</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Customer</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Price</th>
              <th class="px-4 py-2 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="job in jobs" :key="job.id" class="border-b last:border-0 hover:bg-muted/50 transition-colors">
              <td class="px-4 py-2 font-medium">{{ job.name }}</td>
              <td class="px-4 py-2">
                <!-- Multi-color support -->
                <div v-if="job.print_job_spools && job.print_job_spools.length" class="flex flex-wrap gap-1">
                  <div
                    v-for="pjs in job.print_job_spools"
                    :key="pjs.id"
                    class="inline-flex items-center gap-1 rounded border px-2 py-0.5 text-xs"
                    :style="{
                      backgroundColor: (pjs.spool?.color_hex || '#999') + '40',
                      borderColor: pjs.spool?.color_hex || '#999',
                      color: pjs.spool?.color_hex || '#999'
                    }"
                  >
                    <span class="font-medium">{{ pjs.spool?.color_name || 'Unknown' }}</span>
                    <span class="text-muted-foreground">({{ pjs.filament_used_g }}g)</span>
                  </div>
                </div>
                <!-- Backward compatibility: single spool -->
                <div v-else-if="job.spool" class="flex items-center gap-2">
                  <div
                    class="h-3 w-3 rounded-full border"
                    :style="{ backgroundColor: job.spool.color_hex }"
                  />
                  {{ job.spool.color_name }}
                </div>
                <div v-else>-</div>
              </td>
              <td class="px-4 py-2">
                <!-- Multi-color: show total or individual amounts -->
                <span v-if="job.print_job_spools && job.print_job_spools.length">
                  {{ job.print_job_spools.reduce((sum, pjs) => sum + pjs.filament_used_g, 0).toFixed(1) }}g
                </span>
                <!-- Backward compatibility -->
                <span v-else-if="job.filament_used_g">{{ job.filament_used_g }}g</span>
                <span v-else>-</span>
              </td>
                <td class="px-4 py-2">{{ formatTime(job.print_time_minutes) }}</td>
                <td class="px-4 py-2">
                  <UiBadge
                    :variant="
                      job.status === 'completed'
                        ? 'default'
                        : job.status === 'failed'
                          ? 'destructive'
                          : 'secondary'
                    "
                  >
                    {{ job.status }}
                  </UiBadge>
                </td>
                <td class="px-4 py-2">
                  {{ job.was_for_customer ? job.customer_name || 'Yes' : '-' }}
                </td>
                <td class="px-4 py-2">
                  {{ job.quoted_price ? `$${job.quoted_price.toFixed(2)}` : '-' }}
                </td>
                <td class="px-4 py-2 text-right">
                  <div class="flex justify-end gap-1">
                    <UiButton
                      v-if="job.status === 'completed' && !job.order_id"
                      variant="ghost"
                      size="icon"
                      @click="handleMoveToProductOnHand(job)"
                      title="Move to Product on Hand"
                    >
                      <Package class="h-4 w-4" />
                    </UiButton>
                    <UiButton
                      variant="ghost"
                      size="icon"
                      @click="handleConvertToProject(job)"
                      title="Convert to Project Template"
                    >
                      <FolderPlus class="h-4 w-4" />
                    </UiButton>
                    <UiButton variant="ghost" size="icon" @click="openEdit(job)">
                      <Pencil class="h-4 w-4" />
                    </UiButton>
                    <UiButton variant="ghost" size="icon" @click="handleDelete(job)">
                      <Trash2 class="h-4 w-4" />
                    </UiButton>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    <!-- Pagination -->
    <UiPagination
      v-if="pageData && pageData.total > 0"
      :model-value="page"
      :total="pageData.total"
      :per-page="perPage"
      @update:model-value="page = $event"
    />

    <PrintJobForm
      v-model:open="formOpen"
      :job="editingJob"
      :spools="spools || []"
      :projects="projects || []"
      @saved="handleSaved"
    />

    <CreateFromPrintJobDialog
      :open="createProductDialogOpen"
      @update:open="createProductDialogOpen = $event"
      :print-job="selectedPrintJob"
      :projects="projects || []"
      @created="handleProductCreated"
    />

    <ConvertToProjectDialog
      :open="convertToProjectDialogOpen"
      @update:open="convertToProjectDialogOpen = $event"
      :print-job="selectedPrintJob"
      :hardware-items="hardwareItems || []"
      @converted="handleProjectConverted"
    />
  </div>
</template>
