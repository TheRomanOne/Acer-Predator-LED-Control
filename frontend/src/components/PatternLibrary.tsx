import type { Pattern } from '../api/types'

interface Props {
  patterns: Pattern[]
  activeId: string | null
  editingId: string | null
  onNew: () => void
  onOpen: (pattern: Pattern) => void
  onApply: (pattern: Pattern) => void
  onDelete: (pattern: Pattern) => void
}

export function PatternLibrary({ patterns, activeId, editingId, onNew, onOpen, onApply, onDelete }: Props) {
  return (
    <section className="library">
      <header className="row">
        <h2>Patterns</h2>
        <span className="spacer" />
        <button type="button" onClick={onNew}>
          + New
        </button>
      </header>
      {patterns.length === 0 && <p className="hint">Nothing saved yet.</p>}
      <ul>
        {patterns.map((pattern) => (
          <li key={pattern.id} className={pattern.id === editingId ? 'selected' : undefined}>
            <button type="button" className="name" onClick={() => onOpen(pattern)}>
              {pattern.name}
              {pattern.id === activeId && <span className="badge">on</span>}
            </button>
            <button type="button" onClick={() => onApply(pattern)} aria-label={`Apply ${pattern.name}`}>
              ▶
            </button>
            <button
              type="button"
              onClick={() => onDelete(pattern)}
              aria-label={`Delete ${pattern.name}`}
            >
              🗑
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}
