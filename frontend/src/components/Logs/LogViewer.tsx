/**
 * Log viewer component.
 */

import { LogEntry } from '../../types'
import './LogViewer.css'

interface LogViewerProps {
  logs: LogEntry[]
}

function LogViewer({ logs }: LogViewerProps) {
  const getLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR':
        return '#e74c3c'
      case 'WARNING':
        return '#f39c12'
      case 'INFO':
        return '#3498db'
      default:
        return '#95a5a6'
    }
  }

  return (
    <div className="log-viewer">
      <h3>Logs</h3>
      <div className="log-entries">
        {logs.length === 0 ? (
          <div className="log-empty">No logs available</div>
        ) : (
          logs.map((log, index) => (
            <div key={index} className="log-entry">
              <span
                className="log-level"
                style={{ color: getLevelColor(log.level) }}
              >
                {log.level}
              </span>
              <span className="log-timestamp">
                {new Date(log.timestamp).toLocaleString()}
              </span>
              <span className="log-message">{log.message}</span>
              {log.agent_id && (
                <span className="log-agent">Agent: {log.agent_id}</span>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default LogViewer

