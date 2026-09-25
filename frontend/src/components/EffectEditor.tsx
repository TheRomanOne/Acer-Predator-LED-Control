import type { Color, Effect } from '../api/types'
import { ColorField, NumberField, SliderField } from './fields'
import { CloseIcon, PlusIcon } from './icons'

interface Props {
  effect: Effect
  onChange: (effect: Effect) => void
}

const ANGLE = { label: 'Angle (°)', min: 0, max: 360, step: 5 }

function RemoveButton({ label, disabled, onClick }: { label: string; disabled: boolean; onClick: () => void }) {
  return (
    <button type="button" className="icon" disabled={disabled} onClick={onClick} aria-label={label}>
      <CloseIcon />
    </button>
  )
}

function AddButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button type="button" className="small ghost" onClick={onClick}>
      <PlusIcon /> {label}
    </button>
  )
}

function ColorList({
  colors,
  onChange,
  min = 1,
}: {
  colors: Color[]
  onChange: (colors: Color[]) => void
  min?: number
}) {
  return (
    <div className="list span">
      {colors.map((color, i) => (
        <div key={i} className="list-row">
          <ColorField
            label={`Colour ${i + 1}`}
            value={color}
            onChange={(c) => onChange(colors.map((x, j) => (j === i ? c : x)))}
          />
          <RemoveButton
            label={`Remove colour ${i + 1}`}
            disabled={colors.length <= min}
            onClick={() => onChange(colors.filter((_, j) => j !== i))}
          />
        </div>
      ))}
      <AddButton label="Colour" onClick={() => onChange([...colors, colors[colors.length - 1]])} />
    </div>
  )
}

export function EffectEditor({ effect, onChange }: Props) {
  const set = <E extends Effect>(patch: Partial<E>) => onChange({ ...effect, ...patch } as Effect)

  switch (effect.type) {
    case 'solid':
      return <ColorField label="Colour" value={effect.color} onChange={(color) => set({ color })} />

    case 'gradient':
      return (
        <>
          <div className="list span">
            {effect.stops.map((stop, i) => (
              <div key={i} className="list-row">
                <ColorField
                  label={`Stop ${i + 1}`}
                  value={stop.color}
                  onChange={(color) =>
                    set({ stops: effect.stops.map((s, j) => (j === i ? { ...s, color } : s)) })
                  }
                />
                <SliderField
                  label="Position"
                  value={stop.position}
                  min={0}
                  max={1}
                  onChange={(position) =>
                    set({ stops: effect.stops.map((s, j) => (j === i ? { ...s, position } : s)) })
                  }
                />
                <RemoveButton
                  label={`Remove stop ${i + 1}`}
                  disabled={effect.stops.length <= 2}
                  onClick={() => set({ stops: effect.stops.filter((_, j) => j !== i) })}
                />
              </div>
            ))}
            <AddButton
              label="Stop"
              onClick={() =>
                set({ stops: [...effect.stops, { position: 1, color: { r: 255, g: 255, b: 255 } }] })
              }
            />
          </div>
          <NumberField {...ANGLE} value={effect.angle_deg} onChange={(angle_deg) => set({ angle_deg })} />
        </>
      )

    case 'wave':
      return (
        <>
          <ColorList colors={effect.colors} onChange={(colors) => set({ colors })} />
          <NumberField label="Speed (cycles/s)" value={effect.speed} step={0.1} onChange={(speed) => set({ speed })} />
          <NumberField
            label="Wavelength (span)"
            value={effect.wavelength}
            min={0.05}
            step={0.05}
            onChange={(wavelength) => set({ wavelength })}
          />
          <NumberField {...ANGLE} value={effect.angle_deg} onChange={(angle_deg) => set({ angle_deg })} />
        </>
      )

    case 'breathing':
      return (
        <>
          <ColorField label="Colour" value={effect.color} onChange={(color) => set({ color })} />
          <NumberField label="Period (s)" value={effect.period_s} min={0.1} onChange={(period_s) => set({ period_s })} />
          <SliderField
            label="Minimum brightness"
            value={effect.min_brightness}
            min={0}
            max={1}
            onChange={(min_brightness) => set({ min_brightness })}
          />
        </>
      )

    case 'rainbow':
      return (
        <>
          <NumberField label="Speed (cycles/s)" value={effect.speed} step={0.05} onChange={(speed) => set({ speed })} />
          <NumberField label="Scale (cycles across)" value={effect.scale} step={0.25} onChange={(scale) => set({ scale })} />
          <NumberField {...ANGLE} value={effect.angle_deg} onChange={(angle_deg) => set({ angle_deg })} />
        </>
      )

    case 'paint':
      return <p className="hint span">Pick a zone in the preview and click its lamps to paint them.</p>

    case 'ripple':
      return (
        <>
          <ColorField label="Colour" value={effect.color} onChange={(color) => set({ color })} />
          <NumberField label="Period (s)" value={effect.period_s} min={0.1} onChange={(period_s) => set({ period_s })} />
          <SliderField label="Origin X" value={effect.origin_x} min={0} max={1} onChange={(origin_x) => set({ origin_x })} />
          <SliderField label="Origin Y" value={effect.origin_y} min={0} max={1} onChange={(origin_y) => set({ origin_y })} />
          <SliderField label="Ring width" value={effect.width} min={0.02} max={1} onChange={(width) => set({ width })} />
        </>
      )

    case 'keyframes':
      return (
        <>
          <div className="list span">
            {effect.frames.map((frame, i) => (
              <div key={i} className="list-row">
                <NumberField
                  label="Time (s)"
                  value={frame.time_s}
                  min={0}
                  onChange={(time_s) =>
                    set({ frames: effect.frames.map((f, j) => (j === i ? { ...f, time_s } : f)) })
                  }
                />
                <ColorField
                  label="Colour"
                  value={frame.color}
                  onChange={(color) =>
                    set({ frames: effect.frames.map((f, j) => (j === i ? { ...f, color } : f)) })
                  }
                />
                <RemoveButton
                  label={`Remove frame ${i + 1}`}
                  disabled={effect.frames.length <= 1}
                  onClick={() => set({ frames: effect.frames.filter((_, j) => j !== i) })}
                />
              </div>
            ))}
            <AddButton
              label="Frame"
              onClick={() => {
                const last = effect.frames[effect.frames.length - 1]
                set({ frames: [...effect.frames, { time_s: last.time_s + 1, color: last.color }] })
              }}
            />
          </div>
          <label className="checkbox span">
            <input
              type="checkbox"
              checked={effect.interpolate}
              onChange={(e) => set({ interpolate: e.target.checked })}
            />
            Fade between frames
          </label>
        </>
      )
  }
}
