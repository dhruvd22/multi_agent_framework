/**
 * Execution flow visualization component.
 */

import ReactFlow, { Node, Edge } from 'react-flow-renderer'
import './ExecutionFlow.css'

interface ExecutionFlowProps {
  data: any
}

function ExecutionFlow({ data }: ExecutionFlowProps) {
  // Generate nodes and edges from execution data
  const nodes: Node[] = data?.plan?.steps?.map((step: any, index: number) => ({
    id: step.step_id,
    type: 'default',
    position: { x: index * 200, y: 100 },
    data: { label: step.description },
  })) || []

  const edges: Edge[] = data?.plan?.steps?.flatMap((step: any) =>
    step.dependencies?.map((dep: string) => ({
      id: `${dep}-${step.step_id}`,
      source: dep,
      target: step.step_id,
    })) || []
  ) || []

  return (
    <div className="execution-flow">
      <h3>Execution Flow</h3>
      <div className="flow-container">
        {nodes.length > 0 ? (
          <ReactFlow nodes={nodes} edges={edges} fitView />
        ) : (
          <div className="flow-empty">No execution data available</div>
        )}
      </div>
    </div>
  )
}

export default ExecutionFlow

