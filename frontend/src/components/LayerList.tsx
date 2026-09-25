import type { Device, EffectType, Layer } from '../api/types'
import { EFFECT_LABELS, EFFECT_TYPES } from '../editor/effects'
import type { EditorAction } from '../editor/reducer'
import { ChevronDownIcon, ChevronUpIcon, CloseIcon } from './icons'

interface Props {
  layers: Layer[]
  selected: number | null
  devices: Device[]
  dispatch: (action: EditorAction) => void
}

function zoneSummary(layer: Layer, devices: Device[]): string {
  if (layer.devices === null) return 'All zones'
  const names = layer.devices.map((id) => devices.find((d) => d.id === id)?.name ?? id)
  return names.length === 0 ? 'No zones' : names.join(', ')
}

export function LayerList({ layers, selected, devices, dispatch }: Props) {
  const top = layers.length - 1
  return (
    <section className="layers">
      <header className="panel-header">
        <h2>Layers</h2>
        <select
          className="add-layer"
          value=""
          aria-label="Add layer"
          onChange={(e) => {
            if (e.target.value) dispatch({ type: 'addLayer', effectType: e.target.value as EffectType })
          }}
        >
          <option value="">Add layer…</option>
          {EFFECT_TYPES.map((type) => (
            <option key={type} value={type}>
              {EFFECT_LABELS[type]}
            </option>
          ))}
        </select>
      </header>
      {layers.length === 0 ? (
        <p className="empty">No layers yet. Add one to start designing.</p>
      ) : (
        <ol className="layer-list">
          {/* Rendered top-most first, like a paint program: the last layer wins. */}
          {[...layers.keys()].reverse().map((index) => {
            const layer = layers[index]
            const isSelected = index === selected
            return (
              <li
                key={index}
                className={`layer-row${isSelected ? ' selected' : ''}${layer.enabled ? '' : ' disabled'}`}
                onClick={() => dispatch({ type: 'selectLayer', index })}
              >
                <input
                  type="checkbox"
                  checked={layer.enabled}
                  aria-label="Enabled"
                  onClick={(e) => e.stopPropagation()}
                  onChange={(e) =>
                    dispatch({ type: 'updateLayer', index, layer: { enabled: e.target.checked } })
                  }
                />
                <span className="layer-title">
                  <strong>{EFFECT_LABELS[layer.effect.type]}</strong>
                  <span className="layer-zones">{zoneSummary(layer, devices)}</span>
                </span>
                <span className="layer-actions">
                  <button
                    type="button"
                    className="icon"
                    aria-label="Move up"
                    disabled={index === top}
                    onClick={(e) => {
                      e.stopPropagation()
                      dispatch({ type: 'moveLayer', index, direction: 1 })
                    }}
                  >
                    <ChevronUpIcon />
                  </button>
                  <button
                    type="button"
                    className="icon"
                    aria-label="Move down"
                    disabled={index === 0}
                    onClick={(e) => {
                      e.stopPropagation()
                      dispatch({ type: 'moveLayer', index, direction: -1 })
                    }}
                  >
                    <ChevronDownIcon />
                  </button>
                  <button
                    type="button"
                    className="icon danger"
                    aria-label="Remove layer"
                    onClick={(e) => {
                      e.stopPropagation()
                      dispatch({ type: 'removeLayer', index })
                    }}
                  >
                    <CloseIcon />
                  </button>
                </span>
              </li>
            )
          })}
        </ol>
      )}
    </section>
  )
}
