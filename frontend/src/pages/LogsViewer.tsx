/**
 * Logs viewer page.
 * 
 * Displays logs, errors, and warnings with filtering capabilities.
 */

import { useEffect, useState } from 'react'
import { logsApi } from '../services/api'
import { createLogsWebSocket } from '../services/websocket'
import type { LogEntry } from '../types'
import LogViewer from '../components/Logs/LogViewer'
import LogFilters from '../components/Logs/LogFilters'
import ErrorPanel from '../components/Logs/ErrorPanel'
import './LogsViewer.css'

function LogsViewer() {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [errors, setErrors] = useState<LogEntry[]>([])
  const [warnings, setWarnings] = useState<LogEntry[]>([])
  const [filters, setFilters] = useState({
    level: '',
    agent_id: '',
    task_id: '',
  })

  useEffect(() => {
    loadLogs()
  }, [filters])

  useEffect(() => {
    const ws = createLogsWebSocket((data) => {
      if (data.type === 'log') {
        setLogs((prev) => [data.data, ...prev])
      }
    })

    ws.connect()

    return () => {
      ws.disconnect()
    }
  }, [])

  const loadLogs = async () => {
    try {
      const [logsData, errorsData, warningsData] = await Promise.all([
        logsApi.getLogs(filters),
        logsApi.getErrors(),
        logsApi.getWarnings(),
      ])

      // Cast API response to our type (API returns level as string, we expect union type)
      setLogs(logsData as LogEntry[])
      setErrors(errorsData as LogEntry[])
      setWarnings(warningsData as LogEntry[])
    } catch (error) {
      console.error('Failed to load logs:', error)
    }
  }

  return (
    <div className="logs-viewer">
      <h2>Logs & Error Management</h2>
      <div className="logs-viewer-content">
        <div className="logs-sidebar">
          <LogFilters filters={filters} onFiltersChange={setFilters} />
          <ErrorPanel errors={errors} warnings={warnings} />
        </div>
        <div className="logs-main">
          <LogViewer logs={logs} />
        </div>
      </div>
    </div>
  )
}

export default LogsViewer

