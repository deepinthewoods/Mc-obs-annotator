import React from 'react';

interface EventStatisticsProps {
  statistics: { [key: string]: number };
  totalCount: number;
}

const EVENT_TYPE_COLORS: { [key: string]: string } = {
  Combat: '🔴',
  Boss: '🟣',
  Block: '🔵',
  Item: '🟢',
  Exploration: '🔵',
  Achievement: '🟡',
  Explosion: '🟠',
  Manual: '🟡',
};

export const EventStatistics: React.FC<EventStatisticsProps> = ({
  statistics,
  totalCount,
}) => {
  const entries = Object.entries(statistics).sort((a, b) => b[1] - a[1]);

  return (
    <div className="event-statistics">
      <h2>📊 Event Statistics</h2>
      <div className="statistics-grid">
        {entries.map(([type, count]) => (
          <div key={type} className="stat-item">
            {EVENT_TYPE_COLORS[type] || '⚪'} {type}: {count}
          </div>
        ))}
        {entries.length > 0 && (
          <div className="stat-item total">
            Total: {totalCount}
          </div>
        )}
      </div>
    </div>
  );
};
