import { afterEach, describe, expect, it, vi } from 'vitest'

import { api, ApiError, openFrames } from './client'

function mockFetch(status: number, body: unknown) {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(body === undefined ? null : JSON.stringify(body), { status }),
  )
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  vi.unstubAllGlobals()
  vi.useRealTimers()
})

class FakeSocket {
  static instances: FakeSocket[] = []
  onmessage: ((e: { data: string }) => void) | null = null
  onclose: (() => void) | null = null
  onopen: (() => void) | null = null
  closed = false
  url: string
  constructor(url: string) {
    this.url = url
    FakeSocket.instances.push(this)
  }
  close() {
    this.closed = true
  }
}

describe('openFrames', () => {
  it('reconnects with growing delays and resets after a successful connection', () => {
    vi.useFakeTimers()
    FakeSocket.instances = []
    vi.stubGlobal('WebSocket', FakeSocket)
    vi.stubGlobal('location', { protocol: 'http:', host: 'localhost:5173' })

    const close = openFrames(() => {})
    expect(FakeSocket.instances).toHaveLength(1)

    FakeSocket.instances[0].onclose?.()
    vi.advanceTimersByTime(999)
    expect(FakeSocket.instances).toHaveLength(1)
    vi.advanceTimersByTime(1)
    expect(FakeSocket.instances).toHaveLength(2)

    FakeSocket.instances[1].onclose?.()
    vi.advanceTimersByTime(1999)
    expect(FakeSocket.instances).toHaveLength(2)
    vi.advanceTimersByTime(1)
    expect(FakeSocket.instances).toHaveLength(3)

    FakeSocket.instances[2].onopen?.()
    FakeSocket.instances[2].onclose?.()
    vi.advanceTimersByTime(1000)
    expect(FakeSocket.instances).toHaveLength(4)

    close()
    FakeSocket.instances[3].onclose?.()
    vi.advanceTimersByTime(10000)
    expect(FakeSocket.instances).toHaveLength(4)
    expect(FakeSocket.instances[3].closed).toBe(true)
  })
})

describe('api', () => {
  it('posts a preview body as JSON', async () => {
    const fetchMock = mockFetch(200, { pattern_id: null, preview: true })
    const body = { name: 'x', layers: [], brightness: 1 }

    const result = await api.preview(body)

    expect(result).toEqual({ pattern_id: null, preview: true })
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/playback/preview')
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body)).toEqual(body)
  })

  it('throws an ApiError carrying the status and detail', async () => {
    mockFetch(404, { detail: 'pattern nope not found' })

    await expect(api.getPattern('nope')).rejects.toMatchObject<Partial<ApiError>>({
      status: 404,
      message: 'pattern nope not found',
    })
  })

  it('treats 204 as a void result', async () => {
    mockFetch(204, undefined)

    await expect(api.deletePattern('abc')).resolves.toBeUndefined()
  })
})
