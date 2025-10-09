import { Card } from './Card';
import type { Costs } from '@/lib/types';

interface PricingCardProps {
  costs: Costs | null;
}

export function PricingCard({ costs }: PricingCardProps) {
  if (!costs) return null;

  return (
    <Card>
      <div className="flex justify-between items-center mb-2">
        <div className="text-text-dim text-sm font-semibold">Preços</div>
        <div className="flex flex-col items-end">
          <span className="text-text-dim text-xs">Hoje</span>
          <span className="text-text font-semibold">
            {costs.today_cost != null ? costs.today_cost.toFixed(2) : '—'}
          </span>
          <span className="text-text-dim text-xs">R$</span>
        </div>
      </div>
      
      <div className="text-text-dim text-xs mb-2">
        Últ.24h: <span className="text-text">{costs.last24_cost != null ? costs.last24_cost.toFixed(2) : '—'}</span> R$ · 
        24h próximos: <span className="text-text">{costs.forecast_cost_24h != null ? costs.forecast_cost_24h.toFixed(2) : '—'}</span> R$
      </div>
      
      <div className="grid gap-1.5 text-xs">
        <div className="flex justify-between">
          <span className="text-text-dim">Off-peak</span>
          <span className="text-text">
            Últ.24h: R$ {costs.by_period?.off?.toFixed(2) ?? '0.00'} · 
            Próx.24h: R$ {costs.forecast_by_period?.off?.toFixed(2) ?? '0.00'}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-text-dim">Intermediário</span>
          <span className="text-text">
            Últ.24h: R$ {costs.by_period?.mid?.toFixed(2) ?? '0.00'} · 
            Próx.24h: R$ {costs.forecast_by_period?.mid?.toFixed(2) ?? '0.00'}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-text-dim">Ponta (pico)</span>
          <span className="text-text">
            Últ.24h: R$ {costs.by_period?.peak?.toFixed(2) ?? '0.00'} · 
            Próx.24h: R$ {costs.forecast_by_period?.peak?.toFixed(2) ?? '0.00'}
          </span>
        </div>
      </div>
    </Card>
  );
}
