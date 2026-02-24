import { createRouter, createWebHistory } from 'vue-router'
import { ensureAccessToken, isAuthenticated } from '@/lib/api'
import AppShell from '@/components/layout/AppShell.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    // ========================================================================
    // Public Routes (No Auth Required)
    // ========================================================================
    {
      path: '/login',
      name: 'login',
      component: () => import('@/pages/LoginPage.vue'),
      meta: { public: true },
    },

    // ========================================================================
    // Protected Routes (Auth Required)
    // ========================================================================
    {
      path: '/',
      component: AppShell,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('@/pages/DashboardPage.vue'),
        },
        {
          path: 'spools',
          name: 'spools',
          component: () => import('@/pages/SpoolsPage.vue'),
        },
        {
          path: 'print-jobs',
          name: 'print-jobs',
          component: () => import('@/pages/PrintJobsPage.vue'),
        },
        {
          path: 'hardware',
          name: 'hardware',
          component: () => import('@/pages/HardwarePage.vue'),
        },
        {
          path: 'projects',
          name: 'projects',
          component: () => import('@/pages/ProjectsPage.vue'),
        },
        {
          path: 'orders',
          name: 'orders',
          component: () => import('@/pages/OrdersPage.vue'),
        },
        {
          path: 'product-on-hand',
          name: 'product-on-hand',
          component: () => import('@/pages/ProductOnHandPage.vue'),
        },
        {
          path: 'cost-estimator',
          name: 'cost-estimator',
          component: () => import('@/pages/CostEstimatorPage.vue'),
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('@/pages/SettingsPage.vue'),
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('@/pages/ProfilePage.vue'),
        },
      ],
    },

    // ========================================================================
    // 404 Catch-All
    // ========================================================================
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

// ============================================================================
// Navigation Guards
// ============================================================================

router.beforeEach(async (to, from, next) => {
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)

  let authenticated = isAuthenticated()
  if (requiresAuth && !authenticated) {
    authenticated = await ensureAccessToken()
  }

  if (requiresAuth && !authenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  if (authenticated && to.name === 'login') {
    next({ name: 'dashboard' })
    return
  }

  next()
})
