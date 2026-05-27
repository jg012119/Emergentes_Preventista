import { useEffect, useState } from 'react'
import { Loader, Mail, Phone, Save, UserRound } from 'lucide-react'
import { getProfile, updateProfile } from '../services/api'

export default function Profile() {
  const [profile, setProfile] = useState(null)
  const [form, setForm] = useState({ name: '', phone: '' })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    getProfile()
      .then((data) => {
        setProfile(data)
        setForm({ name: data.name || '', phone: data.phone || '' })
      })
      .catch((err) => setError(err.message || 'No se pudo cargar el perfil'))
      .finally(() => setLoading(false))
  }, [])

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSaving(true)
    setMessage('')
    setError('')
    try {
      const updated = await updateProfile(form)
      setProfile(updated)
      setForm({ name: updated.name || '', phone: updated.phone || '' })
      setMessage('Perfil actualizado correctamente')
    } catch (err) {
      setError(err.message || 'No se pudo actualizar el perfil')
    } finally {
      setSaving(false)
    }
  }

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
        <h2>Perfil</h2>
        <p>Datos de la cuenta que usa el panel de administrador</p>
      </div>

      <div className="profile-layout">
        <section className="card profile-card">
          <div className="profile-avatar">
            <UserRound size={34} />
          </div>
          <h3>{profile?.name || 'Administrador'}</h3>
          <p>{profile?.email}</p>
          <div className="profile-meta">
            <span><Mail size={15} /> {profile?.email || '-'}</span>
            <span><Phone size={15} /> {profile?.phone || '-'}</span>
          </div>
        </section>

        <form className="card profile-form" onSubmit={handleSubmit}>
          <h3>Editar datos</h3>
          {message ? <div className="success-text">{message}</div> : null}
          {error ? <div className="error-text">{error}</div> : null}

          <div className="form-group">
            <label htmlFor="profile-name">Nombre</label>
            <input
              id="profile-name"
              value={form.name}
              onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
              placeholder="Nombre del administrador"
            />
          </div>

          <div className="form-group">
            <label htmlFor="profile-email">Correo electronico</label>
            <input id="profile-email" value={profile?.email || ''} disabled />
          </div>

          <div className="form-group">
            <label htmlFor="profile-phone">Telefono</label>
            <input
              id="profile-phone"
              value={form.phone}
              onChange={(event) => setForm((prev) => ({ ...prev, phone: event.target.value }))}
              placeholder="Telefono de contacto"
            />
          </div>

          <button className="btn btn-primary" type="submit" disabled={saving}>
            <Save size={16} />
            {saving ? 'Guardando...' : 'Guardar cambios'}
          </button>
        </form>
      </div>
    </>
  )
}
