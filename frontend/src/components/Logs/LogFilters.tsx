/**
 * Log filters component.
 */

import './LogFilters.css'

interface LogFiltersProps {
  filters: {
    level: string
    agent_id: string
    task_id: string
  }
  onFiltersChange: (filters: any) => void
}

function LogFilters({ filters, onFiltersChange }: LogFiltersProps) {
  return (
    <div className="log-filters">
      <h3>Filters</h3>
      <div className="filter-group">
        <label>Level</label>
        <select
          value={filters.level}
          onChange={(e) =>
            onFiltersChange({ ...filters, level: e.target.value })
          }
        >
          <option value="">All</option>
          <option value="ERROR">Error</option>
          <option value="WARNING">Warning</option>
          <option value="INFO">Info</option>
          <option value="DEBUG">Debug</option>
        </select>
      </div>
      <div className="filter-group">
        <label>Agent ID</label>
        <input
          type="text"
          value={filters.agent_id}
          onChange={(e) =>
            onFiltersChange({ ...filters, agent_id: e.target.value })
          }
          placeholder="Filter by agent..."
        />
      </div>
      <div className="filter-group">
        <label>Task ID</label>
        <input
          type="text"
          value={filters.task_id}
          onChange={(e) =>
            onFiltersChange({ ...filters, task_id: e.target.value })
          }
          placeholder="Filter by task..."
        />
      </div>
    </div>
  )
}

export default LogFilters

