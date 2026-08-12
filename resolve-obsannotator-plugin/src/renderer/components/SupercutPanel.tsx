import React, { useState, useCallback, useMemo } from 'react';
import { Marker } from '../types/marker';
import { SupercutOptions } from '../types/api';

interface SupercutPanelProps {
  markers: Marker[];
  videoFile: string;
  onGenerate: (bpm: number, noteDivision: string, options: SupercutOptions) => void;
  loading?: boolean;
}

type NoteDivision = 'whole' | 'half' | 'quarter' | 'eighth' | 'sixteenth';

export const SupercutPanel: React.FC<SupercutPanelProps> = ({
  markers,
  videoFile,
  onGenerate,
  loading = false,
}) => {
  const [bpm, setBpm] = useState<number>(120);
  const [noteDivision, setNoteDivision] = useState<NoteDivision>('half');
  const [sortChronologically, setSortChronologically] = useState(true);
  const [randomize, setRandomize] = useState(false);
  const [skipDuplicates, setSkipDuplicates] = useState(true);
  const [duplicateThreshold, setDuplicateThreshold] = useState(3.0);
  const [addCrossfades, setAddCrossfades] = useState(true);
  const [crossfadeDuration, setCrossfadeDuration] = useState(0.2);
  const [addBeatMarkers, setAddBeatMarkers] = useState(true);
  const [timelineName, setTimelineName] = useState('Supercut_120BPM');

  const clipDuration = useMemo(() => {
    const noteMultipliers = {
      whole: 4.0,
      half: 2.0,
      quarter: 1.0,
      eighth: 0.5,
      sixteenth: 0.25,
    };
    const beatDuration = 60.0 / bpm;
    return beatDuration * noteMultipliers[noteDivision];
  }, [bpm, noteDivision]);

  const estimatedLength = useMemo(() => {
    const beatInterval = 60.0 / bpm;
    const totalSeconds = markers.length * beatInterval;
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = Math.floor(totalSeconds % 60);
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  }, [markers.length, bpm]);

  const handleGenerate = useCallback(() => {
    const options: SupercutOptions = {
      sort_chronologically: sortChronologically,
      randomize,
      skip_duplicates_within_seconds: skipDuplicates ? duplicateThreshold : 0,
      add_crossfades: addCrossfades,
      crossfade_duration: crossfadeDuration,
      add_beat_markers: addBeatMarkers,
      output_timeline_name: timelineName,
    };

    onGenerate(bpm, noteDivision, options);
  }, [
    bpm,
    noteDivision,
    sortChronologically,
    randomize,
    skipDuplicates,
    duplicateThreshold,
    addCrossfades,
    crossfadeDuration,
    addBeatMarkers,
    timelineName,
    onGenerate,
  ]);

  return (
    <div className="supercut-panel">
      <h2>🎵 BPM Supercut Generator</h2>
      <div className="supercut-content">
        <div className="form-row">
          <label>Song BPM:</label>
          <input
            type="number"
            value={bpm}
            onChange={(e) => {
              const newBpm = parseInt(e.target.value);
              setBpm(newBpm);
              setTimelineName(`Supercut_${newBpm}BPM`);
            }}
            min={60}
            max={200}
            className="bpm-input"
          />
          <span className="info-text">ℹ️ Use a BPM detector if unsure</span>
        </div>

        <div className="form-row">
          <label>Note Division:</label>
          <div className="radio-group">
            <label>
              <input
                type="radio"
                value="whole"
                checked={noteDivision === 'whole'}
                onChange={() => setNoteDivision('whole')}
              />
              Whole
            </label>
            <label>
              <input
                type="radio"
                value="half"
                checked={noteDivision === 'half'}
                onChange={() => setNoteDivision('half')}
              />
              Half
            </label>
            <label>
              <input
                type="radio"
                value="quarter"
                checked={noteDivision === 'quarter'}
                onChange={() => setNoteDivision('quarter')}
              />
              Quarter
            </label>
            <label>
              <input
                type="radio"
                value="eighth"
                checked={noteDivision === 'eighth'}
                onChange={() => setNoteDivision('eighth')}
              />
              Eighth
            </label>
            <label>
              <input
                type="radio"
                value="sixteenth"
                checked={noteDivision === 'sixteenth'}
                onChange={() => setNoteDivision('sixteenth')}
              />
              Sixteenth
            </label>
          </div>
        </div>

        <div className="form-row">
          <label>Clip Duration:</label>
          <span>{clipDuration.toFixed(2)} seconds (auto-calculated from BPM)</span>
        </div>

        <div className="form-row">
          <label>Source:</label>
          <span>Use filtered markers above ({markers.length} events)</span>
        </div>

        <div className="form-row">
          <label>Estimated Length:</label>
          <span>{estimatedLength} ({markers.length} clips × {clipDuration.toFixed(2)}s)</span>
        </div>

        <div className="options-section">
          <label>Options:</label>
          <div className="checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={addCrossfades}
                onChange={(e) => setAddCrossfades(e.target.checked)}
              />
              Add crossfade transitions (
              <input
                type="number"
                value={crossfadeDuration}
                onChange={(e) => setCrossfadeDuration(parseFloat(e.target.value))}
                min={0.1}
                max={2.0}
                step={0.1}
                className="inline-input"
                disabled={!addCrossfades}
              />
              seconds)
            </label>
            <label>
              <input
                type="checkbox"
                checked={sortChronologically}
                onChange={(e) => {
                  setSortChronologically(e.target.checked);
                  if (e.target.checked) setRandomize(false);
                }}
              />
              Sort clips chronologically
            </label>
            <label>
              <input
                type="checkbox"
                checked={randomize}
                onChange={(e) => {
                  setRandomize(e.target.checked);
                  if (e.target.checked) setSortChronologically(false);
                }}
              />
              Randomize clip order
            </label>
            <label>
              <input
                type="checkbox"
                checked={skipDuplicates}
                onChange={(e) => setSkipDuplicates(e.target.checked)}
              />
              Skip duplicate events within{' '}
              <input
                type="number"
                value={duplicateThreshold}
                onChange={(e) => setDuplicateThreshold(parseFloat(e.target.value))}
                min={0.5}
                max={10.0}
                step={0.5}
                className="inline-input"
                disabled={!skipDuplicates}
              />
              seconds
            </label>
            <label>
              <input
                type="checkbox"
                checked={addBeatMarkers}
                onChange={(e) => setAddBeatMarkers(e.target.checked)}
              />
              Add beat markers to timeline
            </label>
          </div>
        </div>

        <div className="form-row">
          <label>Output Timeline Name:</label>
          <input
            type="text"
            value={timelineName}
            onChange={(e) => setTimelineName(e.target.value)}
            className="timeline-name-input"
          />
        </div>

        <div className="button-row">
          <button
            onClick={handleGenerate}
            disabled={loading || markers.length === 0 || !videoFile}
            className="generate-button"
          >
            {loading ? 'Generating...' : 'Generate Supercut'}
          </button>
        </div>
      </div>
    </div>
  );
};
