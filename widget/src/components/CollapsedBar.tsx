import { useEffect, useState } from 'react'

interface CollapsedBarProps {
  brandName: string
  suggestions: string[]
  animate: boolean
  onClick: () => void
  onSuggestionClick: (suggestion: string) => void
}

export function CollapsedBar({
  brandName,
  suggestions,
  animate,
  onClick,
  onSuggestionClick,
}: CollapsedBarProps) {
  const [visible, setVisible] = useState(!animate)

  useEffect(() => {
    if (animate) {
      requestAnimationFrame(() => setVisible(true))
    }
  }, [animate])

  return (
    <div className={`zk-collapsed-bar ${visible ? 'zk-collapsed-bar--visible' : ''}`}>
      <div className="zk-collapsed-bar__border" onClick={onClick}>
        <div className="zk-collapsed-bar__inner">
          <svg
            className="zk-collapsed-bar__icon"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.3-4.3" />
          </svg>
          <span className="zk-collapsed-bar__placeholder">
            Ask {brandName} a question&hellip;
          </span>
        </div>
      </div>
      {suggestions.length > 0 && (
        <div className="zk-collapsed-bar__chips">
          {suggestions.slice(0, 2).map((suggestion, idx) => (
            <button
              key={idx}
              className="zk-chip"
              onClick={(e) => {
                e.stopPropagation()
                onSuggestionClick(suggestion)
              }}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
