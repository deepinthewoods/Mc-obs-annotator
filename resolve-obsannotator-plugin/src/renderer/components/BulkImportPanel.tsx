import React, { useState, useCallback, useEffect } from 'react';
import { useBulkImport } from '../hooks/useBulkImport';
import { Session, SilenceRemovalSettings, MulticamTrack } from '../types/bulk';
import { loadPersistedSettings, savePersistedSettings } from '../hooks/usePersistedSettings';

interface BulkImportPanelProps {
  isConnected: boolean;
}

export const BulkImportPanel: React.FC<BulkImportPanelProps> = ({ isConnected }) => {
  const persisted = loadPersistedSettings();
  const [sourceFolder, setSourceFolder] = useState(persisted.sourceFolder || '');
  const [outputFolder, setOutputFolder] = useState(persisted.outputFolder || '');

  const bulkImport = useBulkImport();

  // Persist folders when they change
  useEffect(() => {
    savePersistedSettings({ sourceFolder, outputFolder });
  }, [sourceFolder, outputFolder]);

  const handleBrowseFolder = useCallback(async (setter: (path: string) => void) => {
    const { ipcRenderer } = require('electron');
    const dirPath = await ipcRenderer.invoke('select-directory');
    if (dirPath) {
      setter(dirPath);
    }
  }, []);

  const handleScan = useCallback(async () => {
    if (!sourceFolder) {
      alert('Please enter a source folder path');
      return;
    }

    try {
      await bulkImport.scanFolder(sourceFolder);
    } catch (error) {
      alert(`Failed to scan folder: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }, [sourceFolder, bulkImport]);

  const handleProcessAll = useCallback(async (resume: boolean = false) => {
    if (!sourceFolder || !outputFolder) {
      alert('Please enter source and output folder paths');
      return;
    }

    if (bulkImport.selectedSessionIds.size === 0) {
      alert('Please select at least one session to process');
      return;
    }

    try {
      const result = await bulkImport.processAll(sourceFolder, outputFolder, undefined, resume);
      if (result) {
        alert(
          `Processing complete!\n\n` +
          `Extracted: ${result.extracted} clips\n` +
          (result.skippedExisting > 0 ? `Already existed: ${result.skippedExisting}\n` : '') +
          `Skipped (black): ${result.skipped}\n` +
          `Errors: ${result.errors}`
        );
      }
    } catch (error) {
      alert(`Failed to process: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }, [sourceFolder, outputFolder, bulkImport]);

  const formatSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
  };

  const formatDuration = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const progressPercent = bulkImport.totalClips > 0
    ? Math.round((bulkImport.currentClip / bulkImport.totalClips) * 100)
    : 0;

  return (
    <div className="bulk-import-panel">
      <h2>Bulk Import</h2>

      <div className="bulk-import-content">
        {/* Folder Selection */}
        <div className="bulk-folders">
          <div className="file-input-row">
            <label>Source Folder:</label>
            <input
              type="text"
              value={sourceFolder}
              onChange={(e) => setSourceFolder(e.target.value)}
              placeholder="E:/recordings"
              className="file-input"
            />
            <button
              onClick={() => handleBrowseFolder(setSourceFolder)}
              className="browse-button"
            >
              Browse
            </button>
            <button
              onClick={handleScan}
              disabled={bulkImport.isScanning || !sourceFolder}
              className="browse-button"
            >
              {bulkImport.isScanning ? 'Scanning...' : 'Scan'}
            </button>
          </div>

          <div className="file-input-row">
            <label>Output Folder:</label>
            <input
              type="text"
              value={outputFolder}
              onChange={(e) => setOutputFolder(e.target.value)}
              placeholder="D:/extracted"
              className="file-input"
            />
            <button
              onClick={() => handleBrowseFolder(setOutputFolder)}
              className="browse-button"
            >
              Browse
            </button>
          </div>
        </div>

        {/* Settings */}
        <div className="bulk-settings">
          <h3>Settings</h3>
          <div className="settings-grid">
            <div className="setting-row">
              <label>Chapter buffer:</label>
              <input
                type="number"
                value={bulkImport.settings.chapterBuffer}
                onChange={(e) => bulkImport.updateSettings({ chapterBuffer: parseFloat(e.target.value) })}
                min={0}
                max={5}
                step={0.1}
                className="inline-input"
              />
              <span className="info-text">seconds before/after</span>
            </div>

            <div className="checkbox-options">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={bulkImport.settings.mergeOverlapping}
                  onChange={(e) => bulkImport.updateSettings({ mergeOverlapping: e.target.checked })}
                />
                Merge overlapping clips
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={bulkImport.settings.skipBlackClips}
                  onChange={(e) => bulkImport.updateSettings({ skipBlackClips: e.target.checked })}
                />
                Skip entirely black clips
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={bulkImport.settings.createTimelines}
                  onChange={(e) => bulkImport.updateSettings({ createTimelines: e.target.checked })}
                  disabled={!isConnected}
                />
                Create Resolve timelines
                {!isConnected && <span className="info-text">(Resolve not connected)</span>}
              </label>
            </div>
          </div>
        </div>

        {/* Silence Removal Settings */}
        <div className="bulk-settings">
          <h3>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={bulkImport.settings.silenceRemoval.enabled}
                onChange={(e) => bulkImport.updateSettings({
                  silenceRemoval: { ...bulkImport.settings.silenceRemoval, enabled: e.target.checked }
                })}
              />
              Silence Removal
            </label>
            <span className="info-text">(recording clips only)</span>
          </h3>
          {bulkImport.settings.silenceRemoval.enabled && (
            <div className="settings-grid">
              <div className="setting-row">
                <label>Silence threshold:</label>
                <input
                  type="range"
                  min={-50}
                  max={-20}
                  step={1}
                  value={bulkImport.settings.silenceRemoval.silenceThresholdDb}
                  onChange={(e) => bulkImport.updateSettings({
                    silenceRemoval: { ...bulkImport.settings.silenceRemoval, silenceThresholdDb: parseFloat(e.target.value) }
                  })}
                  className="inline-input"
                />
                <span className="info-text">{bulkImport.settings.silenceRemoval.silenceThresholdDb} dB</span>
              </div>

              <div className="setting-row">
                <label>Min silence duration:</label>
                <input
                  type="range"
                  min={0.3}
                  max={3.0}
                  step={0.1}
                  value={bulkImport.settings.silenceRemoval.minSilenceDuration}
                  onChange={(e) => bulkImport.updateSettings({
                    silenceRemoval: { ...bulkImport.settings.silenceRemoval, minSilenceDuration: parseFloat(e.target.value) }
                  })}
                  className="inline-input"
                />
                <span className="info-text">{bulkImport.settings.silenceRemoval.minSilenceDuration}s</span>
              </div>

              <div className="setting-row">
                <label>Speech padding:</label>
                <input
                  type="range"
                  min={0.05}
                  max={0.5}
                  step={0.05}
                  value={bulkImport.settings.silenceRemoval.padding}
                  onChange={(e) => bulkImport.updateSettings({
                    silenceRemoval: { ...bulkImport.settings.silenceRemoval, padding: parseFloat(e.target.value) }
                  })}
                  className="inline-input"
                />
                <span className="info-text">{bulkImport.settings.silenceRemoval.padding}s</span>
              </div>

              <div className="setting-row">
                <label>Max silence for auto-reset:</label>
                <input
                  type="range"
                  min={5}
                  max={60}
                  step={1}
                  value={bulkImport.settings.silenceRemoval.maxSilenceForReset}
                  onChange={(e) => bulkImport.updateSettings({
                    silenceRemoval: { ...bulkImport.settings.silenceRemoval, maxSilenceForReset: parseFloat(e.target.value) }
                  })}
                  className="inline-input"
                />
                <span className="info-text">{bulkImport.settings.silenceRemoval.maxSilenceForReset}s</span>
              </div>
            </div>
          )}
        </div>

        {/* Multicam Cameras */}
        <div className="bulk-settings">
          <h3>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={bulkImport.settings.multicam.enabled}
                onChange={(e) => bulkImport.updateSettings({
                  multicam: { ...bulkImport.settings.multicam, enabled: e.target.checked }
                })}
              />
              Multicam Cameras
            </label>
          </h3>
          {bulkImport.settings.multicam.enabled && (
            <div className="settings-grid">
              <div className="info-text" style={{ marginBottom: '8px' }}>
                Main video (no prefix) is always Camera 1. Map filename prefixes to additional cameras.
              </div>
              {bulkImport.settings.multicam.tracks.map((track, index) => (
                <div key={index} className="setting-row" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <input
                    type="text"
                    value={track.prefix}
                    onChange={(e) => {
                      const newTracks = [...bulkImport.settings.multicam.tracks];
                      newTracks[index] = { ...newTracks[index], prefix: e.target.value };
                      bulkImport.updateSettings({
                        multicam: { ...bulkImport.settings.multicam, tracks: newTracks }
                      });
                    }}
                    placeholder="prefix"
                    className="inline-input"
                    style={{ width: '80px' }}
                  />
                  <input
                    type="text"
                    value={track.trackName}
                    onChange={(e) => {
                      const newTracks = [...bulkImport.settings.multicam.tracks];
                      newTracks[index] = { ...newTracks[index], trackName: e.target.value };
                      bulkImport.updateSettings({
                        multicam: { ...bulkImport.settings.multicam, tracks: newTracks }
                      });
                    }}
                    placeholder="Track Name"
                    className="inline-input"
                    style={{ width: '120px' }}
                  />
                  <span className="info-text">Cam</span>
                  <input
                    type="number"
                    value={track.cameraNumber}
                    onChange={(e) => {
                      const newTracks = [...bulkImport.settings.multicam.tracks];
                      newTracks[index] = { ...newTracks[index], cameraNumber: parseInt(e.target.value) || 2 };
                      bulkImport.updateSettings({
                        multicam: { ...bulkImport.settings.multicam, tracks: newTracks }
                      });
                    }}
                    min={2}
                    max={9}
                    className="inline-input"
                    style={{ width: '50px' }}
                  />
                  <button
                    onClick={() => {
                      const newTracks = bulkImport.settings.multicam.tracks.filter((_, i) => i !== index);
                      bulkImport.updateSettings({
                        multicam: { ...bulkImport.settings.multicam, tracks: newTracks }
                      });
                    }}
                    className="clear-button"
                    style={{ padding: '2px 6px' }}
                  >
                    Remove
                  </button>
                </div>
              ))}
              <button
                onClick={() => {
                  const nextCam = bulkImport.settings.multicam.tracks.length > 0
                    ? Math.max(...bulkImport.settings.multicam.tracks.map(t => t.cameraNumber)) + 1
                    : 2;
                  const newTrack: MulticamTrack = {
                    prefix: `spec${nextCam - 1}`,
                    trackName: `Spectator ${nextCam - 1}`,
                    cameraNumber: nextCam
                  };
                  bulkImport.updateSettings({
                    multicam: {
                      ...bulkImport.settings.multicam,
                      tracks: [...bulkImport.settings.multicam.tracks, newTrack]
                    }
                  });
                }}
                className="browse-button"
                style={{ marginTop: '4px' }}
              >
                + Add Track
              </button>
              <div className="info-text" style={{ marginTop: '8px' }}>
                After import, right-click timeline in Media Pool &rarr; "Convert Timeline to Multicam Clip" for Speed Editor.
              </div>
            </div>
          )}
        </div>

        {/* Event Type Filter */}
        {Object.keys(bulkImport.availableEventTypes).length > 0 && (
          <div className="bulk-settings">
            <div className="event-type-header">
              <h3>Event Types</h3>
              <div className="selection-buttons">
                <button onClick={bulkImport.enableAllEventTypes} className="select-button">
                  All
                </button>
                <button onClick={bulkImport.disableAllEventTypes} className="clear-button">
                  None
                </button>
              </div>
            </div>
            <div className="event-types-grid">
              {Object.entries(bulkImport.availableEventTypes)
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([eventType, count]) => (
                  <label key={eventType} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={bulkImport.settings.enabledEventTypes.includes(eventType)}
                      onChange={() => bulkImport.toggleEventType(eventType)}
                    />
                    {eventType} ({count})
                  </label>
                ))}
            </div>
          </div>
        )}

        {/* Session List */}
        {bulkImport.sessions.length > 0 && (
          <div className="bulk-sessions">
            <div className="sessions-header">
              <h3>Sessions Found: {bulkImport.sessions.length} ({bulkImport.totalSize})</h3>
              <div className="selection-buttons">
                <button onClick={bulkImport.selectAllSessions} className="select-button">
                  Select All
                </button>
                <button onClick={bulkImport.clearSelection} className="clear-button">
                  Clear
                </button>
              </div>
            </div>

            <div className="sessions-list">
              {bulkImport.sessions.map((session: Session) => (
                <div
                  key={session.id}
                  className={`session-item ${bulkImport.selectedSessionIds.has(session.id) ? 'selected' : ''}`}
                  onClick={() => bulkImport.toggleSessionSelection(session.id)}
                >
                  <input
                    type="checkbox"
                    checked={bulkImport.selectedSessionIds.has(session.id)}
                    onChange={() => bulkImport.toggleSessionSelection(session.id)}
                    onClick={(e) => e.stopPropagation()}
                  />
                  <div className="session-info">
                    <span className="session-name">
                      {session.videoFile.split(/[/\\]/).pop()}
                    </span>
                    <span className="session-details">
                      {formatSize(session.videoSize)} | {formatDuration(session.duration)} | {session.markerSummary.total} markers
                    </span>
                  </div>
                  <div className="session-markers">
                    <span className="marker-badge chapters">{session.markerSummary.chapters} chapters</span>
                    {session.markerSummary.startEndPairs > 0 && (
                      <span className="marker-badge recordings">{session.markerSummary.startEndPairs} recordings</span>
                    )}
                    {session.markerSummary.pois > 0 && (
                      <span className="marker-badge pois">{session.markerSummary.pois} POIs</span>
                    )}
                    {session.multicamFiles && session.multicamFiles.length > 0 && (
                      <span className="marker-badge" title={session.multicamFiles.map(f => f.prefix).join(', ')}>
                        Multicam: {session.multicamFiles.length + 1} angles
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Action Buttons */}
            <div className="bulk-actions">
              <button
                onClick={() => handleProcessAll(false)}
                disabled={
                  bulkImport.isExtracting ||
                  bulkImport.selectedSessionIds.size === 0 ||
                  !outputFolder
                }
                className="generate-button"
              >
                {bulkImport.isExtracting ? 'Processing...' : `Process ${bulkImport.selectedSessionIds.size} Session(s)`}
              </button>
              <button
                onClick={() => handleProcessAll(true)}
                disabled={
                  bulkImport.isExtracting ||
                  bulkImport.selectedSessionIds.size === 0 ||
                  !outputFolder
                }
                className="generate-button"
                title="Resume processing, skipping clips that already exist in the output folder"
              >
                Resume
              </button>
            </div>
          </div>
        )}

        {/* Progress Display */}
        {bulkImport.isExtracting && (
          <div className="bulk-progress">
            <h3>{bulkImport.isPaused ? 'Paused' : 'Processing...'}</h3>

            <div className="progress-section">
              <div className="progress-label">
                Clip {bulkImport.currentClip} of {bulkImport.totalClips}: {bulkImport.currentFile}
              </div>
              <div className="progress-bar">
                <div
                  className="progress-fill clip-progress"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
              <div className="progress-percent">
                {progressPercent}%
                {bulkImport.estimatedTimeRemaining && (
                  <span className="eta"> — {bulkImport.estimatedTimeRemaining}</span>
                )}
              </div>
            </div>

            <div className="progress-stats">
              <span className="stat extracted">Extracted: {bulkImport.extractedCount}</span>
              {bulkImport.skippedExistingCount > 0 && (
                <span className="stat skipped-existing">Already existed: {bulkImport.skippedExistingCount}</span>
              )}
              <span className="stat skipped">Skipped (black): {bulkImport.skippedCount}</span>
              <span className="stat errors">Errors: {bulkImport.errorCount}</span>
            </div>

            <div className="progress-buttons">
              <button
                onClick={bulkImport.isPaused ? bulkImport.resumeProcessing : bulkImport.pauseProcessing}
                className="pause-button"
              >
                {bulkImport.isPaused ? 'Resume' : 'Pause'}
              </button>
              <button
                onClick={bulkImport.cancelProcessing}
                className="cancel-button"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Error Display */}
        {bulkImport.error && (
          <div className="bulk-error">
            <span className="error-icon">Error:</span>
            <span className="error-message">{bulkImport.error}</span>
            <button onClick={bulkImport.clearError} className="clear-button">
              Dismiss
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
