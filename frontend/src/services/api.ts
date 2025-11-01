/**
 * API client for backend communication.
 */

import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface Task {
  task_id: string
  status: string
  description: string
  plan?: any
  results?: any
}

export interface CreateTaskRequest {
  description: string
  requirements?: string[]
  constraints?: Record<string, any>
}

export const tasksApi = {
  createTask: async (request: CreateTaskRequest): Promise<Task> => {
    const response = await apiClient.post('/api/tasks/', request)
    return response.data
  },

  getTask: async (taskId: string): Promise<Task> => {
    const response = await apiClient.get(`/api/tasks/${taskId}`)
    return response.data
  },

  getTaskLogs: async (taskId: string): Promise<any[]> => {
    const response = await apiClient.get(`/api/tasks/${taskId}/logs`)
    return response.data
  },
}

export interface Agent {
  agent_id: string
  agent_type: string
  status: string
  capabilities: any
  current_task_id?: string
}

export const agentsApi = {
  listAgents: async (): Promise<Agent[]> => {
    const response = await apiClient.get('/api/agents/')
    return response.data
  },

  getAgent: async (agentId: string): Promise<Agent> => {
    const response = await apiClient.get(`/api/agents/${agentId}`)
    return response.data
  },
}

export interface LogEntry {
  timestamp: string
  level: string
  message: string
  agent_id?: string
  task_id?: string
  metadata?: Record<string, any>
}

export const logsApi = {
  getLogs: async (params?: {
    level?: string
    agent_id?: string
    task_id?: string
    limit?: number
    offset?: number
  }): Promise<LogEntry[]> => {
    const response = await apiClient.get('/api/logs/', { params })
    return response.data
  },

  getErrors: async (taskId?: string): Promise<LogEntry[]> => {
    const response = await apiClient.get('/api/logs/errors', {
      params: taskId ? { task_id: taskId } : {},
    })
    return response.data
  },

  getWarnings: async (taskId?: string): Promise<LogEntry[]> => {
    const response = await apiClient.get('/api/logs/warnings', {
      params: taskId ? { task_id: taskId } : {},
    })
    return response.data
  },
}

export default apiClient

