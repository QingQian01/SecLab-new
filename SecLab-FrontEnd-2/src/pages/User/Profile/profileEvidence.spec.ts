import { describe, expect, it } from 'vitest'
import { hasProfileLearningEvidence } from './profileEvidence'

describe('hasProfileLearningEvidence', () => {
  it('rejects an empty snapshot even if legacy scores are non-zero', () => {
    expect(hasProfileLearningEvidence({
      snapshot_id: 'profile-empty',
      overall_score: 9,
      ai_collaboration_score: 60,
      profile_summary_json: {
        evidence: {
          eventCount: 0,
          aiInteractionCount: 0,
          aiAskCount: 0,
          questionSubmitCount: 0,
          flagSubmitCount: 0,
          labStartCount: 0,
          activeDayCount: 0,
        },
      },
    })).toBe(false)
  })

  it('accepts a snapshot with a real submission', () => {
    expect(hasProfileLearningEvidence({
      snapshot_id: 'profile-with-answer',
      profile_summary_json: {
        evidence: { questionSubmitCount: 1 },
      },
    })).toBe(true)
  })
})
