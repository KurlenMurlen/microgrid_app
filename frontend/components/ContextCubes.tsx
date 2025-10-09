'use client';

import { useEffect, useRef } from 'react';
import type { KPIs, Equipment, Costs } from '@/lib/types';

interface ContextCubeProps {
  title: string;
  body: string;
}

function ContextCube({ title, body }: ContextCubeProps) {
  const bodyRef = useRef<HTMLDivElement>(null);
  const cubeRef = useRef<HTMLDivElement>(null);
  const prevBodyRef = useRef<string>(body);

  useEffect(() => {
    if (prevBodyRef.current !== body && bodyRef.current && cubeRef.current) {
      cubeRef.current.classList.add('flash');
      bodyRef.current.classList.add('change');
      
      const timer = setTimeout(() => {
        cubeRef.current?.classList.remove('flash');
        bodyRef.current?.classList.remove('change');
      }, 600);
      
      prevBodyRef.current = body;
      return () => clearTimeout(timer);
    }
  }, [body]);

  return (
    <div
      ref={cubeRef}
      className="cube bg-surface border border-border rounded-lg p-3 transition-smooth"
    >
      <div className="text-text-dim text-xs font-semibold mb-1.5">{title}</div>
      <div ref={bodyRef} className="text-text text-sm leading-relaxed">
        {body}
      </div>
    </div>
  );
}

interface ContextCubesProps {
  contextText: string;
  kpis?: KPIs;
  equipment?: Equipment;
  costs?: Costs;
}

export function ContextCubes({ contextText, kpis, equipment, costs }: ContextCubesProps) {
  const loadText =
    kpis?.current_load_kw != null
      ? `${kpis.current_load_kw.toFixed(2)} kW (média 24h ${kpis.avg_24h_kw != null ? kpis.avg_24h_kw.toFixed(2) : '—'})`
      : '—';

  const tempText = kpis?.current_temp_c != null ? `${kpis.current_temp_c.toFixed(1)} °C` : '—';

  const pvText = equipment ? `${equipment.pv_kw.toFixed(2)} kW` : '—';

  const battFlow = equipment?.battery_kw ?? 0;
  const battWord = battFlow > 0 ? 'descarreg.' : battFlow < 0 ? 'carreg.' : 'repouso';
  const battText = equipment
    ? `${Math.abs(battFlow).toFixed(2)} kW (${battWord}) • SOC ${equipment.battery_soc}%`
    : '—';

  const gridText = equipment ? `${equipment.grid_kw.toFixed(2)} kW` : '—';

  let costText = '—';
  if (costs) {
    const rn = costs.rate_now != null ? `${costs.rate_now.toFixed(2)} R$/kWh` : '—';
    const cnow = costs.current_cost != null ? `${costs.current_cost.toFixed(2)} R$/h` : '—';
    const c24 = costs.forecast_cost_24h != null ? `${costs.forecast_cost_24h.toFixed(2)} R$` : '—';
    const np = costs.next_peak_ts ? new Date(costs.next_peak_ts) : null;
    const npStr = np
      ? `${String(np.getHours()).padStart(2, '0')}:${String(np.getMinutes()).padStart(2, '0')}`
      : '—';
    let extras = '';
    if (costs.today_cost != null) extras += ` • Hoje: R$ ${costs.today_cost.toFixed(2)}`;
    if (costs.last24_cost != null) extras += ` • Últ.24h: R$ ${costs.last24_cost.toFixed(2)}`;
    costText = `Tarifa agora: ${rn} • Inst.: ${cnow} • 24h: ${c24} • Próx. pico: ${npStr}${extras}`;
  }

  return (
    <div className="grid gap-3">
      <ContextCube title="Contexto" body={contextText || '—'} />
      <ContextCube title="Carga" body={loadText} />
      <ContextCube title="Solar" body={pvText} />
      <ContextCube title="Bateria" body={battText} />
      <ContextCube title="Rede" body={gridText} />
      <ContextCube title="Clima" body={tempText} />
      <ContextCube title="Custo" body={costText} />
    </div>
  );
}
