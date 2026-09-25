import type { Color, EffectType, Layer, Pattern, PatternBody } from '../api/types'
import { defaultEffect } from './effects'

export interface EditorState {
  draft: PatternBody
  /** id of the saved pattern this draft came from; null for a new pattern. */
  patternId: string | null
  selectedLayer: number | null
  /** Device shown in the preview map; null until the user picks one (the app shows the first). */
  zone: string | null
}

export type EditorAction =
  | { type: 'new' }
  | { type: 'load'; pattern: Pattern }
  | { type: 'saved'; pattern: Pattern }
  | { type: 'setName'; name: string }
  | { type: 'setBrightness'; brightness: number }
  | { type: 'selectLayer'; index: number | null }
  | { type: 'selectZone'; deviceId: string }
  | { type: 'addLayer'; effectType: EffectType }
  | { type: 'updateLayer'; index: number; layer: Partial<Layer> }
  | { type: 'removeLayer'; index: number }
  | { type: 'moveLayer'; index: number; direction: -1 | 1 }
  | { type: 'paintLamps'; deviceId: string; lampIds: number[]; color: Color }

export function initialEditorState(): EditorState {
  return {
    draft: { name: 'Untitled', layers: [], brightness: 1 },
    patternId: null,
    selectedLayer: null,
    zone: null,
  }
}

function withDraft(state: EditorState, draft: Partial<PatternBody>): EditorState {
  return { ...state, draft: { ...state.draft, ...draft } }
}

function replaceLayer(state: EditorState, index: number, layer: Layer): EditorState {
  return withDraft(state, {
    layers: state.draft.layers.map((existing, i) => (i === index ? layer : existing)),
  })
}

/** Select a layer; a paint layer bound to a device brings that device into the preview. */
function selectLayer(state: EditorState, index: number | null): EditorState {
  const layer = index === null ? undefined : state.draft.layers[index]
  const paintedDevice = layer?.effect.type === 'paint' ? layer.devices?.[0] : undefined
  return { ...state, selectedLayer: index, zone: paintedDevice ?? state.zone }
}

export function editorReducer(state: EditorState, action: EditorAction): EditorState {
  switch (action.type) {
    case 'new':
      return { ...initialEditorState(), zone: state.zone }
    case 'load': {
      const { id, ...draft } = action.pattern
      return selectLayer(
        { draft, patternId: id, selectedLayer: null, zone: state.zone },
        draft.layers.length ? 0 : null,
      )
    }
    case 'saved':
      return { ...state, patternId: action.pattern.id }
    case 'setName':
      return withDraft(state, { name: action.name })
    case 'setBrightness':
      return withDraft(state, { brightness: action.brightness })
    case 'selectLayer':
      return selectLayer(state, action.index)
    case 'selectZone':
      return { ...state, zone: action.deviceId }
    case 'addLayer': {
      const layer: Layer = {
        effect: defaultEffect(action.effectType),
        opacity: 1,
        devices: null,
        enabled: true,
      }
      const layers = [...state.draft.layers, layer]
      return { ...withDraft(state, { layers }), selectedLayer: layers.length - 1 }
    }
    case 'updateLayer':
      return replaceLayer(state, action.index, {
        ...state.draft.layers[action.index],
        ...action.layer,
      })
    case 'removeLayer': {
      const layers = state.draft.layers.filter((_, i) => i !== action.index)
      const selectedLayer = layers.length ? Math.min(action.index, layers.length - 1) : null
      return { ...withDraft(state, { layers }), selectedLayer }
    }
    case 'moveLayer': {
      const target = action.index + action.direction
      if (target < 0 || target >= state.draft.layers.length) return state
      const layers = [...state.draft.layers]
      ;[layers[action.index], layers[target]] = [layers[target], layers[action.index]]
      return { ...withDraft(state, { layers }), selectedLayer: target }
    }
    case 'paintLamps': {
      const index = state.selectedLayer
      if (index === null) return state
      const layer = state.draft.layers[index]
      if (layer.effect.type !== 'paint') return state
      // A paint layer is bound to one device; painting elsewhere starts a fresh canvas.
      const sameDevice = layer.devices?.[0] === action.deviceId
      const colors = { ...(sameDevice ? layer.effect.colors : {}) }
      for (const lampId of action.lampIds) colors[lampId] = action.color
      const painted = replaceLayer(state, index, {
        ...layer,
        devices: [action.deviceId],
        effect: { type: 'paint', colors },
      })
      return { ...painted, zone: action.deviceId }
    }
  }
}
