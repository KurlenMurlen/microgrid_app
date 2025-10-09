import { Card } from './Card';
import type { Alert } from '@/lib/types';

interface AlertsProps {
  alerts: Alert[];
}

export function Alerts({ alerts }: AlertsProps) {
  const alertColors = {
    info: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-800 dark:text-blue-200',
    warn: 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800 text-yellow-800 dark:text-yellow-200',
    crit: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-800 dark:text-red-200',
  };

  return (
    <Card>
      <div className="text-text-dim text-sm font-semibold mb-2.5">Alertas</div>
      <div className="grid gap-2">
        {alerts.length === 0 ? (
          <div className="px-3 py-2 rounded-lg bg-muted border border-border text-text-dim text-sm">
            Sem alertas
          </div>
        ) : (
          alerts.map((alert, idx) => (
            <div
              key={idx}
              className={`px-3 py-2 rounded-lg border text-sm ${alertColors[alert.level]}`}
            >
              {alert.message}
            </div>
          ))
        )}
      </div>
    </Card>
  );
}
