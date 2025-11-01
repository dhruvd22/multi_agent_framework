/**
 * Task management page component.
 */

import { useState } from 'react'
import { tasksApi, CreateTaskRequest } from '../services/api'
import TaskList from '../components/TaskList'
import TaskForm from '../components/TaskForm'
import './TaskManagement.css'

function TaskManagement() {
  const [tasks, setTasks] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  const handleCreateTask = async (request: CreateTaskRequest) => {
    setLoading(true)
    try {
      const task = await tasksApi.createTask(request)
      setTasks([...tasks, task])
    } catch (error) {
      console.error('Failed to create task:', error)
      alert('Failed to create task. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="task-management">
      <h2>Task Management</h2>
      <div className="task-management-content">
        <div className="task-form-section">
          <TaskForm onSubmit={handleCreateTask} loading={loading} />
        </div>
        <div className="task-list-section">
          <TaskList tasks={tasks} />
        </div>
      </div>
    </div>
  )
}

export default TaskManagement

