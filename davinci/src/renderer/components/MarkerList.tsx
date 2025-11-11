import React, { useState } from 'react';
import { Marker } from '../types/marker';

interface MarkerListProps {
  markers: Marker[];
  totalCount: number;
  selectedMarkers: Set<number>;
  onToggleMarker: (markerId: number) => void;
  onToggleAll: () => void;
}

export const MarkerList: React.FC<MarkerListProps> = ({
  markers,
  totalCount,
  selectedMarkers,
  onToggleMarker,
  onToggleAll,
}) => {
  const [sortBy, setSortBy] = useState<'time' | 'type'>('time');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const formatTime = (seconds: number): string => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const getColorEmoji = (color: string | null): string => {
    const colorMap: { [key: string]: string } = {
      ResolveColorRed: '🔴',
      ResolveColorOrange: '🟠',
      ResolveColorYellow: '🟡',
      ResolveColorGreen: '🟢',
      ResolveColorCyan: '🔵',
      ResolveColorBlue: '🔵',
      ResolveColorPurple: '🟣',
      ResolveColorPink: '🌸',
    };
    return color ? colorMap[color] || '⚪' : '⚪';
  };

  const sortedMarkers = [...markers].sort((a, b) => {
    let comparison = 0;
    if (sortBy === 'time') {
      comparison = a.timestampSeconds - b.timestampSeconds;
    } else {
      comparison = a.type.localeCompare(b.type);
    }
    return sortOrder === 'asc' ? comparison : -comparison;
  });

  const allSelected = markers.length > 0 && markers.every((m) => selectedMarkers.has(m.id));

  return (
    <div className="marker-list">
      <h3>
        📋 Filtered Markers ({markers.length} visible / {totalCount} total)
      </h3>

      <div className="marker-table">
        <table>
          <thead>
            <tr>
              <th>
                <input type="checkbox" checked={allSelected} onChange={onToggleAll} />
              </th>
              <th
                className="sortable"
                onClick={() => {
                  if (sortBy === 'time') {
                    setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                  } else {
                    setSortBy('time');
                    setSortOrder('asc');
                  }
                }}
              >
                Time {sortBy === 'time' && (sortOrder === 'asc' ? '▲' : '▼')}
              </th>
              <th>Color</th>
              <th
                className="sortable"
                onClick={() => {
                  if (sortBy === 'type') {
                    setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                  } else {
                    setSortBy('type');
                    setSortOrder('asc');
                  }
                }}
              >
                Type {sortBy === 'type' && (sortOrder === 'asc' ? '▲' : '▼')}
              </th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {sortedMarkers.length === 0 ? (
              <tr>
                <td colSpan={5} className="empty-state">
                  No markers match the current filters
                </td>
              </tr>
            ) : (
              sortedMarkers.map((marker) => (
                <tr key={marker.id} className={selectedMarkers.has(marker.id) ? 'selected' : ''}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selectedMarkers.has(marker.id)}
                      onChange={() => onToggleMarker(marker.id)}
                    />
                  </td>
                  <td>{formatTime(marker.timestampSeconds)}</td>
                  <td>{getColorEmoji(marker.color)}</td>
                  <td>{marker.type}</td>
                  <td>{marker.subtype || marker.text}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
