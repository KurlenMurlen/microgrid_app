// API client for Flask backend

import type { DashboardResponse, SourceType, AlgoType, ModeType } from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export interface DashboardParams {
  source?: SourceType;
  algo?: AlgoType;
  mode?: ModeType;
  goal?: string;
  soc_min?: number;
  factor?: number;
  pv_factor?: number;
  batt_limit?: number;
  soc_init?: number;
}

export async function fetchDashboard(params: DashboardParams = {}): Promise<DashboardResponse> {
  const searchParams = new URLSearchParams();
  
  if (params.source) searchParams.set('source', params.source);
  if (params.algo) searchParams.set('algo', params.algo);
  if (params.mode) searchParams.set('mode', params.mode);
  if (params.goal) searchParams.set('goal', params.goal);
  if (params.soc_min !== undefined) searchParams.set('soc_min', params.soc_min.toString());
  if (params.factor !== undefined) searchParams.set('factor', params.factor.toString());
  if (params.pv_factor !== undefined) searchParams.set('pv_factor', params.pv_factor.toString());
  if (params.batt_limit !== undefined) searchParams.set('batt_limit', params.batt_limit.toString());
  if (params.soc_init !== undefined) searchParams.set('soc_init', params.soc_init.toString());

  const response = await fetch(`${API_URL}/api/dashboard?${searchParams.toString()}`);
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  
  return response.json();
}

export interface ExportParams {
  source?: SourceType;
  range?: string;
}

export function getExportUrl(params: ExportParams = {}): string {
  const searchParams = new URLSearchParams();
  
  if (params.source) searchParams.set('source', params.source);
  if (params.range) searchParams.set('range', params.range);
  
  return `${API_URL}/api/export?${searchParams.toString()}`;
}

export interface StreamParams {
  source?: SourceType;
  factor?: number;
  pv_factor?: number;
  batt_limit?: number;
  soc_init?: number;
}

export function createStreamUrl(params: StreamParams = {}): string {
  const searchParams = new URLSearchParams();
  
  if (params.source) searchParams.set('source', params.source);
  if (params.factor !== undefined) searchParams.set('factor', params.factor.toString());
  if (params.pv_factor !== undefined) searchParams.set('pv_factor', params.pv_factor.toString());
  if (params.batt_limit !== undefined) searchParams.set('batt_limit', params.batt_limit.toString());
  if (params.soc_init !== undefined) searchParams.set('soc_init', params.soc_init.toString());
  
  return `${API_URL}/api/stream?${searchParams.toString()}`;
}
