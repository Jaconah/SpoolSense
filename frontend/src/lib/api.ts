const BASE = "/api/v1";

// ============================================================================
// Token Management
// ============================================================================

let accessToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setTokens(accessToken: string): void {
  setAccessToken(accessToken);
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function clearTokens(): void {
  accessToken = null;
}

export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

export async function ensureAccessToken(): Promise<boolean> {
  if (getAccessToken()) return true;
  const token = await refreshAccessToken();
  return !!token;
}

// ============================================================================
// Request Handler with Auth
// ============================================================================

let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function onRefreshed(token: string) {
  refreshSubscribers.forEach((callback) => callback(token));
  refreshSubscribers = [];
}

function addRefreshSubscriber(callback: (token: string) => void) {
  refreshSubscribers.push(callback);
}

async function refreshAccessToken(): Promise<string | null> {
  try {
    const response = await fetch("/auth/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
      credentials: "include",
    });

    if (!response.ok) {
      clearTokens();
      window.location.href = "/login";
      return null;
    }

    const data = await response.json();
    setAccessToken(data.access_token);
    return data.access_token;
  } catch (error) {
    clearTokens();
    window.location.href = "/login";
    return null;
  }
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  // Add authorization header if token exists
  const token = getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string> || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let res = await fetch(`${BASE}${url}`, {
    ...options,
    headers,
    credentials: "include",
  });

  // Handle 401 (Unauthorized) - try to refresh token
  if (res.status === 401 && !url.includes("/auth/")) {
    if (!isRefreshing) {
      isRefreshing = true;
      const newToken = await refreshAccessToken();
      isRefreshing = false;

      if (newToken) {
        onRefreshed(newToken);
        // Retry original request with new token
        headers["Authorization"] = `Bearer ${newToken}`;
        res = await fetch(`${BASE}${url}`, {
          ...options,
          headers,
          credentials: "include",
        });
      }
    } else {
      // Wait for token refresh to complete
      const newToken = await new Promise<string>((resolve) => {
        addRefreshSubscriber((token) => resolve(token));
      });
      headers["Authorization"] = `Bearer ${newToken}`;
      res = await fetch(`${BASE}${url}`, {
        ...options,
        headers,
        credentials: "include",
      });
    }
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));

    // Handle 429 (Too Many Requests) - rate limited
    if (res.status === 429) {
      const retryAfter = res.headers.get('Retry-After');
      const wait = retryAfter ? ` Please wait ${retryAfter} seconds before trying again.` : '';
      throw new Error(`Too many attempts.${wait}`);
    }

    // Handle 403 (Forbidden) - account suspended
    if (res.status === 403) {
      throw new Error(body.detail || "Account suspended - contact support");
    }

    // Handle 422 (Validation Error) - show detailed errors
    if (res.status === 422 && body.detail) {
      // Pydantic validation errors come in different formats
      if (Array.isArray(body.detail)) {
        // Array of validation errors
        const errors = body.detail.map((err: any) =>
          `${err.loc.join('.')}: ${err.msg}`
        ).join(', ');
        throw new Error(`Validation error: ${errors}`);
      } else if (typeof body.detail === 'string') {
        // Simple string error
        throw new Error(body.detail);
      } else {
        // Structured object error (e.g., spool shortage from Issue #17)
        const err = new Error(JSON.stringify(body.detail)) as any;
        err.response = { status: res.status, data: body };
        throw err;
      }
    }

    const detail = Array.isArray(body.detail)
      ? body.detail.map((e: any) => e.msg).join(', ')
      : body.detail;
    throw new Error(detail || `Request failed: ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// Request handler for non-API routes (auth, admin, export)
async function rawRequest<T>(url: string, options?: RequestInit): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string> || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    ...options,
    headers,
    credentials: "include",
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));

    if (res.status === 429) {
      const retryAfter = res.headers.get('Retry-After');
      const wait = retryAfter ? ` Please wait ${retryAfter} seconds before trying again.` : '';
      throw new Error(`Too many attempts.${wait}`);
    }

    const detail = Array.isArray(body.detail)
      ? body.detail.map((e: any) => e.msg).join(', ')
      : body.detail;
    throw new Error(detail || `Request failed: ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  get: <T>(url: string) => request<T>(url),
  post: <T>(url: string, data: unknown) =>
    request<T>(url, { method: "POST", body: JSON.stringify(data) }),
  put: <T>(url: string, data: unknown) =>
    request<T>(url, { method: "PUT", body: JSON.stringify(data) }),
  patch: <T>(url: string, data: unknown) =>
    request<T>(url, { method: "PATCH", body: JSON.stringify(data) }),
  delete: <T>(url: string) => request<T>(url, { method: "DELETE" }),
};

// Paginated response envelope (matches backend PaginatedResponse[T])
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  pages: number
}

// Types matching backend schemas
export interface FilamentType {
  id: number;
  name: string;
  abbreviation: string;
  description: string | null;
  is_default: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export interface Manufacturer {
  id: number;
  name: string;
  website: string | null;
  is_default: boolean;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export interface Spool {
  id: number;
  filament_type_id: number;
  manufacturer_id: number;
  color_name: string;
  color_hex: string;
  total_weight_g: number;
  remaining_weight_g: number;
  remaining_percent: number;
  cost_per_kg: number;

  // New pricing schema
  msrp: number;  // Customer pricing reference
  purchase_price: number;  // What you paid (P&L)

  // Legacy pricing fields (kept for backwards compatibility)
  normal_price: number | null;
  is_sale_price: boolean;

  purchase_date: string | null;
  tracking_id: string | null;
  location: string | null;
  notes: string | null;
  is_active: boolean;
  filament_type: FilamentType;
  manufacturer: Manufacturer;
  created_at: string;
  updated_at: string;
}

// Spool Validation (Issue #17)
export interface SpoolShortage {
  spool_id: number;
  tracking_id: string | null;
  color_name: string;
  filament_type_name: string;
  manufacturer_name: string | null;
  current_weight_g: number;
  requested_weight_g: number;
  resulting_weight_g: number;
  shortage_g: number;
  within_reserve: boolean;
}

export interface SpoolValidationResponse {
  is_valid: boolean;
  has_warnings: boolean;
  shortages: SpoolShortage[];
  message: string | null;
}

export interface PrintJobSpool {
  id: number;
  spool_id: number;
  spool: Spool;
  filament_used_g: number;
  position: number;
}

export interface PrintJob {
  id: number;
  project_id: number | null;
  order_id: number | null;
  name: string;
  description: string | null;
  print_time_minutes: number | null;
  status: "completed" | "failed" | "cancelled";
  was_for_customer: boolean;
  customer_name: string | null;
  quoted_price: number | null;
  notes: string | null;
  printed_at: string | null;
  created_at: string;
  updated_at: string;

  // Multi-color support (new)
  print_job_spools: PrintJobSpool[];

  // DEPRECATED: Backward compatibility (will be null for new multi-color jobs)
  spool_id: number | null;
  spool: Spool | null;
  filament_used_g: number | null;
}

export interface Settings {
  id: number;
  currency_symbol: string;
  electricity_rate_kwh: number;
  printer_wattage: number;
  hourly_rate: number;
  machine_depreciation_rate: number;
  profit_margin_percent: number;
  fixed_fee_per_order: number;
  webhook_url: string | null;
  webhook_enabled: boolean;
  webhook_events: string;
  webhook_order_due_days: number;
  enable_shipping: boolean;
  default_shipping_charge: number;
  low_spool_threshold_g: number;
  show_spool_location: boolean;

  // Feature Module Toggles
  enable_hardware: boolean;
  enable_projects: boolean;
  enable_orders: boolean;
  enable_products_on_hand: boolean;

  // Spool Validation Settings
  enable_spool_negative_prevention: boolean;
  minimum_spool_reserve_g: number;

  // Behavior Toggles
  enable_low_spool_alerts: boolean;
  enable_tracking_id_auto_generation: boolean;

  // What's New tracking
  last_seen_version: string | null;

  created_at: string;
  updated_at: string;
}

export interface SpoolCostBreakdown {
  spool_id: number;
  color_name: string;
  filament_type: string;
  grams: number;
  filament_cost: number;
}

export interface CostBreakdown {
  // NEW: Per-spool details (empty array for backward compat with Quick Estimate)
  spool_costs: SpoolCostBreakdown[];

  // Aggregated costs
  filament_cost: number;
  electricity_cost: number;
  time_cost: number;
  depreciation_cost: number;
  fixed_fee: number;
  subtotal: number;
  profit_margin_percent: number;
  profit: number;
  total: number;
  currency_symbol: string;
}

export interface DashboardStats {
  total_spools: number;
  total_orders: number;
  sold_orders: number;
  order_revenue: number;
  currency_symbol: string;
}

export interface DashboardData {
  stats: DashboardStats;
  spools: Spool[];
}

export interface HardwareItem {
  id: number;
  name: string;
  brand: string | null;
  purchase_url: string | null;
  purchase_price: number;
  quantity_purchased: number;
  quantity_in_stock: number;
  low_stock_threshold: number | null;
  cost_per_item: number;
  is_low_stock: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface HardwareSummary {
  total_items: number;
  total_invested: number;
  total_in_stock_value: number;
  low_stock_items: number;
  currency_symbol: string;
}

export interface ProjectHardware {
  id: number;
  hardware_item_id: number;
  quantity: number;
  hardware_item: HardwareItem;
}

export interface ProjectFilament {
  id: number;
  filament_type_id: number;
  filament_type: FilamentType;
  grams: number;
  position: number;
  color_note: string | null;
}

export interface Project {
  id: number;
  name: string;
  model_url: string | null;
  filament_grams: number | null;  // DEPRECATED
  print_time_hours: number | null;
  sell_price: number | null;
  description: string | null;
  notes: string | null;
  is_active: boolean;

  // Multi-color support (new)
  project_filaments: ProjectFilament[];

  // Hardware items
  hardware: ProjectHardware[];

  created_at: string;
  updated_at: string;
}

export interface OrderSpool {
  id: number;
  spool_id: number;
  spool: Spool;
  filament_grams: number;
  position: number;
  cost_per_kg_snapshot: number;
}

export interface OrderHardware {
  id: number;
  hardware_item_id: number | null;
  quantity: number;
  unit_cost_snapshot: number;
  hardware_name_snapshot: string | null;
  hardware_brand_snapshot: string | null;
  is_one_off: boolean;
  one_off_name: string | null;
  one_off_cost: number | null;
  hardware_item: HardwareItem | null;
}

export interface Order {
  id: number;
  project_id: number | null;
  custom_name: string | null;
  custom_price: number | null;
  customer_name: string | null;
  customer_contact: string | null;
  customer_location: string | null;
  status: "ordered" | "printed" | "finished" | "sold";
  filament_grams_snapshot: number | null;
  print_time_hours_snapshot: number | null;
  quoted_price: number | null;
  due_date: string | null;
  shipping_charge: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;

  // Multi-color support (new)
  order_spools: OrderSpool[];

  // Hardware items
  order_hardware: OrderHardware[];

  // DEPRECATED: Backward compatibility (will be null for new multi-color orders)
  spool_id: number | null;
}

export interface OrderHardwareInput {
  hardware_item_id?: number | null;
  quantity: number;
  is_one_off?: boolean;
  one_off_name?: string | null;
  one_off_cost?: number | null;
}

export interface OrderProfitBreakdown {
  revenue: number;
  shipping_revenue: number;
  filament_cost: number;
  hardware_cost: number;
  electricity_cost: number;
  time_cost: number;
  depreciation_cost: number;
  total_cost: number;
  profit: number;
  currency_symbol: string;
}

export interface InventoryItem {
  id: number;
  customer_name: string;
  storage_location: string | null;
  items: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProductOnHandHardware {
  id: number;
  name: string;
  quantity: number;
  cost_per_item: number;
}

export interface ProductOnHand {
  id: number;
  project_id: number | null;
  print_job_id: number;
  name: string;
  status: "printed" | "completed";
  location: string | null;
  notes: string | null;
  created_at: string;

  // Computed fields
  project_name: string | null;
  color: string;
  filament_cost: number;
  hardware_cost: number;
  total_cost: number;
  sell_price: number | null;
  potential_profit: number | null;
  hardware_items: ProductOnHandHardware[];
}

export interface ProductOnHandStats {
  total_count: number;
  total_value: number;
  total_potential_profit: number;
}

export interface OrderSummary {
  total_orders: number;
  ordered_orders: number;
  printed_orders: number;
  finished_orders: number;
  sold_orders: number;
  total_revenue: number;
  total_cost: number;
  total_profit: number;
  currency_symbol: string;
}

// ============================================================================
// Spool Usage History (Issue #102)
// ============================================================================

export interface SpoolUsageEntry {
  type: 'print_job' | 'order'
  id: number
  name: string
  filament_used_g: number
  date: string | null
  status: string
}

export interface SpoolUsage {
  spool_id: number
  total_weight_g: number
  remaining_weight_g: number
  total_consumed_g: number
  entries: SpoolUsageEntry[]
}

// ============================================================================
// Order Invoice (Issue #100)
// ============================================================================

export interface OrderInvoiceFilamentLine {
  color_name: string
  filament_type: string
  color_hex: string
  grams: number
}

export interface OrderInvoiceHardwareLine {
  name: string
  brand: string | null
  quantity: number
  unit_cost: number
}

export interface OrderInvoice {
  order_id: number
  customer_name: string | null
  customer_contact: string | null
  customer_location: string | null
  status: string
  item_name: string | null
  quoted_price: number | null
  shipping_charge: number | null
  due_date: string | null
  created_at: string
  filament_lines: OrderInvoiceFilamentLine[]
  hardware_lines: OrderInvoiceHardwareLine[]
  currency_symbol: string
  notes: string | null
}

// ============================================================================
// Authentication Types
// ============================================================================

export interface User {
  id: number;
  name: string | null;
  tenant_id: string;
}

export interface LoginRequest {
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

// ============================================================================
// Authentication API
// ============================================================================

export const authApi = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await rawRequest<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    });
    if (response.access_token) {
      setTokens(response.access_token);
    }
    return response;
  },

  logout: async (): Promise<void> => {
    try {
      await rawRequest("/auth/logout", { method: "POST" });
    } catch {
      // Ignore errors on logout
    }
    clearTokens();
  },

  changePassword: async (data: ChangePasswordRequest): Promise<{ message: string }> => {
    return rawRequest("/auth/change-password", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  getCurrentUser: async (): Promise<User> => {
    return rawRequest("/auth/me", { method: "GET" });
  },
};

// ============================================================================
// Export API
// ============================================================================

