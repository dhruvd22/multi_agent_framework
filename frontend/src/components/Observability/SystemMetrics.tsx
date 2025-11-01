/**
 * System metrics component.
 */

import './SystemMetrics.css'

function SystemMetrics() {
  return (
    <div className="system-metrics">
      <h3>System Metrics</h3>
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">Token Usage</div>
          <div className="metric-value">0</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Budget Used</div>
          <div className="metric-value">$0.00</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Tasks Completed</div>
          <div className="metric-value">0</div>
        </div>
      </div>
    </div>
  )
}

export default SystemMetrics

