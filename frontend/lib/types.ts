// TypeScript interfaces for Microgrid Dashboard API

export interface KPIs {
  last_updated: string;
  current_load_kw: number;
  avg_24h_kw: number | null;
  peak_24h_kw: number | null;
  current_temp_c: number | null;
}

export interface Equipment {
  pv_kw: number;
  load_kw: number;
  battery_kw: number;
  grid_kw: number;
  battery_soc: number;
}

export interface Alert {
  level: 'info' | 'warn' | 'crit';
  message: string;
}

export interface PlotData {
  x: string[];
  y: number[];
  type?: string;
  name?: string;
  mode?: string;
  fill?: string;
  fillcolor?: string;
  line?: {
    color?: string;
    width?: number;
  };
  marker?: {
    color?: string;
    size?: number;
    symbol?: string;
  };
  hovertemplate?: string;
  showlegend?: boolean;
  yaxis?: string;
  text?: string[];
}

export interface PlotLayout {
  title: string;
  xaxis?: {
    title?: string;
  };
  yaxis?: {
    title?: string;
  };
  yaxis2?: any;
  paper_bgcolor?: string;
  plot_bgcolor?: string;
  font?: {
    color?: string;
  };
  margin?: {
    t?: number;
    r?: number;
    b?: number;
    l?: number;
  };
  barmode?: string;
}

export interface PlotConfig {
  data: PlotData[];
  layout: PlotLayout;
  anomalies?: Anomaly[];
}

export interface Anomaly {
  x: string;
  y: number;
  text?: string;
}

export interface DailySeries {
  x: string[];
  y_mean: number[];
  y_max: number[];
}

export interface Metrics {
  mae_test: number;
}

export interface CostPeriod {
  off: number;
  mid: number;
  peak: number;
}

export interface Costs {
  rate_now: number | null;
  current_cost: number | null;
  forecast_cost_24h: number | null;
  today_cost: number | null;
  last24_cost: number | null;
  by_period: CostPeriod;
  forecast_by_period: CostPeriod;
  next_peak_ts: string | null;
}

export interface OptimizationStep {
  ts: string;
  load_kw: number;
  pv_kw: number;
  grid_base_kw: number;
  batt_kw: number;
  grid_opt_kw: number;
  rate: number;
  soc_pct: number;
}

export interface Optimization {
  baseline_cost: number;
  optimized_cost: number;
  savings: number;
  plan: OptimizationStep[];
  discharge_threshold?: number;
  charge_threshold?: number;
}

export interface Goal {
  raw: string;
  monthly_target: number;
  daily_target: number;
}

export interface SimParams {
  factor: number;
  pv_factor: number;
  batt_limit: number;
  soc_init: number;
}

export interface DashboardResponse {
  consumption: PlotConfig;
  forecast: PlotConfig;
  metrics: Metrics;
  temperature: PlotConfig;
  daily: DailySeries;
  kpis: KPIs;
  equipment: Equipment;
  context: string;
  alerts: Alert[];
  source: string;
  mode: string;
  goal: Goal | null;
  soc_min: number;
  algo: string;
  sim: SimParams | null;
  costs: Costs;
  optimization: Optimization;
}

export interface StreamTick {
  tick: {
    x: string;
    y: number;
    temp: number;
  };
  kpis: KPIs;
  equipment: Equipment;
  context: string;
  alerts: Alert[];
}

export type SourceType = 'live' | 'db' | 'csv' | 'sim';
export type AlgoType = 'rf' | 'linear' | 'ridge' | 'lasso';
export type ModeType = 'normal' | 'economico' | 'conforto';
