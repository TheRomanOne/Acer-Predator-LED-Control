import type { Device, Frame, Pattern, PatternBody, Playback, Status } from './types'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!response.ok) {
    const detail = await response
      .json()
      .then((body: { detail?: unknown }) => body.detail)
      .catch(() => undefined)
    throw new ApiError(
      response.status,
      typeof detail === 'string' ? detail : `${response.status} ${response.statusText}`,
    )
  }
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

const json = (method: string, body: unknown): RequestInit => ({
  method,
  body: JSON.stringify(body),
})

export const api = {
  getDevices: () => request<Device[]>('/api/devices'),
  listPatterns: () => request<Pattern[]>('/api/patterns'),
  getPattern: (id: string) => request<Pattern>(`/api/patterns/${id}`),
  createPattern: (body: PatternBody) => request<Pattern>('/api/patterns', json('POST', body)),
  updatePattern: (id: string, body: PatternBody) =>
    request<Pattern>(`/api/patterns/${id}`, json('PUT', body)),
  deletePattern: (id: string) => request<void>(`/api/patterns/${id}`, { method: 'DELETE' }),
  getPlayback: () => request<Playback>('/api/playback'),
  getStatus: () => request<Status>('/api/status'),
  apply: (patternId: string) =>
    request<Playback>('/api/playback/apply', json('POST', { pattern_id: patternId })),
  preview: (body: PatternBody) => request<Playback>('/api/playback/preview', json('POST', body)),
  stop: () => request<Playback>('/api/playback/stop', { method: 'POST' }),
}

const RECONNECT_MIN_MS = 1000
const RECONNECT_MAX_MS = 10000

/** Subscribe to rendered frames; reconnects (with backoff) until the returned function is called. */
export function openFrames(onFrame: (frame: Frame) => void): () => void {
  let socket: WebSocket | null = null
  let closed = false
  let retry: ReturnType<typeof setTimeout> | undefined
  let delay = RECONNECT_MIN_MS

  const connect = () => {
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
    socket = new WebSocket(`${protocol}://${location.host}/api/ws/frames`)
    socket.onopen = () => {
      delay = RECONNECT_MIN_MS
    }
    socket.onmessage = (event) => onFrame(JSON.parse(event.data) as Frame)
    socket.onclose = () => {
      if (closed) return
      retry = setTimeout(connect, delay)
      delay = Math.min(delay * 2, RECONNECT_MAX_MS)
    }
  }
  connect()

  return () => {
    closed = true
    clearTimeout(retry)
    socket?.close()
  }
}
