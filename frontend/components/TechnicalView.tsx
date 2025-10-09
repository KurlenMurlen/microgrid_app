'use client';

import { Badge } from './Badge';
import { Select } from './Select';
import { RangeSlider } from './RangeSlider';
import { Card } from './Card';
import { PlotlyChart, ConsumptionPlot } from './PlotlyChart';
import { ContextCubes } from './ContextCubes';
import { Alerts } from './Alerts';
import { PricingCard } from './PricingCard';
import { OptimizationCard } from './OptimizationCard';
import { getExportUrl } from '@/lib/api';
import type { DashboardResponse, SourceType, AlgoType, ModeType } from '@/lib/types';

interface TechnicalViewProps {
  data: DashboardResponse | null;
  source: SourceType;
  algo: AlgoType;
  mode: ModeType;
  goal: string;
  socMin: number;
  simFactor: number;
  simPv: number;
  simBatt: number;
  simSoc: number;
  onSourceChange: (value: SourceType) => void;
  onAlgoChange: (value: AlgoType) => void;
  onModeChange: (value: ModeType) => void;
  onGoalChange: (value: string) => void;
  onSocMinChange: (value: number) => void;
  onSimFactorChange: (value: number) => void;
  onSimPvChange: (value: number) => void;
  onSimBattChange: (value: number) => void;
  onSimSocChange: (value: number) => void;
}

export function TechnicalView({
  data,
  source,
  algo,
  mode,
  goal,
  socMin,
  simFactor,
  simPv,
  simBatt,
  simSoc,
  onSourceChange,
  onAlgoChange,
  onModeChange,
  onGoalChange,
  onSocMinChange,
  onSimFactorChange,
  onSimPvChange,
  onSimBattChange,
  onSimSocChange,
}: TechnicalViewProps) {
  const showSimControls = source === 'sim';
  const exportUrl = getExportUrl({ source, range: '7d' });

  const algoName = algo === 'linear' ? 'LinearReg' : algo === 'ridge' ? 'Ridge' : algo === 'lasso' ? 'Lasso' : 'RandomForest';

  return (
    <div className="technical-view">
      {/* Topbar */}
      <header className="sticky top-0 z-10 flex justify-between items-center gap-gap px-5 py-gap border-b border-border backdrop-blur-xl bg-surface/90 shadow-sm">
        <div className="flex items-center gap-2.5">
          <div
            className="w-2.5 h-2.5 rounded-full bg-gradient-to-br from-accent-2 to-accent"
            style={{
              boxShadow: '0 0 0 4px color-mix(in oklab, var(--accent-2) 20%, transparent)',
            }}
          ></div>
          <span className="font-semibold text-text">Microrrede</span>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <Badge variant={source === 'live' || source === 'sim' ? 'live' : 'default'}>
            {source === 'live' || source === 'sim' ? 'AO VIVO' : 'ESTÁTICO'}
          </Badge>
          <Badge>
            MAE: <strong>{data?.metrics.mae_test.toFixed(3) ?? '-'}</strong> kW
          </Badge>

          <Select
            value={source}
            onChange={(v) => onSourceChange(v as SourceType)}
            options={[
              { value: 'live', label: 'Ao vivo' },
              { value: 'db', label: 'Banco (SQLite)' },
              { value: 'csv', label: 'CSV Sintético' },
              { value: 'sim', label: 'Simulação' },
            ]}
          />

          <Select
            value={algo}
            onChange={(v) => onAlgoChange(v as AlgoType)}
            options={[
              { value: 'rf', label: 'Random Forest' },
              { value: 'linear', label: 'Linear Regression' },
              { value: 'ridge', label: 'Ridge' },
              { value: 'lasso', label: 'Lasso' },
            ]}
          />

          <Select
            value={mode}
            onChange={(v) => onModeChange(v as ModeType)}
            options={[
              { value: 'normal', label: 'Gasto normal' },
              { value: 'economico', label: 'Econômico' },
              { value: 'conforto', label: 'Conforto' },
            ]}
          />

          <input
            type="text"
            value={goal}
            onChange={(e) => onGoalChange(e.target.value)}
            placeholder="Ex.: quero economizar 200 reais por mês"
            className="px-3 py-1.5 bg-surface border border-border rounded-full text-sm text-text placeholder:text-text-dim hover:border-accent focus:outline-none focus:border-accent-2 focus:ring-2 focus:ring-accent-2/20 transition-smooth min-w-[320px]"
          />

          <RangeSlider
            label="SOC mínimo"
            value={socMin}
            onChange={onSocMinChange}
            min={0}
            max={80}
            step={5}
            formatter={(v) => `${v}%`}
          />

          {showSimControls && (
            <div className="flex items-center gap-3 pl-3 border-l border-border">
              <RangeSlider
                label="Carga"
                value={simFactor}
                onChange={onSimFactorChange}
                min={0.5}
                max={1.5}
                step={0.05}
                formatter={(v) => `${v.toFixed(2)}x`}
              />
              <RangeSlider
                label="PV"
                value={simPv}
                onChange={onSimPvChange}
                min={0.5}
                max={2}
                step={0.1}
                formatter={(v) => `${v.toFixed(1)}x`}
              />
              <RangeSlider
                label="Bateria"
                value={simBatt}
                onChange={onSimBattChange}
                min={0}
                max={5}
                step={0.5}
                formatter={(v) => `${v.toFixed(1)} kW`}
              />
              <RangeSlider
                label="SOC"
                value={simSoc}
                onChange={onSimSocChange}
                min={0}
                max={100}
                step={5}
                formatter={(v) => `${Math.round(v)}%`}
              />
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1800px] mx-auto px-5 py-gap-lg grid grid-cols-1 xl:grid-cols-[1fr_380px] gap-gap-lg">
        {/* Main Column */}
        <section className="space-y-gap-lg">
          <div>
            <h1 className="text-2xl font-bold text-text mb-1">Monitoramento e Previsão</h1>
            <p className="text-text-dim text-sm">
              Consumo recente, previsão 24h e estado simplificado da microrrede. Atualização contínua.
            </p>
          </div>

          {/* Consumption & Forecast */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-gap">
            <Card>
              <div className="flex justify-between items-center mb-3">
                <div className="text-text-dim text-sm font-semibold">Consumo · últimos 7 dias</div>
                <small className="text-text-dim text-xs">
                  {data?.kpis.last_updated
                    ? new Date(data.kpis.last_updated).toLocaleString('pt-BR')
                    : '—'}
                </small>
              </div>
              {data && <ConsumptionPlot config={data.consumption} anomalies={data.consumption.anomalies} />}
              <p className="text-text-dim text-xs mt-2">
                Interpretação: oscilações refletem padrões diários/semanais de carga e variações de temperatura.
              </p>
            </Card>

            <Card>
              <div className="flex justify-between items-center mb-3">
                <div className="text-text-dim text-sm font-semibold">Previsão de consumo para as próximas 24h</div>
                <div className="flex items-center gap-1.5">
                  <Badge variant="ml">{algoName}</Badge>
                  <Badge variant="ml">scikit-learn</Badge>
                </div>
              </div>
              {data && <PlotlyChart config={data.forecast} />}
              <p className="text-text-dim text-xs mt-2">
                Interpretação: projeção baseada em lags de consumo + hora/dia/temperatura.
              </p>
            </Card>
          </div>

          {/* Temperature & Equipment */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-gap">
            <Card>
              <div className="text-text-dim text-sm font-semibold mb-3">Temperatura · últimos 7 dias</div>
              {data && <PlotlyChart config={data.temperature} />}
              <p className="text-text-dim text-xs mt-2">
                Interpretação: auxilia na compreensão de sazonalidade térmica e impacto em carga.
              </p>
            </Card>

            <Card>
              <div className="text-text-dim text-sm font-semibold mb-3">Microrrede · estado atual</div>
              <EquipmentState data={data} />
              <p className="text-text-dim text-xs mt-2">
                Interpretação: fluxos estimados (PV→Carga/Bateria, Rede→Carga). SOC indica nível da bateria.
              </p>
            </Card>
          </div>

          {/* Daily Aggregation */}
          <Card>
            <div className="flex justify-between items-baseline mb-3">
              <div className="text-text-dim text-sm font-semibold">Agregações diárias</div>
              <div className="flex gap-4">
                <KPI label="Atual" value={data?.kpis.current_load_kw.toFixed(2) ?? '—'} unit="kW" />
                <KPI label="Média 24h" value={data?.kpis.avg_24h_kw?.toFixed(2) ?? '—'} unit="kW" />
                <KPI label="Pico 24h" value={data?.kpis.peak_24h_kw?.toFixed(2) ?? '—'} unit="kW" />
                <KPI label="Temp" value={data?.kpis.current_temp_c?.toFixed(1) ?? '—'} unit="°C" />
              </div>
            </div>
            {data && <DailyPlot data={data} />}
            <p className="text-text-dim text-xs mt-2">
              Interpretação: tendências médias e picos ajudam a identificar cargas críticas e períodos de maior consumo.
            </p>
          </Card>

          {/* Footer */}
          <div className="flex justify-between items-center">
            <p className="text-text-dim text-xs">
              Atualiza a cada 15s. Fonte: <span className="text-text">{source}</span>.
            </p>
            <a
              href={exportUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-2.5 py-1.5 border border-border rounded-full bg-muted text-text-dim text-sm hover:bg-surface hover:border-accent transition-smooth"
            >
              Exportar CSV (7d)
            </a>
          </div>
        </section>

        {/* Sidebar */}
        <aside className="space-y-gap-lg">
          {data && (
            <>
              <ContextCubes
                contextText={data.context}
                kpis={data.kpis}
                equipment={data.equipment}
                costs={data.costs}
              />
              <Alerts alerts={data.alerts} />
              <PricingCard costs={data.costs} />
              <OptimizationCard optimization={data.optimization} mode={mode} goal={data.goal} />
            </>
          )}
        </aside>
      </main>
    </div>
  );
}

function KPI({ label, value, unit }: { label: string; value: string; unit: string }) {
  return (
    <div className="flex flex-col items-end">
      <span className="text-text-dim text-xs">{label}</span>
      <strong className="text-text text-base">{value}</strong>
      <small className="text-text-dim text-xs">{unit}</small>
    </div>
  );
}

function EquipmentState({ data }: { data: DashboardResponse | null }) {
  if (!data) return null;

  const { equipment } = data;
  const soc = Math.max(0, Math.min(100, equipment.battery_soc));

  return (
    <div className="grid grid-cols-2 gap-3">
      <div className="flex flex-col items-center p-3 bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/10 border border-yellow-200 dark:border-yellow-800 rounded-lg">
        <span className="text-text-dim text-xs mb-1">PV</span>
        <strong className="text-text text-xl">{equipment.pv_kw.toFixed(2)}</strong>
        <span className="text-text-dim text-xs">kW</span>
      </div>

      <div className="flex flex-col items-center p-3 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/10 border border-blue-200 dark:border-blue-800 rounded-lg">
        <span className="text-text-dim text-xs mb-1">Carga</span>
        <strong className="text-text text-xl">{equipment.load_kw.toFixed(2)}</strong>
        <span className="text-text-dim text-xs">kW</span>
      </div>

      <div className="flex flex-col items-center p-3 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/10 border border-purple-200 dark:border-purple-800 rounded-lg">
        <span className="text-text-dim text-xs mb-1">Rede</span>
        <strong className="text-text text-xl">{equipment.grid_kw.toFixed(2)}</strong>
        <span className="text-text-dim text-xs">kW</span>
      </div>

      <div className="flex flex-col items-center p-3 bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/10 border border-green-200 dark:border-green-800 rounded-lg">
        <span className="text-text-dim text-xs mb-1">Bateria</span>
        <strong className="text-text text-xl">{Math.abs(equipment.battery_kw).toFixed(2)}</strong>
        <span className="text-text-dim text-xs">kW</span>
        <div className="w-full h-2 bg-muted rounded-full mt-2 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-green-400 to-green-600 transition-all duration-500"
            style={{ width: `${soc}%` }}
          ></div>
        </div>
        <small className="text-text-dim text-xs mt-1">{soc}%</small>
      </div>
    </div>
  );
}

function DailyPlot({ data }: { data: DashboardResponse }) {
  const plotData = [
    {
      x: data.daily.x,
      y: data.daily.y_mean,
      type: 'scatter',
      name: 'Média',
      line: { color: '#60a5fa' },
    },
    {
      x: data.daily.x,
      y: data.daily.y_max,
      type: 'bar',
      name: 'Pico',
      marker: { color: '#818cf8' },
    },
  ];

  return <PlotlyChart config={{ data: plotData, layout: { title: '' } }} height={300} />;
}
