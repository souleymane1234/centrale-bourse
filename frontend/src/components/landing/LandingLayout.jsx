import { Link, Outlet, useLocation } from 'react-router-dom';
import { Moon } from 'lucide-react';
import logo from '../../assets/logo.svg';

const NAV_LINKS = [
  { hash: '#fonctionnalites', label: 'Fonctionnalités' },
  { hash: '#tarifs', label: 'Tarification' },
  { hash: '#faq', label: 'FAQ' },
];

function NavAnchor({ hash, label, pathname }) {
  const href = pathname === '/bienvenue' ? hash : `/bienvenue${hash}`;

  return (
    <a
      href={href}
      className="text-sm font-medium text-slate-600 transition hover:text-slate-900"
    >
      {label}
    </a>
  );
}

export default function LandingLayout() {
  const { pathname } = useLocation();

  return (
    <div className="min-h-screen bg-[#f4f7fa]">
      <header className="sticky top-0 z-50 border-b border-slate-200/90 bg-white">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
          <Link to="/bienvenue" className="flex shrink-0 items-center gap-2.5">
            <img
              src={logo}
              alt=""
              className="h-9 w-9 rounded-lg bg-amber-400 object-contain p-1 ring-1 ring-amber-500/30"
            />
            <span className="text-base font-bold text-slate-900">BRVM Agent</span>
          </Link>

          <nav className="flex items-center gap-4 sm:gap-6 lg:gap-8">
            <div className="hidden items-center gap-6 md:flex lg:gap-8">
              {NAV_LINKS.map((item) => (
                <NavAnchor
                  key={item.hash}
                  hash={item.hash}
                  label={item.label}
                  pathname={pathname}
                />
              ))}
            </div>

            <div className="flex items-center gap-3 sm:gap-4">
              <button
                type="button"
                aria-label="Mode sombre (bientôt disponible)"
                className="hidden rounded-lg p-2 text-slate-600 transition hover:bg-slate-100 hover:text-slate-900 sm:inline-flex"
                disabled
              >
                <Moon className="h-5 w-5" strokeWidth={1.75} aria-hidden />
              </button>
              <span
                className="hidden text-sm font-medium text-slate-500 sm:inline"
                aria-label="Langue : français"
              >
                FR
              </span>
              <Link
                to="/profil"
                className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
              >
                Commencer
              </Link>
            </div>
          </nav>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
