import type { Device, EffectType, Layer } from '../api/types'
import { EFFECT_LABELS, EFFECT_TYPES } from '../editor/effects'
import type { EditorAction } from '../editor/reducer'

interface Props {
  layers: Layer[]
  selected: number | null
  devices: Device[]
  dispatch: (action: EditorAction) => void
}

export function LayerList({ layers, selected, devices, dispatch }: Props) {
  return (
    <section className="layers">
      <header className="row">
        <h2>Layers</h2>
        <select
          value=""
          aria-label="Add layer"
          onChange={(e) => {
            if (e.target.value) dispatch({ type: 'addLayer', effectType: e.target.value as EffectType })
          }}
        >
          <option value="">+ Add layer…</option>
          {EFFECT_TYPES.map((type) => (
            <option key={type} value={type}>
              {EFFECT_LABELS[type]}
            </option>
          ))}
        </select>
      </header>
      {layers.length === 0 && <p className="hint">No layers yet. Add one to start painting light.</p>}
      <ol>
        {/* Rendered top-most first, like a paint program: the last layer wins. */}
        {[...layers.keys()].reverse().map((index) => {
          const layer = layers[index]
          return (
            <li
              key={index}
              className={index === selected ? 'selected' : undefined}
              onClick={() => dispatch({ type: 'selectLayer', index })}
            >
              <div className="row">
                <input
                  type="checkbox"
                  checked={layer.enabled}
                  aria-label="Enabled"
                  onClick={(e) => e.stopPropagation()}
                  onChange={(e) =>
                    dispatch({ type: 'updateLayer', index, layer: { enabled: e.target.checked } })
                  }
                />
                <strong>{EFFECT_LABELS[layer.effect.type]}</strong>
                <span className="spacer" />
                <button
                  type="button"
                  aria-label="Move up"
                  onClick={(e) => {
                    e.stopPropagation()
                    dispatch({ type: 'moveLayer', index, direction: 1 })
                  }}
                >
                  ↑
                </button>
                <button
                  type="button"
                  aria-label="Move down"
                  onClick={(e) => {
                    e.stopPropagation()
                    dispatch({ type: 'moveLayer', index, direction: -1 })
                  }}
                >
                  ↓
                </button>
                <button
                  type="button"
                  aria-label="Remove layer"
                  onClick={(e) => {
                    e.stopPropagation()
                    dispatch({ type: 'removeLayer', index })
                  }}
                >
                  ×
                </button>
              </div>
              {index === selected && (
                <div className="layer-settings" onClick={(e) => e.stopPropagation()}>
                  <label className="field">
                    <span>
                      Opacity <em>{layer.opacity.toFixed(2)}</em>
                    </span>
                    <input
                      type="range"
                      min={0}
                      max={1}
                      step={0.01}
                      value={layer.opacity}
                      onChange={(e) =>
                        dispatch({
                          type: 'updateLayer',
                          index,
                          layer: { opacity: Number(e.target.value) },
                        })
                      }
                    />
                  </label>
                  <fieldset className="devices">
                    <legend>Zones</legend>
                    {devices.map((device) => {
                      const targeted = layer.devices === null || layer.devices.includes(device.id)
                      return (
                        <label key={device.id} className="checkbox">
                          <input
                            type="checkbox"
                            checked={targeted}
                            onChange={(e) => {
                              const current = layer.devices ?? devices.map((d) => d.id)
                              const next = e.target.checked
                                ? [...current, device.id]
                                : current.filter((id) => id !== device.id)
                              const all = next.length === devices.length
                              dispatch({ type: 'updateLayer', index, layer: { devices: all ? null : next } })
                            }}
                          />
                          {device.name}
                        </label>
                      )
                    })}
                  </fieldset>
                </div>
              )}
            </li>
          )
        })}
      </ol>
    </section>
  )
}
