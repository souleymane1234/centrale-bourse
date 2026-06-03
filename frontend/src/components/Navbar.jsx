import { NavLink } from 'react-router-dom';
import { GitCompareArrows, Home, Newspaper, Star, User } from 'lucide-react';
import logo from '../assets/logo.png';
import { BRAND_NAME, BRAND_TAGLINE } from '../config/brand';

const links = [
  { to: '/', label: 'Accueil', shortLabel: 'Accueil', end: true, Icon: Home },
  { to: '/actualites', label: 'Actualités', shortLabel: 'Actus', Icon: Newspaper },
  { to: '/comparer', label: 'Comparer actions', shortLabel: 'Comparer', Icon: GitCompareArrows },
  { to: '/suivi', label: 'Suivi', shortLabel: 'Suivi', Icon: Star },
  { to: '/profil', label: 'Profil', shortLabel: 'Profil', Icon: User },
];

function LogoLink({ compact = false }) {
  return (
    <NavLink
      to="/"
      className="group flex shrink-0 items-center gap-2.5 rounded-xl py-1 transition hover:opacity-90"
    >
      <img
        src={logo}
        alt={BRAND_NAME}
        className="h-9 w-9 object-contain transition group-hover:opacity-90 md:h-10 md:w-10"
      />
      {!compact && (
        <div className="leading-tight">
          <span className="block text-base font-bold tracking-tight text-slate-900">{BRAND_NAME}</span>
          <span className="block text-[11px] font-medium text-slate-500">{BRAND_TAGLINE}</span>
        </div>
      )}
    </NavLink>
  );
}

function DesktopNavLink({ link }) {
  const { Icon } = link;
  return (
    <NavLink
      to={link.to}
      end={link.end}
      className={({ isActive }) =>
        [
          'flex items-center gap-2 whitespace-nowrap rounded-lg px-3.5 py-2 text-sm font-medium transition-all duration-200',
          isActive
            ? 'bg-white text-brand-700 shadow-sm ring-1 ring-slate-200/80'
            : 'text-slate-600 hover:bg-white/60 hover:text-slate-900',
        ].join(' ')
      }
    >
      <Icon className="h-4 w-4 shrink-0" strokeWidth={2} aria-hidden />
      {link.label}
    </NavLink>
  );
}

function MobileNavLink({ link }) {
  const { Icon } = link;
  return (
    <NavLink
      to={link.to}
      end={link.end}
      className={({ isActive }) =>
        [
          'flex flex-1 flex-col items-center justify-center gap-0.5 px-1 py-2 text-[10px] font-medium transition-colors',
          isActive ? 'text-brand-600' : 'text-slate-500 hover:text-slate-800',
        ].join(' ')
      }
    >
      {({ isActive }) => (
        <>
          <span
            className={[
              'flex h-9 w-9 items-center justify-center rounded-xl transition-colors',
              isActive ? 'bg-brand-50' : 'bg-transparent',
            ].join(' ')}
          >
            <Icon className="h-5 w-5 shrink-0" strokeWidth={isActive ? 2.25 : 2} aria-hidden />
          </span>
          <span className="max-w-[4.5rem] truncate">{link.shortLabel}</span>
        </>
      )}
    </NavLink>
  );
}

export default function Navbar() {
  return (
    <>
      {/* Barre supérieure : logo seul sur mobile, navigation complète sur desktop */}
      <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/95 shadow-sm backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 md:h-16">
          <div className="md:hidden">
            <LogoLink compact />
          </div>
          <div className="hidden md:block">
            <LogoLink />
          </div>

          <nav className="hidden md:block" aria-label="Navigation principale">
            <ul className="flex items-center gap-0.5 rounded-xl bg-slate-100/90 p-1 lg:gap-1">
              {links.map((link) => (
                <li key={link.to}>
                  <DesktopNavLink link={link} />
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </header>

      {/* Bottom bar — mobile uniquement */}
      <nav
        className="fixed inset-x-0 bottom-0 z-50 border-t border-slate-200/90 bg-white/95 shadow-[0_-4px_24px_rgba(15,23,42,0.08)] backdrop-blur-md md:hidden"
        aria-label="Navigation mobile"
        style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
      >
        <ul className="mx-auto flex h-16 max-w-lg items-stretch">
          {links.map((link) => (
            <li key={link.to} className="flex min-w-0 flex-1">
              <MobileNavLink link={link} />
            </li>
          ))}
        </ul>
      </nav>
    </>
  );
}
