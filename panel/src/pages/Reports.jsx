import { useEffect, useState } from 'react'
import {
  BarChart3,
  Bot,
  CheckCircle2,
  Loader,
  MessageCircle,
  Send,
  Store,
  Target,
  TrendingUp,
  Users,
} from 'lucide-react'
import { getAgentReport } from '../services/api'

const fmtMoney = (value) => `Bs ${Number(value || 0).toFixed(2)}`
const fmtPct = (value) => `${Number(value || 0).toFixed(1)}%`

function StatCard({ icon: Icon, label, value, color = 'var(--accent-light)', bg = 'var(--accent-bg)' }) {
  return (
    <div className="card stat-card">
      <div className="stat-icon" style={{ background: bg }}>
        <Icon color={color} />
      </div>
      <div className="stat-info">
        <h3>{value}</h3>
        <p>{label}</p>
      </div>
    </div>
  )
}

function ProgressRow({ label, value, total, tone = 'var(--accent)' }) {
  const pct = total ? Math.round((value / total) * 100) : 0
  return (
    <div className="progress-row">
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
      <div className="progress-track">
        <span style={{ width: `${pct}%`, background: tone }} />
      </div>
    </div>
  )
}

export default function Reports() {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getAgentReport()
      .then(setReport)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
        <Loader className="spin" size={32} />
      </div>
    )
  }

  if (!report) {
    return (
      <div className="empty-state">
        No se pudo cargar el reporte del agente preventista
      </div>
    )
  }

  const totalStatus = report.status_breakdown.reduce((sum, row) => sum + row.count, 0)
  const timelineMax = Math.max(...report.timeline.map(row => Math.max(row.orders, row.auto_messages)), 1)

  return (
    <>
      <div className="page-header">
        <h2>Reportes del agente</h2>
        <p>Indicadores del preventista: pedidos tomados, cierre y actividad automatizada</p>
      </div>

      <div className="cards-grid">
        <StatCard icon={Bot} label="Mensajes automaticos" value={report.summary.auto_messages} />
        <StatCard icon={MessageCircle} label="Promedio mensajes/pedido" value={report.summary.avg_messages_per_order} color="var(--info)" bg="var(--info-bg)" />
        <StatCard icon={Target} label="Pedidos con agente" value={report.summary.orders_with_agent} color="var(--warning)" bg="var(--warning-bg)" />
        <StatCard icon={CheckCircle2} label="Tasa de cierre efectivo" value={fmtPct(report.closing.close_rate)} color="var(--success)" bg="var(--success-bg)" />
      </div>

      <div className="cards-grid">
        <StatCard icon={Users} label="Clientes contactados" value={report.summary.customers_touched} />
        <StatCard icon={Store} label="Sucursales con pedidos" value={report.summary.active_stores} color="var(--success)" bg="var(--success-bg)" />
        <StatCard icon={TrendingUp} label="Pipeline abierto" value={fmtMoney(report.values.pipeline_value)} color="var(--info)" bg="var(--info-bg)" />
        <StatCard icon={Send} label="Participacion del agente" value={fmtPct(report.summary.agent_share)} color="var(--warning)" bg="var(--warning-bg)" />
      </div>

      <div className="report-grid">
        <section className="card report-panel">
          <div className="report-panel-header">
            <div>
              <h3>Embudo preventista</h3>
              <p>Del pedido tomado al cierre comercial</p>
            </div>
            <BarChart3 color="var(--accent-light)" />
          </div>
          <div className="funnel">
            <div>
              <span>Pedidos tomados</span>
              <strong>{report.summary.orders_taken}</strong>
            </div>
            <div>
              <span>Abiertos</span>
              <strong>{report.closing.open_orders}</strong>
            </div>
            <div>
              <span>Cerrados</span>
              <strong>{report.closing.closed_orders}</strong>
            </div>
            <div>
              <span>Confirmados</span>
              <strong>{report.closing.confirmed_orders}</strong>
            </div>
          </div>
          <div className="value-grid">
            <div>
              <span>Valor solicitado</span>
              <strong>{fmtMoney(report.values.total_value)}</strong>
            </div>
            <div>
              <span>Valor confirmado</span>
              <strong>{fmtMoney(report.values.confirmed_value)}</strong>
            </div>
            <div>
              <span>Valor rechazado</span>
              <strong>{fmtMoney(report.values.rejected_value)}</strong>
            </div>
          </div>
        </section>

        <section className="card report-panel">
          <div className="report-panel-header">
            <div>
              <h3>Estados de pedidos</h3>
              <p>Distribucion actual del trabajo comercial</p>
            </div>
          </div>
          <div className="progress-list">
            {report.status_breakdown.length === 0 ? (
              <div className="empty-state">Sin pedidos registrados</div>
            ) : report.status_breakdown.map(row => (
              <ProgressRow
                key={row.status}
                label={row.status}
                value={row.count}
                total={totalStatus}
                tone={row.status === 'confirmado' ? 'var(--success)' : row.status === 'rechazado' ? 'var(--danger)' : 'var(--accent)'}
              />
            ))}
          </div>
        </section>
      </div>

      <section className="card report-panel" style={{ marginBottom: 24 }}>
        <div className="report-panel-header">
          <div>
            <h3>Actividad del agente por dia</h3>
            <p>Pedidos creados versus mensajes automaticos enviados</p>
          </div>
        </div>
        <div className="timeline-bars">
          {report.timeline.length === 0 ? (
            <div className="empty-state">Sin actividad reciente</div>
          ) : report.timeline.map(row => (
            <div className="timeline-day" key={row.date}>
              <span>{row.date.slice(5)}</span>
              <div>
                <i className="orders-bar" style={{ height: `${Math.max((row.orders / timelineMax) * 100, row.orders ? 8 : 0)}%` }} />
                <i className="messages-bar" style={{ height: `${Math.max((row.auto_messages / timelineMax) * 100, row.auto_messages ? 8 : 0)}%` }} />
              </div>
            </div>
          ))}
        </div>
        <div className="legend">
          <span><i className="orders-dot" /> Pedidos</span>
          <span><i className="messages-dot" /> Mensajes automaticos</span>
        </div>
      </section>

      <div className="report-grid three-columns">
        <div className="table-container">
          <div className="table-header">
            <h3>Clientes con mayor actividad</h3>
          </div>
          <table>
            <thead>
              <tr>
                <th>Cliente</th>
                <th>Pedidos</th>
                <th>Valor</th>
              </tr>
            </thead>
            <tbody>
              {report.top_clients.length === 0 ? (
                <tr><td colSpan={3} className="empty-cell">Sin clientes</td></tr>
              ) : report.top_clients.map(client => (
                <tr key={client.client_id}>
                  <td>{client.client_name}</td>
                  <td>{client.orders}</td>
                  <td>{fmtMoney(client.value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="table-container">
          <div className="table-header">
            <h3>Sucursales mas atendidas</h3>
          </div>
          <table>
            <thead>
              <tr>
                <th>Sucursal</th>
                <th>Pedidos</th>
                <th>Valor</th>
              </tr>
            </thead>
            <tbody>
              {report.top_stores.length === 0 ? (
                <tr><td colSpan={3} className="empty-cell">Sin sucursales</td></tr>
              ) : report.top_stores.map(store => (
                <tr key={store.store_id}>
                  <td>{store.store_name}</td>
                  <td>{store.orders}</td>
                  <td>{fmtMoney(store.value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="table-container">
          <div className="table-header">
            <h3>Productos detectados</h3>
          </div>
          <table>
            <thead>
              <tr>
                <th>Producto</th>
                <th>Cant.</th>
                <th>Valor</th>
              </tr>
            </thead>
            <tbody>
              {report.top_products.length === 0 ? (
                <tr><td colSpan={3} className="empty-cell">Sin productos</td></tr>
              ) : report.top_products.map(product => (
                <tr key={product.product_id}>
                  <td>{product.product_name}</td>
                  <td>{product.quantity}</td>
                  <td>{fmtMoney(product.value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}
