/**
 * Layout component with navigation.
 */

import { Link, Outlet } from 'react-router-dom'
import './Layout.css'

function Layout() {
  return (
    <div className="layout">
      <nav className="navbar">
        <div className="nav-brand">
          <h1>Multi-Agent Framework</h1>
        </div>
        <ul className="nav-links">
          <li>
            <Link to="/">Tasks</Link>
          </li>
          <li>
            <Link to="/observability">Observability</Link>
          </li>
          <li>
            <Link to="/logs">Logs</Link>
          </li>
        </ul>
      </nav>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout

