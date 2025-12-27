import React from 'react';
import { Marker } from '../types/marker';

interface MarkerListProps {
  markers: Marker[];
  selectedIds: Set<number>;
  onToggleSelection: (id: number) => void;
  onSelectAll: () => void;
  onClearSelection: () => void;
}

const COLOR_EMOJI_MAP: { [key: string]: string } = {
  ResolveColorRed: '🔴',
  ResolveColorOrange: '🟠',
  ResolveColorYellow: '🟡',
  ResolveColorGreen: '🟢',
  ResolveColorCyan: '🔵',
  ResolveColorBlue: '🔵',
  ResolveColorPurple: '🟣',
  ResolveColorPink: '🩷',
  Red: '🔴',
  Orange: '🟠',
  Yellow: '🟡',
  Green: '🟢',
  Cyan: '🔵',
  Blue: '🔵',
  Purple: '🟣',
  Pink: '🩷',
};

export const MarkerList: React.FC<MarkerListProps> = ({
  markers,
  selectedIds,
  onToggleSelection,
  onSelectAll,
  onClearSelection,
}) => {
  const formatTimecode = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getColorEmoji = (color: string | null): string => {
    if (!color) return '⚪';
    return COLOR_EMOJI_MAP[color] || '⚪';
  };

  const allSelected = markers.length > 0 && markers.every(m => selectedIds.has(m.id));

  return (
    <div className="marker-list">
      <div className="marker-list-header">
        <h2>📋 Filtered Markers ({markers.length} total)</h2>
        <div className="selection-buttons">
          {allSelected ? (
            <button onClick={onClearSelection} className="select-button">
              Clear Selection
            </button>
          ) : (
            <button onClick={onSelectAll} className="select-button">
              Select All
            </button>
          )}
        </div>
      </div>

      <div className="marker-table-container">
        <table className="marker-table">
          <thead>
            <tr>
              <th className="checkbox-column">
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={allSelected ? onClearSelection : onSelectAll}
                />
              </th>
              <th>Time</th>
              <th>Color</th>
              <th>Type</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {markers.length === 0 ? (
              <tr>
                <td colSpan={5} className="empty-message">
                  No markers to display
                </td>
              </tr>
            ) : (
              markers.map(marker => (
                <tr
                  key={marker.id}
                  className={selectedIds.has(marker.id) ? 'selected' : ''}
                >
                  <td className="checkbox-column">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(marker.id)}
                      onChange={() => onToggleSelection(marker.id)}
                    />
                  </td>
                  <td>{formatTimecode(marker.timestampSeconds)}</td>
                  <td className="color-column">{getColorEmoji(marker.color)}</td>
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
