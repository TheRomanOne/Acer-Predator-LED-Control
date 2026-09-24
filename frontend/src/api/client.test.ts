import { afterEach, describe, expect, it, vi } from 'vitest'

import { api, ApiError } from './client'

function mockFetch(status: number, body: unknown) {
  const fetchMock = vi.fn().mockResolvedValue(
    new Response(body === undefined ? null : JSON.stringify(body), { status }),
  )
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => vi.unstubAllGlobals())

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
