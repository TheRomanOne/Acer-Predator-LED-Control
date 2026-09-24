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
