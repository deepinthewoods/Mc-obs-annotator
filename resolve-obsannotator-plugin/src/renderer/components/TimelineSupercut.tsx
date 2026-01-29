import React, { useState, useCallback } from 'react';
import { useTimelineSupercut } from '../hooks/useTimelineSupercut';

interface TimelineSupercutProps {
  isConnected: boolean;
}

export const TimelineSupercut: React.FC<TimelineSupercutProps> = ({ isConnected }) => {
  const {
    isLoading,
    filteredClips,
    timelineName,
    selectedIndices,
    enabledEventTypes,
    eventTypes,
    error,
    readTimeline,
    toggleClipSelection,
    selectAllFiltered,
    clearSelection,
    toggleEventType,
    enableAllEventTypes,
    disableAllEventTypes,
    generateSupercut
  } = useTimelineSupercut();

  const [bpm, setBpm] = useState(120);
  const [noteDivision, setNoteDivision] = useState('quarter');
  const [timelineNameInput, setTimelineNameInput] = useState('');
  const [randomize, setRandomize] = useState(false);
  const [addCrossfades, setAddCrossfades] = useState(false);
  const [crossfadeDuration, setCrossfadeDuration] = useState(0.2);
  const [addBeatMarkers, setAddBeatMarkers] = useState(true);

  const noteMultipliers: Record<string, number> = {
    whole: 4.0,
    half: 2.0,
    quarter: 1.0,
    eighth: 0.5,
    sixteenth: 0.25
  };

  const clipDuration = (60.0 / bpm) * (noteMultipliers[noteDivision] || 1.0);
  const selectedCount = Array.from(selectedIndices).filter(i =>
    filteredClips.some(c => c.index === i)
  ).length;
  const estimatedLength = selectedCount * clipDuration;

  const handleGenerate = useCallback(async () => {
    try {
      const result = await generateSupercut(bpm, noteDivision, {
        randomize,
        add_crossfades: addCrossfades,
        crossfade_duration: crossfadeDuration,
        add_beat_markers: addBeatMarkers,
        output_timeline_name: timelineNameInput || `Supercut_${bpm}BPM`
      });
      if (result) {
        alert(
          `Supercut created!\n\nTimeline: ${result.timeline_name}\nClips: ${result.clips_added}\nDuration: ${result.duration_seconds?.toFixed(2)}s`
        );
      }
    } catch {
      // error already set in hook
    }
  }, [bpm, noteDivision, randomize, addCrossfades, crossfadeDuration, addBeatMarkers, timelineNameInput, generateSupercut]);

  return (
    <div className="panel">
      <h2>Timeline Supercut</h2>
      <p className="panel-description">
        Read clips from the current Resolve timeline, filter by event type, and generate a BPM-synced supercut.
      </p>

      {!isConnected && (
        <div className="warning-banner">
          Not connected to DaVinci Resolve. Make sure Resolve is running.
        </div>
      )}

      {error && <div className="error-banner">{error}</div>}

      {/* Read Timeline */}
      <div className="form-group">
        <button
          onClick={readTimeline}
          disabled={isLoading || !isConnected}
          className="primary-button"
        >
          {isLoading ? 'Reading...' : 'Read Timeline'}
        </button>
        {timelineName && (
          <span className="info-text" style={{ marginLeft: '12px' }}>
            Timeline: <strong>{timelineName}</strong> ({filteredClips.length} clips shown)
          </span>
        )}
      </div>

      {/* Event Type Filters */}
      {Object.keys(eventTypes).length > 0 && (
        <div className="form-group">
          <label>Filter by Event Type:</label>
          <div className="event-type-controls">
            <button onClick={enableAllEventTypes} className="small-button">All</button>
            <button onClick={disableAllEventTypes} className="small-button">None</button>
          </div>
          <div className="checkbox-grid">
            {Object.entries(eventTypes).map(([type, count]) => (
              <label key={type} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={enabledEventTypes.has(type)}
                  onChange={() => toggleEventType(type)}
                />
                {type} ({count})
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Clip List */}
      {filteredClips.length > 0 && (
        <div className="form-group">
          <div className="list-header">
            <label>Clips ({selectedCount} of {filteredClips.length} selected)</label>
            <div>
              <button onClick={selectAllFiltered} className="small-button">Select All</button>
              <button onClick={clearSelection} className="small-button">Clear</button>
            </div>
          </div>
          <div className="clip-list">
            {filteredClips.map(clip => (
              <div
                key={clip.index}
                className={`clip-item ${selectedIndices.has(clip.index) ? 'selected' : ''}`}
                onClick={() => toggleClipSelection(clip.index)}
              >
                <input
                  type="checkbox"
                  checked={selectedIndices.has(clip.index)}
                  onChange={() => toggleClipSelection(clip.index)}
                />
                <span className="clip-name">{clip.name}</span>
                <span className="event-badge">{clip.eventType}</span>
                <span className="clip-duration">{clip.duration.toFixed(2)}s</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* BPM / Note Division Controls */}
      {filteredClips.length > 0 && (
        <>
          <div className="form-group">
            <label>BPM:</label>
            <input
              type="number"
              value={bpm}
              onChange={e => setBpm(Math.max(60, Math.min(200, parseInt(e.target.value) || 120)))}
              min={60}
              max={200}
              className="number-input"
            />
          </div>

          <div className="form-group">
            <label>Note Division:</label>
            <div className="radio-group">
              {['whole', 'half', 'quarter', 'eighth', 'sixteenth'].map(div => (
                <label key={div} className="radio-label">
                  <input
                    type="radio"
                    name="noteDivision"
                    value={div}
                    checked={noteDivision === div}
                    onChange={() => setNoteDivision(div)}
                  />
                  {div.charAt(0).toUpperCase() + div.slice(1)}
                </label>
              ))}
            </div>
            <span className="info-text">
              Clip duration: {clipDuration.toFixed(3)}s | Estimated length: {estimatedLength.toFixed(1)}s
            </span>
          </div>

          <div className="form-group">
            <label>Output Timeline Name:</label>
            <input
              type="text"
              value={timelineNameInput}
              onChange={e => setTimelineNameInput(e.target.value)}
              placeholder={`Supercut_${bpm}BPM`}
              className="text-input"
            />
          </div>

          {/* Options */}
          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={randomize}
                onChange={e => setRandomize(e.target.checked)}
              />
              Randomize clip order
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={addBeatMarkers}
                onChange={e => setAddBeatMarkers(e.target.checked)}
              />
              Add beat markers
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={addCrossfades}
                onChange={e => setAddCrossfades(e.target.checked)}
              />
              Add crossfade transitions
            </label>
            {addCrossfades && (
              <div className="sub-option">
                <label>Crossfade Duration (s):</label>
                <input
                  type="number"
                  value={crossfadeDuration}
                  onChange={e => setCrossfadeDuration(parseFloat(e.target.value) || 0.2)}
                  min={0.1}
                  max={2.0}
                  step={0.1}
                  className="number-input"
                />
              </div>
            )}
          </div>

          <button
            onClick={handleGenerate}
            disabled={isLoading || selectedCount === 0 || !isConnected}
            className="primary-button generate-button"
          >
            {isLoading ? 'Generating...' : `Generate Supercut (${selectedCount} clips)`}
          </button>
        </>
      )}
    </div>
  );
};
