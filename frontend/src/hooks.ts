import { useCallback, useEffect, useRef, useState } from 'react'

import { api, openFrames } from './api/client'
import type { Device, Frame, Pattern, Playback, Status } from './api/types'

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

const STATUS_POLL_MS = 2000

/** Backend status (playback, achieved fps, per-zone health), polled; null until first reply. */
export function useStatus(): Status | null {
  const [status, setStatus] = useState<Status | null>(null)
  useEffect(() => {
    let cancelled = false
    const poll = () =>
      api
        .getStatus()
        .then((s) => {
          if (!cancelled) setStatus(s)
        })
        .catch(() => {
          if (!cancelled) setStatus(null)
        })
    poll()
    const handle = setInterval(poll, STATUS_POLL_MS)
    return () => {
      cancelled = true
      clearInterval(handle)
    }
  }, [])
  return status
}

/** Latest rendered frame from the backend, or null while nothing is playing. */
export function useFrames(playing: boolean): Frame | null {
  const [frame, setFrame] = useState<Frame | null>(null)
  useEffect(() => openFrames(setFrame), [])
  return playing ? frame : null
}

/** Calls `effect` once `value` has stopped changing for `delayMs`; the initial value never fires. */
export function useDebouncedEffect<T>(value: T, delayMs: number, effect: (value: T) => void) {
  // Compare against the last seen value rather than a "first render" flag: StrictMode runs
  // mount effects twice, and a flag would fire the effect for the untouched initial value.
  const seen = useRef(value)
  // Callers pass a fresh closure every render; keep the latest one without re-arming the timer.
  const latest = useRef(effect)
  useEffect(() => {
    latest.current = effect
  })
  useEffect(() => {
    if (Object.is(seen.current, value)) return
    seen.current = value
    const handle = setTimeout(() => latest.current(value), delayMs)
    return () => clearTimeout(handle)
  }, [value, delayMs])
}
