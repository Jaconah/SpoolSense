<script setup lang="ts">
import { computed } from 'vue'
import {
  Listbox,
  ListboxButton,
  ListboxOption,
  ListboxOptions,
} from '@headlessui/vue'
import { Check, ChevronDown } from 'lucide-vue-next'
import { cn } from '@/lib/utils'

export interface SelectOption {
  value: string
  label: string
}

const props = defineProps<{
  modelValue: string
  options: SelectOption[]
  placeholder?: string
  class?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const selectedLabel = computed(() => {
  const opt = props.options.find((o) => o.value === props.modelValue)
  return opt?.label || props.placeholder || ''
})

const triggerClasses = computed(() => cn(
  'flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-hidden focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
  props.class
))
</script>

<template>
  <Listbox :model-value="modelValue" @update:model-value="emit('update:modelValue', $event)">
    <div class="relative">
      <ListboxButton :class="triggerClasses">
        <span class="block truncate" :class="{ 'text-muted-foreground': !modelValue }">{{ selectedLabel }}</span>
        <ChevronDown class="h-4 w-4 opacity-50" />
      </ListboxButton>

      <transition
        leave-active-class="transition duration-100 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <ListboxOptions
          class="absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-md border bg-popover py-1 text-popover-foreground shadow-md focus:outline-hidden"
        >
          <ListboxOption
            v-for="option in options"
            :key="option.value"
            :value="option.value"
            v-slot="{ active, selected }"
          >
            <div
              :class="cn(
                'relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-hidden',
                active && 'bg-accent text-accent-foreground'
              )"
            >
              <span v-if="selected" class="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
                <Check class="h-4 w-4" />
              </span>
              <span>{{ option.label }}</span>
            </div>
          </ListboxOption>
        </ListboxOptions>
      </transition>
    </div>
  </Listbox>
</template>
