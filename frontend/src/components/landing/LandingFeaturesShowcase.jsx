import {
  BarChart3,
  GitCompareArrows,
  Landmark,
  LineChart,
  Newspaper,
  PieChart,
  Rows3,
  Trophy,
} from 'lucide-react';

import imgCharts from '../../assets/landing/feature-charts.png';
import imgCompanies from '../../assets/landing/feature-companies.png';
import imgCompareSector from '../../assets/landing/feature-compare-sector.png';
import imgFinancials from '../../assets/landing/feature-financials.png';
import imgHeadToHead from '../../assets/landing/feature-head-to-head.png';
import imgNews from '../../assets/landing/feature-news.png';
import imgRankings from '../../assets/landing/feature-rankings.png';
import imgTechnical from '../../assets/landing/feature-technical.png';

const FEATURES = [
  {
    Icon: Rows3,
    title: 'Sociétés cotées à la BRVM',
    description:
      'Retrouvez toutes les valeurs de la cote avec cours du jour, variation, secteur et accès rapide à la fiche détaillée de chaque société.',
    image: imgCompanies,
    imageAlt: 'Grille des sociétés cotées avec cours et variations',
  },
  {
    Icon: LineChart,
    title: 'Courbes et variations',
    description:
      'Suivez l’évolution des prix en temps réel : ouverture, plus haut, plus bas, volume et historique graphique pour chaque titre.',
    image: imgCharts,
    imageAlt: 'Graphique de cours et indicateurs de séance',
    reverse: true,
  },
  {
    Icon: BarChart3,
    title: 'Analyse technique',
    description:
      'Moyennes mobiles SMA 20 et 50, RSI (14) et MACD sur des graphiques clairs pour repérer tendances et signaux.',
    image: imgTechnical,
    imageAlt: 'Analyse technique SMA, RSI et MACD',
  },
  {
    Icon: PieChart,
    title: 'Structure du capital & indicateurs financiers',
    description:
      'Structure du capital, tableau des indicateurs sur 5 ans, évolution du chiffre d’affaires et du résultat net — extraits des rapports officiels.',
    image: imgFinancials,
    imageAlt: 'Structure du capital et évolutions financières',
    reverse: true,
  },
  {
    Icon: Newspaper,
    title: 'Actualités boursières',
    description:
      'Fil d’actualités du marché BRVM, communiqués des sociétés cotées et annonces importantes pour rester informé.',
    image: imgNews,
    imageAlt: 'Fil d’actualités boursières',
  },
  {
    Icon: GitCompareArrows,
    title: 'Comparaison par secteur',
    description:
      'Comparez les sociétés d’un même secteur : KPI en lignes, valeurs en colonnes, regroupés par thème comme sur les plateformes pro.',
    image: imgCompareSector,
    imageAlt: 'Comparaison des sociétés par secteur',
    reverse: true,
  },
  {
    Icon: Landmark,
    title: 'Comparer 2 actions du même secteur',
    description:
      'Choisissez un secteur puis deux sociétés : tableau face-à-face, critères gagnants et score investisseur calculé vs les pairs du secteur.',
    image: imgHeadToHead,
    imageAlt: 'Comparaison détaillée entre deux entreprises',
  },
  {
    Icon: Trophy,
    title: 'Classement par secteur',
    description:
      'Palmarès sectoriels : meilleur rendement dividende, croissance du CA (CAGR 5 ans), marge nette et autres classements par secteur.',
    image: imgRankings,
    imageAlt: 'Classements par secteur',
    reverse: true,
  },
];

function FeatureRow({ Icon, title, description, image, imageAlt, reverse = false }) {
  const textBlock = (
    <div className="flex max-w-xl flex-col justify-center">
      <span className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl border border-slate-200 bg-white shadow-sm">
        <Icon className="h-6 w-6 text-slate-700" strokeWidth={1.75} aria-hidden />
      </span>
      <h3 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">{title}</h3>
      <p className="mt-4 text-base leading-relaxed text-slate-600 sm:text-lg">{description}</p>
    </div>
  );

  const imageBlock = (
    <div className="relative">
      <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white p-2 shadow-[0_20px_50px_-20px_rgba(15,23,42,0.15)]">
        <img src={image} alt={imageAlt} className="block h-auto w-full rounded-xl" loading="lazy" />
      </div>
    </div>
  );

  return (
    <div className="grid items-center gap-10 lg:grid-cols-2 lg:gap-16">
      {reverse ? (
        <>
          <div className="order-2 lg:order-1">{imageBlock}</div>
          <div className="order-1 lg:order-2">{textBlock}</div>
        </>
      ) : (
        <>
          {textBlock}
          {imageBlock}
        </>
      )}
    </div>
  );
}

export default function LandingFeaturesShowcase() {
  return (
    <section
      id="fonctionnalites"
      className="relative border-t border-slate-200/80 bg-[#f4f7fa] py-28 sm:py-32 lg:py-36"
      style={{
        backgroundImage: 'radial-gradient(circle, rgb(148 163 184 / 0.35) 1px, transparent 1px)',
        backgroundSize: '24px 24px',
      }}
    >
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wide text-brand-700">Fonctionnalités</p>
          <h2 className="mt-3 text-3xl font-bold text-slate-900 sm:text-4xl">
            Tout pour analyser la BRVM
          </h2>
          <p className="mt-4 text-base text-slate-600 sm:text-lg">
            De la liste des sociétés cotées aux comparaisons sectorielles, une plateforme complète pour
            investir avec méthode.
          </p>
        </div>

        <div className="mt-20 space-y-28 sm:space-y-32 lg:space-y-40">
          {FEATURES.map((feature) => (
            <FeatureRow key={feature.title} {...feature} />
          ))}
        </div>
      </div>
    </section>
  );
}
