import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, CheckCircle, XCircle, Loader, Truck, Save } from 'lucide-react'
import { getOrder, updateOrderStatus, updateOrderDeliveryDate } from '../services/api'

function formatInputDate(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function getDeliveryDateLimits() {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const maxDate = new Date(today)
  maxDate.setDate(today.getDate() + 7)
  return {
    min: formatInputDate(today),
    max: formatInputDate(maxDate),
  }
}

export default function OrderDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [order, setOrder] = useState(null)
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState('')
  const [deliveryDate, setDeliveryDate] = useState('')
  const [updatingDate, setUpdatingDate] = useState(false)

  useEffect(() => {
    getOrder(id)
      .then((data) => {
        setOrder(data)
        setDeliveryDate(data.delivery_date || '')
      })
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

  const changeDeliveryDate = async () => {
    if (!deliveryDate) {
      alert('Selecciona una fecha de entrega')
      return
    }

    setUpdatingDate(true)
    try {
      const updated = await updateOrderDeliveryDate(id, deliveryDate)
      setOrder(updated)
      setDeliveryDate(updated.delivery_date || '')
    } catch (err) {
      alert(err.message)
    } finally {
      setUpdatingDate(false)
    }
  }

  if (loading || !order) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
        <Loader size={32} />
      </div>
    )
  }

  const dateLimits = getDeliveryDateLimits()
  const dateChanged = Boolean(deliveryDate && deliveryDate !== order.delivery_date)

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
                {order.status !== 'pagado' && (order.status === 'en_proceso' || order.status === 'confirmado') && (
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={() => changeStatus('pagado')}
                    disabled={!!updating}
                  >
                    <CheckCircle size={16} />
                    {updating === 'pagado' ? 'Marcando Pagado...' : 'Marcar como Pagado'}
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
                <div className="delivery-date-editor">
                  <input
                    type="date"
                    value={deliveryDate}
                    min={dateLimits.min}
                    max={dateLimits.max}
                    onChange={(event) => setDeliveryDate(event.target.value)}
                  />
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={changeDeliveryDate}
                    disabled={updatingDate || !dateChanged}
                  >
                    <Save size={14} />
                    {updatingDate ? 'Guardando...' : 'Guardar'}
                  </button>
                </div>
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
