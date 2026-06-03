import { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import { formatCurrency } from '../../utils/format';

export default function AlertFormModal({ open, onClose, ticker, companyName, currentPrice, onSubmit }) {
  const [direction, setDirection] = useState('above');
  const [targetPrice, setTargetPrice] = useState('');
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!open) return;
    setDirection('above');
    setTargetPrice(currentPrice != null ? String(Math.round(currentPrice)) : '');
    setNote('');
    setError(null);
  }, [open, currentPrice, ticker]);

  if (!open) return null;

  const handleSubmit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await onSubmit({
        ticker,
        direction,
        target_price: Number(targetPrice),
        note: note.trim() || undefined,
      });
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/50 p-4 sm:items-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="alert-modal-title"
    >
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 id="alert-modal-title" className="text-lg font-bold text-slate-900">
              Nouvelle alerte
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              {companyName} ({ticker})
              {currentPrice != null ? ` · cours ${formatCurrency(currentPrice)}` : ''}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            aria-label="Fermer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div>
            <span className="text-xs font-semibold uppercase text-slate-500">Condition</span>
            <div className="mt-2 flex gap-2">
              <button
                type="button"
                onClick={() => setDirection('above')}
                className={`flex-1 rounded-lg border px-3 py-2 text-sm font-semibold ${
                  direction === 'above'
                    ? 'border-brand-500 bg-brand-50 text-brand-800'
                    : 'border-slate-200 text-slate-600'
                }`}
              >
                Au-dessus de
              </button>
              <button
                type="button"
                onClick={() => setDirection('below')}
                className={`flex-1 rounded-lg border px-3 py-2 text-sm font-semibold ${
                  direction === 'below'
                    ? 'border-brand-500 bg-brand-50 text-brand-800'
                    : 'border-slate-200 text-slate-600'
                }`}
              >
                En dessous de
              </button>
            </div>
          </div>

          <div>
            <label htmlFor="target-price" className="text-xs font-semibold uppercase text-slate-500">
              Prix cible (FCFA)
            </label>
            <input
              id="target-price"
              type="number"
              min="1"
              step="1"
              required
              value={targetPrice}
              onChange={(e) => setTargetPrice(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </div>

          <div>
            <label htmlFor="alert-note" className="text-xs font-semibold uppercase text-slate-500">
              Note (optionnel)
            </label>
            <input
              id="alert-note"
              type="text"
              maxLength={255}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </div>

          <p className="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-600">
            L&apos;alerte est visible dans Suivi dès que le cours atteint le seuil. Les notifications
            email et SMS arrivent prochainement.
          </p>

          {error ? <p className="text-sm text-rose-700">{error}</p> : null}

          <div className="flex gap-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-xl border border-slate-200 py-2.5 text-sm font-semibold text-slate-700"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={busy}
              className="flex-1 rounded-xl bg-brand-600 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-60"
            >
              {busy ? 'Enregistrement…' : 'Créer l’alerte'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
