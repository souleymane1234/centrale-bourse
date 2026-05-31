export default function LandingFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className="border-t border-slate-200 bg-white py-8">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 px-4 text-xs font-medium uppercase tracking-wide text-slate-500 sm:flex-row sm:px-6 lg:px-8">
        <p>© {year} BRVM Agent. Tous droits réservés.</p>
        <p className="sm:text-right">Un produit de KS Solution</p>
      </div>
    </footer>
  );
}
