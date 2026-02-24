/**
 * Design System Tokens
 *
 * Centralized spacing, padding, and responsive grid constants
 * for consistent UI across the application.
 */

export const spacing = {
  formContainer: 'p-6',
  cardHeader: 'p-6 space-y-1.5',
  cardContent: 'p-6 pt-0',
  cardFooter: 'p-6 pt-4',
  alert: 'p-4',
  fieldGroup: 'space-y-4',
  gridGap: 'gap-4',
} as const

export const responsive = {
  gridSingle: 'grid grid-cols-1 gap-4',
  gridDouble: 'grid grid-cols-1 sm:grid-cols-2 gap-4',
  gridTriple: 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4',
  gridQuad: 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4',
} as const

export const touchTargets = {
  minHeight: 'h-10', // 40px minimum for touch accessibility
  iconButton: 'h-10 w-10',
} as const
