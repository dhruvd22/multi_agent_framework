/**
 * Error and warning panel component.
 */

import { LogEntry } from '../../types'
import './ErrorPanel.css'

interface ErrorPanelProps {
  errors: LogEntry[]
  warnings: LogEntry[]
}

function ErrorPanel({ errors, warnings }: ErrorPanelProps) {
  return (
    <div className="error-panel">
      <h3>Errors & Warnings</h3>
      <div className="error-summary">
        <div className="summary-item error">
          <span className="summary-count">{errors.length}</span>
          <span className="summary-label">Errors</span>
        </div>
        <div className="summary-item warning">
          <span className="summary-count">{warnings.length}</span>
          <span className="summary-label">Warnings</span>
        </div>
      </div>
    </div>
  )
}

export default ErrorPanel

