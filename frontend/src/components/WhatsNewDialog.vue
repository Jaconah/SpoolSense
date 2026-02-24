<script setup lang="ts">
import { computed } from 'vue'
import { Sparkles, CheckCircle2, X } from 'lucide-vue-next'
import UiButton from '@/components/ui/UiButton.vue'
import { CHANGELOG, APP_VERSION } from '@/lib/changelog'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ 'update:open': [value: boolean] }>()

// Show latest release at top, rest as history
const latest = computed(() => CHANGELOG[0])
const history = computed(() => CHANGELOG.slice(1))

function close() {
  emit('update:open', false)
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-150"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="open"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60"
        @click.self="close"
      >
        <Transition
          enter-active-class="transition-all duration-200"
          enter-from-class="opacity-0 scale-95"
          enter-to-class="opacity-100 scale-100"
          leave-active-class="transition-all duration-150"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-0 scale-95"
        >
          <div
            v-if="open"
            class="relative w-full max-w-lg max-h-[85vh] flex flex-col rounded-xl border bg-background shadow-2xl overflow-hidden"
          >
            <!-- Header -->
            <div class="flex items-start justify-between p-6 pb-4 border-b">
              <div class="flex items-center gap-3">
                <div class="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                  <Sparkles class="h-5 w-5 text-primary" />
                </div>
                <div>
                  <h2 class="text-lg font-semibold">What's New</h2>
                  <p class="text-sm text-muted-foreground">v{{ APP_VERSION }}</p>
                </div>
              </div>
              <button
                @click="close"
                class="rounded-md p-1 text-muted-foreground hover:text-foreground transition-colors"
              >
                <X class="h-5 w-5" />
              </button>
            </div>

            <!-- Scrollable content -->
            <div class="overflow-y-auto flex-1 p-6 space-y-6">
              <!-- Latest release -->
              <div v-if="latest">
                <div class="flex items-center gap-2 mb-3">
                  <span class="inline-flex items-center rounded-full bg-primary px-2.5 py-0.5 text-xs font-semibold text-primary-foreground">
                    v{{ latest.version }}
                  </span>
                  <span class="font-semibold">{{ latest.name }}</span>
                  <span class="text-xs text-muted-foreground ml-auto">{{ latest.date }}</span>
                </div>
                <ul class="space-y-2">
                  <li
                    v-for="(item, i) in latest.highlights"
                    :key="i"
                    class="flex items-start gap-2 text-sm"
                  >
                    <CheckCircle2 class="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                    <span>{{ item }}</span>
                  </li>
                </ul>
              </div>

              <!-- Previous releases -->
              <div v-if="history.length" class="border-t pt-4">
                <p class="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-4">Previous Releases</p>
                <div class="space-y-5">
                  <div v-for="entry in history" :key="entry.version">
                    <div class="flex items-center gap-2 mb-2">
                      <span class="inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium text-muted-foreground">
                        v{{ entry.version }}
                      </span>
                      <span class="text-sm font-medium">{{ entry.name }}</span>
                      <span class="text-xs text-muted-foreground ml-auto">{{ entry.date }}</span>
                    </div>
                    <ul class="space-y-1.5">
                      <li
                        v-for="(item, i) in entry.highlights"
                        :key="i"
                        class="flex items-start gap-2 text-sm text-muted-foreground"
                      >
                        <span class="mt-1.5 h-1.5 w-1.5 rounded-full bg-muted-foreground/50 shrink-0" />
                        <span>{{ item }}</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            <!-- Footer -->
            <div class="border-t px-6 py-4 flex justify-end">
              <UiButton @click="close">Got it!</UiButton>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
