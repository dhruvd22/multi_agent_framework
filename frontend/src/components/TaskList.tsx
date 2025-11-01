/**
 * Task list component.
 */

import { Task } from '../types'
import TaskCard from './TaskCard'
import './TaskList.css'

interface TaskListProps {
  tasks: Task[]
}

function TaskList({ tasks }: TaskListProps) {
  if (tasks.length === 0) {
    return (
      <div className="task-list-empty">
        <p>No tasks yet. Create a task to get started!</p>
      </div>
    )
  }

  return (
    <div className="task-list">
      <h3>Tasks ({tasks.length})</h3>
      <div className="task-list-grid">
        {tasks.map((task) => (
          <TaskCard key={task.task_id} task={task} />
        ))}
      </div>
    </div>
  )
}

export default TaskList

