import { describe, expect, it } from 'vitest'

import type { PatternBody } from '../api/types'
import { editorReducer, initialEditorState, type EditorState } from './reducer'

const BLUE = { r: 0, g: 0, b: 255 }

function withLayers(...types: Array<'solid' | 'paint' | 'wave'>): EditorState {
  return types.reduce(
    (state, type) => editorReducer(state, { type: 'addLayer', effectType: type }),
    initialEditorState(),
  )
}

describe('editorReducer', () => {
  it('starts with an empty, unnamed draft', () => {
    const state = initialEditorState()

    expect(state.draft).toEqual<PatternBody>({ name: 'Untitled', layers: [], brightness: 1 })
    expect(state.selectedLayer).toBeNull()
    expect(state.patternId).toBeNull()
  })

  it('adds a layer with a sensible default effect and selects it', () => {
    const state = withLayers('wave')

    expect(state.draft.layers).toHaveLength(1)
    expect(state.draft.layers[0].effect.type).toBe('wave')
    expect(state.draft.layers[0].opacity).toBe(1)
    expect(state.draft.layers[0].enabled).toBe(true)
    expect(state.selectedLayer).toBe(0)
  })

  it('updates the effect of a layer without touching its siblings', () => {
    const state = withLayers('solid', 'solid')

    const next = editorReducer(state, {
      type: 'updateLayer',
      index: 1,
      layer: { effect: { type: 'solid', color: BLUE } },
    })

    expect(next.draft.layers[1].effect).toEqual({ type: 'solid', color: BLUE })
    expect(next.draft.layers[0]).toBe(state.draft.layers[0])
  })

  it('removes a layer and keeps the selection in range', () => {
    const state = withLayers('solid', 'solid')

    const next = editorReducer(state, { type: 'removeLayer', index: 1 })

    expect(next.draft.layers).toHaveLength(1)
    expect(next.selectedLayer).toBe(0)
    expect(editorReducer(next, { type: 'removeLayer', index: 0 }).selectedLayer).toBeNull()
  })

  it('moves a layer up or down within bounds', () => {
    const state = withLayers('solid', 'wave')

    const moved = editorReducer(state, { type: 'moveLayer', index: 1, direction: -1 })

    expect(moved.draft.layers.map((l) => l.effect.type)).toEqual(['wave', 'solid'])
    expect(moved.selectedLayer).toBe(0)
    expect(editorReducer(moved, { type: 'moveLayer', index: 0, direction: -1 })).toBe(moved)
  })

  it('paints lamps into the selected paint layer, scoped to that device', () => {
    const state = withLayers('paint')

    const next = editorReducer(state, {
      type: 'paintLamps',
      deviceId: 'kb',
      lampIds: [3, 7],
      color: BLUE,
    })

    const layer = next.draft.layers[0]
    expect(layer.devices).toEqual(['kb'])
    expect(layer.effect).toEqual({ type: 'paint', colors: { 3: BLUE, 7: BLUE } })
  })

  it('ignores paint when the selected layer is not a paint layer', () => {
    const state = withLayers('solid')

    expect(
      editorReducer(state, { type: 'paintLamps', deviceId: 'kb', lampIds: [1], color: BLUE }),
    ).toBe(state)
  })

  it('loads a saved pattern and remembers its id', () => {
    const state = editorReducer(initialEditorState(), {
      type: 'load',
      pattern: { id: 'abc', name: 'Sunset', layers: [], brightness: 0.4 },
    })

    expect(state.patternId).toBe('abc')
    expect(state.draft).toEqual({ name: 'Sunset', layers: [], brightness: 0.4 })
  })
})

describe('editorReducer preview zone', () => {
  it('starts without a zone and switches to the selected one', () => {
    expect(initialEditorState().zone).toBeNull()

    const next = editorReducer(initialEditorState(), { type: 'selectZone', deviceId: 'ring' })

    expect(next.zone).toBe('ring')
  })

  it('follows the painted device and a bound paint layer when it is selected', () => {
    const painted = editorReducer(withLayers('solid', 'paint'), {
      type: 'paintLamps',
      deviceId: 'kb',
      lampIds: [1],
      color: BLUE,
    })
    expect(painted.zone).toBe('kb')

    const elsewhere = editorReducer(painted, { type: 'selectZone', deviceId: 'ring' })
    const solidSelected = editorReducer(elsewhere, { type: 'selectLayer', index: 0 })
    expect(solidSelected.zone).toBe('ring')

    expect(editorReducer(solidSelected, { type: 'selectLayer', index: 1 }).zone).toBe('kb')
  })

  it('keeps the zone across new and loaded patterns', () => {
    const state = editorReducer(initialEditorState(), { type: 'selectZone', deviceId: 'ring' })

    expect(editorReducer(state, { type: 'new' }).zone).toBe('ring')
    expect(
      editorReducer(state, {
        type: 'load',
        pattern: { id: 'abc', name: 'Sunset', layers: [], brightness: 0.4 },
      }).zone,
    ).toBe('ring')
  })
})
