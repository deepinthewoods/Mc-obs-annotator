import React, { useState, useEffect } from 'react';
import { SupercutOptions } from '../types/api';

interface SupercutPanelProps {
  markerCount: number;
  onGenerate: (bpm: number, noteDivision: string, options: SupercutOptions) => void;
  isLoading: boolean;
}

export const SupercutPanel: React.FC<SupercutPanelProps> = ({
  markerCount,
  onGenerate,
  isLoading,
}) => {
  const [bpm, setBpm] = useState(120);
  const [noteDivision, setNoteDivision] = useState<'whole' | 'half' | 'quarter' | 'eighth' | 'sixteenth'>('half');
  const [clipDuration, setClipDuration] = useState(1.0);
  const [addCrossfades, setAddCrossfades] = useState(true);
  const [crossfadeDuration, setCrossfadeDuration] = useState(0.2);
  const [sortChronologically, setSortChronologically] = useState(true);
  const [randomize, setRandomize] = useState(false);
  const [skipDuplicates, setSkipDuplicates] = useState(true);
  const [skipDuplicatesThreshold, setSkipDuplicatesThreshold] = useState(3.0);
  const [addBeatMarkers, setAddBeatMarkers] = useState(true);
  const [timelineName, setTimelineName] = useState('Supercut_120BPM');

  // Calculate clip duration based on BPM and note division
  useEffect(() => {
    const noteMultipliers = {
      whole: 4.0,
      half: 2.0,
      quarter: 1.0,
      eighth: 0.5,
      sixteenth: 0.25,
    };
    const beatDuration = 60.0 / bpm;
    const duration = beatDuration * noteMultipliers[noteDivision];
    setClipDuration(duration);
  }, [bpm, noteDivision]);

  // Update timeline name when BPM changes
  useEffect(() => {
    setTimelineName(`Supercut_${bpm}BPM`);
  }, [bpm]);

  const estimatedLength = markerCount * (60.0 / bpm);
  const formatTime = (seconds: number): string => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const handleGenerate = () => {
    const options: SupercutOptions = {
      sort_chronologically: sortChronologically,
      randomize: randomize,
      skip_duplicates_within_seconds: skipDuplicates ? skipDuplicatesThreshold : undefined,
      add_crossfades: addCrossfades,
      crossfade_duration: addCrossfades ? crossfadeDuration : undefined,
      add_beat_markers: addBeatMarkers,
      output_timeline_name: timelineName,
    };

    onGenerate(bpm, noteDivision, options);
  };

  return (
    <div className="supercut-panel">
      <h3>🎵 BPM Supercut Generator</h3>

      <div className="supercut-section">
        <label>Song BPM:</label>
        <input
          type="number"
          min={60}
          max={200}
          value={bpm}
          onChange={(e) => setBpm(parseInt(e.target.value) || 120)}
        />
        <span className="hint">Use a BPM detector if unsure</span>
      </div>

      <div className="supercut-section">
        <label>Note Division:</label>
        <div className="radio-group">
          {(['whole', 'half', 'quarter', 'eighth', 'sixteenth'] as const).map((division) => (
            <label key={division} className="radio-label">
              <input
                type="radio"
                name="noteDivision"
                value={division}
                checked={noteDivision === division}
                onChange={() => setNoteDivision(division)}
              />
              <span>{division.charAt(0).toUpperCase() + division.slice(1)}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="supercut-section">
        <label>Clip Duration:</label>
        <span className="value">
          {clipDuration.toFixed(2)} seconds (auto-calculated from BPM)
        </span>
      </div>

      <div className="supercut-section">
        <label>Source:</label>
        <span className="value">Use filtered markers above ({markerCount} events)</span>
        <span className="value">
          Estimated supercut length: {formatTime(estimatedLength)} ({markerCount} clips ×{' '}
          {clipDuration.toFixed(1)}s)
        </span>
      </div>

      <div className="supercut-section">
        <label>Options:</label>
        <div className="checkbox-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={addCrossfades}
              onChange={(e) => setAddCrossfades(e.target.checked)}
            />
            <span>Add crossfade transitions</span>
          </label>
          {addCrossfades && (
            <input
              type="number"
              min={0.1}
              max={1.0}
              step={0.1}
              value={crossfadeDuration}
              onChange={(e) => setCrossfadeDuration(parseFloat(e.target.value) || 0.2)}
              className="inline-input"
            />
          )}

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={sortChronologically}
              onChange={(e) => {
                setSortChronologically(e.target.checked);
                if (e.target.checked) setRandomize(false);
              }}
            />
            <span>Sort clips chronologically</span>
          </label>

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={randomize}
              onChange={(e) => {
                setRandomize(e.target.checked);
                if (e.target.checked) setSortChronologically(false);
              }}
            />
            <span>Randomize clip order</span>
          </label>

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={skipDuplicates}
              onChange={(e) => setSkipDuplicates(e.target.checked)}
            />
            <span>Skip duplicate events within</span>
          </label>
          {skipDuplicates && (
            <input
              type="number"
              min={0.5}
              max={10.0}
              step={0.5}
              value={skipDuplicatesThreshold}
              onChange={(e) => setSkipDuplicatesThreshold(parseFloat(e.target.value) || 3.0)}
              className="inline-input"
            />
          )}
          {skipDuplicates && <span>seconds</span>}

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={addBeatMarkers}
              onChange={(e) => setAddBeatMarkers(e.target.checked)}
            />
            <span>Add beat markers to timeline</span>
          </label>
        </div>
      </div>

      <div className="supercut-section">
        <label>Output Timeline Name:</label>
        <input
          type="text"
          value={timelineName}
          onChange={(e) => setTimelineName(e.target.value)}
        />
      </div>

      <div className="supercut-actions">
        <button
          onClick={handleGenerate}
          disabled={markerCount === 0 || isLoading}
          className="primary-button"
        >
          {isLoading ? 'Generating...' : 'Generate Supercut'}
        </button>
      </div>
    </div>
  );
};
