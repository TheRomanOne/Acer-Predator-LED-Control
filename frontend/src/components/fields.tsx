import type { Color } from '../api/types'
import { colorToHex, hexToColor } from '../color'

interface NumberFieldProps {
  label: string
  value: number
  onChange: (value: number) => void
  min?: number
  max?: number
  step?: number
}

export function NumberField({ label, value, onChange, min, max, step = 0.1 }: NumberFieldProps) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        type="number"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </label>
  )
}

interface SliderFieldProps extends NumberFieldProps {
  min: number
  max: number
}

export function SliderField({ label, value, onChange, min, max, step = 0.01 }: SliderFieldProps) {
  return (
    <label className="field">
      <span>
        {label} <em>{value.toFixed(2)}</em>
      </span>
      <input
        type="range"
        value={value}
        min={min}
        max={max}
        step={step}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </label>
  )
}

interface ColorFieldProps {
  label: string
  value: Color
  onChange: (value: Color) => void
}

export function ColorField({ label, value, onChange }: ColorFieldProps) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        type="color"
        value={colorToHex(value)}
        onChange={(e) => onChange(hexToColor(e.target.value))}
      />
    </label>
  )
}
