import type { Device, Frame, ZoneHealth } from '../api/types'
import { rgbCss } from '../color'

const OFF = 'rgb(28, 28, 34)'

interface Props {
  devices: Device[]
  frame: Frame | null
  health: Record<string, ZoneHealth>
  /** Zone whose lamp map is open in the editor, if any. */
  inspected: string | null
  onInspect: (deviceId: string | null) => void
}

/** Compact per-zone observability: live colour strip, frame counter and error state. */
export function ZoneStatusBar({ devices, frame, health, inspected, onInspect }: Props) {
  return (
    <footer className="status-bar">
      {devices.map((device) => {
        const colors = frame?.[device.id]
        const zone = health[device.id]
        const failing = (zone?.errors ?? 0) > 0 && zone?.last_error
        const title = failing ? `${zone.errors} errors · ${zone.last_error}` : 'OK'
        return (
          <button
            key={device.id}
            type="button"
            className="zone-status"
            aria-pressed={inspected === device.id}
            onClick={() => onInspect(inspected === device.id ? null : device.id)}
          >
            <span className={`dot ${failing ? 'bad' : 'ok'}`} title={title} />
            <span className="zone-name">{device.name}</span>
            <svg
              className="strip"
              viewBox={`0 0 ${device.lamp_count} 1`}
              preserveAspectRatio="none"
              aria-label={`${device.name} lamps`}
            >
              {device.lamps.map((lamp) => (
                <rect
                  key={lamp.id}
                  x={lamp.id}
                  y={0}
                  width={1}
                  height={1}
                  fill={colors?.[lamp.id] ? rgbCss(colors[lamp.id]) : OFF}
                />
              ))}
            </svg>
            <span className="muted mono">{zone?.frames ?? 0}</span>
            {failing && <span className="error-text">{zone.last_error}</span>}
          </button>
        )
      })}
    </footer>
  )
}
