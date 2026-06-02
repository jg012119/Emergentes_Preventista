import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ShoppingCart, Clock, CheckCircle, XCircle, Loader } from 'lucide-react'
import { getOrders } from '../services/api'

export default function Dashboard() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    getOrders()
      .then(setOrders)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const stats = {
    total: orders.length,
    pendiente: orders.filter(o => o.status === 'pendiente').length,
    confirmado: orders.filter(o => o.status === 'confirmado' || o.status === 'pagado').length,
    rechazado: orders.filter(o => o.status === 'rechazado').length,
    en_proceso: orders.filter(o => o.status === 'en_proceso').length,
  }

  const recent = orders.slice(0, 5)

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
        <Loader className="spin" size={32} />
      </div>
    )
  }

  return (
    <>
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Resumen de pedidos del sistema</p>
      </div>

      <div className="cards-grid">
        <div className="card stat-card">
          <div className="stat-icon" style={{ background: 'var(--accent-bg)' }}>
            <ShoppingCart color="var(--accent-light)" />
          </div>
          <div className="stat-info">
            <h3>{stats.total}</h3>
            <p>Total pedidos</p>
          </div>
        </div>
        <div className="card stat-card">
          <div className="stat-icon" style={{ background: 'var(--warning-bg)' }}>
            <Clock color="var(--warning)" />
          </div>
          <div className="stat-info">
            <h3>{stats.pendiente}</h3>
            <p>Pendientes</p>
          </div>
        </div>
        <div className="card stat-card">
          <div className="stat-icon" style={{ background: 'var(--success-bg)' }}>
            <CheckCircle color="var(--success)" />
          </div>
          <div className="stat-info">
            <h3>{stats.confirmado}</h3>
            <p>Confirmados / Pagados</p>
          </div>
        </div>
        <div className="card stat-card">
          <div className="stat-icon" style={{ background: 'var(--danger-bg)' }}>
            <XCircle color="var(--danger)" />
          </div>
          <div className="stat-info">
            <h3>{stats.rechazado}</h3>
            <p>Rechazados</p>
          </div>
        </div>
      </div>

      <div className="table-container">
        <div className="table-header">
          <h3>Pedidos recientes</h3>
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/orders')}>
            Ver todos
          </button>
        </div>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Tienda</th>
              <th>Total</th>
              <th>Estado</th>
              <th>Fecha</th>
            </tr>
          </thead>
          <tbody>
            {recent.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '40px' }}>
                  No hay pedidos todavía
                </td>
              </tr>
            ) : (
              recent.map(order => (
                <tr key={order.id} onClick={() => navigate(`/orders/${order.id}`)} style={{ cursor: 'pointer' }}>
                  <td style={{ fontFamily: 'monospace', color: 'var(--accent-light)' }}>#{order.id.slice(0, 8)}</td>
                  <td>{order.store_name || '—'}</td>
                  <td>Bs {Number(order.total).toFixed(2)}</td>
                  <td><span className={`badge badge-${order.status}`}>{order.status}</span></td>
                  <td style={{ color: 'var(--text-secondary)' }}>
                    {order.created_at ? new Date(order.created_at).toLocaleDateString('es-BO') : '—'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </>
  )
}
