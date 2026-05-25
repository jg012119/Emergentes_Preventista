import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getOrders } from '../services/api'

const STATUS_OPTIONS = ['todos', 'pendiente', 'confirmado', 'rechazado', 'en_proceso', 'borrador']

export default function Orders() {
  const [orders, setOrders] = useState([])
  const [filter, setFilter] = useState('todos')
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    const statusParam = filter === 'todos' ? undefined : filter
    setLoading(true)
    getOrders(statusParam)
      .then(setOrders)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [filter])

  return (
    <>
      <div className="page-header">
        <h2>Pedidos</h2>
        <p>Lista de todos los pedidos recibidos</p>
      </div>

      <div className="filter-tabs">
        {STATUS_OPTIONS.map(s => (
          <button
            key={s}
            className={`filter-tab ${filter === s ? 'active' : ''}`}
            onClick={() => setFilter(s)}
          >
            {s === 'todos' ? 'Todos' : s.charAt(0).toUpperCase() + s.slice(1).replace('_', ' ')}
          </button>
        ))}
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Tienda</th>
              <th>Productos</th>
              <th>Total</th>
              <th>Entrega</th>
              <th>Estado</th>
              <th>Creado</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  Cargando...
                </td>
              </tr>
            ) : orders.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  No hay pedidos con este filtro
                </td>
              </tr>
            ) : (
              orders.map(order => (
                <tr key={order.id} onClick={() => navigate(`/orders/${order.id}`)} style={{ cursor: 'pointer' }}>
                  <td style={{ fontFamily: 'monospace', color: 'var(--accent-light)' }}>
                    #{order.id.slice(0, 8)}
                  </td>
                  <td>{order.store_name || '—'}</td>
                  <td>{order.items?.length || 0} items</td>
                  <td style={{ fontWeight: 600 }}>Bs {Number(order.total).toFixed(2)}</td>
                  <td style={{ color: 'var(--text-secondary)' }}>{order.delivery_date || '—'}</td>
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
