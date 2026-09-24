import { useCallback, useEffect, useRef, useState } from 'react'

import { api, openFrames } from './api/client'
import type { Device, Frame, Pattern, Playback } from './api/types'

export function useDevices(): Device[] {
  const [devices, setDevices] = useState<Device[]>([])
  useEffect(() => {
    api.getDevices().then(setDevices).catch(console.error)
  }, [])
  return devices
}

export function usePatterns(): [Pattern[], () => Promise<void>] {
  const [patterns, setPatterns] = useState<Pattern[]>([])
  const refresh = useCallback(() => api.listPatterns().then(setPatterns), [])
  useEffect(() => {
    refresh().catch(console.error)
  }, [refresh])
  return [patterns, refresh]
}

export function usePlayback(): [Playback, (next: Playback) => void] {
  const [playback, setPlayback] = useState<Playback>({ pattern_id: null, preview: false })
  useEffect(() => {
    api.getPlayback().then(setPlayback).catch(console.error)
  }, [])
  return [playback, setPlayback]
}

/** Latest rendered frame from the backend, or null while nothing is playing. */
export function useFrames(playing: boolean): Frame | null {
  const [frame, setFrame] = useState<Frame | null>(null)
  useEffect(() => openFrames(setFrame), [])
  return playing ? frame : null
}

/** Calls `effect` once `value` has stopped changing for `delayMs`, skipping the first render. */
export function useDebouncedEffect<T>(value: T, delayMs: number, effect: (value: T) => void) {
  const first = useRef(true)
  useEffect(() => {
    if (first.current) {
      first.current = false
      return
    }
    const handle = setTimeout(() => effect(value), delayMs)
    return () => clearTimeout(handle)
    // `effect` is intentionally not a dependency: callers pass fresh closures every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, delayMs])
}
