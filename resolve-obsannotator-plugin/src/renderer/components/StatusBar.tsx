import React from 'react';

interface StatusBarProps {
  isConnected: boolean;
  projectOpen: boolean;
  markerCount: number;
  error?: string | null;
}

export const StatusBar: React.FC<StatusBarProps> = ({
  isConnected,
  projectOpen,
  markerCount,
  error,
}) => {
  return (
    <div className={`status-bar ${error ? 'error' : ''}`}>
      {error ? (
        <>
          <span className="status-icon">❌</span>
          <span>Error: {error}</span>
        </>
      ) : (
        <>
          <span className="status-icon">
            {isConnected && projectOpen ? '✅' : '⚠️'}
          </span>
          <span>
            {isConnected
              ? projectOpen
                ? `Connected to DaVinci Resolve | ${markerCount} markers ready`
                : 'Connected to DaVinci Resolve | No project open'
              : 'Not connected to DaVinci Resolve'}
          </span>
        </>
      )}
    </div>
  );
};
