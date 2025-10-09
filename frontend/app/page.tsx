'use client';

import { useState, useEffect } from 'react';
import { HomeView } from '@/components/HomeView';
import { TechnicalView } from '@/components/TechnicalView';
import { NavArrows } from '@/components/NavArrows';
import { useDashboard, useSSEStream, useInterval } from '@/lib/hooks';
import type { SourceType, AlgoType, ModeType } from '@/lib/types';

export default function Home() {
  const [currentView, setCurrentView] = useState<'home' | 'technical'>('home');
  const [source, setSource] = useState<SourceType>('db');
  const [algo, setAlgo] = useState<AlgoType>('rf');
  const [mode, setMode] = useState<ModeType>('normal');
  const [goal, setGoal] = useState('');
  const [socMin, setSocMin] = useState(0);
  const [simFactor, setSimFactor] = useState(1.0);
  const [simPv, setSimPv] = useState(1.0);
  const [simBatt, setSimBatt] = useState(2.0);
  const [simSoc, setSimSoc] = useState(50);

  // Fetch dashboard data
  const { data, loading, error, refresh } = useDashboard({
    source,
    algo,
    mode,
    goal: goal || undefined,
    soc_min: socMin,
    factor: source === 'sim' ? simFactor : undefined,
    pv_factor: source === 'sim' ? simPv : undefined,
    batt_limit: source === 'sim' ? simBatt : undefined,
    soc_init: source === 'sim' ? simSoc : undefined,
  });

  // SSE stream for live/sim modes
  const streamEnabled = source === 'live' || source === 'sim';
  const tick = useSSEStream(
    {
      source,
      factor: source === 'sim' ? simFactor : undefined,
      pv_factor: source === 'sim' ? simPv : undefined,
      batt_limit: source === 'sim' ? simBatt : undefined,
      soc_init: source === 'sim' ? simSoc : undefined,
    },
    streamEnabled
  );

  // Auto-refresh every 15 seconds
  useInterval(() => {
    if (!streamEnabled) {
      refresh();
    }
  }, 15000);

  // Handle hash navigation
  useEffect(() => {
    const hash = window.location.hash;
    if (hash === '#technical') {
      setCurrentView('technical');
    } else {
      setCurrentView('home');
    }
  }, []);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' && currentView === 'home') {
        setCurrentView('technical');
        window.location.hash = 'technical';
      } else if (e.key === 'ArrowLeft' && currentView === 'technical') {
        setCurrentView('home');
        window.location.hash = 'home';
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentView]);

  const navigateToHome = () => {
    setCurrentView('home');
    window.location.hash = 'home';
  };

  const navigateToTechnical = () => {
    setCurrentView('technical');
    window.location.hash = 'technical';
  };

  // Update data with SSE tick if in streaming mode
  const displayData = tick && streamEnabled ? { ...data!, kpis: tick.kpis, equipment: tick.equipment } : data;

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-500 mb-2">Error Loading Dashboard</h1>
          <p className="text-text-dim">{error.message}</p>
          <button
            onClick={refresh}
            className="mt-4 px-4 py-2 bg-accent-2 text-white rounded-full hover:bg-accent transition-smooth"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      <NavArrows
        currentView={currentView}
        onNavigateToHome={navigateToHome}
        onNavigateToTechnical={navigateToTechnical}
      />

      <div
        className={`view-container ${currentView === 'home' ? 'show-home' : 'show-technical'}`}
      >
        <HomeView data={displayData} />
        <TechnicalView
          data={displayData}
          source={source}
          algo={algo}
          mode={mode}
          goal={goal}
          socMin={socMin}
          simFactor={simFactor}
          simPv={simPv}
          simBatt={simBatt}
          simSoc={simSoc}
          onSourceChange={(v) => {
            setSource(v);
            refresh();
          }}
          onAlgoChange={(v) => {
            setAlgo(v);
            refresh();
          }}
          onModeChange={(v) => {
            setMode(v);
            refresh();
          }}
          onGoalChange={setGoal}
          onSocMinChange={setSocMin}
          onSimFactorChange={setSimFactor}
          onSimPvChange={setSimPv}
          onSimBattChange={setSimBatt}
          onSimSocChange={setSimSoc}
        />
      </div>

      {loading && (
        <div className="fixed bottom-4 right-4 px-4 py-2 bg-surface border border-border rounded-full shadow-card-md">
          <span className="text-text-dim text-sm">Carregando...</span>
        </div>
      )}
    </>
  );
}