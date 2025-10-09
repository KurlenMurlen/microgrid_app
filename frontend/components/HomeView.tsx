'use client';

import { useEffect, useRef, useState } from 'react';
import type { DashboardResponse } from '@/lib/types';

interface HomeViewProps {
  data: DashboardResponse | null;
}

export function HomeView({ data }: HomeViewProps) {
  const [displayValues, setDisplayValues] = useState({
    daily: 0,
    monthly: 0,
    annual: 0,
  });

  useEffect(() => {
    if (!data) return;

    const daily = data.optimization?.savings || 0;
    const monthly = daily * 30;
    const annual = daily * 365;

    // Animate counter
    const duration = 800;
    const steps = 60;
    const increment = {
      daily: daily / steps,
      monthly: monthly / steps,
      annual: annual / steps,
    };

    let currentStep = 0;
    const interval = setInterval(() => {
      currentStep++;
      if (currentStep >= steps) {
        setDisplayValues({ daily, monthly, annual });
        clearInterval(interval);
      } else {
        setDisplayValues({
          daily: increment.daily * currentStep,
          monthly: increment.monthly * currentStep,
          annual: increment.annual * currentStep,
        });
      }
    }, duration / steps);

    return () => clearInterval(interval);
  }, [data?.optimization?.savings]);

  const formatCurrency = (value: number) => `R$ ${value.toFixed(2)}`;
  const formatCurrencyShort = (value: number) => {
    if (value >= 1000) return `R$ ${(value / 1000).toFixed(1)}k`;
    return `R$ ${value.toFixed(0)}`;
  };

  // Calculate ring progress
  const goal = data?.goal;
  const costs = data?.costs;
  const daily = displayValues.daily;
  const monthly = displayValues.monthly;
  const annual = displayValues.annual;

  let dailyPercent = 0;
  let monthlyPercent = 0;
  let annualPercent = 0;

  if (goal && goal.daily_target && goal.daily_target > 0) {
    dailyPercent = Math.min((daily / goal.daily_target) * 100, 100);
    monthlyPercent = Math.min((monthly / (goal.daily_target * 30)) * 100, 100);
    annualPercent = Math.min((annual / (goal.daily_target * 365)) * 100, 100);
  } else {
    const baseline = costs?.last24_cost || data?.optimization?.baseline_cost || 10;
    const dailySavingsRate = baseline > 0 ? (daily / baseline) * 100 : 0;
    const monthlySavingsRate = baseline * 30 > 0 ? (monthly / (baseline * 30)) * 100 : 0;
    const annualSavingsRate = baseline * 365 > 0 ? (annual / (baseline * 365)) * 100 : 0;

    dailyPercent = Math.min(Math.max(dailySavingsRate, daily > 0.01 ? 10 : 0), 90);
    monthlyPercent = Math.min(Math.max(monthlySavingsRate, monthly > 0.3 ? 10 : 0), 90);
    annualPercent = Math.min(Math.max(annualSavingsRate, annual > 3.65 ? 10 : 0), 90);
  }

  // Calculate stroke dash offsets
  const dailyCircumference = 2 * Math.PI * 80;
  const monthlyCircumference = 2 * Math.PI * 120;
  const annualCircumference = 2 * Math.PI * 160;

  const dailyOffset = dailyCircumference * (1 - dailyPercent / 100);
  const monthlyOffset = monthlyCircumference * (1 - monthlyPercent / 100);
  const annualOffset = annualCircumference * (1 - annualPercent / 100);

  const percentText =
    goal && goal.daily_target && goal.daily_target > 0
      ? `${Math.round(dailyPercent)}% da meta`
      : daily > 0
        ? `${Math.round(dailyPercent)}% economia`
        : '';

  return (
    <div className="home-view">
      <div className="flex flex-col items-center justify-center min-h-screen px-8 py-12">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-accent-2 to-accent bg-clip-text text-transparent mb-3">
            Economia da Microrrede
          </h1>
          <p className="text-xl text-text-dim">Otimização inteligente em tempo real</p>
        </div>

        <div className="relative mb-12">
          <svg className="economy-circles" viewBox="0 0 400 400" width="400" height="400">
            <defs>
              <linearGradient id="gradient1" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#6ee7b7" stopOpacity="1" />
                <stop offset="100%" stopColor="#60a5fa" stopOpacity="1" />
              </linearGradient>
              <linearGradient id="gradient2" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#60a5fa" stopOpacity="1" />
                <stop offset="100%" stopColor="#818cf8" stopOpacity="1" />
              </linearGradient>
              <linearGradient id="gradient3" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#818cf8" stopOpacity="1" />
                <stop offset="100%" stopColor="#a78bfa" stopOpacity="1" />
              </linearGradient>
            </defs>

            {/* Outer ring: Annual */}
            <circle
              cx="200"
              cy="200"
              r="160"
              fill="none"
              stroke="url(#gradient3)"
              strokeWidth="20"
              opacity="0.3"
              strokeDasharray={annualCircumference}
              strokeDashoffset="0"
              transform="rotate(-90 200 200)"
            />
            <circle
              cx="200"
              cy="200"
              r="160"
              fill="none"
              stroke="url(#gradient3)"
              strokeWidth="20"
              strokeDasharray={annualCircumference}
              strokeDashoffset={annualOffset}
              strokeLinecap="round"
              transform="rotate(-90 200 200)"
              className="transition-all duration-1000 ease-out"
            />

            {/* Middle ring: Monthly */}
            <circle
              cx="200"
              cy="200"
              r="120"
              fill="none"
              stroke="url(#gradient2)"
              strokeWidth="18"
              opacity="0.3"
              strokeDasharray={monthlyCircumference}
              strokeDashoffset="0"
              transform="rotate(-90 200 200)"
            />
            <circle
              cx="200"
              cy="200"
              r="120"
              fill="none"
              stroke="url(#gradient2)"
              strokeWidth="18"
              strokeDasharray={monthlyCircumference}
              strokeDashoffset={monthlyOffset}
              strokeLinecap="round"
              transform="rotate(-90 200 200)"
              className="transition-all duration-1000 ease-out"
            />

            {/* Inner ring: Daily */}
            <circle
              cx="200"
              cy="200"
              r="80"
              fill="none"
              stroke="url(#gradient1)"
              strokeWidth="16"
              opacity="0.3"
              strokeDasharray={dailyCircumference}
              strokeDashoffset="0"
              transform="rotate(-90 200 200)"
            />
            <circle
              cx="200"
              cy="200"
              r="80"
              fill="none"
              stroke="url(#gradient1)"
              strokeWidth="16"
              strokeDasharray={dailyCircumference}
              strokeDashoffset={dailyOffset}
              strokeLinecap="round"
              transform="rotate(-90 200 200)"
              className="transition-all duration-1000 ease-out"
            />

            {/* Center text */}
            <text x="200" y="180" textAnchor="middle" className="fill-text-dim text-sm">
              Economia
            </text>
            <text x="200" y="210" textAnchor="middle" className="fill-text text-3xl font-bold">
              {formatCurrencyShort(annual)}
            </text>
          </svg>

          {/* Ring labels */}
          <div className="absolute -bottom-24 left-0 right-0 flex justify-around px-8">
            <div className="flex flex-col items-center gap-1">
              <span className="text-text-dim text-sm">Diária</span>
              <span className="text-text font-semibold">{formatCurrency(daily)}</span>
              {percentText && <span className="text-accent-2 text-xs">{percentText}</span>}
            </div>
            <div className="flex flex-col items-center gap-1">
              <span className="text-text-dim text-sm">Mensal</span>
              <span className="text-text font-semibold">{formatCurrency(monthly)}</span>
              {goal && goal.daily_target && (
                <span className="text-accent-2 text-xs">{Math.round(monthlyPercent)}% da meta</span>
              )}
            </div>
            <div className="flex flex-col items-center gap-1">
              <span className="text-text-dim text-sm">Anual</span>
              <span className="text-text font-semibold">{formatCurrency(annual)}</span>
              {goal && goal.daily_target && (
                <span className="text-accent-2 text-xs">{Math.round(annualPercent)}% da meta</span>
              )}
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 w-full max-w-6xl mt-24">
          <MetricCard
            icon="⚡"
            label="Consumo Atual"
            value={data ? `${data.kpis.current_load_kw.toFixed(2)} kW` : '0.00 kW'}
          />
          <MetricCard
            icon="🔋"
            label="Bateria"
            value={data ? `${data.equipment.battery_soc}%` : '50%'}
          />
          <MetricCard
            icon="☀️"
            label="Geração Solar"
            value={data ? `${data.equipment.pv_kw.toFixed(2)} kW` : '0.00 kW'}
          />
          <MetricCard
            icon="💰"
            label="Tarifa Atual"
            value={data?.costs?.rate_now != null ? `R$ ${data.costs.rate_now.toFixed(2)}/kWh` : 'R$ 0,00/kWh'}
          />
          <MetricCard
            icon="🕐"
            label="Próximo Pico"
            value={
              data?.costs?.next_peak_ts
                ? new Date(data.costs.next_peak_ts).toLocaleTimeString('pt-BR', {
                    hour: '2-digit',
                    minute: '2-digit',
                  })
                : '—'
            }
          />
          {data && data.alerts.length > 0 && (
            <MetricCard icon="⚠️" label="Alertas" value={data.alerts.length.toString()} />
          )}
        </div>
      </div>
    </div>
  );
}

function MetricCard({ icon, label, value }: { icon: string; label: string; value: string }) {
  return (
    <div className="flex items-center gap-3 p-4 bg-surface border border-border rounded-card-sm shadow-card-sm hover:shadow-card-md transition-smooth">
      <div className="text-3xl">{icon}</div>
      <div className="flex flex-col">
        <span className="text-text-dim text-xs">{label}</span>
        <span className="text-text font-semibold text-sm">{value}</span>
      </div>
    </div>
  );
}
