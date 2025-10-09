// Custom React hooks for Microgrid Dashboard

import { useState, useEffect, useCallback, useRef } from 'react';
import { fetchDashboard, createStreamUrl, type DashboardParams, type StreamParams } from './api';
import type { DashboardResponse, StreamTick } from './types';

export function useDashboard(params: DashboardParams, enabled = true) {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const refresh = useCallback(async () => {
    if (!enabled) return;
    
    try {
      setLoading(true);
      setError(null);
      const result = await fetchDashboard(params);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, [params, enabled]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { data, loading, error, refresh };
}

export function useSSEStream(params: StreamParams, enabled: boolean) {
  const [tick, setTick] = useState<StreamTick | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!enabled) {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      return;
    }

    const url = createStreamUrl(params);
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.addEventListener('tick', (e) => {
      try {
        const data = JSON.parse(e.data) as StreamTick;
        setTick(data);
      } catch (err) {
        console.error('Failed to parse SSE message:', err);
      }
    });

    eventSource.onerror = () => {
      // EventSource will automatically retry
      console.warn('SSE connection error, will retry...');
    };

    return () => {
      eventSource.close();
    };
  }, [params, enabled]);

  return tick;
}

export function useInterval(callback: () => void, delay: number | null) {
  const savedCallback = useRef(callback);

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (delay === null) return;

    const id = setInterval(() => savedCallback.current(), delay);
    return () => clearInterval(id);
  }, [delay]);
}
