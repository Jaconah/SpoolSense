<script setup lang="ts">
import { ref } from 'vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiCardHeader from '@/components/ui/UiCardHeader.vue'
import UiCardTitle from '@/components/ui/UiCardTitle.vue'
import UiCardContent from '@/components/ui/UiCardContent.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiPasswordStrength from '@/components/ui/UiPasswordStrength.vue'
import { usePasswordStrength } from '@/composables/use-password-strength'
import { authApi } from '@/lib/api'
import { Save, Key } from 'lucide-vue-next'

// Change password state
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const { strength: passwordStrength } = usePasswordStrength(newPassword)
const passwordSaving = ref(false)
const passwordSuccess = ref('')
const passwordError = ref('')

async function changePassword() {
  passwordError.value = ''
  passwordSuccess.value = ''
  if (!currentPassword.value || !newPassword.value) {
    passwordError.value = 'All fields are required'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    passwordError.value = 'New passwords do not match'
    return
  }
  passwordSaving.value = true
  try {
    await authApi.changePassword({
      current_password: currentPassword.value,
      new_password: newPassword.value,
    })
    passwordSuccess.value = 'Password changed successfully.'
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
  } catch (e: any) {
    passwordError.value = e.message
  } finally {
    passwordSaving.value = false
  }
}
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-3xl font-bold">My Profile</h1>

    <UiCard>
      <UiCardHeader>
        <UiCardTitle>Change Password</UiCardTitle>
      </UiCardHeader>
      <UiCardContent>
        <div class="space-y-4 max-w-sm">
          <div class="space-y-1.5">
            <label class="text-sm font-medium">Current Password</label>
            <UiInput
              v-model="currentPassword"
              type="password"
              placeholder="Current password"
              autocomplete="current-password"
            />
          </div>
          <div class="space-y-1.5">
            <label class="text-sm font-medium">New Password</label>
            <UiInput
              v-model="newPassword"
              type="password"
              placeholder="New password"
              autocomplete="new-password"
            />
            <UiPasswordStrength v-if="newPassword" :strength="passwordStrength" />
          </div>
          <div class="space-y-1.5">
            <label class="text-sm font-medium">Confirm New Password</label>
            <UiInput
              v-model="confirmPassword"
              type="password"
              placeholder="Confirm new password"
              autocomplete="new-password"
            />
          </div>
          <UiAlert v-if="passwordError" variant="error">{{ passwordError }}</UiAlert>
          <UiAlert v-if="passwordSuccess" variant="success">{{ passwordSuccess }}</UiAlert>
          <UiButton @click="changePassword" :disabled="passwordSaving">
            <Key class="h-4 w-4 mr-2" />
            {{ passwordSaving ? 'Changing…' : 'Change Password' }}
          </UiButton>
        </div>
      </UiCardContent>
    </UiCard>
  </div>
</template>
