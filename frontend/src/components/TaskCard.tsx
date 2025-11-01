/**
 * Task card component.
 */

import { Task } from '../types'
import './TaskCard.css'

interface TaskCardProps {
  task: Task
}

function TaskCard({ task }: TaskCardProps) {
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return '#27ae60'
      case 'error':
        return '#e74c3c'
      case 'executing':
        return '#3498db'
      default:
        return '#95a5a6'
    }
  }

  return (
    <div className="task-card">
      <div className="task-card-header">
        <span
          className="task-status"
          style={{ backgroundColor: getStatusColor(task.status) }}
        >
          {task.status}
        </span>
        <span className="task-id">{task.task_id.slice(0, 8)}</span>
      </div>
      <div className="task-card-body">
        <p className="task-description">{task.description}</p>
        {task.plan && (
          <div className="task-plan-info">
            <strong>Plan:</strong> {task.plan.steps?.length || 0} steps
          </div>
        )}
      </div>
    </div>
  )
}

export default TaskCard

