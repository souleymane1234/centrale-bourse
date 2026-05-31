import { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

export default function FinancialMetricChart({
  title,
  series = [],
  valueLabel = 'M FCFA',
  className = 'h-56',
  color = '#3b82f6',
}) {
  const rows = useMemo(
    () =>
      [...(series || [])]
        .filter((row) => row?.year != null && row?.value_mfcfa != null)
        .sort((a, b) => Number(a.year) - Number(b.year)),
    [series]
  );

  const labels = rows.map((row) => String(row.year));
  const values = rows.map((row) => Number(row.value_mfcfa));

  const data = {
    labels,
    datasets: [
      {
        label: title,
        data: values,
        backgroundColor: color,
        borderRadius: 4,
        maxBarThickness: 48,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      title: {
        display: Boolean(title),
        text: title,
        color: '#475569',
        font: { size: 13, weight: '600' },
        padding: { bottom: 8 },
      },
      tooltip: {
        backgroundColor: '#0f172a',
        callbacks: {
          label(context) {
            const value = context.parsed.y;
            return ` ${Number(value).toLocaleString('fr-FR')} ${valueLabel}`;
          },
        },
      },
    },
    scales: {
      x: {
        ticks: { color: '#94a3b8', font: { size: 11 } },
        grid: { display: false },
        border: { display: false },
      },
      y: {
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
      <div
        className={`flex ${className} w-full items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50/50 text-sm text-slate-500`}
      >
        Données indisponibles
      </div>
    );
  }

  return (
    <div className={`${className} w-full`}>
      <Bar data={data} options={options} />
    </div>
  );
}
