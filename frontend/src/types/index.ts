/**
 * Type definitions for the application.
 */

export interface Task {
  task_id: string
  status: string
  description: string
  plan?: ExecutionPlan
  results?: Record<string, any>
}

export interface ExecutionPlan {
  plan_id: string
  task_id: string
  steps: PlanStep[]
  created_at: string
  status: string
}

export interface PlanStep {
  step_id: string
  description: string
  agent_type: string
  dependencies: string[]
  status: string
  result?: any
}

export interface Agent {
  agent_id: string
  agent_type: string
  status: string
  capabilities: AgentCapabilities
  current_task_id?: string
}

export interface AgentCapabilities {
  can_plan: boolean
  can_execute: boolean
  can_criticize: boolean
  can_write_code: boolean
  can_run_tests: boolean
  can_execute_scripts: boolean
}

export interface LogEntry {
  timestamp: string
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG'
  message: string
  agent_id?: string
  task_id?: string
  metadata?: Record<string, any>
}

