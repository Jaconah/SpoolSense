import { ref, watch, provide, inject, type Ref } from 'vue'

type Theme = 'dark' | 'light' | 'system'

interface ThemeState {
  theme: Ref<Theme>
  setTheme: (t: Theme) => void
}

const ThemeSymbol = Symbol('theme')

export function provideTheme(defaultTheme: Theme = 'system', storageKey = 'spoolsense-theme') {
  const stored = localStorage.getItem(storageKey) as Theme | null
  const theme = ref<Theme>(stored || defaultTheme)

  function applyTheme(t: Theme) {
    const root = document.documentElement
    root.classList.remove('light', 'dark')
    if (t === 'system') {
      const sys = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
      root.classList.add(sys)
    } else {
      root.classList.add(t)
    }
  }

  watch(theme, (val) => {
    localStorage.setItem(storageKey, val)
    applyTheme(val)
  }, { immediate: true })

  const state: ThemeState = {
    theme,
    setTheme: (t: Theme) => { theme.value = t },
  }

  provide(ThemeSymbol, state)
  return state
}

export function useTheme(): ThemeState {
  const state = inject<ThemeState>(ThemeSymbol)
  if (!state) throw new Error('useTheme must be used within a component that called provideTheme')
  return state
}
