import { useReducer, useState } from 'react'

import { api } from './api/client'
import type { Color, Pattern } from './api/types'
import { EffectEditor } from './components/EffectEditor'
import { ColorField } from './components/fields'
import { LayerList } from './components/LayerList'
import { PatternLibrary } from './components/PatternLibrary'
import { ZoneView } from './components/ZoneView'
import { EFFECT_LABELS } from './editor/effects'
import { editorReducer, initialEditorState } from './editor/reducer'
import { useDebouncedEffect, useDevices, useFrames, usePatterns, usePlayback } from './hooks'

const PREVIEW_DEBOUNCE_MS = 120

export default function App() {
  const devices = useDevices()
  const [patterns, refreshPatterns] = usePatterns()
  const [playback, setPlayback] = usePlayback()
  const [editor, dispatch] = useReducer(editorReducer, undefined, initialEditorState)
  const [livePreview, setLivePreview] = useState(true)
  const [brush, setBrush] = useState<Color>({ r: 255, g: 255, b: 255 })
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

  const selectedLayer = editor.selectedLayer === null ? null : editor.draft.layers[editor.selectedLayer]
  const paintTarget = selectedLayer?.effect.type === 'paint' ? selectedLayer : null
  const paintedLamps = (deviceId: string) =>
    new Set(
      paintTarget?.devices?.[0] === deviceId
        ? Object.keys(paintTarget.effect.type === 'paint' ? paintTarget.effect.colors : {}).map(Number)
        : [],
    )

  const save = async () => {
    const saved = editor.patternId
      ? await api.updatePattern(editor.patternId, editor.draft)
      : await api.createPattern(editor.draft)
    dispatch({ type: 'saved', pattern: saved })
    await refreshPatterns()
    return saved
  }

  const apply = (pattern: Pattern) => run(api.apply(pattern.id).then(setPlayback))

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
          <input type="checkbox" checked={livePreview} onChange={(e) => setLivePreview(e.target.checked)} />
          Live preview
        </label>
        <span className="spacer" />
        <button type="button" onClick={() => run(save())}>
          Save
        </button>
        <button type="button" className="primary" onClick={() => run(save().then(apply))}>
          Save &amp; apply
        </button>
        <button type="button" onClick={() => run(api.stop().then(setPlayback))}>
          Stop (firmware)
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
            run(api.deletePattern(pattern.id).then(refreshPatterns).then(api.getPlayback).then(setPlayback))
            if (editor.patternId === pattern.id) dispatch({ type: 'new' })
          }}
        />

        <main className="zones">
          {devices.length === 0 && <p className="hint">No LampArray devices found.</p>}
          {devices.map((device) => (
            <ZoneView
              key={device.id}
              device={device}
              colors={frame?.[device.id] ?? null}
              selected={paintedLamps(device.id)}
              onLampClick={(lampId) =>
                dispatch({ type: 'paintLamps', deviceId: device.id, lampIds: [lampId], color: brush })
              }
            />
          ))}
          {paintTarget && (
            <p className="hint">
              Painting{' '}
              <strong>
                {devices.find((d) => d.id === paintTarget.devices?.[0])?.name ?? 'any zone'}
              </strong>
              : click lamps to colour them with the brush.
            </p>
          )}
        </main>

        <aside className="inspector">
          <LayerList
            layers={editor.draft.layers}
            selected={editor.selectedLayer}
            devices={devices}
            dispatch={dispatch}
          />
          {selectedLayer && editor.selectedLayer !== null && (
            <section className="effect">
              <h2>{EFFECT_LABELS[selectedLayer.effect.type]}</h2>
              {paintTarget && <ColorField label="Brush" value={brush} onChange={setBrush} />}
              <EffectEditor
                effect={selectedLayer.effect}
                onChange={(effect) =>
                  dispatch({ type: 'updateLayer', index: editor.selectedLayer!, layer: { effect } })
                }
              />
            </section>
          )}
        </aside>
      </div>
    </div>
  )
}
