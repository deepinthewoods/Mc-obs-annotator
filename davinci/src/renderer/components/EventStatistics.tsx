import React from 'react';
import { MarkerStatistics } from '../types/marker';

interface EventStatisticsProps {
  statistics: MarkerStatistics;
  total: number;
}

const EVENT_COLORS: { [key: string]: string } = {
  Combat: '#ff4444',
  Boss: '#aa44ff',
  Block: '#4488ff',
  Item: '#44ff44',
  Exploration: '#44ffff',
  Achievement: '#ffff44',
  Explosion: '#ff8844',
  Manual: '#888888',
};

export const EventStatistics: React.FC<EventStatisticsProps> = ({ statistics, total }) => {
  return (
    <div className="event-statistics">
      <h3>📊 Event Statistics</h3>
      <div className="stats-grid">
        {Object.entries(statistics).map(([type, count]) => (
          <div key={type} className="stat-item">
            <span
              className="stat-color"
              style={{ backgroundColor: EVENT_COLORS[type] || '#888888' }}
            ></span>
            <span className="stat-label">{type}:</span>
            <span className="stat-count">{count}</span>
          </div>
        ))}
        <div className="stat-item stat-total">
          <span className="stat-label">Total:</span>
          <span className="stat-count">{total}</span>
        </div>
      </div>
    </div>
  );
};
