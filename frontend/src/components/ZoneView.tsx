import { useMemo, type MouseEvent } from 'react'

import type { Device } from '../api/types'
import { rgbCss } from '../color'
import { keyLabel } from '../keys'

const VIEW_WIDTH = 100
const OFF = 'rgb(28, 28, 34)'

interface Props {
  device: Device
  /** Live colours indexed by lamp id, or null when nothing is playing. */
  colors: Array<[number, number, number]> | null
  selected: Set<number>
  onLampClick: (lampId: number, event: MouseEvent) => void
}

/** Lamp radius from the closest pair of lamps, so any layout renders without overlap. */
function lampRadius(device: Device, height: number): number {
  let closest = Infinity
  const pts = device.lamps.map((l) => [l.x * VIEW_WIDTH, l.y * height] as const)
  for (let i = 0; i < pts.length; i++) {
    for (let j = i + 1; j < pts.length; j++) {
      const d = Math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1])
      if (d > 0 && d < closest) closest = d
    }
  }
  return Number.isFinite(closest) ? Math.min(closest * 0.42, 6) : 4
}

export function ZoneView({ device, colors, selected, onLampClick }: Props) {
  const height = Math.max(8, (VIEW_WIDTH * device.height_mm) / Math.max(device.width_mm, 1))
  const radius = useMemo(() => lampRadius(device, height), [device, height])
  const pad = radius + 1

  return (
    <figure className="zone">
      <figcaption>
        {device.name} <span className="muted">· {device.lamp_count} lamps</span>
      </figcaption>
      <svg
        viewBox={`${-pad} ${-pad} ${VIEW_WIDTH + 2 * pad} ${height + 2 * pad}`}
        role="img"
        aria-label={device.name}
      >
        {device.lamps.map((lamp) => {
          const rgb = colors?.[lamp.id]
          const label = keyLabel(lamp.key)
          return (
            <g
              key={lamp.id}
              role="button"
              tabIndex={0}
              aria-label={label ? `${label} (lamp ${lamp.id})` : `lamp ${lamp.id}`}
              aria-pressed={selected.has(lamp.id)}
              className="lamp"
              style={{ fill: rgb ? rgbCss(rgb) : OFF }}
              onClick={(event) => onLampClick(lamp.id, event)}
            >
              <circle cx={lamp.x * VIEW_WIDTH} cy={lamp.y * height} r={radius} />
              {label && (
                <text
                  x={lamp.x * VIEW_WIDTH}
                  y={lamp.y * height}
                  fontSize={radius * (label.length > 2 ? 0.55 : 0.9)}
                >
                  {label}
                </text>
              )}
            </g>
          )
        })}
      </svg>
    </figure>
  )
}
