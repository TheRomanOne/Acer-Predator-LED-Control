import { describe, expect, it } from 'vitest'

import { keyLabel } from './keys'

describe('keyLabel', () => {
  it('maps HID keyboard usages to short labels', () => {
    expect(keyLabel(0x04)).toBe('A')
    expect(keyLabel(0x1e)).toBe('1')
    expect(keyLabel(0x29)).toBe('Esc')
    expect(keyLabel(0x3a)).toBe('F1')
    expect(keyLabel(0x2c)).toBe('Space')
    expect(keyLabel(0x58)).toBe('Enter')
  })

  it('returns an empty label for unbound lamps and unknown usages', () => {
    expect(keyLabel(0)).toBe('')
    expect(keyLabel(0xffff)).toBe('')
  })
})
