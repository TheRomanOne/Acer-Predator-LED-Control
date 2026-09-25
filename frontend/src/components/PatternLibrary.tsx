import type { Pattern } from '../api/types'
import { PlayIcon, PlusIcon, TrashIcon } from './icons'

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
      <header className="panel-header">
        <h2>Patterns</h2>
        <button type="button" className="small" onClick={onNew}>
          <PlusIcon /> New
        </button>
      </header>
      {patterns.length === 0 ? (
        <p className="empty">Nothing saved yet. Design a pattern and press Save.</p>
      ) : (
        <ul className="pattern-list">
          {patterns.map((pattern) => {
            const active = pattern.id === activeId
            return (
              <li key={pattern.id} className={`pattern-row${pattern.id === editingId ? ' selected' : ''}`}>
                <button type="button" className="pattern-open" onClick={() => onOpen(pattern)}>
                  <span className={`dot ${active ? 'ok' : ''}`} title={active ? 'Playing' : undefined} />
                  <span className="pattern-title">{pattern.name}</span>
                </button>
                <span className="row-actions">
                  <button
                    type="button"
                    className="icon"
                    onClick={() => onApply(pattern)}
                    aria-label={`Apply ${pattern.name}`}
                  >
                    <PlayIcon />
                  </button>
                  <button
                    type="button"
                    className="icon danger"
                    onClick={() => onDelete(pattern)}
                    aria-label={`Delete ${pattern.name}`}
                  >
                    <TrashIcon />
                  </button>
                </span>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
