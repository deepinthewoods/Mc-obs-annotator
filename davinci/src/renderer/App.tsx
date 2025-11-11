import React, { useState, useEffect } from 'react';
import { Marker, MarkerStatistics } from './types/marker';
import { SupercutOptions } from './types/api';
import { useEdlParser } from './hooks/useEdlParser';
import { useMarkerFilter } from './hooks/useMarkerFilter';
import { useResolveApi } from './hooks/useResolveApi';
import { FileBrowser } from './components/FileBrowser';
import { EventStatistics } from './components/EventStatistics';
import { FilterPanel } from './components/FilterPanel';
import { MarkerList } from './components/MarkerList';
import { SupercutPanel } from './components/SupercutPanel';
import { StatusBar } from './components/StatusBar';
import './styles/globals.css';

export const App: React.FC = () => {
  const [videoFile, setVideoFile] = useState('');
  const [edlFile, setEdlFile] = useState('');
  const [videoDuration, setVideoDuration] = useState(0);
  const [allMarkers, setAllMarkers] = useState<Marker[]>([]);
  const [statistics, setStatistics] = useState<MarkerStatistics>({});
  const [selectedMarkers, setSelectedMarkers] = useState<Set<number>>(new Set());

  const { parseEdl, isLoading: isParsingEdl, error: edlError } = useEdlParser();
  const { filteredMarkers, filters, setFilters } = useMarkerFilter(allMarkers);
  const { isConnected, isLoading: isResolveLoading, error: resolveError, checkHealth, importMarkers, generateSupercut } = useResolveApi();

  // Check Resolve connection on mount and periodically
  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  // Initialize selected markers when filtered markers change
  useEffect(() => {
    setSelectedMarkers(new Set(filteredMarkers.map((m) => m.id)));
  }, [filteredMarkers]);

  const handleLoadFiles = async () => {
    if (!edlFile) {
      alert('Please select an EDL file');
      return;
    }

    const result = await parseEdl(edlFile);
    if (result && result.markers) {
      setAllMarkers(result.markers);
      setStatistics(result.statistics || {});

      // Try to get video duration (simplified for now)
      if (result.markers.length > 0) {
        const maxTime = Math.max(...result.markers.map((m) => m.timestampSeconds));
        setVideoDuration(maxTime + 60); // Add buffer
      }
    } else if (edlError) {
      alert(`Failed to load EDL: ${edlError}`);
    }
  };

  const handleToggleMarker = (markerId: number) => {
    const newSelected = new Set(selectedMarkers);
    if (newSelected.has(markerId)) {
      newSelected.delete(markerId);
    } else {
      newSelected.add(markerId);
    }
    setSelectedMarkers(newSelected);
  };

  const handleToggleAll = () => {
    if (selectedMarkers.size === filteredMarkers.length) {
      setSelectedMarkers(new Set());
    } else {
      setSelectedMarkers(new Set(filteredMarkers.map((m) => m.id)));
    }
  };

  const handleImportSelected = async () => {
    const markersToImport = filteredMarkers.filter((m) => selectedMarkers.has(m.id));
    if (markersToImport.length === 0) {
      alert('No markers selected');
      return;
    }

    const result = await importMarkers(markersToImport);
    if (result) {
      alert(`Successfully imported ${result.imported} of ${result.total} markers`);
    } else if (resolveError) {
      alert(`Failed to import markers: ${resolveError}`);
    }
  };

  const handleImportAll = async () => {
    if (filteredMarkers.length === 0) {
      alert('No markers to import');
      return;
    }

    const result = await importMarkers(filteredMarkers);
    if (result) {
      alert(`Successfully imported ${result.imported} of ${result.total} markers`);
    } else if (resolveError) {
      alert(`Failed to import markers: ${resolveError}`);
    }
  };

  const handleGenerateSupercut = async (
    bpm: number,
    noteDivision: string,
    options: SupercutOptions
  ) => {
    if (!videoFile) {
      alert('Please select a video file');
      return;
    }

    if (filteredMarkers.length === 0) {
      alert('No markers to use for supercut');
      return;
    }

    const result = await generateSupercut(videoFile, filteredMarkers, bpm, noteDivision, options);
    if (result) {
      alert(
        `Successfully generated supercut!\n` +
          `Timeline: ${result.timeline_name}\n` +
          `Clips: ${result.clips_added}\n` +
          `Duration: ${result.duration_seconds?.toFixed(1)}s`
      );
    } else if (resolveError) {
      alert(`Failed to generate supercut: ${resolveError}`);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>ObsAnnotator - DaVinci Resolve Companion</h1>
      </header>

      <main className="app-main">
        <FileBrowser
          videoFile={videoFile}
          edlFile={edlFile}
          onVideoFileChange={setVideoFile}
          onEdlFileChange={setEdlFile}
          onLoadFiles={handleLoadFiles}
          isLoading={isParsingEdl}
        />

        {allMarkers.length > 0 && (
          <>
            <EventStatistics statistics={statistics} total={allMarkers.length} />

            <FilterPanel
              filters={filters}
              onFiltersChange={setFilters}
              statistics={statistics}
              videoDuration={videoDuration}
            />

            <MarkerList
              markers={filteredMarkers}
              totalCount={allMarkers.length}
              selectedMarkers={selectedMarkers}
              onToggleMarker={handleToggleMarker}
              onToggleAll={handleToggleAll}
            />

            <div className="import-actions">
              <button
                onClick={handleImportSelected}
                disabled={selectedMarkers.size === 0 || !isConnected || isResolveLoading}
                className="primary-button"
              >
                Import Selected to Timeline ({selectedMarkers.size})
              </button>
              <button
                onClick={handleImportAll}
                disabled={filteredMarkers.length === 0 || !isConnected || isResolveLoading}
                className="primary-button"
              >
                Import All Filtered ({filteredMarkers.length})
              </button>
            </div>

            <SupercutPanel
              markerCount={filteredMarkers.length}
              onGenerate={handleGenerateSupercut}
              isLoading={isResolveLoading}
            />
          </>
        )}
      </main>

      <StatusBar isConnected={isConnected} markerCount={filteredMarkers.length} />
    </div>
  );
};
