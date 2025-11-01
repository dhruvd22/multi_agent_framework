/**
 * Observability dashboard page.
 * 
 * Provides real-time visualization of agent execution flow,
 * system metrics, and agent activity.
 */

import { useEffect, useState } from 'react'
import { createExecutionWebSocket } from '../services/websocket'
import ExecutionFlow from '../components/Observability/ExecutionFlow'
import AgentActivity from '../components/Observability/AgentActivity'
import SystemMetrics from '../components/Observability/SystemMetrics'
import './Observability.css'

function Observability() {
  const [executionData, setExecutionData] = useState<any>(null)

  useEffect(() => {
    const ws = createExecutionWebSocket((data) => {
      if (data.type === 'execution_update') {
        setExecutionData(data.data)
      }
    })

    ws.connect()

    return () => {
      ws.disconnect()
    }
  }, [])

  return (
    <div className="observability">
      <h2>Observability Dashboard</h2>
      <div className="observability-grid">
        <div className="observability-section">
          <ExecutionFlow data={executionData} />
        </div>
        <div className="observability-section">
          <AgentActivity />
        </div>
        <div className="observability-section">
          <SystemMetrics />
        </div>
      </div>
    </div>
  )
}

export default Observability

