import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, ExternalLink } from 'lucide-react';
import { fetchNewsArticle } from '../api/client';
import Spinner from '../components/Spinner';
import { formatDateTime } from '../utils/format';
import { newsBadgeClass } from '../utils/newsBadges';
import { companyPath } from '../utils/routing';

function ArticleMedia({ article, className = '' }) {
  if (article.media_type === 'video' && article.video_url) {
    return (
      <div className={`aspect-video w-full overflow-hidden rounded-xl bg-black ${className}`}>
        <iframe
          title={article.title}
          src={article.video_url}
          className="h-full w-full border-0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        />
      </div>
    );
  }

  if (article.image_url) {
    return (
      <img
        src={article.image_url}
        alt=""
        className={`w-full rounded-xl object-cover ${className}`}
      />
    );
  }

  return null;
}

function ArticleBody({ article }) {
  if (article.body_html) {
    return (
      <div
        className="prose prose-slate max-w-none text-slate-700 prose-p:leading-relaxed"
        dangerouslySetInnerHTML={{ __html: article.body_html }}
      />
    );
  }

  const paragraphs = (article.body || '').split(/\n\n+/).filter(Boolean);
  return (
    <div className="columns-1 gap-8 text-base leading-relaxed text-slate-700 lg:columns-2">
      {paragraphs.map((paragraph, index) => (
        <p key={index} className="mb-4 break-inside-avoid">
          {paragraph}
        </p>
      ))}
    </div>
  );
}

function ArticleSidebar({ article }) {
  return (
    <aside className="space-y-4 lg:sticky lg:top-4 lg:self-start">
      <div className="flex flex-wrap gap-2">
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${newsBadgeClass(article.badge_key)}`}
        >
          {article.badge}
        </span>
        {article.ticker ? (
          <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700">
            {article.ticker}
          </span>
        ) : null}
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-card">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Publication</p>
        <time className="mt-1 block text-sm font-medium text-slate-900" dateTime={article.published_at}>
          {formatDateTime(article.published_at)}
        </time>
        {article.author ? (
          <>
            <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Auteur</p>
            <p className="mt-1 text-sm font-medium text-slate-900">{article.author}</p>
          </>
        ) : null}
        <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Source</p>
        <p className="mt-1 text-sm font-medium text-slate-900">{article.source}</p>
        {article.ticker ? (
          <>
            <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Société</p>
            <Link
              to={companyPath(article.ticker)}
              className="mt-1 inline-block text-sm font-bold text-brand-700 hover:underline"
            >
              Voir {article.ticker}
            </Link>
          </>
        ) : null}
      </div>

      {article.source_url ? (
        <a
          href={article.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-2 rounded-xl border border-brand-200 bg-brand-50 px-4 py-3 text-sm font-semibold text-brand-800 hover:bg-brand-100"
        >
          <ExternalLink className="h-4 w-4" />
          Source officielle
        </a>
      ) : null}
    </aside>
  );
}

export default function NewsDetailPage() {
  const { slug } = useParams();
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchNewsArticle(slug);
        if (!cancelled) {
          setArticle(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Actualité introuvable.');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [slug]);

  if (loading) {
    return <Spinner label="Chargement de l'article..." />;
  }

  if (error || !article) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
        <div className="card mx-auto max-w-lg text-center text-sm text-rose-700">
          <p>{error || 'Article introuvable.'}</p>
          <Link
            to="/actualites"
            className="mt-4 inline-flex items-center gap-1 font-semibold text-brand-700 hover:underline"
          >
            <ArrowLeft className="h-4 w-4" />
            Retour au fil
          </Link>
        </div>
      </div>
    );
  }

  const hasMedia = article.media_type || article.image_url;

  return (
    <div className="mx-auto max-w-7xl px-4 py-5 sm:px-6 lg:py-6">
      <Link
        to="/actualites"
        className="mb-4 inline-flex items-center gap-1 text-sm font-semibold text-brand-700 hover:text-brand-800"
      >
        <ArrowLeft className="h-4 w-4" />
        Actualités
      </Link>

      <div className="lg:grid lg:grid-cols-[1fr_280px] lg:gap-6 xl:grid-cols-[1fr_300px]">
        <article className="min-w-0 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-card">
          <div className="border-b border-slate-100 p-4 sm:p-5 lg:hidden">
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${newsBadgeClass(article.badge_key)}`}
              >
                {article.badge}
              </span>
              {article.ticker ? (
                <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700">
                  {article.ticker}
                </span>
              ) : null}
            </div>
            <h1 className="mt-3 text-2xl font-bold leading-tight text-slate-900">{article.title}</h1>
            <p className="mt-2 text-sm text-slate-500">
              {article.author ? `${article.author} · ` : ''}
              <time dateTime={article.published_at}>{formatDateTime(article.published_at)}</time>
            </p>
          </div>

          {hasMedia && (
            <div className="border-b border-slate-100 p-4 sm:p-5">
              <ArticleMedia article={article} className="max-h-[min(52vh,480px)]" />
            </div>
          )}

          <div className="hidden border-b border-slate-100 p-5 lg:block">
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${newsBadgeClass(article.badge_key)}`}
              >
                {article.badge}
              </span>
              {article.ticker ? (
                <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700">
                  {article.ticker}
                </span>
              ) : null}
            </div>
            <h1 className="mt-3 text-3xl font-bold leading-tight text-slate-900 xl:text-4xl">
              {article.title}
            </h1>
            {article.excerpt ? (
              <p className="mt-3 text-lg font-medium text-slate-700">{article.excerpt}</p>
            ) : null}
          </div>

          <div className="p-4 sm:p-5 lg:p-6">
            {article.excerpt && (
              <p className="mb-4 text-base font-medium text-slate-700 lg:hidden">{article.excerpt}</p>
            )}
            <ArticleBody article={article} />
          </div>
        </article>

        <div className="mt-4 hidden lg:mt-0 lg:block">
          <ArticleSidebar article={article} />
        </div>
      </div>

      <div className="mt-4 lg:hidden">
        {article.source_url ? (
          <a
            href={article.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-2 rounded-xl border border-brand-200 bg-brand-50 px-4 py-3 text-sm font-semibold text-brand-800"
          >
            <ExternalLink className="h-4 w-4" />
            Source officielle
          </a>
        ) : null}
      </div>
    </div>
  );
}
