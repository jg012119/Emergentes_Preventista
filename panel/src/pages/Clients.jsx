import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Building2, Loader, Mail, Phone, ReceiptText, Search, Store, UserRound } from 'lucide-react'
import { getClients } from '../services/api'

const fmtMoney = (value) => `Bs ${Number(value || 0).toFixed(2)}`
const fmtDate = (value) => value ? new Date(value).toLocaleDateString('es-BO') : '-'

function matchesClient(client, term) {
  const q = term.trim().toLowerCase()
  if (!q) return true
  const text = [
    client.name,
    client.email,
    client.phone,
    ...client.stores.map(store => `${store.name} ${store.address} ${store.phone || ''}`),
    ...client.orders.map(order => `${order.id} ${order.store_name} ${order.status}`),
  ].join(' ').toLowerCase()
  return text.includes(q)
}

export default function Clients() {
  const [clients, setClients] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    getClients()
      .then((data) => {
        setClients(data)
        setSelectedId(data[0]?.id || '')
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const filtered = useMemo(
    () => clients.filter(client => matchesClient(client, query)),
    [clients, query],
  )

  const selected = filtered.find(client => client.id === selectedId) || filtered[0]

  useEffect(() => {
    if (filtered.length && !filtered.some(client => client.id === selectedId)) {
      setSelectedId(filtered[0].id)
    }
  }, [filtered, selectedId])

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
        <h2>Clientes</h2>
        <p>Consulta clientes, sucursales y pedidos asociados al preventista</p>
      </div>

      <div className="client-layout">
        <section className="client-list">
          <div className="search-box">
            <Search size={18} />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Buscar cliente, sucursal o pedido"
            />
          </div>

          <div className="client-list-body">
            {filtered.length === 0 ? (
              <div className="empty-state">No hay clientes con esa busqueda</div>
            ) : filtered.map(client => (
              <button
                key={client.id}
                className={`client-row ${selected?.id === client.id ? 'active' : ''}`}
                onClick={() => setSelectedId(client.id)}
              >
                <span className="client-avatar"><UserRound size={18} /></span>
                <span>
                  <strong>{client.name}</strong>
                  <small>{client.metrics.stores} sucursales · {client.metrics.orders} pedidos</small>
                </span>
              </button>
            ))}
          </div>
        </section>

        <section className="client-detail">
          {!selected ? (
            <div className="empty-state">Selecciona un cliente para ver sus datos</div>
          ) : (
            <>
              <div className="client-hero">
                <div>
                  <h3>{selected.name}</h3>
                  <div className="client-contact">
                    <span><Mail size={14} /> {selected.email}</span>
                    <span><Phone size={14} /> {selected.phone || '-'}</span>
                  </div>
                </div>
                <span className="badge badge-confirmado">Cliente activo</span>
              </div>

              <div className="cards-grid compact-grid">
                <div className="card stat-card">
                  <div className="stat-icon" style={{ background: 'var(--accent-bg)' }}>
                    <Store color="var(--accent-light)" />
                  </div>
                  <div className="stat-info">
                    <h3>{selected.metrics.stores}</h3>
                    <p>Sucursales</p>
                  </div>
                </div>
                <div className="card stat-card">
                  <div className="stat-icon" style={{ background: 'var(--info-bg)' }}>
                    <ReceiptText color="var(--info)" />
                  </div>
                  <div className="stat-info">
                    <h3>{selected.metrics.orders}</h3>
                    <p>Pedidos</p>
                  </div>
                </div>
                <div className="card stat-card">
                  <div className="stat-icon" style={{ background: 'var(--success-bg)' }}>
                    <Building2 color="var(--success)" />
                  </div>
                  <div className="stat-info">
                    <h3>{fmtMoney(selected.metrics.total_value)}</h3>
                    <p>Valor solicitado</p>
                  </div>
                </div>
              </div>

              <div className="report-grid two-columns">
                <div className="table-container">
                  <div className="table-header">
                    <h3>Sucursales del cliente</h3>
                  </div>
                  <table>
                    <thead>
                      <tr>
                        <th>Sucursal</th>
                        <th>Direccion</th>
                        <th>Telefono</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selected.stores.length === 0 ? (
                        <tr><td colSpan={3} className="empty-cell">Sin sucursales</td></tr>
                      ) : selected.stores.map(store => (
                        <tr key={store.id}>
                          <td>{store.name}</td>
                          <td style={{ color: 'var(--text-secondary)' }}>{store.address}</td>
                          <td>{store.phone || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="table-container">
                  <div className="table-header">
                    <h3>Pedidos del cliente</h3>
                  </div>
                  <table>
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Sucursal</th>
                        <th>Total</th>
                        <th>Estado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selected.orders.length === 0 ? (
                        <tr><td colSpan={4} className="empty-cell">Sin pedidos</td></tr>
                      ) : selected.orders.map(order => (
                        <tr key={order.id} onClick={() => navigate(`/orders/${order.id}`)} style={{ cursor: 'pointer' }}>
                          <td style={{ fontFamily: 'monospace', color: 'var(--accent-light)' }}>#{order.id.slice(0, 8)}</td>
                          <td>{order.store_name || '-'}</td>
                          <td>{fmtMoney(order.total)}</td>
                          <td><span className={`badge badge-${order.status}`}>{order.status}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="table-container" style={{ marginTop: 20 }}>
                <div className="table-header">
                  <h3>Historial detallado</h3>
                </div>
                <table>
                  <thead>
                    <tr>
                      <th>Pedido</th>
                      <th>Sucursal</th>
                      <th>Items</th>
                      <th>Entrega</th>
                      <th>Creado</th>
                      <th>Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selected.orders.length === 0 ? (
                      <tr><td colSpan={6} className="empty-cell">Todavia no hay pedidos registrados</td></tr>
                    ) : selected.orders.map(order => (
                      <tr key={order.id} onClick={() => navigate(`/orders/${order.id}`)} style={{ cursor: 'pointer' }}>
                        <td style={{ fontFamily: 'monospace', color: 'var(--accent-light)' }}>#{order.id.slice(0, 8)}</td>
                        <td>{order.store_name || '-'}</td>
                        <td>{order.items_count}</td>
                        <td>{order.delivery_date || '-'}</td>
                        <td style={{ color: 'var(--text-secondary)' }}>{fmtDate(order.created_at)}</td>
                        <td style={{ fontWeight: 700 }}>{fmtMoney(order.total)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </section>
      </div>
    </>
  )
}
