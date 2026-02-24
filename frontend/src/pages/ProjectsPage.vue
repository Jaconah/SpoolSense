<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePaginatedProjects, useHardware, useDebounce } from '@/composables/use-data'
import UiButton from '@/components/ui/UiButton.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiCardContent from '@/components/ui/UiCardContent.vue'
import UiBadge from '@/components/ui/UiBadge.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiPagination from '@/components/ui/UiPagination.vue'
import ProjectForm from '@/components/projects/ProjectForm.vue'
import ProjectCard from '@/components/projects/ProjectCard.vue'
import { Plus, Pencil, Trash2, ExternalLink, Search } from 'lucide-vue-next'
import { api, type Project } from '@/lib/api'

const route = useRoute()
const router = useRouter()

const formOpen = ref(false)
const editingProject = ref<Project | null>(null)
const page = ref(Number(route.query.page) || 1)
const perPage = ref(Number(route.query.per_page) || 25)
const searchInput = ref(String(route.query.search || ''))
const debouncedSearch = useDebounce(searchInput)

const params = computed(() => {
  const p: Record<string, any> = {}
  if (debouncedSearch.value) p.search = debouncedSearch.value
  p.page = page.value
  p.per_page = perPage.value
  return p
})

const { data: pageData, loading, refresh } = usePaginatedProjects(params)
const projects = computed(() => pageData.value?.items ?? [])
const { data: hardware } = useHardware()

// Reset page on search change
watch([debouncedSearch], () => { page.value = 1 })

// Sync URL
watch([page, perPage, debouncedSearch], () => {
  const query: Record<string, string> = {}
  if (page.value !== 1) query.page = String(page.value)
  if (perPage.value !== 25) query.per_page = String(perPage.value)
  if (searchInput.value) query.search = searchInput.value
  router.replace({ query })
})

async function handleDelete(project: Project) {
  if (!confirm(`Delete project "${project.name}"?`)) return
  try {
    await api.delete(`/projects/${project.id}`)
    refresh()
  } catch (e: any) {
    alert(e.message)
  }
}

function openCreate() {
  editingProject.value = null
  formOpen.value = true
}

function openEdit(project: Project) {
  editingProject.value = project
  formOpen.value = true
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold">Projects</h1>
      <div class="flex gap-2">
        <UiButton @click="openCreate">
          <Plus class="mr-2 h-4 w-4" /> Add Project
        </UiButton>
      </div>
    </div>

    <!-- Search + Filters -->
    <div class="flex flex-wrap gap-2">
      <div class="relative flex-1 min-w-[180px] max-w-xs">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <UiInput v-model="searchInput" placeholder="Search projects..." class="pl-9" />
      </div>
      <select
        v-model="perPage"
        class="h-10 rounded-md border border-input bg-background px-3 text-sm"
      >
        <option :value="10">10 / page</option>
        <option :value="25">25 / page</option>
        <option :value="50">50 / page</option>
        <option :value="100">100 / page</option>
      </select>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center text-muted-foreground">Loading...</div>

    <!-- Empty State -->
    <UiCard v-else-if="!projects.length && !pageData?.total">
      <UiCardContent class="p-8 text-center text-muted-foreground">
        No projects yet. Create your first project template!
      </UiCardContent>
    </UiCard>

    <!-- Mobile: Cards -->
    <div v-else class="grid gap-3 md:hidden">
      <ProjectCard
        v-for="project in projects"
        :key="project.id"
        :project="project"
        @edit="openEdit"
        @delete="handleDelete"
      />
    </div>

    <!-- Desktop: Table -->
    <div v-if="!loading && projects.length" class="hidden md:block rounded-lg border bg-card overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b bg-muted/50">
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Name</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Filament</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Print Time</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Sell Price</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Hardware</th>
              <th class="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wide text-muted-foreground">Model</th>
              <th class="px-4 py-2 text-right text-xs font-semibold uppercase tracking-wide text-muted-foreground">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="project in projects" :key="project.id" class="border-b last:border-0 hover:bg-muted/50 transition-colors">
              <td class="px-4 py-2 font-medium">{{ project.name }}</td>
              <td class="px-4 py-2">{{ project.filament_grams ? `${project.filament_grams}g` : '-' }}</td>
                <td class="px-4 py-2">{{ project.print_time_hours ? `${project.print_time_hours}h` : '-' }}</td>
                <td class="px-4 py-2">{{ project.sell_price != null ? `$${project.sell_price.toFixed(2)}` : '-' }}</td>
                <td class="px-4 py-2">
                  <div v-if="project.hardware.length" class="flex flex-wrap gap-1">
                    <UiBadge v-for="h in project.hardware" :key="h.id" variant="secondary">
                      {{ h.quantity }}x {{ h.hardware_item.name }}
                    </UiBadge>
                  </div>
                  <span v-else class="text-muted-foreground">-</span>
                </td>
                <td class="px-4 py-2">
                  <a
                    v-if="project.model_url"
                    :href="project.model_url"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="inline-flex items-center gap-1 text-primary hover:underline"
                  >
                    <ExternalLink class="h-3 w-3" /> Link
                  </a>
                  <span v-else class="text-muted-foreground">-</span>
                </td>
                <td class="px-4 py-2 text-right">
                  <div class="flex justify-end gap-1">
                    <UiButton variant="ghost" size="icon" @click="openEdit(project)">
                      <Pencil class="h-4 w-4" />
                    </UiButton>
                    <UiButton variant="ghost" size="icon" @click="handleDelete(project)">
                      <Trash2 class="h-4 w-4" />
                    </UiButton>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    <!-- Pagination -->
    <UiPagination
      v-if="pageData && pageData.total > 0"
      :model-value="page"
      :total="pageData.total"
      :per-page="perPage"
      @update:model-value="page = $event"
    />

    <ProjectForm
      v-model:open="formOpen"
      :project="editingProject"
      :hardware-items="hardware || []"
      @saved="refresh"
    />
  </div>
</template>
