<script setup lang="ts">
import {
  Dialog,
  DialogPanel,
  TransitionRoot,
  TransitionChild,
} from '@headlessui/vue'
import { X } from 'lucide-vue-next'
import { cn } from '@/lib/utils'
import { computed } from 'vue'

const props = defineProps<{
  open: boolean
  class?: string
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
}>()

const panelClasses = computed(() => cn(
  'relative w-full transform rounded-lg border bg-background shadow-2xl transition-all',
  'max-w-md md:max-w-2xl lg:max-w-3xl', // Responsive max-width
  'max-h-[85vh] md:max-h-[90vh]', // Viewport-relative height
  'flex flex-col', // Flex container for proper scrolling
  props.class
))

function close() {
  emit('update:open', false)
}
</script>

<template>
  <TransitionRoot :show="open" as="template">
    <Dialog @close="close" class="relative z-50">
      <TransitionChild
        enter="ease-out duration-300"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="ease-in duration-200"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-black/60 backdrop-blur-xs" />
      </TransitionChild>

      <div class="fixed inset-0 flex items-center justify-center p-3 sm:p-4 md:p-6">
        <TransitionChild
          enter="ease-out duration-300"
          enter-from="opacity-0 scale-95 translate-y-4"
          enter-to="opacity-100 scale-100 translate-y-0"
          leave="ease-in duration-200"
          leave-from="opacity-100 scale-100 translate-y-0"
          leave-to="opacity-0 scale-95 translate-y-4"
        >
          <DialogPanel :class="panelClasses">
            <!-- Header with close button - fixed -->
            <div class="relative px-4 sm:px-6 pt-4 sm:pt-6 pb-3 sm:pb-4 border-b border-border/50 shrink-0">
              <button
                class="absolute right-3 sm:right-4 top-3 sm:top-4 rounded-md p-1.5 opacity-70 ring-offset-background transition-all hover:opacity-100 hover:bg-muted focus:outline-hidden focus:ring-2 focus:ring-ring focus:ring-offset-2"
                @click="close"
                type="button"
              >
                <X class="h-4 w-4" />
                <span class="sr-only">Close</span>
              </button>
              <slot name="header" />
            </div>

            <!-- Scrollable content area -->
            <div class="overflow-y-auto px-4 sm:px-6 py-4 sm:py-5 flex-1">
              <slot />
            </div>

            <!-- Footer - fixed at bottom -->
            <div class="px-4 sm:px-6 pb-4 sm:pb-6 pt-3 sm:pt-4 border-t border-border/50 shrink-0">
              <slot name="footer" />
            </div>
          </DialogPanel>
        </TransitionChild>
      </div>
    </Dialog>
  </TransitionRoot>
</template>
