<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePaginatedOrders, useProjects, useSpools, useOrderSummary, useHardware, useDebounce } from '@/composables/use-data'
import UiButton from '@/components/ui/UiButton.vue'
import UiBadge from '@/components/ui/UiBadge.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiCardContent from '@/components/ui/UiCardContent.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiPagination from '@/components/ui/UiPagination.vue'
import OrderForm from '@/components/orders/OrderForm.vue'
import OrderCard from '@/components/orders/OrderCard.vue'
import { Plus, Pencil, Trash2, TrendingUp, TrendingDown, ChevronUp, ChevronDown, Play, Search } from 'lucide-vue-next'
import { api, type Order, type OrderProfitBreakdown } from '@/lib/api'

const route = useRoute()
const router = useRouter()

const filterStatus = ref(String(route.query.status || 'all'))
const formOpen = ref(false)
const editingOrder = ref<Order | null>(null)
const profitOrder = ref<Order | null>(null)
const profitData = ref<OrderProfitBreakdown | null>(null)
const profitLoading = ref(false)
const sortColumn = ref<'order' | 'customer' | 'status' | 'quoted' | 'due_date' | null>(null)
const sortDirection = ref<'asc' | 'desc'>('asc')
const page = ref(Number(route.query.page) || 1)
const perPage = ref(Number(route.query.per_page) || 25)
const searchInput = ref(String(route.query.search || ''))
const debouncedSearch = useDebounce(searchInput)

const params = computed(() => {
  const p: Record<string, any> = {}
  if (filterStatus.value !== 'all') p.status = filterStatus.value
  if (debouncedSearch.value) p.search = debouncedSearch.value
  p.page = page.value
  p.per_page = perPage.value
  return p
})

const { data: pageData, loading, refresh } = usePaginatedOrders(params)
const orders = computed(() => pageData.value?.items ?? [])
const { data: projects } = useProjects()
const { data: hardwareItems } = useHardware()
const { data: spools } = useSpools()
const { data: summary, refresh: refreshSummary } = useOrderSummary()

// Reset page on filter/search change
watch([debouncedSearch, filterStatus], () => { page.value = 1 })

// Sync URL
watch([page, perPage, debouncedSearch, filterStatus], () => {
  const query: Record<string, string> = {}
  if (page.value !== 1) query.page = String(page.value)
  if (perPage.value !== 25) query.per_page = String(perPage.value)
  if (searchInput.value) query.search = searchInput.value
  if (filterStatus.value !== 'all') query.status = filterStatus.value
  router.replace({ query })
})

const sortedOrders = computed(() => {
  if (!orders.value || !sortColumn.value) return orders.value

  const sorted = [...orders.value].sort((a, b) => {
    let aVal: any, bVal: any

    switch (sortColumn.value) {
      case 'order':
        aVal = orderName(a).toLowerCase()
        bVal = orderName(b).toLowerCase()
        break
      case 'customer':
        aVal = (a.customer_name || '').toLowerCase()
        bVal = (b.customer_name || '').toLowerCase()
        break
      case 'status':
        aVal = a.status
        bVal = b.status
        break
      case 'quoted':
        aVal = a.quoted_price || 0
        bVal = b.quoted_price || 0
        break
      case 'due_date':
        aVal = a.due_date ? new Date(a.due_date).getTime() : 0
        bVal = b.due_date ? new Date(b.due_date).getTime() : 0
        break
      default:
        return 0
    }

    if (aVal < bVal) return sortDirection.value === 'asc' ? -1 : 1
    if (aVal > bVal) return sortDirection.value === 'asc' ? 1 : -1
    return 0
  })

  return sorted
})

const statusOptions = [
  { value: 'all', label: 'All Statuses' },
  { value: 'ordered', label: 'Ordered' },
  { value: 'printed', label: 'Printed' },
  { value: 'finished', label: 'Finished' },
  { value: 'sold', label: 'Sold' },
]

function statusVariant(status: string) {
  switch (status) {
    case 'sold': return 'default' as const
    case 'finished': return 'secondary' as const
    case 'printed': return 'secondary' as const
    default: return 'outline' as const
  }
}

async function handleDelete(order: Order) {
  if (!confirm('Delete this order?')) return
  try {
    await api.delete(`/orders/${order.id}`)
    refresh()
    refreshSummary()
  } catch (e: any) {
    alert(e.message)
  }
}

async function showProfit(order: Order) {
  profitOrder.value = order
  profitLoading.value = true
  try {
    profitData.value = await api.get<OrderProfitBreakdown>(`/orders/${order.id}/profit`)
  } catch {
    profitData.value = null
  } finally {
    profitLoading.value = false
  }
}

function openCreate() {
  editingOrder.value = null
  formOpen.value = true
}

function openEdit(order: Order) {
  editingOrder.value = order
  formOpen.value = true
}

function onSaved() {
  refresh()
  refreshSummary()
}

function orderName(order: Order): string {
  if (order.custom_name) return order.custom_name
  const project = projects.value?.find((p) => p.id === order.project_id)
  return project?.name || `Order #${order.id}`
}

function toggleSort(column: typeof sortColumn.value) {
  if (sortColumn.value === column) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = column
    sortDirection.value = 'asc'
  }
}

async function createPrintJob(order: Order) {
  if (!order.project_id || !order.spool_id) {
    alert('Order must have a project and spool to create print job')
    return
  }

  if (!confirm(`Create print job for "${orderName(order)}"? This will deduct filament from the spool.`)) return

  try {
    await api.post(`/orders/${order.id}/create-print-job`, {})
    alert('Print job created successfully!')
  } catch (e: any) {
    alert(`Error: ${e.message}`)
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">Orders</h1>
      <div class="flex gap-2">
        <UiButton @click="openCreate">
          <Plus class="mr-2 h-4 w-4" /> New Order
        </UiButton>
      </div>
    </div>

    <!-- Summary Cards -->
    <div v-if="summary" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <UiCard>
        <UiCardContent class="p-3 sm:p-4">
          <p class="text-xs sm:text-sm text-muted-foreground">Total Orders</p>
          <p class="text-xl sm:text-2xl font-bold">{{ summary.total_orders }}</p>
          <p class="text-xs text-muted-foreground">{{ summary.sold_orders }} sold</p>
        </UiCardContent>
      </UiCard>
      <UiCard>
        <UiCardContent class="p-3 sm:p-4">
          <p class="text-xs sm:text-sm text-muted-foreground">Revenue</p>
          <p class="text-xl sm:text-2xl font-bold">{{ summary.currency_symbol }}{{ summary.total_revenue.toFixed(2) }}</p>
          <p class="text-xs text-muted-foreground">from sold orders</p>
        </UiCardContent>
      </UiCard>
      <UiCard>
        <UiCardContent class="p-3 sm:p-4">
          <p class="text-xs sm:text-sm text-muted-foreground">Total Cost</p>
          <p class="text-xl sm:text-2xl font-bold">{{ summary.currency_symbol }}{{ summary.total_cost.toFixed(2) }}</p>
        </UiCardContent>
      </UiCard>
      <UiCard>
        <UiCardContent class="p-3 sm:p-4">
          <p class="text-xs sm:text-sm text-muted-foreground">Profit</p>
          <p :class="['text-xl sm:text-2xl font-bold', summary.total_profit >= 0 ? 'text-green-600' : 'text-red-600']">
            {{ summary.currency_symbol }}{{ summary.total_profit.toFixed(2) }}
          </p>
        </UiCardContent>
      </UiCard>
    </div>

    <!-- Search + Filter -->
    <div class="flex flex-wrap gap-2">
      <div class="relative flex-1 min-w-[180px] max-w-xs">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <UiInput v-model="searchInput" placeholder="Search orders..." class="pl-9" />
      </div>
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
    <UiCard v-else-if="!orders.length && !pageData?.total">
      <UiCardContent class="p-8 text-center text-muted-foreground">
        No orders found. Create your first order!
      </UiCardContent>
    </UiCard>

    <!-- Mobile: Cards -->
    <div v-else class="grid gap-3 md:hidden">
      <OrderCard
        v-for="order in sortedOrders"
        :key="order.id"
        :order="order"
        :order-name="orderName(order)"
        @edit="openEdit"
        @delete="handleDelete"
        @show-profit="showProfit"
        @create-print-job="createPrintJob"
      />
    </div>

    <!-- Desktop: Table -->
    <div v-if="!loading && orders.length" class="hidden md:block rounded-lg border bg-card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b bg-muted/50">
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                <button @click="toggleSort('order')" class="inline-flex items-center gap-1 hover:text-primary">
                  Order
                  <ChevronUp v-if="sortColumn === 'order' && sortDirection === 'asc'" class="h-3 w-3" />
                  <ChevronDown v-else-if="sortColumn === 'order' && sortDirection === 'desc'" class="h-3 w-3" />
                </button>
              </th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                <button @click="toggleSort('customer')" class="inline-flex items-center gap-1 hover:text-primary">
                  Customer
                  <ChevronUp v-if="sortColumn === 'customer' && sortDirection === 'asc'" class="h-3 w-3" />
                  <ChevronDown v-else-if="sortColumn === 'customer' && sortDirection === 'desc'" class="h-3 w-3" />
                </button>
              </th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                <button @click="toggleSort('status')" class="inline-flex items-center gap-1 hover:text-primary">
                  Status
                  <ChevronUp v-if="sortColumn === 'status' && sortDirection === 'asc'" class="h-3 w-3" />
                  <ChevronDown v-else-if="sortColumn === 'status' && sortDirection === 'desc'" class="h-3 w-3" />
                </button>
              </th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                <button @click="toggleSort('quoted')" class="inline-flex items-center gap-1 hover:text-primary">
                  Quoted
                  <ChevronUp v-if="sortColumn === 'quoted' && sortDirection === 'asc'" class="h-3 w-3" />
                  <ChevronDown v-else-if="sortColumn === 'quoted' && sortDirection === 'desc'" class="h-3 w-3" />
                </button>
              </th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                <button @click="toggleSort('due_date')" class="inline-flex items-center gap-1 hover:text-primary">
                  Due Date
                  <ChevronUp v-if="sortColumn === 'due_date' && sortDirection === 'asc'" class="h-3 w-3" />
                  <ChevronDown v-else-if="sortColumn === 'due_date' && sortDirection === 'desc'" class="h-3 w-3" />
                </button>
              </th>
              <th class="px-4 py-2 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="order in sortedOrders" :key="order.id" class="border-b last:border-0 hover:bg-muted/50 transition-colors">
              <td class="px-4 py-2 font-medium">{{ orderName(order) }}</td>
              <td class="px-4 py-2">{{ order.customer_name || '-' }}</td>
                <td class="px-4 py-2">
                  <UiBadge :variant="statusVariant(order.status)">
                    {{ order.status.replace('_', ' ') }}
                  </UiBadge>
                </td>
                <td class="px-4 py-2">
                  {{ order.quoted_price != null ? `$${order.quoted_price.toFixed(2)}` : '-' }}
                </td>
                <td class="px-4 py-2">
                  {{ order.due_date ? new Date(order.due_date).toLocaleDateString() : '-' }}
                </td>
                <td class="px-4 py-2 text-right">
                  <div class="flex justify-end gap-1">
                    <UiButton
                      v-if="order.project_id && order.spool_id && order.status === 'ordered'"
                      variant="ghost"
                      size="icon"
                      @click="createPrintJob(order)"
                      title="Create Print Job"
                    >
                      <Play class="h-4 w-4" />
                    </UiButton>
                    <UiButton variant="ghost" size="icon" @click="showProfit(order)" title="Profit/Loss">
                      <TrendingUp class="h-4 w-4" />
                    </UiButton>
                    <UiButton variant="ghost" size="icon" @click="openEdit(order)">
                      <Pencil class="h-4 w-4" />
                    </UiButton>
                    <UiButton variant="ghost" size="icon" @click="handleDelete(order)">
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

    <!-- Profit Detail Inline -->
    <UiCard v-if="profitOrder && profitData">
      <UiCardContent class="p-4">
        <div class="mb-3 flex items-center justify-between">
          <h3 class="font-semibold">P&L: {{ orderName(profitOrder) }}</h3>
          <UiButton variant="ghost" size="sm" @click="profitOrder = null">Close</UiButton>
        </div>
        <div class="grid gap-2 text-sm sm:grid-cols-2">
          <div class="flex justify-between border-b pb-1">
            <span class="text-muted-foreground">Revenue</span>
            <span class="font-medium">{{ profitData.currency_symbol }}{{ profitData.revenue.toFixed(2) }}</span>
          </div>
          <div class="flex justify-between border-b pb-1">
            <span class="text-muted-foreground">Shipping Revenue</span>
            <span class="font-medium">{{ profitData.currency_symbol }}{{ profitData.shipping_revenue.toFixed(2) }}</span>
          </div>
          <div class="flex justify-between border-b pb-1">
            <span class="text-muted-foreground">Filament Cost</span>
            <span>-{{ profitData.currency_symbol }}{{ profitData.filament_cost.toFixed(2) }}</span>
          </div>
          <div class="flex justify-between border-b pb-1">
            <span class="text-muted-foreground">Hardware Cost</span>
            <span>-{{ profitData.currency_symbol }}{{ profitData.hardware_cost.toFixed(2) }}</span>
          </div>
          <div class="flex justify-between border-b pb-1">
            <span class="text-muted-foreground">Electricity</span>
            <span>-{{ profitData.currency_symbol }}{{ profitData.electricity_cost.toFixed(2) }}</span>
          </div>
          <div class="flex justify-between border-b pb-1">
            <span class="text-muted-foreground">Time Cost</span>
            <span>-{{ profitData.currency_symbol }}{{ profitData.time_cost.toFixed(2) }}</span>
          </div>
          <div class="flex justify-between border-b pb-1">
            <span class="text-muted-foreground">Depreciation</span>
            <span>-{{ profitData.currency_symbol }}{{ profitData.depreciation_cost.toFixed(2) }}</span>
          </div>
          <div class="col-span-full flex justify-between border-t pt-2 font-semibold">
            <span>Profit</span>
            <span :class="profitData.profit >= 0 ? 'text-green-600' : 'text-red-600'">
              {{ profitData.currency_symbol }}{{ profitData.profit.toFixed(2) }}
            </span>
          </div>
        </div>
      </UiCardContent>
    </UiCard>

    <OrderForm
      v-model:open="formOpen"
      :order="editingOrder"
      :projects="projects || []"
      :spools="spools || []"
      :hardware-items="hardwareItems || []"
      @saved="onSaved"
    />
  </div>
</template>
