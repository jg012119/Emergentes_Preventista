import { useEffect, useState } from 'react'
import { Plus, Edit, Trash2, X } from 'lucide-react'
import { getProducts, createProduct, updateProduct, deleteProduct } from '../services/api'

const EMPTY = { name: '', category: 'Bebidas', price: 0, stock: 0, active: true }

export default function Products() {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState(null) // null | 'create' | 'edit'
  const [form, setForm] = useState({ ...EMPTY })
  const [editId, setEditId] = useState(null)
  const [saving, setSaving] = useState(false)

  const load = () => {
    setLoading(true)
    getProducts()
      .then(setProducts)
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const openCreate = () => {
    setForm({ ...EMPTY })
    setEditId(null)
    setModal('create')
  }

  const openEdit = (p) => {
    setForm({ name: p.name, category: p.category, price: p.price, stock: p.stock, active: p.active })
    setEditId(p.id)
    setModal('edit')
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      if (modal === 'create') {
        await createProduct({ ...form, price: Number(form.price), stock: Number(form.stock) })
      } else {
        await updateProduct(editId, { ...form, price: Number(form.price), stock: Number(form.stock) })
      }
      setModal(null)
      load()
    } catch (err) {
      alert(err.message)
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id, name) => {
    if (!confirm(`¿Desactivar el producto "${name}"?`)) return
    try {
      await deleteProduct(id)
      load()
    } catch (err) {
      alert(err.message)
    }
  }

  return (
    <>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2>Productos</h2>
          <p>Catálogo de productos AJE</p>
        </div>
        <button className="btn btn-primary" onClick={openCreate}>
          <Plus size={18} /> Nuevo producto
        </button>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Categoría</th>
              <th>Precio</th>
              <th>Stock</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>Cargando...</td></tr>
            ) : products.length === 0 ? (
              <tr><td colSpan={6} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>No hay productos</td></tr>
            ) : (
              products.map(p => (
                <tr key={p.id}>
                  <td style={{ fontWeight: 500 }}>{p.name}</td>
                  <td><span className="badge" style={{ background: 'var(--accent-bg)', color: 'var(--accent-light)' }}>{p.category}</span></td>
                  <td>Bs {Number(p.price).toFixed(2)}</td>
                  <td style={{ fontWeight: 600, color: p.stock < 10 ? 'var(--danger)' : 'var(--success)' }}>{p.stock}</td>
                  <td>
                    <span className={`badge ${p.active ? 'badge-confirmado' : 'badge-rechazado'}`}>
                      {p.active ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td>
                    <div className="btn-group">
                      <button className="btn btn-ghost btn-sm" onClick={() => openEdit(p)}><Edit size={14} /></button>
                      <button className="btn btn-ghost btn-sm" onClick={() => handleDelete(p.id, p.name)} style={{ color: 'var(--danger)' }}>
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {modal && (
        <div className="modal-overlay" onClick={() => setModal(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3>{modal === 'create' ? 'Nuevo Producto' : 'Editar Producto'}</h3>
              <button className="btn btn-ghost btn-sm" onClick={() => setModal(null)}><X size={18} /></button>
            </div>
            <form onSubmit={handleSave}>
              <div className="form-group">
                <label>Nombre</label>
                <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
              </div>
              <div className="form-group">
                <label>Categoría</label>
                <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                  <option>Bebidas</option>
                  <option>Hidratantes</option>
                  <option>Jugos</option>
                  <option>Energizantes</option>
                  <option>Agua</option>
                  <option>Té</option>
                  <option>General</option>
                </select>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div className="form-group">
                  <label>Precio (Bs)</label>
                  <input type="number" step="0.01" min="0" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} required />
                </div>
                <div className="form-group">
                  <label>Stock</label>
                  <input type="number" min="0" value={form.stock} onChange={(e) => setForm({ ...form, stock: e.target.value })} required />
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-ghost" onClick={() => setModal(null)}>Cancelar</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Guardando...' : 'Guardar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}
