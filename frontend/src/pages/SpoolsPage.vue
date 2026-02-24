<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useFilamentTypes, useManufacturers, usePaginatedSpools, useDebounce } from '@/composables/use-data'
import UiButton from '@/components/ui/UiButton.vue'
import UiBadge from '@/components/ui/UiBadge.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiCardContent from '@/components/ui/UiCardContent.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiAlertTitle from '@/components/ui/UiAlertTitle.vue'
import UiAlertDescription from '@/components/ui/UiAlertDescription.vue'
import UiPagination from '@/components/ui/UiPagination.vue'
import SpoolForm from '@/components/spools/SpoolForm.vue'
import SpoolImportDialog from '@/components/spools/SpoolImportDialog.vue'
import SpoolCard from '@/components/dashboard/SpoolCard.vue'
import { Plus, Pencil, Trash2, AlertTriangle, X, Search, History, Upload } from 'lucide-vue-next'
import { api, type Spool } from '@/lib/api'
import { cn } from '@/lib/utils'
import UiDialog from '@/components/ui/UiDialog.vue'
import UiDialogTitle from '@/components/ui/UiDialogTitle.vue'
import { useSpoolUsage } from '@/composables/use-data'

const route = useRoute()
const router = useRouter()

const filterType = ref(String(route.query.type || 'all'))
const filterMfg = ref(String(route.query.mfg || 'all'))
const filterStatus = ref(String(route.query.status || 'all'))
const formOpen = ref(false)
const importOpen = ref(false)
const editingSpool = ref<Spool | null>(null)
const usageSpoolId = ref<number | null>(null)
const usageOpen = ref(false)
const { data: usageData, loading: usageLoading } = useSpoolUsage(usageSpoolId)

function openUsage(spool: Spool) {
  usageSpoolId.value = spool.id
  usageOpen.value = true
}
const page = ref(Number(route.query.page) || 1)
const perPage = ref(Number(route.query.per_page) || 25)
const searchInput = ref(String(route.query.search || ''))
const debouncedSearch = useDebounce(searchInput)

// Low/empty spool alerts
const alerts = ref<{ threshold_g: number; empty_spools: any[]; low_spools: any[] } | null>(null)
const showAlerts = ref(true)

async function fetchAlerts() {
  try {
    const data = await api.get<{ threshold_g: number; empty_spools: any[]; low_spools: any[] }>('/spools/alerts/low-and-empty')
    if (data.empty_spools.length > 0 || data.low_spools.length > 0) {
      alerts.value = data
    }
  } catch (e) {
    console.error('Failed to fetch alerts:', e)
  }
}

onMounted(() => {
  fetchAlerts()
})

const statusOptions = [
  { value: 'all', label: 'All Statuses' },
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
]

const params = computed(() => {
  const p: Record<string, any> = {}
  if (filterType.value !== 'all') p.filament_type_id = Number(filterType.value)
  if (filterMfg.value !== 'all') p.manufacturer_id = Number(filterMfg.value)
  if (filterStatus.value === 'active') p.is_active = true
  else if (filterStatus.value === 'inactive') p.is_active = false
  if (debouncedSearch.value) p.search = debouncedSearch.value
  p.page = page.value
  p.per_page = perPage.value
  return p
})

const { data: pageData, loading, refresh } = usePaginatedSpools(params)
const spools = computed(() => pageData.value?.items ?? [])
const { data: filamentTypes } = useFilamentTypes()
const { data: manufacturers } = useManufacturers()

// Reset page on filter/search change
watch([debouncedSearch, filterType, filterMfg, filterStatus], () => { page.value = 1 })

// Sync URL
watch([page, perPage, debouncedSearch, filterType, filterMfg, filterStatus], () => {
  const query: Record<string, string> = {}
  if (page.value !== 1) query.page = String(page.value)
  if (perPage.value !== 25) query.per_page = String(perPage.value)
  if (searchInput.value) query.search = searchInput.value
  if (filterType.value !== 'all') query.type = filterType.value
  if (filterMfg.value !== 'all') query.mfg = filterMfg.value
  if (filterStatus.value !== 'all') query.status = filterStatus.value
  router.replace({ query })
})

const typeOptions = computed(() => [
  { value: 'all', label: 'All Types' },
  ...(filamentTypes.value?.map((ft) => ({ value: String(ft.id), label: ft.name })) || []),
])

const mfgOptions = computed(() => [
  { value: 'all', label: 'All Manufacturers' },
  ...(manufacturers.value?.map((m) => ({ value: String(m.id), label: m.name })) || []),
])

async function handleDelete(spool: Spool) {
  if (!confirm(`Delete spool "${spool.color_name}"?`)) return
  try {
    await api.delete(`/spools/${spool.id}`)
    refresh()
  } catch (e: any) {
    alert(e.message)
  }
}

function openCreate() {
  editingSpool.value = null
  formOpen.value = true
}

function openEdit(spool: Spool) {
  editingSpool.value = spool
  formOpen.value = true
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">Spools</h1>
      <div class="flex gap-2">
        <UiButton variant="outline" @click="importOpen = true">
          <Upload class="mr-2 h-4 w-4" /> Import CSV
        </UiButton>
        <UiButton @click="openCreate">
          <Plus class="mr-2 h-4 w-4" /> Add Spool
        </UiButton>
      </div>
    </div>

    <!-- Low/Empty Spool Alerts -->
    <div v-if="alerts && showAlerts" class="space-y-2">
      <UiAlert v-if="alerts.empty_spools.length > 0" variant="error" class="py-3">
        <div class="flex items-start gap-3">
          <AlertTriangle class="h-4 w-4 mt-0.5 shrink-0" />
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between gap-2 mb-1">
              <span class="text-sm font-semibold">Empty Spools ({{ alerts.empty_spools.length }})</span>
              <UiButton size="sm" variant="ghost" class="h-6 px-2" @click="showAlerts = false">
                <X class="h-3 w-3" />
              </UiButton>
            </div>
            <p class="text-xs text-muted-foreground">
              {{ alerts.empty_spools.map(s => `${s.tracking_id || '#' + s.id} ${s.color_name}`).join(', ') }}
            </p>
          </div>
        </div>
      </UiAlert>

      <UiAlert v-if="alerts.low_spools.length > 0" variant="warning" class="py-3">
        <div class="flex items-start gap-3">
          <AlertTriangle class="h-4 w-4 mt-0.5 shrink-0" />
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between gap-2 mb-1">
              <span class="text-sm font-semibold">Low Spools ({{ alerts.low_spools.length }})</span>
              <UiButton size="sm" variant="ghost" class="h-6 px-2" @click="showAlerts = false">
                <X class="h-3 w-3" />
              </UiButton>
            </div>
            <p class="text-xs text-muted-foreground">
              {{ alerts.low_spools.map(s => `${s.tracking_id || '#' + s.id} ${s.color_name} (${s.remaining_weight_g}g)`).join(', ') }}
            </p>
          </div>
        </div>
      </UiAlert>
    </div>

    <!-- Filters + Search -->
    <div class="flex flex-wrap gap-2">
      <div class="relative flex-1 min-w-[180px] max-w-xs">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <UiInput v-model="searchInput" placeholder="Search spools..." class="pl-9" />
      </div>
      <UiSelect v-model="filterType" :options="typeOptions" class="w-full sm:w-[160px]" />
      <UiSelect v-model="filterMfg" :options="mfgOptions" class="w-full sm:w-[160px]" />
      <UiSelect v-model="filterStatus" :options="statusOptions" class="w-full sm:w-[160px]" />
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
    <UiCard v-else-if="!spools.length && !pageData?.total">
      <UiCardContent class="p-8 text-center text-muted-foreground">
        No spools found. Add your first spool!
      </UiCardContent>
    </UiCard>

    <!-- Mobile: Cards -->
    <div v-else class="grid gap-3 md:hidden">
      <SpoolCard
        v-for="spool in spools"
        :key="spool.id"
        :spool="spool"
        @edit="openEdit"
        @delete="handleDelete"
      />
    </div>

    <!-- Desktop: Table -->
    <div v-if="!loading && spools.length" class="hidden md:block rounded-lg border bg-card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b bg-muted/50">
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">ID</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Color</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Type</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Manufacturer</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Remaining</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Cost/kg</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Status</th>
              <th class="px-4 py-2 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="spool in spools" :key="spool.id" class="border-b last:border-0 hover:bg-muted/50 transition-colors">
              <td class="px-4 py-2">
                  <UiBadge variant="outline" class="font-mono text-xs">
                    {{ spool.tracking_id || `#${spool.id}` }}
                  </UiBadge>
                </td>
                <td class="px-4 py-2">
                  <div class="flex items-center gap-2">
                    <div
                      class="h-4 w-4 rounded-full border"
                      :style="{ backgroundColor: spool.color_hex }"
                    />
                    <span class="font-medium">{{ spool.color_name }}</span>
                  </div>
                </td>
                <td class="px-4 py-2">{{ spool.filament_type.name }}</td>
                <td class="px-4 py-2">{{ spool.manufacturer.name }}</td>
                <td class="px-4 py-2">
                  <div class="flex items-center gap-2">
                    <div class="h-2 w-16 rounded-full bg-muted">
                      <div
                        :class="cn(
                          'h-2 rounded-full',
                          spool.remaining_percent > 50
                            ? 'bg-green-500'
                            : spool.remaining_percent > 20
                              ? 'bg-yellow-500'
                              : 'bg-red-500'
                        )"
                        :style="{ width: `${Math.min(spool.remaining_percent, 100)}%` }"
                      />
                    </div>
                    <span class="text-xs text-muted-foreground">{{ spool.remaining_percent }}%</span>
                  </div>
                </td>
                <td class="px-4 py-2">${{ spool.cost_per_kg.toFixed(2) }}</td>
                <td class="px-4 py-2">
                  <UiBadge :variant="spool.is_active ? 'default' : 'secondary'">
                    {{ spool.is_active ? 'Active' : 'Inactive' }}
                  </UiBadge>
                </td>
                <td class="px-4 py-2 text-right">
                  <div class="flex justify-end gap-1">
                    <UiButton variant="ghost" size="icon" @click="openUsage(spool)" title="Usage History">
                      <History class="h-4 w-4" />
                    </UiButton>
                    <UiButton variant="ghost" size="icon" @click="openEdit(spool)">
                      <Pencil class="h-4 w-4" />
                    </UiButton>
                    <UiButton variant="ghost" size="icon" @click="handleDelete(spool)">
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

    <SpoolForm
      v-model:open="formOpen"
      :spool="editingSpool"
      :filament-types="filamentTypes || []"
      :manufacturers="manufacturers || []"
      @saved="refresh"
    />

    <SpoolImportDialog v-model:open="importOpen" @imported="refresh" />

    <!-- Usage History Modal -->
    <UiDialog :open="usageOpen" @update:open="usageOpen = $event">
      <template #header>
        <UiDialogTitle>Usage History</UiDialogTitle>
      </template>

      <div v-if="usageLoading" class="py-8 text-center text-muted-foreground">Loading...</div>
      <div v-else-if="usageData">
        <!-- Summary -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
          <div class="rounded-lg border bg-muted/30 p-3 text-center">
            <p class="text-xs text-muted-foreground">Total</p>
            <p class="text-lg font-bold">{{ usageData.total_weight_g }}g</p>
          </div>
          <div class="rounded-lg border bg-muted/30 p-3 text-center">
            <p class="text-xs text-muted-foreground">Consumed</p>
            <p class="text-lg font-bold">{{ usageData.total_consumed_g }}g</p>
          </div>
          <div class="rounded-lg border bg-muted/30 p-3 text-center">
            <p class="text-xs text-muted-foreground">Remaining</p>
            <p class="text-lg font-bold">{{ usageData.remaining_weight_g }}g</p>
          </div>
        </div>

        <!-- Discrepancy warning -->
        <div
          v-if="Math.abs(usageData.total_consumed_g - (usageData.total_weight_g - usageData.remaining_weight_g)) > 0.5"
          class="mb-4 rounded-md border border-yellow-500/50 bg-yellow-500/10 p-3 text-sm text-yellow-700 dark:text-yellow-400"
        >
          Note: tracked consumption ({{ usageData.total_consumed_g }}g) differs from weight difference
          ({{ (usageData.total_weight_g - usageData.remaining_weight_g).toFixed(1) }}g) — spool weight may have been adjusted manually.
        </div>

        <!-- Entries -->
        <div v-if="usageData.entries.length === 0" class="py-6 text-center text-sm text-muted-foreground">
          No usage recorded for this spool.
        </div>
        <table v-else class="w-full text-sm">
          <thead>
            <tr class="border-b">
              <th class="pb-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Date</th>
              <th class="pb-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Name</th>
              <th class="pb-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Type</th>
              <th class="pb-2 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Used</th>
              <th class="pb-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="entry in usageData.entries" :key="`${entry.type}-${entry.id}`" class="border-b last:border-0">
              <td class="py-2 text-muted-foreground">{{ entry.date ? new Date(entry.date).toLocaleDateString() : '—' }}</td>
              <td class="py-2 font-medium">{{ entry.name }}</td>
              <td class="py-2 capitalize text-muted-foreground">{{ entry.type === 'print_job' ? 'Print Job' : 'Order' }}</td>
              <td class="py-2 text-right">{{ entry.filament_used_g }}g</td>
              <td class="py-2">
                <UiBadge
                  :variant="entry.status === 'completed' || entry.status === 'sold' ? 'default' : entry.status === 'failed' ? 'destructive' : 'secondary'"
                  class="text-xs"
                >
                  {{ entry.status }}
                </UiBadge>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </UiDialog>
  </div>
</template>
