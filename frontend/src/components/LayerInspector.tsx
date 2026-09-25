import type { Device, Layer } from '../api/types'
import { EFFECT_LABELS } from '../editor/effects'
import type { EditorAction } from '../editor/reducer'
import { EffectEditor } from './EffectEditor'
import { SliderField } from './fields'

interface Props {
  layer: Layer
  index: number
  devices: Device[]
  dispatch: (action: EditorAction) => void
}

/** Settings of the selected layer: blending, target zones and the effect's own parameters. */
export function LayerInspector({ layer, index, devices, dispatch }: Props) {
  const update = (patch: Partial<Layer>) => dispatch({ type: 'updateLayer', index, layer: patch })

  const toggleZone = (deviceId: string, targeted: boolean) => {
    const current = layer.devices ?? devices.map((d) => d.id)
    const next = targeted ? [...current, deviceId] : current.filter((id) => id !== deviceId)
    update({ devices: next.length === devices.length ? null : next })
  }

  return (
    <section className="inspector">
      <header className="panel-header">
        <h2>{EFFECT_LABELS[layer.effect.type]}</h2>
      </header>
      <div className="fields">
        <SliderField
          label="Opacity"
          value={layer.opacity}
          min={0}
          max={1}
          onChange={(opacity) => update({ opacity })}
        />
        <div className="field span" role="group" aria-label="Zones">
          <span>Zones</span>
          <div className="chips">
            {devices.map((device) => {
              const targeted = layer.devices === null || layer.devices.includes(device.id)
              return (
                <button
                  key={device.id}
                  type="button"
                  className="chip"
                  aria-pressed={targeted}
                  onClick={() => toggleZone(device.id, !targeted)}
                >
                  {device.name}
                </button>
              )
            })}
          </div>
        </div>
      </div>
      <hr />
      <div className="fields">
        <EffectEditor effect={layer.effect} onChange={(effect) => update({ effect })} />
      </div>
    </section>
  )
}
