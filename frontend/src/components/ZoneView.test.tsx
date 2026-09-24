import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { Device } from '../api/types'
import { ZoneView } from './ZoneView'

const KEYBOARD: Device = {
  id: 'kb',
  name: 'Keyboard',
  kind: 'keyboard',
  lamp_count: 2,
  width_mm: 340,
  height_mm: 105,
  lamps: [
    { id: 0, x: 0.1, y: 0.2, key: 0x29 },
    { id: 1, x: 0.5, y: 0.2, key: 0 },
  ],
}

describe('ZoneView', () => {
  it('draws one lamp per device lamp, coloured from the frame, with key labels', () => {
    render(
      <ZoneView
        device={KEYBOARD}
        colors={[
          [255, 0, 0],
          [0, 0, 255],
        ]}
        selected={new Set()}
        onLampClick={() => {}}
      />,
    )

    const lamps = screen.getAllByRole('button')
    expect(lamps).toHaveLength(2)
    expect(lamps[0]).toHaveStyle({ fill: 'rgb(255, 0, 0)' })
    expect(lamps[1]).toHaveStyle({ fill: 'rgb(0, 0, 255)' })
    expect(screen.getByText('Esc')).toBeInTheDocument()
  })

  it('falls back to off when no frame is available and reports clicks', () => {
    const onLampClick = vi.fn()
    render(<ZoneView device={KEYBOARD} colors={null} selected={new Set()} onLampClick={onLampClick} />)

    fireEvent.click(screen.getAllByRole('button')[1])

    expect(onLampClick).toHaveBeenCalledWith(1, expect.anything())
  })

  it('marks selected lamps', () => {
    render(<ZoneView device={KEYBOARD} colors={null} selected={new Set([0])} onLampClick={() => {}} />)

    expect(screen.getAllByRole('button')[0]).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getAllByRole('button')[1]).toHaveAttribute('aria-pressed', 'false')
  })
})
