import { useMemo, type KeyboardEvent } from 'react'

import type { Device } from '../api/types'
import { labelColorOn, rgbCss } from '../color'
import { keyLabel } from '../keys'

const VIEW_WIDTH = 100
const OFF = 'rgb(30, 33, 42)'
const ACTIVATION_KEYS = new Set(['Enter', ' '])

interface Props {
  device: Device
  /** Live colours indexed by lamp id, or null when nothing is playing. */
  colors: Array<[number, number, number]> | null
  selected: Set<number>
  onLampClick: (lampId: number) => void
}

/** Distance between the two closest lamps, so any layout renders without overlap. */
function lampPitch(device: Device, height: number): number {
  let closest = Infinity
  const pts = device.lamps.map((l) => [l.x * VIEW_WIDTH, l.y * height] as const)
  for (let i = 0; i < pts.length; i++) {
    for (let j = i + 1; j < pts.length; j++) {
      const d = Math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1])
      if (d > 0 && d < closest) closest = d
    }
  }
  return Number.isFinite(closest) ? Math.min(closest, 14) : 10
}

export function ZoneView({ device, colors, selected, onLampClick }: Props) {
  const height = Math.max(8, (VIEW_WIDTH * device.height_mm) / Math.max(device.width_mm, 1))
  const pitch = useMemo(() => lampPitch(device, height), [device, height])
  const keycaps = device.kind === 'keyboard'
  // Keycaps nearly touch like real keys; round lamps keep a clear gap.
  const half = pitch * (keycaps ? 0.44 : 0.36)
  const pad = half + 2

  const activate = (lampId: number) => (event: KeyboardEvent) => {
    if (!ACTIVATION_KEYS.has(event.key)) return
    event.preventDefault()
    onLampClick(lampId)
  }

  return (
    <svg
      className="zone-map"
      viewBox={`${-pad} ${-pad} ${VIEW_WIDTH + 2 * pad} ${height + 2 * pad}`}
      role="img"
      aria-label={device.name}
    >
      {device.lamps.map((lamp) => {
        const rgb = colors?.[lamp.id]
        const label = keyLabel(lamp.key)
        const cx = lamp.x * VIEW_WIDTH
        const cy = lamp.y * height
        return (
          <g
            key={lamp.id}
            role="button"
            tabIndex={0}
            aria-label={label ? `${label} (lamp ${lamp.id})` : `lamp ${lamp.id}`}
            aria-pressed={selected.has(lamp.id)}
            className={`lamp lamp-${rgb ? labelColorOn(rgb) : 'light'}`}
            style={{ fill: rgb ? rgbCss(rgb) : OFF }}
            onClick={() => onLampClick(lamp.id)}
            onKeyDown={activate(lamp.id)}
          >
            {keycaps ? (
              <rect x={cx - half} y={cy - half} width={2 * half} height={2 * half} rx={half * 0.3} />
            ) : (
              <circle cx={cx} cy={cy} r={half} />
            )}
            {label && (
              <text x={cx} y={cy} fontSize={half * (label.length > 2 ? 0.8 : 1.15)}>
                {label}
              </text>
            )}
          </g>
        )
      })}
    </svg>
  )
}
