import NewsFeed from '../components/news/NewsFeed';

export default function NewsPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-5 sm:px-6 lg:py-6">
      <header className="mb-4 flex flex-col gap-1 sm:mb-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 lg:text-3xl">Actualités</h1>
          <p className="mt-0.5 text-sm text-slate-600 lg:text-base">
            Marché BRVM, communiqués des sociétés cotées et annonces importantes.
          </p>
        </div>
      </header>

      <NewsFeed />
    </div>
  );
}
