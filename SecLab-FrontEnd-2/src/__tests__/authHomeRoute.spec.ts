import { describe, expect, it } from 'vitest'
import { getHomeRouteForRole } from '../auth'

describe('getHomeRouteForRole', () => {
  it('sends students to the platform home page after login', () => {
    expect(getHomeRouteForRole('student')).toBe('/user/welcome')
  })

  it('keeps teachers on the teacher overview', () => {
    expect(getHomeRouteForRole('teacher')).toBe('/teacher/overview')
  })
})
