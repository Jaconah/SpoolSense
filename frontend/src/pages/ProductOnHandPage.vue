<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api, type ProductOnHand } from '@/lib/api'
import { useProductsOnHand, useProductOnHandStats, useProjects } from '@/composables/use-data'
import ProductOnHandForm from '@/components/product-on-hand/ProductOnHandForm.vue'
import ConvertToOrderDialog from '@/components/product-on-hand/ConvertToOrderDialog.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiCardContent from '@/components/ui/UiCardContent.vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiSelect from '@/components/ui/UiSelect.vue'
import UiLabel from '@/components/ui/UiLabel.vue'
import { Package, ArrowRight, Printer, MapPin, DollarSign, CheckCircle, Wrench } from 'lucide-vue-next'

const router = useRouter()

const selectedProjectId = ref<number | null>(null)
const { data: products, loading, refresh } = useProductsOnHand(computed(() => selectedProjectId.value))
const { data: stats, refresh: refreshStats } = useProductOnHandStats()
const { data: projects } = useProjects()

const editFormOpen = ref(false)
const editingProduct = ref<ProductOnHand | null>(null)
const convertDialogOpen = ref(false)
const convertingProduct = ref<ProductOnHand | null>(null)

const projectOptions = computed(() => {
  if (!projects.value) return []
  return [
    { value: 'all', label: 'All Products' },
    ...projects.value.map(p => ({ value: String(p.id), label: p.name }))
  ]
})

function handleProjectFilter(value: string) {
  selectedProjectId.value = value === 'all' ? null : Number(value)
}

function handleEdit(product: ProductOnHand) {
  editingProduct.value = product
  editFormOpen.value = true
}

function handleConvert(product: ProductOnHand) {
  convertingProduct.value = product
  convertDialogOpen.value = true
}

async function handleConvertSuccess(orderId: number) {
  await refresh()
  await refreshStats()
  router.push(`/orders`)
}

async function handlePrintAnother(product: ProductOnHand) {
  router.push(`/print-jobs`)
}

async function handleMarkCompleted(product: ProductOnHand) {
  const location = prompt(`Mark as Completed\n\nEnter location where this product will be stored:`, product.location || '')
  if (!location) return

  try {
    await api.put(`/products-on-hand/${product.id}`, {
      status: 'completed',
      location: location.trim()
    })
    await refresh()
    await refreshStats()
  } catch (e: any) {
    alert(e.message || 'Failed to mark as completed')
  }
}

async function handleDelete(product: ProductOnHand) {
  if (!confirm(`Delete ${product.name} (${product.color}) from Product on Hand?\n\nThis cannot be undone.`)) return

  try {
    await api.delete(`/products-on-hand/${product.id}`)
    await refresh()
    await refreshStats()
  } catch (e: any) {
    alert(e.message || 'Failed to delete product')
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold">Product on Hand</h1>
        <p class="text-muted-foreground mt-1">
          Finished products ready to sell
        </p>
      </div>
    </div>

    <!-- Stats -->
    <div v-if="stats" class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <UiCard>
        <UiCardContent class="pt-6">
          <div class="flex items-center gap-3">
            <Package class="h-8 w-8 text-blue-500" />
            <div>
              <p class="text-sm text-muted-foreground">Products on Hand</p>
              <p class="text-2xl font-bold">{{ stats.total_count }}</p>
            </div>
          </div>
        </UiCardContent>
      </UiCard>

      <UiCard>
        <UiCardContent class="pt-6">
          <div class="flex items-center gap-3">
            <DollarSign class="h-8 w-8 text-green-500" />
            <div>
              <p class="text-sm text-muted-foreground">Total Value</p>
              <p class="text-2xl font-bold">${{ stats.total_value.toFixed(2) }}</p>
            </div>
          </div>
        </UiCardContent>
      </UiCard>

      <UiCard>
        <UiCardContent class="pt-6">
          <div class="flex items-center gap-3">
            <DollarSign class="h-8 w-8 text-purple-500" />
            <div>
              <p class="text-sm text-muted-foreground">Potential Profit</p>
              <p class="text-2xl font-bold">${{ stats.total_potential_profit.toFixed(2) }}</p>
            </div>
          </div>
        </UiCardContent>
      </UiCard>
    </div>

    <!-- Filter -->
    <div class="flex items-center gap-4">
      <UiLabel for="project-filter">Filter by Project:</UiLabel>
      <UiSelect
        id="project-filter"
        :options="projectOptions"
        :model-value="selectedProjectId ? String(selectedProjectId) : 'all'"
        @update:model-value="handleProjectFilter"
        class="w-64"
      />
    </div>

    <!-- List -->
    <div v-if="loading" class="text-center py-12 text-muted-foreground">
      Loading...
    </div>

    <div v-else-if="!products || products.length === 0" class="text-center py-12">
      <Package class="h-16 w-16 mx-auto text-muted-foreground/50 mb-4" />
      <p class="text-muted-foreground">
        No products on hand yet.
      </p>
      <p class="text-sm text-muted-foreground mt-2">
        Create products from completed print jobs.
      </p>
      <UiButton @click="router.push('/print-jobs')" class="mt-4">
        Go to Print Jobs
      </UiButton>
    </div>

    <div v-else class="grid grid-cols-1 gap-4">
      <UiCard v-for="product in products" :key="product.id">
        <UiCardContent class="pt-6">
          <div class="flex items-start justify-between gap-4">
            <div class="flex-1">
              <!-- Header with Color Badge -->
              <div class="flex items-center gap-3 mb-3">
                <div class="flex items-center gap-3">
                  <div class="w-12 h-12 rounded-lg border-2 border-border shadow-xs flex items-center justify-center bg-linear-to-br from-primary/10 to-primary/5">
                    <span class="text-xl font-bold text-primary">{{ product.color.charAt(0) }}</span>
                  </div>
                  <div>
                    <h3 class="text-xl font-bold">{{ product.name }}</h3>
                    <p class="text-sm font-medium text-primary">{{ product.color }}</p>
                  </div>
                </div>

                <!-- Status Badge -->
                <span v-if="product.status === 'printed'" class="px-3 py-1 text-xs font-medium rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 flex items-center gap-1">
                  <Wrench class="h-3 w-3" />
                  Needs Assembly
                </span>
                <span v-else class="px-3 py-1 text-xs font-medium rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 flex items-center gap-1">
                  <CheckCircle class="h-3 w-3" />
                  Ready to Sell
                </span>
              </div>

              <!-- Project Info (if applicable) -->
              <p v-if="product.project_name" class="text-sm text-muted-foreground mb-3">
                Project: {{ product.project_name }}
              </p>

              <!-- Details Grid -->
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p class="text-muted-foreground flex items-center gap-1">
                    <MapPin class="h-3 w-3" />
                    Location
                  </p>
                  <p class="font-medium">{{ product.location || 'Not set' }}</p>
                </div>

                <div>
                  <p class="text-muted-foreground">Cost</p>
                  <p class="font-medium">${{ product.total_cost.toFixed(2) }}</p>
                  <p class="text-xs text-muted-foreground">
                    Filament: ${{ product.filament_cost.toFixed(2) }}
                    <span v-if="product.hardware_cost > 0"> + Hardware: ${{ product.hardware_cost.toFixed(2) }}</span>
                  </p>
                </div>

                <div>
                  <p class="text-muted-foreground">Sell Price</p>
                  <p class="font-medium">{{ product.sell_price ? `$${product.sell_price.toFixed(2)}` : 'Not set' }}</p>
                </div>

                <div>
                  <p class="text-muted-foreground">Potential Profit</p>
                  <p v-if="product.potential_profit !== null" class="font-medium" :class="product.potential_profit >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'">
                    ${{ product.potential_profit.toFixed(2) }}
                  </p>
                  <p v-else class="font-medium text-muted-foreground">—</p>
                </div>
              </div>

              <!-- Hardware Items (only shown while still needing assembly) -->
              <div v-if="product.status === 'printed' && product.hardware_items && product.hardware_items.length > 0" class="mt-3 p-3 rounded-md bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
                <p class="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2 flex items-center gap-1">
                  <Wrench class="h-4 w-4" />
                  Hardware Needed for Assembly:
                </p>
                <ul class="space-y-1">
                  <li v-for="hw in product.hardware_items" :key="hw.id" class="text-sm text-blue-800 dark:text-blue-200">
                    • {{ hw.name }} ({{ hw.quantity }}x) - ${{ (hw.cost_per_item * hw.quantity).toFixed(2) }}
                  </li>
                </ul>
              </div>

              <!-- Notes -->
              <p v-if="product.notes" class="text-sm text-muted-foreground mt-3 italic">
                {{ product.notes }}
              </p>
            </div>

            <!-- Action Buttons -->
            <div class="flex flex-col gap-2">
              <!-- Primary Action: Mark as Completed or Convert to Order -->
              <UiButton v-if="product.status === 'printed'" size="sm" @click="handleMarkCompleted(product)">
                <CheckCircle class="h-4 w-4 mr-1" />
                Mark as Completed
              </UiButton>
              <UiButton v-else size="sm" @click="handleConvert(product)">
                <ArrowRight class="h-4 w-4 mr-1" />
                Convert to Order
              </UiButton>

              <!-- Secondary Actions -->
              <UiButton size="sm" variant="outline" @click="handlePrintAnother(product)">
                <Printer class="h-4 w-4 mr-1" />
                Print Another
              </UiButton>

              <UiButton size="sm" variant="ghost" @click="handleEdit(product)">
                Edit
              </UiButton>

              <UiButton size="sm" variant="ghost" @click="handleDelete(product)">
                Delete
              </UiButton>
            </div>
          </div>
        </UiCardContent>
      </UiCard>
    </div>

    <!-- Dialogs -->
    <ProductOnHandForm
      :open="editFormOpen"
      @update:open="editFormOpen = $event"
      :product-on-hand="editingProduct"
      @saved="refresh(); refreshStats()"
    />

    <ConvertToOrderDialog
      :open="convertDialogOpen"
      @update:open="convertDialogOpen = $event"
      :product="convertingProduct"
      @converted="handleConvertSuccess"
    />
  </div>
</template>
