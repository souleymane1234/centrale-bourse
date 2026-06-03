import { Link } from 'react-router-dom';
import { BRAND_NAME } from '../../config/brand';

export default function LandingFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className="border-t border-slate-200 bg-white py-8">
      <div className="mx-auto flex max-w-7xl flex-col items-center gap-4 px-4 text-xs font-medium uppercase tracking-wide text-slate-500 sm:flex-row sm:justify-between sm:px-6 lg:px-8">
        <p>© {year} {BRAND_NAME}. Tous droits réservés.</p>
        <nav className="flex flex-wrap items-center justify-center gap-4 normal-case tracking-normal">
          <Link to="/cgu" className="hover:text-slate-800">
            CGU
          </Link>
          <Link to="/confidentialite" className="hover:text-slate-800">
            Confidentialité
          </Link>
        </nav>
        <p className="sm:text-right">Un produit de KS Solution</p>
      </div>
    </footer>
  );
}
