import { useCallback, useEffect, useState } from 'react';
import { fetchNews } from '../../api/client';
import Spinner from '../Spinner';
import NewsCard from './NewsCard';

export default function NewsFeed() {
  const [items, setItems] = useState([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState(null);

  const loadPage = useCallback(async (pageNumber, append) => {
    if (append) {
      setLoadingMore(true);
    } else {
      setLoading(true);
    }
    setError(null);
    try {
      const data = await fetchNews(pageNumber);
      setItems((prev) => (append ? [...prev, ...(data.items || [])] : data.items || []));
      setHasMore(Boolean(data.has_more));
      setPage(data.page || pageNumber);
    } catch (err) {
      setError(err.message || 'Impossible de charger les actualités.');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, []);

  useEffect(() => {
    loadPage(1, false);
  }, [loadPage]);

  if (loading) {
    return <Spinner label="Chargement des actualités..." />;
  }

  if (error) {
    return (
      <div className="card text-center text-sm text-rose-700">
        <p>{error}</p>
        <button
          type="button"
          onClick={() => loadPage(1, false)}
          className="mt-4 rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
        >
          Réessayer
        </button>
      </div>
    );
  }

  if (!items.length) {
    return (
      <div className="card text-center text-sm text-slate-600">
        Aucune actualité pour le moment.
      </div>
    );
  }

  return (
    <div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4 xl:grid-cols-3">
        {items.map((item, index) => {
          const isFeatured = page === 1 && index === 0;
          return (
            <NewsCard
              key={item.id || item.slug}
              item={item}
              featured={isFeatured}
              className={isFeatured ? 'sm:col-span-2 xl:col-span-3' : ''}
            />
          );
        })}
      </div>

      {hasMore ? (
        <div className="mt-4 flex justify-center sm:mt-5">
          <button
            type="button"
            disabled={loadingMore}
            onClick={() => loadPage(page + 1, true)}
            className="rounded-xl border border-slate-200 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50 disabled:opacity-60"
          >
            {loadingMore ? 'Chargement...' : 'Voir plus d\'actualités'}
          </button>
        </div>
      ) : null}
    </div>
  );
}
