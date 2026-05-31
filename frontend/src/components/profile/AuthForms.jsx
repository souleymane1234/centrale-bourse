import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';

export default function AuthForms() {
  const { login, register } = useAuth();
  const [mode, setMode] = useState('login');
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({
    email: '',
    password: '',
    full_name: '',
    phone: '',
    referral_code: '',
  });

  const onChange = (event) => {
    setForm((prev) => ({ ...prev, [event.target.name]: event.target.value }));
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (mode === 'login') {
        await login(form.email, form.password);
      } else {
        await register({
          email: form.email,
          password: form.password,
          full_name: form.full_name,
          phone: form.phone,
          referral_code: form.referral_code || undefined,
        });
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="card max-w-lg">
      <div className="flex gap-2 rounded-xl bg-slate-100 p-1">
        <button
          type="button"
          onClick={() => setMode('login')}
          className={`flex-1 rounded-lg py-2 text-sm font-semibold ${
            mode === 'login' ? 'bg-white text-brand-700 shadow-sm' : 'text-slate-600'
          }`}
        >
          Connexion
        </button>
        <button
          type="button"
          onClick={() => setMode('register')}
          className={`flex-1 rounded-lg py-2 text-sm font-semibold ${
            mode === 'register' ? 'bg-white text-brand-700 shadow-sm' : 'text-slate-600'
          }`}
        >
          Créer un compte
        </button>
      </div>

      <p className="mt-4 text-sm text-slate-600">
        {mode === 'register'
          ? '5 jours d\'accès offerts à l\'inscription, puis abonnement mensuel.'
          : 'Connectez-vous pour gérer votre abonnement et votre parrainage.'}
      </p>

      <form onSubmit={onSubmit} className="mt-5 space-y-3">
        {mode === 'register' && (
          <>
            <input
              name="full_name"
              placeholder="Nom complet"
              value={form.full_name}
              onChange={onChange}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
            />
            <input
              name="phone"
              placeholder="Téléphone (optionnel)"
              value={form.phone}
              onChange={onChange}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
            />
            <input
              name="referral_code"
              placeholder="Code parrain (optionnel)"
              value={form.referral_code}
              onChange={onChange}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm uppercase focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
            />
          </>
        )}
        <input
          name="email"
          type="email"
          required
          placeholder="Email"
          value={form.email}
          onChange={onChange}
          className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
        />
        <input
          name="password"
          type="password"
          required
          minLength={8}
          placeholder="Mot de passe (8 caractères min.)"
          value={form.password}
          onChange={onChange}
          className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-200"
        />

        {error ? (
          <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>
        ) : null}

        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-xl bg-brand-600 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
        >
          {busy ? 'Patientez...' : mode === 'login' ? 'Se connecter' : 'Créer mon compte'}
        </button>
      </form>
    </section>
  );
}
