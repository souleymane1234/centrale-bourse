import { Link } from 'react-router-dom';
import { Play } from 'lucide-react';
import { formatDateTime } from '../../utils/format';
import { newsBadgeClass } from '../../utils/newsBadges';

function MediaPreview({ item, featured }) {
  const imageSrc = item.thumbnail_url || item.image_url;
  if (!imageSrc && item.media_type !== 'video') {
    return null;
  }

  const isVideo = item.media_type === 'video';

  return (
    <div
      className={
        featured
          ? 'relative h-48 w-full shrink-0 overflow-hidden bg-slate-100 sm:h-56 md:h-auto md:min-h-[220px] md:w-[42%] lg:min-h-[260px]'
          : 'relative aspect-[16/10] w-full overflow-hidden bg-slate-100'
      }
    >
      {imageSrc ? (
        <img
          src={imageSrc}
          alt=""
          className="h-full w-full object-cover"
          loading="lazy"
        />
      ) : (
        <div className="flex h-full items-center justify-center text-sm text-slate-500">
          Vidéo
        </div>
      )}
      {isVideo ? (
        <span className="pointer-events-none absolute inset-0 flex items-center justify-center bg-black/25">
          <span
            className={`flex items-center justify-center rounded-full bg-white/95 shadow-lg ${
              featured ? 'h-16 w-16' : 'h-12 w-12'
            }`}
          >
            <Play
              className={`ml-0.5 fill-slate-900 text-slate-900 ${featured ? 'h-8 w-8' : 'h-6 w-6'}`}
              aria-hidden
            />
          </span>
        </span>
      ) : null}
    </div>
  );
}

function CardMeta({ item, compact }) {
  const publishedLabel = formatDateTime(item.published_at);

  return (
    <div className={`flex flex-wrap items-center gap-1.5 ${compact ? 'gap-1' : 'gap-2'}`}>
      <span
        className={`rounded-full px-2 py-0.5 font-semibold ${newsBadgeClass(item.badge_key)} ${
          compact ? 'text-[10px]' : 'text-xs'
        }`}
      >
        {item.badge}
      </span>
      {item.ticker ? (
        <span
          className={`rounded-full bg-slate-100 font-semibold text-slate-700 ${
            compact ? 'px-1.5 py-0.5 text-[10px]' : 'px-2.5 py-0.5 text-xs'
          }`}
        >
          {item.ticker}
        </span>
      ) : null}
      <span className={`text-slate-500 ${compact ? 'text-[10px]' : 'text-xs'}`}>{item.source}</span>
      <span className="text-slate-300">·</span>
      <time className={`text-slate-500 ${compact ? 'text-[10px]' : 'text-xs'}`} dateTime={item.published_at}>
        {publishedLabel}
      </time>
    </div>
  );
}

export default function NewsCard({ item, featured = false, className = '' }) {
  const detailPath = `/actualites/${item.slug}`;
  const compact = !featured;

  return (
    <article
      className={`overflow-hidden rounded-xl border border-slate-200 bg-white shadow-card transition hover:border-slate-300 ${className}`}
    >
      <Link
        to={detailPath}
        className={`block focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 ${
          featured ? 'md:flex md:min-h-[220px]' : ''
        }`}
      >
        {item.media_type ? <MediaPreview item={item} featured={featured} /> : null}

        <div
          className={`flex flex-1 flex-col justify-center ${
            featured ? 'p-4 sm:p-5 md:py-5 md:pr-6' : 'p-3.5 sm:p-4'
          }`}
        >
          <CardMeta item={item} compact={compact} />

          <h2
            className={`mt-2 font-bold leading-snug text-slate-900 ${
              featured ? 'text-xl sm:text-2xl' : 'text-base sm:text-lg'
            }`}
          >
            {item.title}
          </h2>

          {item.excerpt ? (
            <p
              className={`mt-1.5 leading-relaxed text-slate-600 ${
                featured ? 'line-clamp-3 text-sm sm:text-base' : 'line-clamp-2 text-sm'
              }`}
            >
              {item.excerpt}
            </p>
          ) : null}

          <span
            className={`mt-2 font-semibold text-brand-700 ${featured ? 'text-sm' : 'text-xs sm:text-sm'}`}
          >
            Lire la suite →
          </span>
        </div>
      </Link>
    </article>
  );
}
