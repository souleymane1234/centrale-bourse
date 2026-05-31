import { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line, Chart } from 'react-chartjs-2';
import { formatNumber } from '../utils/format';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Tooltip,
  Legend,
  Filler
);

function sortSeries(rows) {
  return [...(rows || [])]
    .filter((row) => row?.date)
    .sort((a, b) => String(a.date).localeCompare(String(b.date)));
}

function formatLabels(rows) {
  return rows.map((row) => {
    const date = new Date(`${row.date}T12:00:00`);
    if (Number.isNaN(date.getTime())) return row.date;
    return date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' });
  });
}

const baseChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: {
      display: true,
      position: 'top',
      labels: { boxWidth: 12, color: '#64748b', font: { size: 11 } },
    },
    tooltip: {
      backgroundColor: '#0f172a',
      titleFont: { size: 12 },
      bodyFont: { size: 12 },
      padding: 10,
    },
  },
  scales: {
    x: {
      ticks: { maxTicksLimit: 8, color: '#94a3b8', font: { size: 11 } },
      grid: { display: false },
      border: { display: false },
    },
  },
};

function LatestBadge({ label, value, suffix = '' }) {
  if (value == null || value === '') return null;
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-700">
      {label}: {formatNumber(value)}
      {suffix}
    </span>
  );
}

function EmptyChart({ className, message }) {
  return (
    <div
      className={`flex ${className} w-full items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50/50 text-sm text-slate-500`}
    >
      {message}
    </div>
  );
}

function SmaPriceChart({ series, className = 'h-64' }) {
  const rows = useMemo(() => sortSeries(series), [series]);
  const labels = useMemo(() => formatLabels(rows), [rows]);

  const data = useMemo(
    () => ({
      labels,
      datasets: [
        {
          label: 'Clôture',
          data: rows.map((r) => r.close),
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.08)',
          fill: false,
          tension: 0.3,
          pointRadius: 0,
          borderWidth: 2,
        },
        {
          label: 'SMA 20',
          data: rows.map((r) => r.sma_20),
          borderColor: '#f59e0b',
          borderDash: [4, 3],
          tension: 0.3,
          pointRadius: 0,
          borderWidth: 1.5,
        },
        {
          label: 'SMA 50',
          data: rows.map((r) => r.sma_50),
          borderColor: '#8b5cf6',
          borderDash: [6, 4],
          tension: 0.3,
          pointRadius: 0,
          borderWidth: 1.5,
        },
      ],
    }),
    [labels, rows]
  );

  const options = useMemo(() => {
    const values = rows.flatMap((r) => [r.close, r.sma_20, r.sma_50]).filter((v) => v != null);
    const min = values.length ? Math.min(...values) : 0;
    const max = values.length ? Math.max(...values) : 0;
    const padding = (max - min) * 0.1 || 50;
    return {
      ...baseChartOptions,
      plugins: {
        ...baseChartOptions.plugins,
        tooltip: {
          ...baseChartOptions.plugins.tooltip,
          callbacks: {
            label(context) {
              return ` ${context.dataset.label}: ${Number(context.parsed.y).toLocaleString('fr-FR')} FCFA`;
            },
          },
        },
      },
      scales: {
        ...baseChartOptions.scales,
        y: {
          min: Math.max(0, min - padding),
          max: max + padding,
          ticks: {
            color: '#94a3b8',
            font: { size: 11 },
            callback: (v) => Number(v).toLocaleString('fr-FR'),
          },
          grid: { color: 'rgba(148, 163, 184, 0.15)' },
          border: { display: false },
        },
      },
    };
  }, [rows]);

  if (!rows.length) return <EmptyChart className={className} message="Données indisponibles" />;

  return (
    <div className={className}>
      <Line data={data} options={options} />
    </div>
  );
}

function RsiChart({ series, className = 'h-48' }) {
  const rows = useMemo(() => sortSeries(series), [series]);
  const labels = useMemo(() => formatLabels(rows), [rows]);

  const data = useMemo(
    () => ({
      labels,
      datasets: [
        {
          label: 'RSI (14)',
          data: rows.map((r) => r.rsi),
          borderColor: '#a855f7',
          backgroundColor: 'rgba(168, 85, 247, 0.12)',
          fill: true,
          tension: 0.3,
          pointRadius: 0,
          borderWidth: 2,
        },
        {
          label: 'Surachat (70)',
          data: rows.map(() => 70),
          borderColor: 'rgba(244, 63, 94, 0.5)',
          borderDash: [4, 4],
          pointRadius: 0,
          borderWidth: 1,
        },
        {
          label: 'Survente (30)',
          data: rows.map(() => 30),
          borderColor: 'rgba(16, 185, 129, 0.5)',
          borderDash: [4, 4],
          pointRadius: 0,
          borderWidth: 1,
        },
      ],
    }),
    [labels, rows]
  );

  const options = useMemo(
    () => ({
      ...baseChartOptions,
      plugins: {
        ...baseChartOptions.plugins,
        legend: {
          ...baseChartOptions.plugins.legend,
          labels: {
            ...baseChartOptions.plugins.legend.labels,
            filter: (item) => item.text === 'RSI (14)',
          },
        },
      },
      scales: {
        ...baseChartOptions.scales,
        y: {
          min: 0,
          max: 100,
          ticks: { color: '#94a3b8', font: { size: 11 }, stepSize: 20 },
          grid: { color: 'rgba(148, 163, 184, 0.15)' },
          border: { display: false },
        },
      },
    }),
    []
  );

  if (!rows.some((r) => r.rsi != null)) {
    return <EmptyChart className={className} message="RSI indisponible" />;
  }

  return (
    <div className={className}>
      <Line data={data} options={options} />
    </div>
  );
}

function MacdChart({ series, className = 'h-52' }) {
  const rows = useMemo(() => sortSeries(series), [series]);
  const labels = useMemo(() => formatLabels(rows), [rows]);

  const histogramColors = rows.map((r) =>
    (r.macd_histogram ?? 0) >= 0 ? 'rgba(16, 185, 129, 0.55)' : 'rgba(244, 63, 94, 0.55)'
  );

  const data = useMemo(
    () => ({
      labels,
      datasets: [
        {
          type: 'bar',
          label: 'Histogramme',
          data: rows.map((r) => r.macd_histogram),
          backgroundColor: histogramColors,
          borderWidth: 0,
          order: 3,
        },
        {
          type: 'line',
          label: 'MACD',
          data: rows.map((r) => r.macd),
          borderColor: '#0ea5e9',
          tension: 0.3,
          pointRadius: 0,
          borderWidth: 2,
          order: 1,
        },
        {
          type: 'line',
          label: 'Signal',
          data: rows.map((r) => r.macd_signal),
          borderColor: '#f97316',
          borderDash: [4, 3],
          tension: 0.3,
          pointRadius: 0,
          borderWidth: 1.5,
          order: 2,
        },
      ],
    }),
    [histogramColors, labels, rows]
  );

  const options = useMemo(
    () => ({
      ...baseChartOptions,
      plugins: {
        ...baseChartOptions.plugins,
        legend: {
          ...baseChartOptions.plugins.legend,
          labels: {
            ...baseChartOptions.plugins.legend.labels,
            filter: (item) => item.text !== 'Histogramme',
          },
        },
      },
      scales: {
        ...baseChartOptions.scales,
        y: {
          ticks: { color: '#94a3b8', font: { size: 11 } },
          grid: { color: 'rgba(148, 163, 184, 0.15)' },
          border: { display: false },
        },
      },
    }),
    []
  );

  if (!rows.some((r) => r.macd != null)) {
    return <EmptyChart className={className} message="MACD indisponible" />;
  }

  return (
    <div className={className}>
      <Chart type="bar" data={data} options={options} />
    </div>
  );
}

export default function TechnicalAnalysisCharts({ series = [], latest = {} }) {
  const last = useMemo(() => {
    const rows = sortSeries(series);
    return rows.length ? rows[rows.length - 1] : {};
  }, [series]);

  const latestValues = {
    rsi: latest.rsi ?? last.rsi,
    macd: latest.macd ?? last.macd,
    sma_20: latest.sma_20 ?? last.sma_20,
    sma_50: latest.sma_50 ?? last.sma_50,
  };

  if (!series?.length) {
    return (
      <section className="card">
        <h3 className="mb-3 text-lg font-bold">Analyse technique</h3>
        <p className="text-sm text-slate-500">Historique insuffisant pour tracer les indicateurs.</p>
      </section>
    );
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-lg font-bold text-slate-900">Analyse technique</h3>
        <div className="flex flex-wrap gap-2">
          <LatestBadge label="RSI" value={latestValues.rsi} />
          <LatestBadge label="MACD" value={latestValues.macd} />
          <LatestBadge label="SMA 20" value={latestValues.sma_20} suffix=" FCFA" />
          <LatestBadge label="SMA 50" value={latestValues.sma_50} suffix=" FCFA" />
        </div>
      </div>

      <div className="card">
        <h4 className="mb-3 text-sm font-semibold text-slate-700">Cours et moyennes mobiles (SMA 20 / 50)</h4>
        <SmaPriceChart series={series} className="h-64" />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h4 className="mb-3 text-sm font-semibold text-slate-700">RSI (14)</h4>
          <RsiChart series={series} className="h-48" />
        </div>
        <div className="card">
          <h4 className="mb-3 text-sm font-semibold text-slate-700">MACD</h4>
          <MacdChart series={series} className="h-52" />
        </div>
      </div>
    </section>
  );
}
