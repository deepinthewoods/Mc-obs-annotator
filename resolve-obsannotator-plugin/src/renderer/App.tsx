import React, { useState, useCallback, useEffect } from 'react';
import { FileBrowser } from './components/FileBrowser';
import { EventStatistics } from './components/EventStatistics';
import { FilterPanel } from './components/FilterPanel';
import { MarkerList } from './components/MarkerList';
import { SupercutPanel } from './components/SupercutPanel';
import { StatusBar } from './components/StatusBar';
import { useEdlParser } from './hooks/useEdlParser';
import { useMarkerFilter } from './hooks/useMarkerFilter';
import { useResolveApi } from './hooks/useResolveApi';
import { SupercutOptions } from './types/api';
import './styles/globals.css';

export const App: React.FC = () => {
  const [videoFile, setVideoFile] = useState('');
  const [edlFile, setEdlFile] = useState('');

  const edlParser = useEdlParser();
  const resolveApi = useResolveApi();
  const markerFilter = useMarkerFilter(edlParser.markers);

  useEffect(() => {
    resolveApi.checkHealth();
    const interval = setInterval(() => {
      resolveApi.checkHealth();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleLoadFiles = useCallback(async () => {
    if (!edlFile) {
      alert('Please select an EDL file');
      return;
    }

    try {
      await edlParser.parseEdl(edlFile);
    } catch (error) {
      alert(`Failed to load EDL file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }, [edlFile, edlParser]);

  const handleImportSelected = useCallback(async () => {
    if (markerFilter.selectedMarkers.length === 0) {
      alert('Please select markers to import');
      return;
    }

    try {
      const result = await resolveApi.importMarkers(markerFilter.selectedMarkers);
      alert(`Successfully imported ${result.imported} of ${result.total} markers`);
    } catch (error) {
      alert(`Failed to import markers: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }, [markerFilter.selectedMarkers, resolveApi]);

  const handleImportAll = useCallback(async () => {
    if (markerFilter.filteredMarkers.length === 0) {
      alert('No markers to import');
      return;
    }

    try {
      const result = await resolveApi.importMarkers(markerFilter.filteredMarkers);
      alert(`Successfully imported ${result.imported} of ${result.total} markers`);
    } catch (error) {
      alert(`Failed to import markers: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }, [markerFilter.filteredMarkers, resolveApi]);

  const handleGenerateSupercut = useCallback(
    async (bpm: number, noteDivision: string, options: SupercutOptions) => {
      if (!videoFile) {
        alert('Please select a video file');
        return;
      }

      if (markerFilter.filteredMarkers.length === 0) {
        alert('No markers available for supercut');
        return;
      }

      try {
        const result = await resolveApi.generateSupercut({
          videoFile,
          markers: markerFilter.filteredMarkers,
          bpm,
          noteDivision: noteDivision as any,
          options,
        });

        alert(
          `Successfully generated supercut!\n\n` +
            `Timeline: ${result.timeline_name}\n` +
            `Clips added: ${result.clips_added}\n` +
            `Duration: ${result.duration_seconds?.toFixed(2)}s`
        );
      } catch (error) {
        alert(`Failed to generate supercut: ${error instanceof Error ? error.message : 'Unknown error'}`);
      }
    },
    [videoFile, markerFilter.filteredMarkers, resolveApi]
  );

  const maxTimestamp = edlParser.markers.length > 0
    ? Math.max(...edlParser.markers.map(m => m.timestampSeconds))
    : 0;

  const globalError = edlParser.error || resolveApi.error;

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
          loading={edlParser.loading}
          markerCount={edlParser.markers.length}
        />

        {edlParser.markers.length > 0 && (
          <>
            <EventStatistics
              statistics={edlParser.statistics}
              totalCount={edlParser.markers.length}
            />

            <FilterPanel
              filters={markerFilter.filters}
              eventTypes={markerFilter.eventTypes}
              statistics={markerFilter.filteredStatistics}
              maxTimestamp={maxTimestamp}
              onFilterChange={markerFilter.updateFilter}
              onClearFilters={markerFilter.clearFilters}
            />

            <MarkerList
              markers={markerFilter.filteredMarkers}
              selectedIds={markerFilter.selectedMarkerIds}
              onToggleSelection={markerFilter.toggleMarkerSelection}
              onSelectAll={markerFilter.selectAllFiltered}
              onClearSelection={markerFilter.clearSelection}
            />

            <div className="import-buttons">
              <button
                onClick={handleImportSelected}
                disabled={markerFilter.selectedMarkers.length === 0 || resolveApi.loading}
                className="import-button"
              >
                Import Selected to Timeline ({markerFilter.selectedMarkers.length})
              </button>
              <button
                onClick={handleImportAll}
                disabled={markerFilter.filteredMarkers.length === 0 || resolveApi.loading}
                className="import-button"
              >
                Import All Filtered ({markerFilter.filteredMarkers.length})
              </button>
            </div>

            <SupercutPanel
              markers={markerFilter.filteredMarkers}
              videoFile={videoFile}
              onGenerate={handleGenerateSupercut}
              loading={resolveApi.loading}
            />
          </>
        )}
      </main>

      <StatusBar
        isConnected={resolveApi.isConnected}
        projectOpen={resolveApi.projectOpen}
        markerCount={markerFilter.filteredMarkers.length}
        error={globalError}
      />
    </div>
  );
};
