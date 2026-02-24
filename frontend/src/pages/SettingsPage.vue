<script setup lang="ts">
import { inject } from 'vue'
import { useSettings, useFilamentTypes, useManufacturers } from '@/composables/use-data'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiCardHeader from '@/components/ui/UiCardHeader.vue'
import UiCardTitle from '@/components/ui/UiCardTitle.vue'
import UiCardContent from '@/components/ui/UiCardContent.vue'
import UiTabs from '@/components/ui/UiTabs.vue'
import UiTabsList from '@/components/ui/UiTabsList.vue'
import UiTab from '@/components/ui/UiTab.vue'
import UiTabPanels from '@/components/ui/UiTabPanels.vue'
import UiTabPanel from '@/components/ui/UiTabPanel.vue'
import GeneralSettings from '@/components/settings/GeneralSettings.vue'
import AdvancedSettings from '@/components/settings/AdvancedSettings.vue'
import TypeManager from '@/components/settings/TypeManager.vue'
import { getAccessToken } from '@/lib/api'
import { Download, MapPin } from 'lucide-vue-next'

const openOnboarding = inject<() => void>('openOnboarding')

function restartTour() {
  localStorage.removeItem('tour_dismissed')
  openOnboarding?.()
}

const { data: settings, loading, refresh: refreshSettings } = useSettings()
const { data: filamentTypes, refresh: refreshTypes } = useFilamentTypes()
const { data: manufacturers, refresh: refreshMfgs } = useManufacturers()

const exports = [
  { label: 'Spools', filename: 'spools.csv', description: 'All spool inventory with weight and cost data' },
  { label: 'Print Jobs', filename: 'print-jobs.csv', description: 'All logged print jobs with filament usage' },
  { label: 'Orders', filename: 'orders.csv', description: 'All customer orders and status' },
  { label: 'Hardware', filename: 'hardware.csv', description: 'Hardware inventory items and stock levels' },
  { label: 'Projects', filename: 'projects.csv', description: 'Project templates with filament and time estimates' },
]

async function downloadCsv(filename: string) {
  const token = getAccessToken()
  const res = await fetch(`/api/v1/export/${filename}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) return
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div v-if="loading || !settings" class="p-8 text-center text-muted-foreground">Loading...</div>
  <div v-else class="space-y-6">
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <h1 class="text-3xl font-bold">Settings</h1>
      <UiButton variant="outline" size="sm" @click="restartTour">
        <MapPin class="h-4 w-4 mr-2" /> Setup Tour
      </UiButton>
    </div>

    <UiTabs>
      <UiTabsList>
        <UiTab>General</UiTab>
        <UiTab>Filament Types</UiTab>
        <UiTab>Manufacturers</UiTab>
        <UiTab>Advanced</UiTab>
        <UiTab>Export</UiTab>
      </UiTabsList>

      <UiTabPanels>
        <UiTabPanel>
          <UiCard>
            <UiCardHeader>
              <UiCardTitle>Cost Calculation Rates</UiCardTitle>
            </UiCardHeader>
            <UiCardContent>
              <GeneralSettings :settings="settings" @saved="refreshSettings" />
            </UiCardContent>
          </UiCard>
        </UiTabPanel>

        <UiTabPanel>
          <UiCard>
            <UiCardHeader>
              <UiCardTitle>Filament Types</UiCardTitle>
            </UiCardHeader>
            <UiCardContent>
              <TypeManager
                title="Manage Filament Types"
                :items="filamentTypes || []"
                endpoint="/filament-types"
                has-abbreviation
                @changed="refreshTypes"
              />
            </UiCardContent>
          </UiCard>
        </UiTabPanel>

        <UiTabPanel>
          <UiCard>
            <UiCardHeader>
              <UiCardTitle>Manufacturers</UiCardTitle>
            </UiCardHeader>
            <UiCardContent>
              <TypeManager
                title="Manage Manufacturers"
                :items="manufacturers || []"
                endpoint="/manufacturers"
                has-website
                @changed="refreshMfgs"
              />
            </UiCardContent>
          </UiCard>
        </UiTabPanel>

        <UiTabPanel>
          <UiCard>
            <UiCardHeader>
              <UiCardTitle>Advanced</UiCardTitle>
            </UiCardHeader>
            <UiCardContent>
              <AdvancedSettings :settings="settings" @saved="refreshSettings" />
            </UiCardContent>
          </UiCard>
        </UiTabPanel>

        <UiTabPanel>
          <UiCard>
            <UiCardHeader>
              <UiCardTitle>Export Data</UiCardTitle>
            </UiCardHeader>
            <UiCardContent>
              <p class="text-sm text-muted-foreground mb-4">
                Download your data as CSV files. All exports include only your data and are compatible with Excel and Google Sheets.
              </p>
              <div class="space-y-2">
                <div
                  v-for="exp in exports"
                  :key="exp.filename"
                  class="flex items-center justify-between rounded-lg border p-3"
                >
                  <div>
                    <p class="font-medium text-sm">{{ exp.label }}</p>
                    <p class="text-xs text-muted-foreground">{{ exp.description }}</p>
                  </div>
                  <UiButton variant="outline" size="sm" @click="downloadCsv(exp.filename)">
                    <Download class="mr-2 h-3 w-3" /> Download
                  </UiButton>
                </div>
              </div>
            </UiCardContent>
          </UiCard>
        </UiTabPanel>
      </UiTabPanels>
    </UiTabs>
  </div>
</template>
