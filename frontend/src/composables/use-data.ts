import { ref, watch, computed, type Ref } from 'vue'
import {
  api,
  type CostBreakdown,
  type DashboardData,
  type FilamentType,
  type HardwareItem,
  type HardwareSummary,
  type InventoryItem,
  type Manufacturer,
  type Order,
  type OrderSummary,
  type PaginatedResponse,
  type PrintJob,
  type ProductOnHand,
  type ProductOnHandStats,
  type Project,
  type Settings,
  type Spool,
  type SpoolUsage,
} from '@/lib/api'

export function useDebounce<T>(value: Ref<T>, delay = 400): Ref<T> {
  const debounced = ref(value.value) as Ref<T>
  let timer: ReturnType<typeof setTimeout> | null = null
  watch(value, (v) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => { debounced.value = v }, delay)
  })
  return debounced
}

function useResource<T>(url: Ref<string> | string) {
  const data = ref<T | null>(null) as Ref<T | null>
  const loading = ref(true)
  const error = ref<string | null>(null)

  function refresh() {
    loading.value = true
    error.value = null
    const resolvedUrl = typeof url === 'string' ? url : url.value
    api
      .get<T>(resolvedUrl)
      .then((res) => { data.value = res })
      .catch((e) => { error.value = e.message })
      .finally(() => { loading.value = false })
  }

  if (typeof url === 'string') {
    refresh()
  } else {
    watch(url, () => refresh(), { immediate: true })
  }

  return { data, loading, error, refresh }
}

// Fetches a paginated endpoint and returns the items array (unwraps PaginatedResponse).
// Use this for dropdown/form composables instead of useResource<T[]>() directly.
function useAllItems<T>(url: Ref<string> | string) {
  const pagedUrl = computed(() => {
    const base = typeof url === 'string' ? url : url.value
    const sep = base.includes('?') ? '&' : '?'
    return `${base}${sep}page=1&per_page=100`
  })
  const { data: raw, loading, error, refresh } = useResource<PaginatedResponse<T>>(pagedUrl)
  const data = computed(() => raw.value?.items ?? null) as Ref<T[] | null>
  return { data, loading, error, refresh }
}

export function useDashboard() {
  return useResource<DashboardData>('/dashboard')
}

export function useSpools(params?: Ref<{
  filament_type_id?: number
  manufacturer_id?: number
  is_active?: boolean
}>) {
  if (!params) return useAllItems<Spool>('/spools')

  const url = ref('/spools')
  watch(params, (p) => {
    const query = new URLSearchParams()
    if (p.filament_type_id !== undefined) query.set('filament_type_id', String(p.filament_type_id))
    if (p.manufacturer_id !== undefined) query.set('manufacturer_id', String(p.manufacturer_id))
    if (p.is_active !== undefined) query.set('is_active', String(p.is_active))
    const qs = query.toString()
    url.value = `/spools${qs ? `?${qs}` : ''}`
  }, { immediate: true })

  return useAllItems<Spool>(url)
}

export function useFilamentTypes() {
  return useResource<FilamentType[]>('/filament-types')
}

export function useManufacturers() {
  return useResource<Manufacturer[]>('/manufacturers')
}

export function usePrintJobs(params?: Ref<{
  status?: string
  was_for_customer?: boolean
  spool_id?: number
}>) {
  if (!params) return useAllItems<PrintJob>('/print-jobs')

  const url = ref('/print-jobs')
  watch(params, (p) => {
    const query = new URLSearchParams()
    if (p.status) query.set('status', p.status)
    if (p.was_for_customer !== undefined) query.set('was_for_customer', String(p.was_for_customer))
    if (p.spool_id !== undefined) query.set('spool_id', String(p.spool_id))
    const qs = query.toString()
    url.value = `/print-jobs${qs ? `?${qs}` : ''}`
  }, { immediate: true })

  return useAllItems<PrintJob>(url)
}

export function useSettings() {
  return useResource<Settings>('/settings')
}

export function useHardware() {
  return useAllItems<HardwareItem>('/hardware')
}

export function useProjects() {
  return useAllItems<Project>('/projects')
}

export function useOrders(params?: Ref<{ status?: string }>) {
  if (!params) return useAllItems<Order>('/orders')

  const url = ref('/orders')
  watch(params, (p) => {
    const query = new URLSearchParams()
    if (p.status) query.set('status', p.status)
    const qs = query.toString()
    url.value = `/orders${qs ? `?${qs}` : ''}`
  }, { immediate: true })

  return useAllItems<Order>(url)
}

export function useOrderSummary() {
  return useResource<OrderSummary>('/orders/summary')
}

export function useHardwareSummary() {
  return useResource<HardwareSummary>('/hardware/summary')
}

export function useInventoryInHand() {
  return useResource<InventoryItem[]>('/inventory-in-hand')
}

export function useProductsOnHand(projectId?: Ref<number | null>) {
  if (!projectId) return useResource<ProductOnHand[]>('/products-on-hand')

  const url = computed(() => {
    const base = '/products-on-hand'
    return projectId.value ? `${base}?project_id=${projectId.value}` : base
  })

  return useResource<ProductOnHand[]>(url)
}

export function useProductOnHandStats() {
  return useResource<ProductOnHandStats>('/products-on-hand/stats')
}

// ============================================================================
// Paginated composables (for list pages with search + pagination)
// ============================================================================

export function usePaginatedSpools(params: Ref<{
  filament_type_id?: number
  manufacturer_id?: number
  is_active?: boolean
  search?: string
  page?: number
  per_page?: number
}>) {
  const url = computed(() => {
    const p = params.value
    const q = new URLSearchParams()
    if (p.filament_type_id !== undefined) q.set('filament_type_id', String(p.filament_type_id))
    if (p.manufacturer_id !== undefined) q.set('manufacturer_id', String(p.manufacturer_id))
    if (p.is_active !== undefined) q.set('is_active', String(p.is_active))
    if (p.search) q.set('search', p.search)
    if (p.page !== undefined) q.set('page', String(p.page))
    if (p.per_page !== undefined) q.set('per_page', String(p.per_page))
    const qs = q.toString()
    return `/spools${qs ? `?${qs}` : ''}`
  })
  return useResource<PaginatedResponse<Spool>>(url)
}

export function usePaginatedOrders(params: Ref<{
  status?: string
  search?: string
  page?: number
  per_page?: number
}>) {
  const url = computed(() => {
    const p = params.value
    const q = new URLSearchParams()
    if (p.status) q.set('status', p.status)
    if (p.search) q.set('search', p.search)
    if (p.page !== undefined) q.set('page', String(p.page))
    if (p.per_page !== undefined) q.set('per_page', String(p.per_page))
    const qs = q.toString()
    return `/orders${qs ? `?${qs}` : ''}`
  })
  return useResource<PaginatedResponse<Order>>(url)
}

export function usePaginatedPrintJobs(params: Ref<{
  status?: string
  was_for_customer?: boolean
  search?: string
  page?: number
  per_page?: number
}>) {
  const url = computed(() => {
    const p = params.value
    const q = new URLSearchParams()
    if (p.status) q.set('status', p.status)
    if (p.was_for_customer !== undefined) q.set('was_for_customer', String(p.was_for_customer))
    if (p.search) q.set('search', p.search)
    if (p.page !== undefined) q.set('page', String(p.page))
    if (p.per_page !== undefined) q.set('per_page', String(p.per_page))
    const qs = q.toString()
    return `/print-jobs${qs ? `?${qs}` : ''}`
  })
  return useResource<PaginatedResponse<PrintJob>>(url)
}

export function usePaginatedHardware(params: Ref<{
  low_stock_only?: boolean
  search?: string
  page?: number
  per_page?: number
}>) {
  const url = computed(() => {
    const p = params.value
    const q = new URLSearchParams()
    if (p.low_stock_only) q.set('low_stock_only', 'true')
    if (p.search) q.set('search', p.search)
    if (p.page !== undefined) q.set('page', String(p.page))
    if (p.per_page !== undefined) q.set('per_page', String(p.per_page))
    const qs = q.toString()
    return `/hardware${qs ? `?${qs}` : ''}`
  })
  return useResource<PaginatedResponse<HardwareItem>>(url)
}

export function usePaginatedProjects(params: Ref<{
  include_inactive?: boolean
  search?: string
  page?: number
  per_page?: number
}>) {
  const url = computed(() => {
    const p = params.value
    const q = new URLSearchParams()
    if (p.include_inactive) q.set('include_inactive', 'true')
    if (p.search) q.set('search', p.search)
    if (p.page !== undefined) q.set('page', String(p.page))
    if (p.per_page !== undefined) q.set('per_page', String(p.per_page))
    const qs = q.toString()
    return `/projects${qs ? `?${qs}` : ''}`
  })
  return useResource<PaginatedResponse<Project>>(url)
}

export function useSpoolUsage(spoolId: Ref<number | null>) {
  const url = computed(() =>
    spoolId.value ? `/spools/${spoolId.value}/usage` : null
  )
  const data = ref<SpoolUsage | null>(null) as Ref<SpoolUsage | null>
  const loading = ref(false)
  const error = ref<string | null>(null)

  function refresh() {
    if (!spoolId.value) return
    loading.value = true
    error.value = null
    api.get<SpoolUsage>(`/spools/${spoolId.value}/usage`)
      .then((res) => { data.value = res })
      .catch((e) => { error.value = e.message })
      .finally(() => { loading.value = false })
  }

  watch(spoolId, (id) => {
    if (id) refresh()
    else data.value = null
  })

  return { data, loading, error, refresh }
}
