import type { ProfileLatestResponse } from '../../../api'

function hasPositiveCount(value: unknown): boolean {
  if (!value || typeof value !== 'object') return false
  return Object.values(value as Record<string, unknown>).some((count) => Number(count || 0) > 0)
}

export function hasProfileLearningEvidence(profile: ProfileLatestResponse | null): boolean {
  if (!profile) return false

  const summary = profile.profile_summary_json
  if (summary && typeof summary === 'object') {
    if ('evidence' in summary) {
      return hasPositiveCount(summary.evidence)
    }
    if ('raw_stats' in summary) {
      return hasPositiveCount(summary.raw_stats)
    }
  }

  return Boolean(
    profile.source_range_start ||
    profile.source_range_end ||
    Number(profile.overall_score || 0) > 0
  )
}
