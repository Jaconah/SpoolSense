<script setup lang="ts">
import { ref, computed, onMounted, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  LayoutDashboard,
  Cylinder,
  Printer,
  Calculator,
  Settings,
  Moon,
  Sun,
  Menu,
  X,
  Wrench,
  FolderOpen,
  ShoppingCart,
  Package,
  Box,
  LogOut,
  User,
  Sparkles,
  MapPin,
} from 'lucide-vue-next'
import UiButton from '@/components/ui/UiButton.vue'
import { useTheme } from '@/composables/use-theme'
import { cn } from '@/lib/utils'
import { authApi, type User as UserType } from '@/lib/api'
import { APP_VERSION } from '@/lib/changelog'

const route = useRoute()
const router = useRouter()
const { theme, setTheme } = useTheme()
const mobileOpen = ref(false)
const currentUser = ref<UserType | null>(null)
const openWhatsNew = inject<() => void>('openWhatsNew')
const openOnboarding = inject<() => void>('openOnboarding')

onMounted(async () => {
  try {
    currentUser.value = await authApi.getCurrentUser()
  } catch (error) {
    // If fetching user fails, they'll be redirected by auth guard
    console.error('Failed to fetch current user:', error)
  }
})

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/spools', label: 'Spools', icon: Cylinder },
  { to: '/print-jobs', label: 'Print Jobs', icon: Printer },
  { to: '/hardware', label: 'Hardware', icon: Wrench },
  { to: '/projects', label: 'Projects', icon: FolderOpen },
  { to: '/orders', label: 'Orders', icon: ShoppingCart },
  { to: '/product-on-hand', label: 'Product on Hand', icon: Box },
  { to: '/cost-estimator', label: 'Cost Estimator', icon: Calculator },
  { to: '/settings', label: 'Settings', icon: Settings },
]

function isActive(path: string) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

function toggleTheme() {
  setTheme(theme.value === 'dark' ? 'light' : 'dark')
}

async function handleLogout() {
  try {
    await authApi.logout()
    router.push('/login')
  } catch (error) {
    console.error('Logout failed:', error)
    // Force logout anyway
    router.push('/login')
  }
}
</script>

<template>
  <!-- Mobile toggle -->
  <div class="fixed top-0 left-0 right-0 z-50 flex items-center border-b bg-background p-3 md:hidden">
    <UiButton variant="ghost" size="icon" @click="mobileOpen = !mobileOpen">
      <X v-if="mobileOpen" class="h-5 w-5" />
      <Menu v-else class="h-5 w-5" />
    </UiButton>
    <span class="ml-2 font-bold">SpoolSense</span>
  </div>

  <!-- Mobile overlay -->
  <div
    v-if="mobileOpen"
    class="fixed inset-0 z-40 bg-black/50 md:hidden"
    @click="mobileOpen = false"
  />

  <!-- Mobile sidebar -->
  <aside
    :class="cn(
      'fixed top-0 left-0 z-40 h-full w-64 transform border-r bg-background transition-transform md:hidden',
      mobileOpen ? 'translate-x-0' : '-translate-x-full'
    )"
  >
    <div class="pt-14">
      <nav class="flex flex-col gap-1 p-4">
        <div class="mb-6 flex items-center gap-2 px-2">
          <Cylinder class="h-6 w-6 text-primary" />
          <span class="text-lg font-bold">SpoolSense</span>
        </div>
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          @click="mobileOpen = false"
          :class="cn(
            'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground',
            isActive(item.to) && 'bg-accent text-accent-foreground'
          )"
        >
          <component :is="item.icon" class="h-4 w-4" />
          {{ item.label }}
        </RouterLink>
        <div class="mt-auto space-y-2 border-t border-gray-200 dark:border-gray-700 pt-4">
          <UiButton variant="ghost" size="sm" class="w-full justify-start gap-3" @click="toggleTheme">
            <Sun v-if="theme === 'dark'" class="h-4 w-4" />
            <Moon v-else class="h-4 w-4" />
            {{ theme === 'dark' ? 'Light Mode' : 'Dark Mode' }}
          </UiButton>

          <RouterLink
            v-if="currentUser"
            to="/profile"
            @click="mobileOpen = false"
            class="block px-2 py-2 text-sm text-gray-600 dark:text-gray-400 rounded-md hover:bg-accent hover:text-accent-foreground transition-colors"
          >
            <div class="flex items-center gap-2 mb-1">
              <User class="h-4 w-4" />
              <span class="font-medium truncate">{{ currentUser.name || 'Owner' }}</span>
            </div>
            <div class="text-xs truncate ml-6"><!-- email removed for self-hosted --></div>
          </RouterLink>

          <UiButton variant="ghost" size="sm" class="w-full justify-start gap-3 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300" @click="handleLogout">
            <LogOut class="h-4 w-4" />
            Logout
          </UiButton>

          <button
            class="w-full flex items-center justify-between px-3 py-1.5 rounded-md text-xs text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
            @click="openWhatsNew?.(); mobileOpen = false"
          >
            <span class="flex items-center gap-2">
              <Sparkles class="h-3.5 w-3.5" />
              What's New
            </span>
            <span class="font-mono">v{{ APP_VERSION }}</span>
          </button>
          <button
            class="w-full flex items-center gap-2 px-3 py-1.5 rounded-md text-xs text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
            @click="openOnboarding?.(); mobileOpen = false"
          >
            <MapPin class="h-3.5 w-3.5" />
            Setup Tour
          </button>
        </div>
      </nav>
    </div>
  </aside>

  <!-- Desktop sidebar -->
  <aside class="hidden md:flex md:w-64 md:flex-col md:border-r md:bg-background">
    <nav class="flex flex-col gap-1 p-4">
      <div class="mb-6 flex items-center gap-2 px-2">
        <Cylinder class="h-6 w-6 text-primary" />
        <span class="text-lg font-bold">SpoolSense</span>
      </div>
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :class="cn(
          'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground',
          isActive(item.to) && 'bg-accent text-accent-foreground'
        )"
      >
        <component :is="item.icon" class="h-4 w-4" />
        {{ item.label }}
      </RouterLink>
      <div class="mt-auto space-y-2 border-t border-gray-200 dark:border-gray-700 pt-4">
        <UiButton variant="ghost" size="sm" class="w-full justify-start gap-3" @click="toggleTheme">
          <Sun v-if="theme === 'dark'" class="h-4 w-4" />
          <Moon v-else class="h-4 w-4" />
          {{ theme === 'dark' ? 'Light Mode' : 'Dark Mode' }}
        </UiButton>

        <RouterLink
          v-if="currentUser"
          to="/profile"
          class="block px-2 py-2 text-sm text-gray-600 dark:text-gray-400 rounded-md hover:bg-accent hover:text-accent-foreground transition-colors"
        >
          <div class="flex items-center gap-2 mb-1">
            <User class="h-4 w-4" />
            <span class="font-medium truncate">{{ currentUser.name || 'Owner' }}</span>
          </div>
          <div class="text-xs truncate ml-6"><!-- email removed for self-hosted --></div>
        </RouterLink>

        <UiButton variant="ghost" size="sm" class="w-full justify-start gap-3 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300" @click="handleLogout">
          <LogOut class="h-4 w-4" />
          Logout
        </UiButton>

        <button
          class="w-full flex items-center justify-between px-3 py-1.5 rounded-md text-xs text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
          @click="openWhatsNew?.()"
        >
          <span class="flex items-center gap-2">
            <Sparkles class="h-3.5 w-3.5" />
            What's New
          </span>
          <span class="font-mono">v{{ APP_VERSION }}</span>
        </button>
        <button
          class="w-full flex items-center gap-2 px-3 py-1.5 rounded-md text-xs text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
          @click="openOnboarding?.()"
        >
          <MapPin class="h-3.5 w-3.5" />
          Setup Tour
        </button>
      </div>
    </nav>
  </aside>
</template>
