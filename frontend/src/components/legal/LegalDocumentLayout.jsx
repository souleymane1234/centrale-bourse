import { Link } from 'react-router-dom';
import logo from '../../assets/logo.png';
import { BRAND_NAME } from '../../config/brand';

export default function LegalDocumentLayout({ title, children }) {
  return (
    <div className="min-h-screen bg-[#f4f7fa]">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex h-16 max-w-3xl items-center justify-between px-4 sm:px-6">
          <Link to="/bienvenue" className="flex items-center gap-2.5">
            <img src={logo} alt={BRAND_NAME} className="h-9 w-9 object-contain" />
            <span className="text-sm font-bold text-slate-900">{BRAND_NAME}</span>
          </Link>
          <Link
            to="/bienvenue"
            className="text-sm font-medium text-slate-600 hover:text-slate-900"
          >
            Retour
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-10 sm:px-6 sm:py-14">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">{title}</h1>
        <p className="mt-2 text-sm text-slate-500">
          Dernière mise à jour : {new Date().toLocaleDateString('fr-FR')}
        </p>
        <div className="prose-legal mt-8 space-y-6 text-sm leading-relaxed text-slate-700">
          {children}
        </div>
        <footer className="mt-12 flex flex-wrap gap-4 border-t border-slate-200 pt-6 text-xs text-slate-500">
          <Link to="/cgu" className="hover:text-slate-800">
            CGU
          </Link>
          <Link to="/confidentialite" className="hover:text-slate-800">
            Confidentialité
          </Link>
          <Link to="/bienvenue" className="hover:text-slate-800">
            Accueil
          </Link>
        </footer>
      </main>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section>
      <h2 className="text-base font-bold text-slate-900">{title}</h2>
      <div className="mt-2 space-y-2">{children}</div>
    </section>
  );
}

export { Section };
