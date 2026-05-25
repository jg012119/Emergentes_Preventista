import { NavLink, useLocation } from 'react-router-dom'
import { LayoutDashboard, ShoppingCart, Package, LogOut } from 'lucide-react'

export default function Layout({ children, onLogout }) {
  const location = useLocation()

  const links = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/orders', label: 'Pedidos', icon: ShoppingCart },
    { to: '/products', label: 'Productos', icon: Package },
  ]

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h1>AJE Panel</h1>
          <span>Gestión de Pedidos</span>
        </div>
        <nav className="sidebar-nav">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === '/'}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? 'active' : ''}`
              }
            >
              <link.icon />
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <button className="sidebar-link" onClick={onLogout} style={{ width: '100%', border: 'none', background: 'none' }}>
            <LogOut />
            Cerrar sesión
          </button>
        </div>
      </aside>
      <main className="main-content">
        {children}
      </main>
    </div>
  )
}
