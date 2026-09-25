import type { Color } from './api/types'

export function colorToHex({ r, g, b }: Color): string {
  return '#' + [r, g, b].map((c) => c.toString(16).padStart(2, '0')).join('')
}

export function hexToColor(hex: string): Color {
  const value = parseInt(hex.replace('#', ''), 16)
  return { r: (value >> 16) & 0xff, g: (value >> 8) & 0xff, b: value & 0xff }
}

export function rgbCss([r, g, b]: [number, number, number]): string {
  return `rgb(${r}, ${g}, ${b})`
}

// Relative-luminance threshold (sRGB, WCAG weights) above which dark text reads better.
const LIGHT_LUMINANCE = 0.45

/** Which label tone stays legible on a lamp of the given colour. */
export function labelColorOn([r, g, b]: [number, number, number]): 'dark' | 'light' {
  const luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
  return luminance > LIGHT_LUMINANCE ? 'dark' : 'light'
}
