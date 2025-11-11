import React from 'react';

interface StatusBarProps {
  isConnected: boolean;
  markerCount: number;
}

export const StatusBar: React.FC<StatusBarProps> = ({ isConnected, markerCount }) => {
  return (
    <div className="status-bar">
      <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
        {isConnected ? '✅' : '❌'} {isConnected ? 'Connected to DaVinci Resolve' : 'Not connected to Resolve'}
      </span>
      <span className="marker-count">
        {markerCount > 0 && `| ${markerCount} markers ready`}
      </span>
    </div>
  );
};
