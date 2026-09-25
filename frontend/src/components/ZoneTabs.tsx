import type { Device, Frame, ZoneHealth } from '../api/types'
import { rgbCss } from '../color'

const OFF = 'rgb(30, 33, 42)'

interface Props {
  devices: Device[]
  frame: Frame | null
  health: Record<string, ZoneHealth>
  /** Zone whose lamp map is open in the preview. */
  selected: string | null
  onSelect: (deviceId: string) => void
}

/** One tab per zone: live colour strip, frame counter and error state; picks the previewed zone. */
export function ZoneTabs({ devices, frame, health, selected, onSelect }: Props) {
  return (
    <div className="zone-tabs" role="tablist" aria-label="Zones">
      {devices.map((device) => {
        const colors = frame?.[device.id]
        const zone = health[device.id]
        const failing = (zone?.errors ?? 0) > 0 && zone?.last_error
        const title = failing ? `${zone.errors} errors · ${zone.last_error}` : 'OK'
        return (
          <button
            key={device.id}
            type="button"
            role="tab"
            className="zone-tab"
            aria-selected={selected === device.id}
            onClick={() => onSelect(device.id)}
          >
            <span className="zone-tab-head">
              <span className={`dot ${failing ? 'bad' : 'ok'}`} title={title} />
              <span className="zone-tab-name">{device.name}</span>
              <span className="zone-tab-frames mono" title="Frames pushed">
                {zone?.frames ?? 0}
              </span>
            </span>
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
            {failing && <span className="zone-tab-error">{zone.last_error}</span>}
          </button>
        )
      })}
    </div>
  )
}
