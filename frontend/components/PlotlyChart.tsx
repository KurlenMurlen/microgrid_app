'use client';

import dynamic from 'next/dynamic';
import type { PlotConfig } from '@/lib/types';

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface PlotlyChartProps {
  config: PlotConfig;
  className?: string;
  height?: number;
}

export function PlotlyChart({ config, className = '', height = 300 }: PlotlyChartProps) {
  const getComputedColor = (varName: string) => {
    if (typeof window === 'undefined') return '#000000';
    return getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
  };

  const layout = {
    ...config.layout,
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: {
      color: getComputedColor('--text'),
    },
    margin: { t: 40, r: 12, b: 40, l: 50 },
    height,
  };

  return (
    <div className={`plot ${className}`}>
      <Plot
        data={config.data as any}
        layout={layout as any}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
}

export function ConsumptionPlot({ config, anomalies }: { config: PlotConfig; anomalies?: any[] }) {
  const plotData = [...config.data];
  
  if (anomalies && anomalies.length > 0) {
    plotData.push({
      x: anomalies.map((a) => a.x),
      y: anomalies.map((a) => a.y),
      text: anomalies.map((a) => a.text || ''),
      mode: 'markers',
      type: 'scatter',
      name: 'Anomalias',
      marker: { color: '#ef4444', size: 8, symbol: 'x' },
      hovertemplate: '%{text}<br>%{x}<br>%{y:.2f} kW',
    } as any);
  }

  return <PlotlyChart config={{ ...config, data: plotData }} />;
}
