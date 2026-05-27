import { NavLink } from 'react-router-dom'
import { LayoutDashboard, ShoppingCart, Package, LogOut, Users, BarChart3, UserRound } from 'lucide-react'

export default function Layout({ children, onLogout }) {
  const links = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/orders', label: 'Pedidos', icon: ShoppingCart },
    { to: '/clients', label: 'Clientes', icon: Users },
    { to: '/reports', label: 'Reportes', icon: BarChart3 },
    { to: '/products', label: 'Productos', icon: Package },
    { to: '/profile', label: 'Perfil', icon: UserRound },
  ]

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h1>AJE Panel</h1>
          <span>Gestion de Pedidos</span>
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
          <button className="sidebar-link logout-link" onClick={onLogout}>
            <LogOut />
            Cerrar sesion
          </button>
        </div>
      </aside>
      <main className="main-content">
        <div className="top-actions">
          <NavLink to="/profile" className="top-action-btn">
            <UserRound />
            Perfil
          </NavLink>
          <button className="top-action-btn danger" onClick={onLogout}>
            <LogOut />
            Cerrar sesion
          </button>
        </div>
        {children}
      </main>
    </div>
  )
}
