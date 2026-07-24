import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'

describe('module question tracking', () => {
  it('links every experiment answer to the active lab session', () => {
    const source = readFileSync(new URL('../index.vue', import.meta.url), 'utf8')

    expect(source).toContain(
      'lab_session_id: labSessionId.value || getLabSessionId() || null',
    )
  })
})
