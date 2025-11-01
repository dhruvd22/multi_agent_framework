/**
 * Task form component.
 */

import { useState, FormEvent } from 'react'
import { CreateTaskRequest } from '../services/api'
import './TaskForm.css'

interface TaskFormProps {
  onSubmit: (request: CreateTaskRequest) => void
  loading: boolean
}

function TaskForm({ onSubmit, loading }: TaskFormProps) {
  const [description, setDescription] = useState('')
  const [requirements, setRequirements] = useState('')
  const [constraints, setConstraints] = useState('')

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()

    const request: CreateTaskRequest = {
      description,
      requirements: requirements
        ? requirements.split('\n').filter((r) => r.trim())
        : [],
      constraints: constraints
        ? JSON.parse(constraints)
        : {},
    }

    onSubmit(request)
    setDescription('')
    setRequirements('')
    setConstraints('')
  }

  return (
    <div className="task-form-container">
      <h3>Create New Task</h3>
      <form onSubmit={handleSubmit} className="task-form">
        <div className="form-group">
          <label htmlFor="description">Task Description</label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
            rows={4}
            placeholder="Describe the task you want the agents to complete..."
          />
        </div>

        <div className="form-group">
          <label htmlFor="requirements">Requirements (one per line)</label>
          <textarea
            id="requirements"
            value={requirements}
            onChange={(e) => setRequirements(e.target.value)}
            rows={3}
            placeholder="Requirement 1&#10;Requirement 2&#10;..."
          />
        </div>

        <div className="form-group">
          <label htmlFor="constraints">Constraints (JSON format)</label>
          <textarea
            id="constraints"
            value={constraints}
            onChange={(e) => setConstraints(e.target.value)}
            rows={2}
            placeholder='{"budget": 10, "timeout": 300}'
          />
        </div>

        <button type="submit" disabled={loading || !description.trim()}>
          {loading ? 'Creating...' : 'Create Task'}
        </button>
      </form>
    </div>
  )
}

export default TaskForm

