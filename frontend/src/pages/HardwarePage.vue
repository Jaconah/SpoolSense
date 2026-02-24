<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePaginatedHardware, useHardwareSummary, useDebounce } from '@/composables/use-data'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiCardHeader from '@/components/ui/UiCardHeader.vue'
import UiCardTitle from '@/components/ui/UiCardTitle.vue'
import UiCardContent from '@/components/ui/UiCardContent.vue'
import UiSwitch from '@/components/ui/UiSwitch.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiPagination from '@/components/ui/UiPagination.vue'
import HardwareForm from '@/components/hardware/HardwareForm.vue'
import HardwareCard from '@/components/hardware/HardwareCard.vue'
import { Plus, Pencil, Trash2, ExternalLink, Package, DollarSign, AlertTriangle, Search } from 'lucide-vue-next'
import { api, type HardwareItem } from '@/lib/api'

const route = useRoute()
const router = useRouter()

const formOpen = ref(false)
const editingItem = ref<HardwareItem | null>(null)
const lowStockOnly = ref(route.query.low_stock === 'true')
const page = ref(Number(route.query.page) || 1)
const perPage = ref(Number(route.query.per_page) || 25)
const searchInput = ref(String(route.query.search || ''))
const debouncedSearch = useDebounce(searchInput)

const params = computed(() => {
  const p: Record<string, any> = {}
  if (lowStockOnly.value) p.low_stock_only = true
  if (debouncedSearch.value) p.search = debouncedSearch.value
  p.page = page.value
  p.per_page = perPage.value
  return p
})

const { data: pageData, loading, refresh } = usePaginatedHardware(params)
const hardware = computed(() => pageData.value?.items ?? [])
const { data: summary } = useHardwareSummary()

// Reset page on filter/search change
watch([debouncedSearch, lowStockOnly], () => { page.value = 1 })

// Sync URL
watch([page, perPage, debouncedSearch, lowStockOnly], () => {
  const query: Record<string, string> = {}
  if (page.value !== 1) query.page = String(page.value)
  if (perPage.value !== 25) query.per_page = String(perPage.value)
  if (searchInput.value) query.search = searchInput.value
  if (lowStockOnly.value) query.low_stock = 'true'
  router.replace({ query })
})

async function handleDelete(item: HardwareItem) {
  if (!confirm(`Delete "${item.name}"?`)) return
  try {
    await api.delete(`/hardware/${item.id}`)
    refresh()
  } catch (e: any) {
    alert(e.message)
  }
}

function openCreate() {
  editingItem.value = null
  formOpen.value = true
}

function openEdit(item: HardwareItem) {
  editingItem.value = item
  formOpen.value = true
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">Hardware Inventory</h1>
      <div class="flex gap-2">
        <UiButton @click="openCreate">
          <Plus class="mr-2 h-4 w-4" /> Add Item
        </UiButton>
      </div>
    </div>

    <!-- Summary Cards -->
    <div v-if="summary" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <UiCard>
        <UiCardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <UiCardTitle class="text-xs sm:text-sm font-medium">Total Items</UiCardTitle>
          <Package class="h-3 w-3 sm:h-4 sm:w-4 text-muted-foreground" />
        </UiCardHeader>
        <UiCardContent class="pb-3">
          <div class="text-xl sm:text-2xl font-bold">{{ summary.total_items }}</div>
        </UiCardContent>
      </UiCard>

      <UiCard>
        <UiCardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <UiCardTitle class="text-xs sm:text-sm font-medium">Total Invested</UiCardTitle>
          <DollarSign class="h-3 w-3 sm:h-4 sm:w-4 text-muted-foreground" />
        </UiCardHeader>
        <UiCardContent class="pb-3">
          <div class="text-xl sm:text-2xl font-bold">{{ summary.currency_symbol }}{{ summary.total_invested.toFixed(2) }}</div>
        </UiCardContent>
      </UiCard>

      <UiCard>
        <UiCardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <UiCardTitle class="text-xs sm:text-sm font-medium">In Stock Value</UiCardTitle>
          <DollarSign class="h-3 w-3 sm:h-4 sm:w-4 text-muted-foreground" />
        </UiCardHeader>
        <UiCardContent class="pb-3">
          <div class="text-xl sm:text-2xl font-bold">{{ summary.currency_symbol }}{{ summary.total_in_stock_value.toFixed(2) }}</div>
        </UiCardContent>
      </UiCard>

      <UiCard>
        <UiCardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
          <UiCardTitle class="text-xs sm:text-sm font-medium">Low Stock Items</UiCardTitle>
          <AlertTriangle class="h-3 w-3 sm:h-4 sm:w-4 text-yellow-500" />
        </UiCardHeader>
        <UiCardContent class="pb-3">
          <div class="text-xl sm:text-2xl font-bold">{{ summary.low_stock_items }}</div>
        </UiCardContent>
      </UiCard>
    </div>

    <!-- Search + Filters -->
    <div class="flex flex-wrap items-center gap-2">
      <div class="relative flex-1 min-w-[180px] max-w-xs">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <UiInput v-model="searchInput" placeholder="Search hardware..." class="pl-9" />
      </div>
      <div class="flex items-center gap-2">
        <UiSwitch v-model="lowStockOnly" />
        <UiLabel>Show Low Stock Only</UiLabel>
      </div>
      <select
        v-model="perPage"
        class="h-10 rounded-md border border-input bg-background px-3 text-sm"
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
    <UiCard v-else-if="!hardware.length && !pageData?.total">
      <UiCardContent class="p-8 text-center text-muted-foreground">
        {{ lowStockOnly ? 'No low stock items' : 'No hardware items yet. Add your first item!' }}
      </UiCardContent>
    </UiCard>

    <!-- Mobile: Cards -->
    <div v-else class="grid gap-3 md:hidden">
      <HardwareCard
        v-for="item in hardware"
        :key="item.id"
        :item="item"
        @edit="openEdit"
        @delete="handleDelete"
      />
    </div>

    <!-- Desktop: Table -->
    <div v-if="!loading && hardware.length" class="hidden md:block rounded-lg border bg-card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b bg-muted/50">
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Name</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Brand</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Price</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Purchased</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Qty On Hand</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Cost/Item</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Link</th>
              <th class="px-4 py-2 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in hardware" :key="item.id" class="border-b last:border-0 hover:bg-muted/50 transition-colors">
              <td class="px-4 py-2">
                  <div class="flex items-center gap-2">
                    <span class="font-medium">{{ item.name }}</span>
                    <span v-if="item.is_low_stock" class="rounded-full bg-yellow-500/10 px-2 py-0.5 text-xs text-yellow-600 dark:text-yellow-500">
                      Low Stock
                    </span>
                  </div>
                </td>
                <td class="px-4 py-2">{{ item.brand || '-' }}</td>
                <td class="px-4 py-2">${{ item.purchase_price.toFixed(2) }}</td>
                <td class="px-4 py-2">{{ item.quantity_purchased }}</td>
                <td class="px-4 py-2">
                  <span :class="item.is_low_stock ? 'font-semibold text-yellow-600 dark:text-yellow-500' : ''">
                    {{ item.quantity_in_stock }}
                  </span>
                </td>
                <td class="px-4 py-2">${{ item.cost_per_item.toFixed(4) }}</td>
                <td class="px-4 py-2">
                  <a
                    v-if="item.purchase_url"
                    :href="item.purchase_url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="inline-flex items-center gap-1 text-primary hover:underline"
                  >
                    <ExternalLink class="h-3 w-3" /> Link
                  </a>
                  <span v-else class="text-muted-foreground">-</span>
                </td>
                <td class="px-4 py-2 text-right">
                  <div class="flex justify-end gap-1">
                    <UiButton variant="ghost" size="icon" @click="openEdit(item)">
                      <Pencil class="h-4 w-4" />
                    </UiButton>
                    <UiButton variant="ghost" size="icon" @click="handleDelete(item)">
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

    <HardwareForm
      v-model:open="formOpen"
      :item="editingItem"
      @saved="refresh"
    />
  </div>
</template>
