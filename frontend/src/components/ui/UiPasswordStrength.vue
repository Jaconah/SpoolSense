<script setup lang="ts">
import { computed } from 'vue'
import type { PasswordStrength } from '@/composables/use-password-strength'
import { Check, X } from 'lucide-vue-next'

const props = defineProps<{
  strength: PasswordStrength
}>()

const barColor = computed(() => {
  switch (props.strength.level) {
    case 'strong': return 'bg-green-500'
    case 'good':   return 'bg-blue-500'
    case 'fair':   return 'bg-yellow-500'
    default:       return 'bg-red-500'
  }
})

const labelColor = computed(() => {
  switch (props.strength.level) {
    case 'strong': return 'text-green-600 dark:text-green-400'
    case 'good':   return 'text-blue-600 dark:text-blue-400'
    case 'fair':   return 'text-yellow-600 dark:text-yellow-400'
    default:       return 'text-red-600 dark:text-red-400'
  }
})

const label = computed(() => {
  return props.strength.level.charAt(0).toUpperCase() + props.strength.level.slice(1)
})
</script>

<template>
  <div class="space-y-2">
    <!-- Strength bar -->
    <div class="flex items-center gap-2">
      <div class="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
        <div
          class="h-full rounded-full transition-all duration-300"
          :class="barColor"
          :style="{ width: `${strength.percent}%` }"
        />
      </div>
      <span class="text-xs font-medium w-12 text-right" :class="labelColor">
        {{ label }}
      </span>
    </div>

    <!-- Requirements checklist -->
    <ul class="grid grid-cols-2 gap-x-4 gap-y-0.5 text-xs text-muted-foreground">
      <li class="flex items-center gap-1.5" :class="strength.requirements.minLength ? 'text-green-600 dark:text-green-400' : ''">
        <Check v-if="strength.requirements.minLength" class="h-3 w-3 shrink-0" />
        <X v-else class="h-3 w-3 shrink-0 opacity-40" />
        8+ characters
      </li>
      <li class="flex items-center gap-1.5" :class="strength.requirements.hasUpper ? 'text-green-600 dark:text-green-400' : ''">
        <Check v-if="strength.requirements.hasUpper" class="h-3 w-3 shrink-0" />
        <X v-else class="h-3 w-3 shrink-0 opacity-40" />
        Uppercase letter
      </li>
      <li class="flex items-center gap-1.5" :class="strength.requirements.hasLower ? 'text-green-600 dark:text-green-400' : ''">
        <Check v-if="strength.requirements.hasLower" class="h-3 w-3 shrink-0" />
        <X v-else class="h-3 w-3 shrink-0 opacity-40" />
        Lowercase letter
      </li>
      <li class="flex items-center gap-1.5" :class="strength.requirements.hasNumber ? 'text-green-600 dark:text-green-400' : ''">
        <Check v-if="strength.requirements.hasNumber" class="h-3 w-3 shrink-0" />
        <X v-else class="h-3 w-3 shrink-0 opacity-40" />
        Number
      </li>
    </ul>
  </div>
</template>
