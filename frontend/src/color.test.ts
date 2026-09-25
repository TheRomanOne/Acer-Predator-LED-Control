import { describe, expect, it } from 'vitest'

import { colorToHex, hexToColor, labelColorOn } from './color'

describe('colour conversion', () => {
  it('round-trips through hex', () => {
    expect(colorToHex({ r: 255, g: 8, b: 0 })).toBe('#ff0800')
    expect(hexToColor('#ff0800')).toEqual({ r: 255, g: 8, b: 0 })
  })
})

describe('labelColorOn', () => {
  it('uses dark text on light lamps and light text on dark ones', () => {
    expect(labelColorOn([255, 255, 255])).toBe('dark')
    expect(labelColorOn([255, 230, 0])).toBe('dark')
    expect(labelColorOn([0, 0, 0])).toBe('light')
    expect(labelColorOn([120, 0, 0])).toBe('light')
  })
})
