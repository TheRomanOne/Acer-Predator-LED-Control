import { useReducer, useState } from 'react'

import { api } from './api/client'
import type { Color, Pattern } from './api/types'
import { EffectEditor } from './components/EffectEditor'
import { ColorField } from './components/fields'
import { LayerList } from './components/LayerList'
import { PatternLibrary } from './components/PatternLibrary'
import { ZoneStatusBar } from './components/ZoneStatusBar'
import { ZoneView } from './components/ZoneView'
import { EFFECT_LABELS } from './editor/effects'
import { editorReducer, initialEditorState } from './editor/reducer'
import {
  useDebouncedEffect,
  useDevices,
  useFrames,
  usePatterns,
  usePlayback,
  useStatus,
} from './hooks'

const PREVIEW_DEBOUNCE_MS = 120

export default function App() {
  const devices = useDevices()
  const [patterns, refreshPatterns] = usePatterns()
  const [playback, setPlayback] = usePlayback()
  const status = useStatus()
  const [editor, dispatch] = useReducer(editorReducer, undefined, initialEditorState)
  const [livePreview, setLivePreview] = useState(true)
  const [brush, setBrush] = useState<Color>({ r: 255, g: 255, b: 255 })
  const [inspected, setInspected] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const playing = playback.pattern_id !== null || playback.preview
  const frame = useFrames(playing)

  const run = (work: Promise<unknown>) =>
    work.then(
      () => setError(null),
      (e: Error) => setError(e.message),
    )

  useDebouncedEffect(editor.draft, PREVIEW_DEBOUNCE_MS, (draft) => {
    if (livePreview) run(api.preview(draft).then(setPlayback))
  })

  const layerIndex = editor.selectedLayer
  const selectedLayer = layerIndex === null ? null : editor.draft.layers[layerIndex]
  const paintLayer = selectedLayer?.effect.type === 'paint' ? selectedLayer : null
  const paintedLamps = new Set(
    paintLayer?.effect.type === 'paint' ? Object.keys(paintLayer.effect.colors).map(Number) : [],
  )
  // The lamp map shows the paint target while painting, otherwise whatever zone was clicked.
  const mapDeviceId = paintLayer ? (paintLayer.devices?.[0] ?? inspected ?? devices[0]?.id) : inspected
  const mapDevice = devices.find((d) => d.id === mapDeviceId) ?? null

  const save = async () => {
    const saved = editor.patternId
      ? await api.updatePattern(editor.patternId, editor.draft)
      : await api.createPattern(editor.draft)
    dispatch({ type: 'saved', pattern: saved })
    await refreshPatterns()
    return saved
  }
  const apply = (pattern: Pattern) => run(api.apply(pattern.id).then(setPlayback))

  const activeName = patterns.find((p) => p.id === playback.pattern_id)?.name
  const playbackLabel = playback.preview ? 'Preview' : activeName ? `Playing ${activeName}` : 'Idle'

  return (
    <div className="app">
      <header className="toolbar">
        <h1>LED Studio</h1>
        <input
          className="pattern-name"
          aria-label="Pattern name"
          value={editor.draft.name}
          onChange={(e) => dispatch({ type: 'setName', name: e.target.value })}
        />
        <label className="field inline">
          <span>Brightness</span>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={editor.draft.brightness}
            onChange={(e) => dispatch({ type: 'setBrightness', brightness: Number(e.target.value) })}
          />
        </label>
        <label className="checkbox">
          <input
            type="checkbox"
            checked={livePreview}
            onChange={(e) => setLivePreview(e.target.checked)}
          />
          Live
        </label>
        <span className="spacer" />
        <span className={`playback ${status ? (playing ? 'on' : '') : 'bad'}`}>
          <span className="dot" />
          {status ? playbackLabel : 'Backend offline'}
          {status && playing && <span className="mono muted"> {status.fps} fps</span>}
        </span>
        <button type="button" onClick={() => run(save())}>
          Save
        </button>
        <button type="button" className="primary" onClick={() => run(save().then(apply))}>
          Apply
        </button>
        <button type="button" onClick={() => run(api.stop().then(setPlayback))}>
          Stop
        </button>
      </header>

      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}

      <div className="workspace">
        <PatternLibrary
          patterns={patterns}
          activeId={playback.pattern_id}
          editingId={editor.patternId}
          onNew={() => dispatch({ type: 'new' })}
          onOpen={(pattern) => dispatch({ type: 'load', pattern })}
          onApply={apply}
          onDelete={(pattern) => {
            if (!confirm(`Delete "${pattern.name}"?`)) return
            run(
              api
                .deletePattern(pattern.id)
                .then(refreshPatterns)
                .then(api.getPlayback)
                .then(setPlayback),
            )
            if (editor.patternId === pattern.id) dispatch({ type: 'new' })
          }}
        />

        <main className="editor">
          <LayerList
            layers={editor.draft.layers}
            selected={layerIndex}
            devices={devices}
            dispatch={dispatch}
          />
          {selectedLayer && layerIndex !== null && (
            <section className="effect">
              <h2>{EFFECT_LABELS[selectedLayer.effect.type]}</h2>
              {paintLayer && <ColorField label="Brush" value={brush} onChange={setBrush} />}
              <EffectEditor
                effect={selectedLayer.effect}
                onChange={(effect) =>
                  dispatch({ type: 'updateLayer', index: layerIndex, layer: { effect } })
                }
              />
            </section>
          )}
          {mapDevice && (
            <section className="lamp-map">
              <ZoneView
                device={mapDevice}
                colors={frame?.[mapDevice.id] ?? null}
                selected={paintLayer?.devices?.[0] === mapDevice.id ? paintedLamps : new Set()}
                onLampClick={(lampId) =>
                  dispatch({
                    type: 'paintLamps',
                    deviceId: mapDevice.id,
                    lampIds: [lampId],
                    color: brush,
                  })
                }
              />
            </section>
          )}
        </main>
      </div>

      <ZoneStatusBar
        devices={devices}
        frame={frame}
        health={Object.fromEntries((status?.zones ?? []).map((z) => [z.id, z]))}
        inspected={inspected}
        onInspect={setInspected}
      />
    </div>
  )
}
