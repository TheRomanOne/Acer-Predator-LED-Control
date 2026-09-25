import type { Color } from '../api/types'
import { ColorField } from './fields'

interface Props {
  brush: Color
  onBrushChange: (brush: Color) => void
  paintedCount: number
  onClear: () => void
  /** Name of the zone the paint layer currently holds colours for, if any. */
  boundZone: string | null
  /** Name of the zone open in the preview. */
  previewZone: string
}

/** Brush and canvas controls shown under the preview while a paint layer is selected. */
export function PaintToolbar({
  brush,
  onBrushChange,
  paintedCount,
  onClear,
  boundZone,
  previewZone,
}: Props) {
  const elsewhere = boundZone !== null && boundZone !== previewZone
  return (
    <div className="paint-toolbar">
      <ColorField label="Brush" value={brush} onChange={onBrushChange} />
      <span className="paint-count">
        <strong className="mono">{paintedCount}</strong> painted
        {boundZone && <span className="muted"> on {boundZone}</span>}
      </span>
      <span className="spacer" />
      {elsewhere ? (
        <span className="hint warn">Painting {previewZone} moves this layer there and clears it.</span>
      ) : (
        <span className="hint">Click a lamp to paint it with the brush colour.</span>
      )}
      <button type="button" className="ghost" disabled={paintedCount === 0} onClick={onClear}>
        Clear
      </button>
    </div>
  )
}
