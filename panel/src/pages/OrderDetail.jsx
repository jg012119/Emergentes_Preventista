import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, CheckCircle, XCircle, Loader, Truck } from 'lucide-react'
import { getOrder, updateOrderStatus } from '../services/api'

export default function OrderDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState('')

  useEffect(() => {
    getOrder(id)
      .then(setOrder)
      .catch(() => navigate('/orders'))
      .finally(() => setLoading(false))
  }, [id])

  const changeStatus = async (status) => {
    setUpdating(status)
    try {
      const updated = await updateOrderStatus(id, status)
      setOrder(updated)
    } catch (err) {
      alert(err.message)
    } finally {
      setUpdating('')
    }
  }

  if (loading || !order) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
        <Loader size={32} />
      </div>
    )
  }

  return (
    <>
      <div style={{ marginBottom: 20 }}>
        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/orders')}>
          <ArrowLeft size={16} /> Volver a pedidos
        </button>
      </div>

      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2>Pedido #{order.id.slice(0, 8)}</h2>
          <p>Detalle completo del pedido</p>
        </div>
        <span className={`badge badge-${order.status}`} style={{ fontSize: '.9rem', padding: '8px 16px' }}>
          {order.status}
        </span>
      </div>

      <div className="detail-grid">
        {/* Main content */}
        <div>
          {/* Products table */}
          <div className="table-container" style={{ marginBottom: 24 }}>
            <div className="table-header">
              <h3>Productos del pedido</h3>
            </div>
            <table>
              <thead>
                <tr>
                  <th>Producto</th>
                  <th>Cantidad</th>
                  <th>Precio Unit.</th>
                  <th>Subtotal</th>
                </tr>
              </thead>
              <tbody>
                {order.items?.map(item => (
                  <tr key={item.id}>
                    <td style={{ fontWeight: 500 }}>{item.product_name || item.product_id.slice(0, 8)}</td>
                    <td>{item.quantity}</td>
                    <td>Bs {Number(item.unit_price).toFixed(2)}</td>
                    <td style={{ fontWeight: 600 }}>Bs {Number(item.subtotal).toFixed(2)}</td>
                  </tr>
                ))}
                <tr>
                  <td colSpan={3} style={{ textAlign: 'right', fontWeight: 700, fontSize: '1rem' }}>
                    TOTAL
                  </td>
                  <td style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--accent-light)' }}>
                    Bs {Number(order.total).toFixed(2)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Status actions */}
          {order.status !== 'borrador' && (
            <div className="card">
              <h3 style={{ marginBottom: 16, fontSize: '1rem' }}>Cambiar estado del pedido</h3>
              <div className="btn-group">
                {order.status !== 'confirmado' && (
                  <button
                    className="btn btn-success btn-sm"
                    onClick={() => changeStatus('confirmado')}
                    disabled={!!updating}
                  >
                    <CheckCircle size={16} />
                    {updating === 'confirmado' ? 'Confirmando...' : 'Confirmar'}
                  </button>
                )}
                {order.status !== 'en_proceso' && order.status === 'confirmado' && (
                  <button
                    className="btn btn-warning btn-sm"
                    onClick={() => changeStatus('en_proceso')}
                    disabled={!!updating}
                  >
                    <Truck size={16} />
                    {updating === 'en_proceso' ? 'Procesando...' : 'En Proceso'}
                  </button>
                )}
                {order.status !== 'rechazado' && (
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => changeStatus('rechazado')}
                    disabled={!!updating}
                  >
                    <XCircle size={16} />
                    {updating === 'rechazado' ? 'Rechazando...' : 'Rechazar'}
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar info */}
        <div>
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="detail-section">
              <h4>Información del pedido</h4>
              <div className="detail-row">
                <span>Tienda</span>
                <span>{order.store_name || '—'}</span>
              </div>
              <div className="detail-row">
                <span>Fecha entrega</span>
                <span>{order.delivery_date || '—'}</span>
              </div>
              <div className="detail-row">
                <span>Creado</span>
                <span>{order.created_at ? new Date(order.created_at).toLocaleString('es-BO') : '—'}</span>
              </div>
              <div className="detail-row">
                <span>Items</span>
                <span>{order.items?.length || 0}</span>
              </div>
            </div>
          </div>

          {order.notes && (
            <div className="card">
              <div className="detail-section">
                <h4>Observaciones</h4>
                <p style={{ fontSize: '.875rem', color: 'var(--text-secondary)' }}>{order.notes}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  )
}
