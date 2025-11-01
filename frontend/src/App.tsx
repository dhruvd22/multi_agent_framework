/**
 * Main application component.
 * 
 * Sets up routing and application layout.
 */

import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import TaskManagement from './pages/TaskManagement'
import Observability from './pages/Observability'
import LogsViewer from './pages/LogsViewer'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<TaskManagement />} />
        <Route path="observability" element={<Observability />} />
        <Route path="logs" element={<LogsViewer />} />
      </Route>
    </Routes>
  )
}

export default App

