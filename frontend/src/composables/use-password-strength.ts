import { computed, type Ref } from 'vue'

export interface PasswordRequirements {
  minLength: boolean
  hasUpper: boolean
  hasLower: boolean
  hasNumber: boolean
}

export interface PasswordStrength {
  level: 'weak' | 'fair' | 'good' | 'strong'
  percent: number
  requirements: PasswordRequirements
}

export function usePasswordStrength(password: Ref<string>) {
  const strength = computed<PasswordStrength>(() => {
    const p = password.value || ''

    const requirements: PasswordRequirements = {
      minLength: p.length >= 8,
      hasUpper:  /[A-Z]/.test(p),
      hasLower:  /[a-z]/.test(p),
      hasNumber: /[0-9]/.test(p),
    }

    const metCount = Object.values(requirements).filter(Boolean).length

    // Base score = number of requirements met (0–4)
    // Bonus points for length beyond the minimum
    let score = metCount
    if (p.length >= 12) score++
    if (p.length >= 16) score++
    score = Math.min(score, 4)

    const levels = ['weak', 'weak', 'fair', 'good', 'strong'] as const
    const level  = levels[score] ?? 'weak'
    const percent = Math.round((score / 4) * 100)

    return { level, percent, requirements }
  })

  return { strength }
}
