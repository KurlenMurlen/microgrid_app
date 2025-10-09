import { Card } from './Card';
import type { Optimization, Goal } from '@/lib/types';

interface OptimizationCardProps {
  optimization: Optimization | null;
  mode: string;
  goal: Goal | null;
}

export function OptimizationCard({ optimization, mode, goal }: OptimizationCardProps) {
  if (!optimization) return null;

  const dailyTarget = goal?.daily_target;
  const isGoalMet = dailyTarget != null && optimization.savings >= dailyTarget;

  return (
    <Card>
      <div className="flex justify-between items-center mb-2">
        <div className="text-text-dim text-sm font-semibold">
          Otimização (modo <span className="text-text">{mode}</span>)
        </div>
        <div className="flex flex-col items-end">
          <span className="text-text-dim text-xs">Economia</span>
          <span className="text-text font-semibold">{optimization.savings.toFixed(2)}</span>
          <span className="text-text-dim text-xs">R$</span>
        </div>
      </div>

      <div className="text-text-dim text-xs mb-2">
        Objetivo: <span className="text-text">{goal ? `R$ ${goal.daily_target.toFixed(2)} / dia` : '—'}</span> · 
        Baseline: <span className="text-text">{optimization.baseline_cost.toFixed(2)}</span> R$ · 
        Otimizado: <span className="text-text">{optimization.optimized_cost.toFixed(2)}</span> R$
      </div>

      <div className="text-text-dim text-xs mb-3">
        {dailyTarget != null ? (
          isGoalMet ? (
            <span className="text-accent-3">Meta diária atingida ✅</span>
          ) : (
            <span>Meta diária ainda não atingida</span>
          )
        ) : (
          '—'
        )}
      </div>

      <div className="grid gap-1.5 text-xs">
        {optimization.plan.slice(0, 8).map((step, idx) => {
          const t = new Date(step.ts);
          const hh = String(t.getHours()).padStart(2, '0');
          const mm = String(t.getMinutes()).padStart(2, '0');

          return (
            <div
              key={idx}
              className="flex justify-between items-center px-2 py-1 rounded bg-muted/50"
            >
              <span className="text-text-dim">{hh}:{mm}</span>
              <span className="text-text">grid: {step.grid_opt_kw.toFixed(2)} kW</span>
              <span className="text-text">batt: {step.batt_kw.toFixed(2)} kW</span>
              <span className="text-text">soc: {Math.round(step.soc_pct)}%</span>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
