import type { Effect, EffectType } from '../api/types'

const WHITE = { r: 255, g: 255, b: 255 }
const CYAN = { r: 0, g: 200, b: 255 }
const MAGENTA = { r: 255, g: 0, b: 160 }

export const EFFECT_LABELS: Record<EffectType, string> = {
  solid: 'Solid colour',
  gradient: 'Gradient',
  wave: 'Wave',
  breathing: 'Breathing',
  rainbow: 'Rainbow',
  paint: 'Paint (per lamp)',
  ripple: 'Ripple',
  keyframes: 'Keyframes',
}

export const EFFECT_TYPES = Object.keys(EFFECT_LABELS) as EffectType[]

export function defaultEffect(type: EffectType): Effect {
  switch (type) {
    case 'solid':
      return { type, color: CYAN }
    case 'gradient':
      return {
        type,
        stops: [
          { position: 0, color: CYAN },
          { position: 1, color: MAGENTA },
        ],
        angle_deg: 0,
      }
    case 'wave':
      return { type, colors: [CYAN, MAGENTA], speed: 0.5, wavelength: 1, angle_deg: 0 }
    case 'breathing':
      return { type, color: WHITE, period_s: 3, min_brightness: 0 }
    case 'rainbow':
      return { type, speed: 0.2, scale: 1, angle_deg: 0 }
    case 'paint':
      return { type, colors: {} }
    case 'ripple':
      return { type, color: WHITE, origin_x: 0.5, origin_y: 0.5, period_s: 2, width: 0.15 }
    case 'keyframes':
      return {
        type,
        frames: [
          { time_s: 0, color: CYAN },
          { time_s: 2, color: MAGENTA },
          { time_s: 4, color: CYAN },
        ],
        interpolate: true,
      }
  }
}
