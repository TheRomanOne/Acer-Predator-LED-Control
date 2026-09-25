import { useReducer, useState } from 'react'

import { api } from './api/client'
import type { Color, Pattern } from './api/types'
import { CloseIcon, PlayIcon, StopIcon } from './components/icons'
import { LayerInspector } from './components/LayerInspector'
import { LayerList } from './components/LayerList'
import { PaintToolbar } from './components/PaintToolbar'
import { PatternLibrary } from './components/PatternLibrary'
import { ZoneTabs } from './components/ZoneTabs'
import { ZoneView } from './components/ZoneView'
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
  const paintedDevice = paintLayer?.devices?.[0] ?? null
  const paintedLamps = new Set(
    paintLayer?.effect.type === 'paint' ? Object.keys(paintLayer.effect.colors).map(Number) : [],
  )
  const zoneId = editor.zone ?? devices[0]?.id ?? null
  const zone = devices.find((d) => d.id === zoneId) ?? null
  const deviceName = (id: string | null) => devices.find((d) => d.id === id)?.name ?? null

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
  const playbackLabel = playback.preview ? 'Previewing' : activeName ? `Playing ${activeName}` : 'Idle'
  const statusTone = !status ? 'bad' : playing ? 'on' : 'off'

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          LED Studio
        </div>
        <input
          className="pattern-name"
          aria-label="Pattern name"
          placeholder="Pattern name"
          value={editor.draft.name}
          onChange={(e) => dispatch({ type: 'setName', name: e.target.value })}
        />
        <label className="brightness">
          <span>Brightness</span>
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={editor.draft.brightness}
            onChange={(e) => dispatch({ type: 'setBrightness', brightness: Number(e.target.value) })}
          />
          <span className="mono">{Math.round(editor.draft.brightness * 100)}%</span>
        </label>
        <span className="spacer" />
        <span className={`status-pill ${statusTone}`} role="status">
          <span className="dot" />
          {status ? playbackLabel : 'Backend offline'}
          {status && playing && <span className="mono muted">{status.fps} fps</span>}
        </span>
        <div className="actions">
          <button type="button" onClick={() => run(save())}>
            Save
          </button>
          <button type="button" className="primary" onClick={() => run(save().then(apply))}>
            <PlayIcon /> Apply
          </button>
          <button type="button" className="ghost" onClick={() => run(api.stop().then(setPlayback))}>
            <StopIcon /> Stop
          </button>
        </div>
      </header>

      {error && (
        <div role="alert" className="banner">
          <span>{error}</span>
          <button type="button" className="icon" aria-label="Dismiss" onClick={() => setError(null)}>
            <CloseIcon />
          </button>
        </div>
      )}

      <div className="workspace">
        <aside className="panel">
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
        </aside>

        <section className="panel editor">
          <LayerList
            layers={editor.draft.layers}
            selected={layerIndex}
            devices={devices}
            dispatch={dispatch}
          />
          {selectedLayer && layerIndex !== null ? (
            <LayerInspector layer={selectedLayer} index={layerIndex} devices={devices} dispatch={dispatch} />
          ) : (
            <p className="empty">Select a layer to edit its effect.</p>
          )}
        </section>

        <main className="panel preview">
          <header className="panel-header">
            <h2>Preview</h2>
            <label className="switch">
              <input
                type="checkbox"
                checked={livePreview}
                onChange={(e) => setLivePreview(e.target.checked)}
              />
              <span className="switch-track" aria-hidden="true" />
              Live on hardware
            </label>
          </header>
          <ZoneTabs
            devices={devices}
            frame={frame}
            health={Object.fromEntries((status?.zones ?? []).map((z) => [z.id, z]))}
            selected={zoneId}
            onSelect={(deviceId) => dispatch({ type: 'selectZone', deviceId })}
          />
          <div className="stage">
            {zone ? (
              <ZoneView
                device={zone}
                colors={frame?.[zone.id] ?? null}
                selected={paintedDevice === zone.id ? paintedLamps : new Set()}
                onLampClick={(lampId) =>
                  dispatch({ type: 'paintLamps', deviceId: zone.id, lampIds: [lampId], color: brush })
                }
              />
            ) : (
              <p className="empty">
                {status ? 'No lighting zones were found on this machine.' : 'Waiting for the backend…'}
              </p>
            )}
          </div>
          {paintLayer && layerIndex !== null && zone && (
            <PaintToolbar
              brush={brush}
              onBrushChange={setBrush}
              paintedCount={paintedLamps.size}
              onClear={() =>
                dispatch({
                  type: 'updateLayer',
                  index: layerIndex,
                  layer: { effect: { type: 'paint', colors: {} } },
                })
              }
              boundZone={deviceName(paintedDevice)}
              previewZone={zone.name}
            />
          )}
        </main>
      </div>
    </div>
  )
}
