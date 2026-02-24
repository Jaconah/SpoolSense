<script setup lang="ts">
import { ref, computed } from 'vue'
import UiButton from '@/components/ui/UiButton.vue'
import UiAlert from '@/components/ui/UiAlert.vue'
import UiDialog from '@/components/ui/UiDialog.vue'
import { Upload, Download, CheckCircle, XCircle, FileText } from 'lucide-vue-next'
import { getAccessToken } from '@/lib/api'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{
  'update:open': [value: boolean]
  imported: []
}>()

// State
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
const preview = ref<Record<string, string>[]>([])
const previewHeaders = ref<string[]>([])
const parseError = ref<string | null>(null)
const importing = ref(false)
const result = ref<{ imported: number; skipped: number; errors: { row: number; reason: string }[] } | null>(null)
const importError = ref<string | null>(null)

const REQUIRED_COLS = ['filament_type', 'manufacturer', 'color_name', 'total_weight_g', 'cost_per_kg']
const PREVIEW_ROWS = 5

const previewValid = computed(() =>
  REQUIRED_COLS.every(col => previewHeaders.value.includes(col))
)

function close() {
  emit('update:open', false)
  // Reset after close animation
  setTimeout(reset, 200)
}

function reset() {
  selectedFile.value = null
  preview.value = []
  previewHeaders.value = []
  parseError.value = null
  result.value = null
  importError.value = null
  if (fileInput.value) fileInput.value.value = ''
}

function parseCSV(text: string): { headers: string[]; rows: Record<string, string>[] } {
  const lines = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n').filter(l => l.trim())
  if (lines.length === 0) return { headers: [], rows: [] }

  // Simple CSV parse — handles quoted fields
  function parseLine(line: string): string[] {
    const fields: string[] = []
    let cur = ''
    let inQuote = false
    for (let i = 0; i < line.length; i++) {
      const ch = line[i]
      if (ch === '"') {
        if (inQuote && line[i + 1] === '"') { cur += '"'; i++ }
        else inQuote = !inQuote
      } else if (ch === ',' && !inQuote) {
        fields.push(cur.trim())
        cur = ''
      } else {
        cur += ch
      }
    }
    fields.push(cur.trim())
    return fields
  }

  const headers = parseLine(lines[0])
  const rows = lines.slice(1).map(line => {
    const vals = parseLine(line)
    const row: Record<string, string> = {}
    headers.forEach((h, i) => { row[h] = vals[i] ?? '' })
    return row
  }).filter(row => Object.values(row).some(v => v.trim()))

  return { headers, rows }
}

function onFileChange(e: Event) {
  parseError.value = null
  result.value = null
  importError.value = null
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) { selectedFile.value = null; return }
  if (!file.name.toLowerCase().endsWith('.csv')) {
    parseError.value = 'Please select a .csv file'
    selectedFile.value = null
    return
  }
  selectedFile.value = file
  const reader = new FileReader()
  reader.onload = (ev) => {
    try {
      const text = ev.target?.result as string
      const { headers, rows } = parseCSV(text)
      previewHeaders.value = headers
      preview.value = rows.slice(0, PREVIEW_ROWS)
    } catch {
      parseError.value = 'Failed to parse CSV. Make sure it is a valid CSV file.'
    }
  }
  reader.readAsText(file)
}

async function downloadTemplate() {
  const token = getAccessToken()
  const res = await fetch('/api/v1/spools/import/template', {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) return
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'spool_import_template.csv'
  a.click()
  URL.revokeObjectURL(url)
}

async function doImport() {
  if (!selectedFile.value) return
  importing.value = true
  importError.value = null
  result.value = null
  try {
    const token = getAccessToken()
    const form = new FormData()
    form.append('file', selectedFile.value)
    const res = await fetch('/api/v1/spools/import', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    })
    const data = await res.json()
    if (!res.ok) {
      const detail = data.detail
      if (detail && typeof detail === 'object' && Array.isArray(detail.errors)) {
        // Validation pass failed — show per-row errors in the result panel
        result.value = { imported: 0, skipped: detail.errors.length, errors: detail.errors }
      } else {
        importError.value = typeof detail === 'string' ? detail : `Import failed (${res.status})`
      }
      return
    }
    result.value = data
    if (data.imported > 0) emit('imported')
  } catch (e: any) {
    importError.value = e.message
  } finally {
    importing.value = false
  }
}
</script>

<template>
  <UiDialog :open="open" @update:open="!$event && close()">
    <template #header>
      <h2 class="text-lg font-semibold">Import Spools from CSV</h2>
    </template>

    <div class="space-y-4">
      <!-- Result view -->
      <div v-if="result" class="space-y-3">
        <div
          class="flex items-center gap-2 font-semibold"
          :class="result.imported > 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'"
        >
          <CheckCircle v-if="result.imported > 0" class="h-5 w-5" />
          <XCircle v-else class="h-5 w-5" />
          {{ result.imported > 0 ? 'Import complete' : 'Validation failed — nothing imported' }}
        </div>
        <div class="grid grid-cols-2 gap-3 text-sm">
          <div class="rounded-lg border bg-muted/30 p-3 text-center">
            <p class="text-xs text-muted-foreground">Imported</p>
            <p class="text-2xl font-bold text-green-600 dark:text-green-400">{{ result.imported }}</p>
          </div>
          <div class="rounded-lg border bg-muted/30 p-3 text-center">
            <p class="text-xs text-muted-foreground">Skipped</p>
            <p class="text-2xl font-bold" :class="result.skipped > 0 ? 'text-yellow-600 dark:text-yellow-400' : ''">
              {{ result.skipped }}
            </p>
          </div>
        </div>
        <div v-if="result.errors.length > 0" class="space-y-1 max-h-40 overflow-y-auto">
          <p class="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Row Errors</p>
          <div
            v-for="err in result.errors"
            :key="err.row"
            class="flex items-start gap-2 text-xs text-red-600 dark:text-red-400"
          >
            <XCircle class="h-3.5 w-3.5 mt-0.5 shrink-0" />
            <span>Row {{ err.row }}: {{ err.reason }}</span>
          </div>
        </div>
      </div>

      <!-- Import form -->
      <template v-else>
        <!-- Download template -->
        <div class="flex items-center justify-between rounded-lg border bg-muted/30 p-3">
          <div class="flex items-center gap-2 text-sm">
            <FileText class="h-4 w-4 text-muted-foreground" />
            <span>Need a template?</span>
          </div>
          <UiButton variant="outline" size="sm" @click="downloadTemplate">
            <Download class="h-3.5 w-3.5 mr-1.5" />
            Download Template
          </UiButton>
        </div>

        <!-- File picker -->
        <div class="space-y-2">
          <label class="text-sm font-medium">Select CSV file</label>
          <input
            ref="fileInput"
            type="file"
            accept=".csv"
            class="block w-full text-sm text-muted-foreground file:mr-3 file:rounded-md file:border file:border-input file:bg-background file:px-3 file:py-1.5 file:text-sm file:font-medium file:cursor-pointer hover:file:bg-accent"
            @change="onFileChange"
          />
          <p class="text-xs text-muted-foreground">
            Required: filament_type, manufacturer, color_name, total_weight_g, cost_per_kg<br>
            Optional: color_hex, remaining_weight_g, purchase_date, location, notes, tracking_id<br>
            Max file size: 5 MB. The entire file is validated before any spools are saved.
          </p>
        </div>

        <UiAlert v-if="parseError" variant="error">{{ parseError }}</UiAlert>
        <UiAlert v-if="importError" variant="error">{{ importError }}</UiAlert>

        <!-- Missing columns warning -->
        <UiAlert v-if="selectedFile && !previewValid && !parseError" variant="warning">
          Missing required columns:
          {{ REQUIRED_COLS.filter(c => !previewHeaders.includes(c)).join(', ') }}
        </UiAlert>

        <!-- Preview table -->
        <div v-if="preview.length > 0 && previewValid" class="space-y-2">
          <p class="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            Preview (first {{ Math.min(preview.length, PREVIEW_ROWS) }} rows)
          </p>
          <div class="overflow-x-auto rounded-lg border text-xs">
            <table class="w-full">
              <thead>
                <tr class="border-b bg-muted/50">
                  <th
                    v-for="col in previewHeaders"
                    :key="col"
                    class="px-2 py-1.5 text-left font-semibold uppercase tracking-wide text-muted-foreground whitespace-nowrap"
                  >{{ col }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in preview" :key="i" class="border-b last:border-0">
                  <td v-for="col in previewHeaders" :key="col" class="px-2 py-1.5 truncate max-w-[120px]">
                    {{ row[col] || '—' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <UiButton variant="outline" @click="close">
          {{ result ? 'Close' : 'Cancel' }}
        </UiButton>
        <UiButton
          v-if="!result"
          :disabled="!selectedFile || !previewValid || importing"
          @click="doImport"
        >
          <Upload class="h-4 w-4 mr-2" />
          {{ importing ? 'Importing…' : 'Import' }}
        </UiButton>
        <UiButton v-else @click="reset">
          Import Another File
        </UiButton>
      </div>
    </template>
  </UiDialog>
</template>
