import { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';

export default function ProfileInfoSection() {
  const { user, saveProfile } = useAuth();
  const [form, setForm] = useState({
    full_name: '',
    phone: '',
    password: '',
  });

  useEffect(() => {
    setForm((prev) => ({
      ...prev,
      full_name: user?.full_name || '',
      phone: user?.phone || '',
    }));
  }, [user?.full_name, user?.phone]);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const onSubmit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setMessage(null);
    setError(null);
    try {
      const payload = {
        full_name: form.full_name,
        phone: form.phone,
      };
      if (form.password) {
        payload.password = form.password;
      }
      await saveProfile(payload);
      setMessage('Profil mis à jour.');
      setForm((prev) => ({ ...prev, password: '' }));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="card">
      <h2 className="text-lg font-bold text-slate-900">Informations personnelles</h2>
      <form onSubmit={onSubmit} className="mt-4 space-y-3">
        <label className="block text-sm">
          <span className="text-slate-500">Email</span>
          <input
            disabled
            value={user?.email || ''}
            className="mt-1 w-full rounded-xl border border-slate-100 bg-slate-50 px-3 py-2.5 text-slate-600"
          />
        </label>
        <label className="block text-sm">
          <span className="text-slate-500">Nom complet</span>
          <input
            value={form.full_name}
            onChange={(e) => setForm((p) => ({ ...p, full_name: e.target.value }))}
            className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
          />
        </label>
        <label className="block text-sm">
          <span className="text-slate-500">Téléphone</span>
          <input
            value={form.phone}
            onChange={(e) => setForm((p) => ({ ...p, phone: e.target.value }))}
            className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
          />
        </label>
        <label className="block text-sm">
          <span className="text-slate-500">Nouveau mot de passe (optionnel)</span>
          <input
            type="password"
            value={form.password}
            onChange={(e) => setForm((p) => ({ ...p, password: e.target.value }))}
            placeholder="Laisser vide pour ne pas changer"
            className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
          />
        </label>

        {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
        {error ? <p className="text-sm text-rose-700">{error}</p> : null}

        <button
          type="submit"
          disabled={busy}
          className="rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {busy ? 'Enregistrement...' : 'Enregistrer'}
        </button>
      </form>
    </section>
  );
}
