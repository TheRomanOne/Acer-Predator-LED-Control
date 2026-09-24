import { describe, expect, it } from 'vitest'

import { colorToHex, hexToColor } from './color'

describe('colour conversion', () => {
  it('round-trips through hex', () => {
    expect(colorToHex({ r: 255, g: 8, b: 0 })).toBe('#ff0800')
    expect(hexToColor('#ff0800')).toEqual({ r: 255, g: 8, b: 0 })
  })
})
