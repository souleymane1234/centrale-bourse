import { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler);

function sortPriceRows(rows) {
  return [...(rows || [])]
    .filter((row) => row?.close != null && row?.date)
    .sort((a, b) => String(a.date).localeCompare(String(b.date)));
}

export default function PriceChart({ historicalPrices, className = 'h-80' }) {
  const rows = useMemo(() => sortPriceRows(historicalPrices), [historicalPrices]);

  const labels = rows.map((row) => {
    const date = new Date(`${row.date}T12:00:00`);
    if (Number.isNaN(date.getTime())) return row.date;
    return date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' });
  });
  const prices = rows.map((row) => Number(row.close));

  const yScale = useMemo(() => {
    if (!prices.length) return {};
    const min = Math.min(...prices);
    const max = Math.max(...prices);
    const spread = max - min;
    const padding = spread > 0 ? spread * 0.12 : Math.max(min * 0.05, 50);
    return {
      min: Math.max(0, min - padding),
      max: max + padding,
    };
  }, [prices]);

  const data = {
    labels,
    datasets: [
      {
        label: 'Clôture',
        data: prices,
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.15)',
        fill: true,
        tension: 0.35,
        pointRadius: 0,
        pointHoverRadius: 4,
        borderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#0f172a',
        titleFont: { size: 12 },
        bodyFont: { size: 12 },
        padding: 10,
        callbacks: {
          label(context) {
            const value = context.parsed.y;
            return ` ${Number(value).toLocaleString('fr-FR')} FCFA`;
          },
        },
      },
    },
    scales: {
      x: {
        ticks: { maxTicksLimit: 8, color: '#94a3b8', font: { size: 11 } },
        grid: { display: false },
        border: { display: false },
      },
      y: {
        min: yScale.min,
        max: yScale.max,
        ticks: {
          color: '#94a3b8',
          font: { size: 11 },
          callback: (value) => Number(value).toLocaleString('fr-FR'),
        },
        grid: { color: 'rgba(148, 163, 184, 0.15)' },
        border: { display: false },
      },
    },
  };

  if (!rows.length) {
    return (
      <div className={`flex ${className} w-full items-center justify-center text-sm text-slate-500`}>
        Historique indisponible
      </div>
    );
  }

  return (
    <div className={`${className} w-full`}>
      <Line data={data} options={options} />
    </div>
  );
}
