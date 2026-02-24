<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@/lib/api'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiAlert from '@/components/ui/UiAlert.vue'

const router = useRouter()

const password = ref('')
const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  error.value = ''

  if (!password.value) {
    error.value = 'Please enter your password'
    return
  }

  loading.value = true

  try {
    await authApi.login({ password: password.value })
    const redirect = router.currentRoute.value.query.redirect as string
    const safePath = redirect && redirect.startsWith('/') && !redirect.startsWith('//') ? redirect : '/'
    router.push(safePath)
  } catch (err: any) {
    error.value = err.message || 'Login failed. Please check your password.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-linear-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 px-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center p-5 bg-indigo-600 dark:bg-indigo-500 rounded-2xl mb-4 shadow-lg">
          <svg class="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
        </div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          SpoolSense
        </h1>
        <p class="text-gray-600 dark:text-gray-400">
          Track your 3D printing inventory and costs
        </p>
      </div>

      <UiCard class="shadow-xl p-8">
        <form @submit.prevent="handleLogin" class="space-y-6">
          <UiAlert v-if="error" variant="error">
            {{ error }}
          </UiAlert>

          <div>
            <label for="password" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Password
            </label>
            <UiInput
              id="password"
              v-model="password"
              type="password"
              placeholder="••••••••"
              required
              autocomplete="current-password"
              :disabled="loading"
            />
          </div>

          <UiButton type="submit" :loading="loading" :disabled="loading" class="w-full">
            <span v-if="!loading">Sign In</span>
            <span v-else>Signing in...</span>
          </UiButton>
        </form>
      </UiCard>
    </div>
  </div>
</template>
