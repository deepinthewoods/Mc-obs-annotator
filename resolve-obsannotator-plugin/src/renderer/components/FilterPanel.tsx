import React from 'react';
import { MarkerFilter } from '../types/marker';

interface FilterPanelProps {
  filters: MarkerFilter;
  eventTypes: string[];
  statistics: { [key: string]: number };
  maxTimestamp: number;
  onFilterChange: (key: keyof MarkerFilter, value: any) => void;
  onClearFilters: () => void;
}

export const FilterPanel: React.FC<FilterPanelProps> = ({
  filters,
  eventTypes,
  statistics,
  maxTimestamp,
  onFilterChange,
  onClearFilters,
}) => {
  const handleEventTypeToggle = (type: string) => {
    const currentTypes = filters.eventTypes || [];
    const newTypes = currentTypes.includes(type)
      ? currentTypes.filter(t => t !== type)
      : [...currentTypes, type];
    onFilterChange('eventTypes', newTypes);
  };

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="filter-panel">
      <h2>🔍 Filter Markers</h2>
      <div className="filter-content">
        <div className="filter-row">
          <label>Search:</label>
          <input
            type="text"
            value={filters.search || ''}
            onChange={(e) => onFilterChange('search', e.target.value)}
            placeholder="contains text"
            className="filter-input"
          />
        </div>

        <div className="filter-row">
          <label>Exclude:</label>
          <input
            type="text"
            value={filters.exclude || ''}
            onChange={(e) => onFilterChange('exclude', e.target.value)}
            placeholder="exclude text"
            className="filter-input"
          />
        </div>

        <div className="time-range-section">
          <label>Time Range:</label>
          <div className="time-inputs">
            <input
              type="number"
              value={filters.timeRangeStart || 0}
              onChange={(e) => onFilterChange('timeRangeStart', parseFloat(e.target.value))}
              min={0}
              max={maxTimestamp}
              step={1}
              className="time-input"
            />
            <span className="time-label">{formatTime(filters.timeRangeStart || 0)}</span>
            <span>to</span>
            <input
              type="number"
              value={filters.timeRangeEnd || maxTimestamp}
              onChange={(e) => onFilterChange('timeRangeEnd', parseFloat(e.target.value))}
              min={0}
              max={maxTimestamp}
              step={1}
              className="time-input"
            />
            <span className="time-label">{formatTime(filters.timeRangeEnd || maxTimestamp)}</span>
          </div>
        </div>

        <div className="event-types-section">
          <label>Event Types:</label>
          <div className="event-types-grid">
            {eventTypes.map(type => {
              const isSelected = !filters.eventTypes || filters.eventTypes.length === 0 || filters.eventTypes.includes(type);
              const count = statistics[type] || 0;
              return (
                <label key={type} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => handleEventTypeToggle(type)}
                  />
                  {type} ({count})
                </label>
              );
            })}
          </div>
        </div>

        <div className="button-row">
          <button onClick={onClearFilters} className="clear-button">
            Clear All Filters
          </button>
        </div>
      </div>
    </div>
  );
};
