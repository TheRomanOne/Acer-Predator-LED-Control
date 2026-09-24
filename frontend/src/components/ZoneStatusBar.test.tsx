import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { Device, ZoneHealth } from '../api/types'
import { ZoneStatusBar } from './ZoneStatusBar'

const RING: Device = {
  id: 'ring',
  name: 'InfiniteRing',
  kind: 'chassis',
  lamp_count: 2,
  width_mm: 360,
  height_mm: 100,
  lamps: [
    { id: 0, x: 0, y: 0, key: 0 },
    { id: 1, x: 1, y: 0, key: 0 },
  ],
}
const KB: Device = { ...RING, id: 'kb', name: 'Keyboard', kind: 'keyboard' }

const healthy: ZoneHealth = { id: 'ring', frames: 120, errors: 0, last_error: null }
const failing: ZoneHealth = { id: 'kb', frames: 3, errors: 7, last_error: 'device unplugged' }

describe('ZoneStatusBar', () => {
  it('shows a live colour strip and frame count per zone', () => {
    render(
      <ZoneStatusBar
        devices={[RING]}
        frame={{ ring: [[255, 0, 0], [0, 0, 255]] }}
        health={{ ring: healthy }}
        inspected={null}
        onInspect={() => {}}
      />,
    )

    const cells = screen.getByLabelText('InfiniteRing lamps').querySelectorAll('rect')
    expect(cells).toHaveLength(2)
    expect(cells[0]).toHaveAttribute('fill', 'rgb(255, 0, 0)')
    expect(screen.getByText('120')).toBeInTheDocument()
    expect(screen.getByTitle('OK')).toBeInTheDocument()
  })

  it('surfaces the last error of a failing zone', () => {
    render(
      <ZoneStatusBar
        devices={[KB]}
        frame={null}
        health={{ kb: failing }}
        inspected={null}
        onInspect={() => {}}
      />,
    )

    expect(screen.getByTitle('7 errors · device unplugged')).toBeInTheDocument()
    expect(screen.getByText('device unplugged')).toBeInTheDocument()
  })

  it('toggles inspection when a zone is clicked', () => {
    const onInspect = vi.fn()
    render(
      <ZoneStatusBar devices={[RING]} frame={null} health={{}} inspected="ring" onInspect={onInspect} />,
    )

    fireEvent.click(screen.getByRole('button', { name: /InfiniteRing/ }))

    expect(onInspect).toHaveBeenCalledWith(null)
    expect(screen.getByRole('button', { name: /InfiniteRing/ })).toHaveAttribute('aria-pressed', 'true')
  })
})
