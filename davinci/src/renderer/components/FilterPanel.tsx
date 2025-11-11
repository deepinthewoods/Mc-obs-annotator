import React from 'react';
import { FilterOptions } from '../types/api';
import { MarkerStatistics } from '../types/marker';

interface FilterPanelProps {
  filters: FilterOptions;
  onFiltersChange: (filters: FilterOptions) => void;
  statistics: MarkerStatistics;
  videoDuration: number;
}

export const FilterPanel: React.FC<FilterPanelProps> = ({
  filters,
  onFiltersChange,
  statistics,
  videoDuration,
}) => {
  const handleSearchChange = (value: string) => {
    onFiltersChange({ ...filters, search: value || undefined });
  };

  const handleExcludeChange = (value: string) => {
    onFiltersChange({ ...filters, exclude: value || undefined });
  };

  const handleEventTypeToggle = (eventType: string) => {
    const currentTypes = filters.eventTypes || [];
    const newTypes = currentTypes.includes(eventType)
      ? currentTypes.filter((t) => t !== eventType)
      : [...currentTypes, eventType];

    onFiltersChange({
      ...filters,
      eventTypes: newTypes.length === Object.keys(statistics).length ? undefined : newTypes,
    });
  };

  const handleTimeRangeChange = (start?: number, end?: number) => {
    onFiltersChange({
      ...filters,
      timeRangeStart: start,
      timeRangeEnd: end,
    });
  };

  const clearFilters = () => {
    onFiltersChange({});
  };

  const formatTime = (seconds: number): string => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const selectedTypes = filters.eventTypes || Object.keys(statistics);

  return (
    <div className="filter-panel">
      <h3>🔍 Filter Markers</h3>

      <div className="filter-section">
        <label>Search:</label>
        <input
          type="text"
          placeholder="Search text..."
          value={filters.search || ''}
          onChange={(e) => handleSearchChange(e.target.value)}
        />
      </div>

      <div className="filter-section">
        <label>Exclude:</label>
        <input
          type="text"
          placeholder="Exclude text..."
          value={filters.exclude || ''}
          onChange={(e) => handleExcludeChange(e.target.value)}
        />
      </div>

      <div className="filter-section">
        <label>Time Range:</label>
        <div className="time-range-inputs">
          <input
            type="number"
            min={0}
            max={videoDuration}
            placeholder="Start (s)"
            value={filters.timeRangeStart || ''}
            onChange={(e) =>
              handleTimeRangeChange(
                e.target.value ? parseFloat(e.target.value) : undefined,
                filters.timeRangeEnd
              )
            }
          />
          <span>to</span>
          <input
            type="number"
            min={0}
            max={videoDuration}
            placeholder="End (s)"
            value={filters.timeRangeEnd || ''}
            onChange={(e) =>
              handleTimeRangeChange(
                filters.timeRangeStart,
                e.target.value ? parseFloat(e.target.value) : undefined
              )
            }
          />
        </div>
      </div>

      <div className="filter-section">
        <label>Event Types:</label>
        <div className="event-type-checkboxes">
          {Object.entries(statistics).map(([type, count]) => (
            <label key={type} className="checkbox-label">
              <input
                type="checkbox"
                checked={selectedTypes.includes(type)}
                onChange={() => handleEventTypeToggle(type)}
              />
              <span>
                {type} ({count})
              </span>
            </label>
          ))}
        </div>
      </div>

      <div className="filter-actions">
        <button onClick={clearFilters}>Clear All Filters</button>
      </div>
    </div>
  );
};
