// Mirrors backend/led_studio/patterns/model.py and api/schemas.py. Keep in sync by hand.

export interface Color {
  r: number
  g: number
  b: number
}

export interface Lamp {
  id: number
  x: number
  y: number
  /** HID keyboard usage bound to this lamp; 0 when not a key. */
  key: number
}

export interface Device {
  id: string
  name: string
  kind: string
  lamp_count: number
  width_mm: number
  height_mm: number
  lamps: Lamp[]
}

export interface GradientStop {
  position: number
  color: Color
}

export interface Keyframe {
  time_s: number
  color: Color
}

export type Effect =
  | { type: 'solid'; color: Color }
  | { type: 'gradient'; stops: GradientStop[]; angle_deg: number }
  | { type: 'wave'; colors: Color[]; speed: number; wavelength: number; angle_deg: number }
  | { type: 'breathing'; color: Color; period_s: number; min_brightness: number }
  | { type: 'rainbow'; speed: number; scale: number; angle_deg: number }
  | { type: 'paint'; colors: Record<number, Color> }
  | {
      type: 'ripple'
      color: Color
      origin_x: number
      origin_y: number
      period_s: number
      width: number
    }
  | { type: 'keyframes'; frames: Keyframe[]; interpolate: boolean }

export type EffectType = Effect['type']

export interface Layer {
  effect: Effect
  opacity: number
  /** null targets every device. */
  devices: string[] | null
  enabled: boolean
}

export interface PatternBody {
  name: string
  layers: Layer[]
  brightness: number
}

export interface Pattern extends PatternBody {
  id: string
}

export interface Playback {
  pattern_id: string | null
  preview: boolean
}

export interface ZoneHealth {
  id: string
  frames: number
  errors: number
  last_error: string | null
}

export interface Status {
  playback: Playback
  fps: number
  zones: ZoneHealth[]
}

/** Device id -> [r, g, b] per lamp, indexed by lamp id. */
export type Frame = Record<string, Array<[number, number, number]>>
