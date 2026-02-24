<script setup lang="ts">
import { ref } from 'vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiInput from '@/components/ui/UiInput.vue'
import UiCard from '@/components/ui/UiCard.vue'
import UiCardContent from '@/components/ui/UiCardContent.vue'
import UiBadge from '@/components/ui/UiBadge.vue'
import UiTooltip from '@/components/ui/UiTooltip.vue'
import { Plus, Pencil, Trash2, Check, X, HelpCircle } from 'lucide-vue-next'
import { api, type FilamentType, type Manufacturer } from '@/lib/api'

type Item = FilamentType | Manufacturer

const props = defineProps<{
  title: string
  items: Item[]
  endpoint: string
  hasWebsite?: boolean
  hasAbbreviation?: boolean
}>()

const emit = defineEmits<{ changed: [] }>()

const adding = ref(false)
const editId = ref<number | null>(null)
const name = ref('')
const abbreviation = ref('')
const extra = ref('')
const error = ref('')

async function handleAdd() {
  if (!name.value.trim()) return
  if (props.hasAbbreviation && !abbreviation.value.trim()) {
    error.value = 'Abbreviation is required'
    return
  }
  error.value = ''
  try {
    const payload: any = { name: name.value.trim() }
    if (props.hasAbbreviation) payload.abbreviation = abbreviation.value.trim().toUpperCase()
    if (props.hasWebsite) payload.website = extra.value.trim() || null
    else payload.description = extra.value.trim() || null
    await api.post(props.endpoint, payload)
    adding.value = false
    name.value = ''
    abbreviation.value = ''
    extra.value = ''
    emit('changed')
  } catch (e: any) {
    error.value = e.message
  }
}

async function handleUpdate(id: number) {
  if (!name.value.trim()) return
  if (props.hasAbbreviation && !abbreviation.value.trim()) {
    error.value = 'Abbreviation is required'
    return
  }
  error.value = ''
  try {
    const payload: any = { name: name.value.trim() }
    if (props.hasAbbreviation) payload.abbreviation = abbreviation.value.trim().toUpperCase()
    if (props.hasWebsite) payload.website = extra.value.trim() || null
    else payload.description = extra.value.trim() || null
    await api.put(`${props.endpoint}/${id}`, payload)
    editId.value = null
    name.value = ''
    abbreviation.value = ''
    extra.value = ''
    emit('changed')
  } catch (e: any) {
    error.value = e.message
  }
}

async function handleDelete(item: Item) {
  if (!confirm(`Delete "${item.name}"?`)) return
  try {
    await api.delete(`${props.endpoint}/${item.id}`)
    emit('changed')
  } catch (e: any) {
    alert(e.message)
  }
}

function startEdit(item: Item) {
  editId.value = item.id
  name.value = item.name
  if (props.hasAbbreviation) {
    abbreviation.value = (item as FilamentType).abbreviation || ''
  }
  extra.value = props.hasWebsite
    ? (item as Manufacturer).website || ''
    : (item as FilamentType).description || ''
  adding.value = false
}

function startAdd() {
  adding.value = true
  editId.value = null
  name.value = ''
  abbreviation.value = ''
  extra.value = ''
  error.value = ''
}
</script>

<template>
  <div class="space-y-3">
    <div class="flex items-center justify-between">
      <h3 class="font-medium">{{ title }}</h3>
      <UiButton size="sm" variant="outline" @click="startAdd">
        <Plus class="mr-1 h-3 w-3" /> Add
      </UiButton>
    </div>

    <p v-if="error" class="text-sm text-red-500">{{ error }}</p>

    <UiCard v-if="adding">
      <UiCardContent class="flex flex-col sm:flex-row items-start sm:items-center gap-2 p-3">
        <UiInput v-model="name" placeholder="Name" class="flex-1 w-full sm:w-auto" autofocus />
        <div v-if="hasAbbreviation" class="flex items-center gap-2 w-full sm:w-auto">
          <UiInput
            v-model="abbreviation"
            placeholder="Abbreviation (e.g., PLA)"
            class="flex-1 sm:w-32"
            maxlength="10"
            @input="abbreviation = abbreviation.toUpperCase()"
          />
          <UiTooltip content="Short code for tracking IDs (e.g., PLA, ABS, CF). Max 10 chars.">
            <HelpCircle class="h-4 w-4 text-muted-foreground cursor-help shrink-0" />
          </UiTooltip>
        </div>
        <UiInput
          v-model="extra"
          :placeholder="hasWebsite ? 'Website URL' : 'Description'"
          class="flex-1 w-full sm:w-auto"
        />
        <div class="flex gap-2 w-full sm:w-auto justify-end">
          <UiButton size="icon" variant="ghost" @click="handleAdd">
            <Check class="h-4 w-4" />
          </UiButton>
          <UiButton size="icon" variant="ghost" @click="adding = false">
            <X class="h-4 w-4" />
          </UiButton>
        </div>
      </UiCardContent>
    </UiCard>

    <div class="space-y-1">
      <template v-for="item in items" :key="item.id">
        <UiCard v-if="editId === item.id">
          <UiCardContent class="flex flex-col sm:flex-row items-start sm:items-center gap-2 p-3">
            <UiInput v-model="name" class="flex-1 w-full sm:w-auto" autofocus />
            <div v-if="hasAbbreviation" class="flex items-center gap-2 w-full sm:w-auto">
              <UiInput
                v-model="abbreviation"
                placeholder="Abbreviation"
                class="flex-1 sm:w-32"
                maxlength="10"
                @input="abbreviation = abbreviation.toUpperCase()"
              />
              <UiTooltip content="Short code for tracking IDs (e.g., PLA, ABS, CF). Max 10 chars.">
                <HelpCircle class="h-4 w-4 text-muted-foreground cursor-help shrink-0" />
              </UiTooltip>
            </div>
            <UiInput
              v-model="extra"
              :placeholder="hasWebsite ? 'Website URL' : 'Description'"
              class="flex-1 w-full sm:w-auto"
            />
            <div class="flex gap-2 w-full sm:w-auto justify-end">
              <UiButton size="icon" variant="ghost" @click="handleUpdate(item.id)">
                <Check class="h-4 w-4" />
              </UiButton>
              <UiButton size="icon" variant="ghost" @click="editId = null">
                <X class="h-4 w-4" />
              </UiButton>
            </div>
          </UiCardContent>
        </UiCard>
        <div
          v-else
          class="flex items-center justify-between rounded-md border px-3 py-2"
        >
          <div class="flex items-center gap-2">
            <span class="font-medium">{{ item.name }}</span>
            <UiBadge v-if="hasAbbreviation && (item as FilamentType).abbreviation" variant="outline" class="text-xs font-mono">
              {{ (item as FilamentType).abbreviation }}
            </UiBadge>
            <UiBadge v-if="item.is_default" variant="secondary" class="text-xs">
              default
            </UiBadge>
            <span class="text-xs text-muted-foreground">({{ item.usage_count }} uses)</span>
          </div>
          <div class="flex gap-1">
            <UiButton size="icon" variant="ghost" @click="startEdit(item)">
              <Pencil class="h-3 w-3" />
            </UiButton>
            <UiButton size="icon" variant="ghost" @click="handleDelete(item)">
              <Trash2 class="h-3 w-3" />
            </UiButton>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
