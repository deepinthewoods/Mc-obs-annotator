import { useState, useCallback, useRef, useEffect } from 'react';
import {
  Session,
  ClipRegions,
  BulkScanResponse,
  BulkAnalyzeResponse,
  BulkSettings,
  BulkCreateTimelinesResponse,
  ExtractProgress,
  BatchProgress,
  TimelineInfo,
  DEFAULT_BULK_SETTINGS,
  DEFAULT_SILENCE_REMOVAL_SETTINGS
} from '../types/bulk';
import { loadPersistedSettings, savePersistedSettings } from './usePersistedSettings';

const { ipcRenderer } = window.require('electron');
const API_BASE_URL = 'http://localhost:8765/api';

export const useBulkImport = () => {
  // Scanning state
  const [isScanning, setIsScanning] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [totalSize, setTotalSize] = useState('');

  // Selection state
  const [selectedSessionIds, setSelectedSessionIds] = useState<Set<string>>(new Set());

  // Analysis state
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzedSessions, setAnalyzedSessions] = useState<Map<string, ClipRegions>>(new Map());
  const [estimatedOutputSize, setEstimatedOutputSize] = useState('');
  const [estimatedReduction, setEstimatedReduction] = useState('');

  // Extraction state
  const [isExtracting, setIsExtracting] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [currentSession, setCurrentSession] = useState(0);
  const [totalSessions, setTotalSessions] = useState(0);
  const [currentClip, setCurrentClip] = useState(0);
  const [totalClips, setTotalClips] = useState(0);
  const [currentFile, setCurrentFile] = useState('');
  const [extractedCount, setExtractedCount] = useState(0);
  const [skippedCount, setSkippedCount] = useState(0);
  const [skippedExistingCount, setSkippedExistingCount] = useState(0);
  const [errorCount, setErrorCount] = useState(0);

  // Time estimation state
  const [startTime, setStartTime] = useState<number | null>(null);
  const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState<string>('');

  // Abort controller for cancellation
  const abortControllerRef = useRef<AbortController | null>(null);

  // Settings - initialize from persisted values
  const [settings, setSettings] = useState<BulkSettings>(() => {
    const persisted = loadPersistedSettings();
    return {
      ...DEFAULT_BULK_SETTINGS,
      ...(persisted.chapterBuffer !== undefined && { chapterBuffer: persisted.chapterBuffer }),
      ...(persisted.poiDuration !== undefined && { poiDuration: persisted.poiDuration }),
      ...(persisted.mergeOverlapping !== undefined && { mergeOverlapping: persisted.mergeOverlapping }),
      ...(persisted.skipBlackClips !== undefined && { skipBlackClips: persisted.skipBlackClips }),
      ...(persisted.createTimelines !== undefined && { createTimelines: persisted.createTimelines }),
      ...(persisted.enabledEventTypes !== undefined && { enabledEventTypes: persisted.enabledEventTypes }),
      silenceRemoval: {
        ...DEFAULT_SILENCE_REMOVAL_SETTINGS,
        ...(persisted.silenceRemoval || {})
      }
    };
  });

  // Persist settings when they change
  useEffect(() => {
    savePersistedSettings({
      enabledEventTypes: settings.enabledEventTypes,
      chapterBuffer: settings.chapterBuffer,
      poiDuration: settings.poiDuration,
      mergeOverlapping: settings.mergeOverlapping,
      skipBlackClips: settings.skipBlackClips,
      createTimelines: settings.createTimelines,
      silenceRemoval: settings.silenceRemoval,
    });
  }, [settings]);

  // Event type state (aggregated from all scanned sessions)
  const [availableEventTypes, setAvailableEventTypes] = useState<{ [key: string]: number }>({});

  // Error state
  const [error, setError] = useState<string | null>(null);

  // Track actual work (non-skipped-existing) for accurate ETA
  const workStartTimeRef = useRef<number | null>(null);
  const workDoneRef = useRef(0);

  // Compute and update time estimate based on actual work done (excludes skipped-existing)
  const updateTimeEstimate = useCallback((completedClips: number, totalClipsCount: number, _processStartTime: number, isSkippedExisting: boolean = false) => {
    if (totalClipsCount <= 0) {
      setEstimatedTimeRemaining('');
      return;
    }

    if (isSkippedExisting) {
      // Don't update ETA for skipped-existing clips — they're instant
      return;
    }

    // Start the work clock on the first real work item
    if (workStartTimeRef.current === null) {
      workStartTimeRef.current = Date.now();
    }
    workDoneRef.current += 1;

    const workDone = workDoneRef.current;
    const workRemaining = totalClipsCount - completedClips;

    if (workDone <= 0 || workRemaining <= 0) {
      setEstimatedTimeRemaining('');
      return;
    }

    const elapsed = (Date.now() - workStartTimeRef.current) / 1000; // seconds
    const rate = workDone / elapsed; // actual clips per second
    const remaining = workRemaining / rate;

    if (remaining < 60) {
      setEstimatedTimeRemaining(`${Math.round(remaining)}s remaining`);
    } else if (remaining < 3600) {
      const mins = Math.floor(remaining / 60);
      const secs = Math.round(remaining % 60);
      setEstimatedTimeRemaining(`${mins}m ${secs}s remaining`);
    } else {
      const hrs = Math.floor(remaining / 3600);
      const mins = Math.round((remaining % 3600) / 60);
      setEstimatedTimeRemaining(`${hrs}h ${mins}m remaining`);
    }
  }, []);

  // Scan folder for sessions
  const scanFolder = useCallback(async (sourceFolder: string, recursive: boolean = false) => {
    try {
      setIsScanning(true);
      setError(null);
      setSessions([]);
      setSelectedSessionIds(new Set());
      setAnalyzedSessions(new Map());

      const response = await fetch(`${API_BASE_URL}/bulk/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sourceFolder, recursive })
      });

      const data: BulkScanResponse = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Failed to scan folder');
      }

      const scannedSessions = data.sessions || [];
      setSessions(scannedSessions);
      setTotalSize(data.totalSize || '');

      // Select all sessions by default
      const allIds = new Set(scannedSessions.map(s => s.id));
      setSelectedSessionIds(allIds);

      // Aggregate event type counts across all sessions
      const aggregated: { [key: string]: number } = {};
      for (const s of scannedSessions) {
        const counts = s.markerSummary?.eventTypeCounts || {};
        for (const [type, count] of Object.entries(counts)) {
          aggregated[type] = (aggregated[type] || 0) + count;
        }
      }
      setAvailableEventTypes(aggregated);

      // If we already have enabled event types (e.g. from persistence), keep the
      // ones that still exist in this scan. Otherwise enable all by default.
      setSettings(prev => {
        if (prev.enabledEventTypes.length > 0) {
          const available = new Set(Object.keys(aggregated));
          const kept = prev.enabledEventTypes.filter(t => available.has(t));
          // If none survived the intersection, enable all
          return { ...prev, enabledEventTypes: kept.length > 0 ? kept : Object.keys(aggregated) };
        }
        return { ...prev, enabledEventTypes: Object.keys(aggregated) };
      });

      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to scan folder';
      setError(message);
      throw err;
    } finally {
      setIsScanning(false);
    }
  }, []);

  // Analyze a single session
  const analyzeSession = useCallback(async (sessionId: string) => {
    try {
      setIsAnalyzing(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/bulk/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId,
          settings: {
            chapterBuffer: settings.chapterBuffer,
            poiDuration: settings.poiDuration,
            mergeOverlapping: settings.mergeOverlapping
          }
        })
      });

      const data: BulkAnalyzeResponse = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Failed to analyze session');
      }

      if (data.clipRegions) {
        setAnalyzedSessions(prev => new Map(prev).set(sessionId, data.clipRegions!));
      }

      setEstimatedOutputSize(data.estimatedOutputSize || '');
      setEstimatedReduction(data.estimatedReduction || '');

      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to analyze session';
      setError(message);
      throw err;
    } finally {
      setIsAnalyzing(false);
    }
  }, [settings]);

  // Extract clips from a session with streaming progress
  const extractSession = useCallback(async (
    sessionId: string,
    outputFolder: string,
    onProgress?: (progress: ExtractProgress) => void
  ) => {
    try {
      setIsExtracting(true);
      setError(null);
      setExtractedCount(0);
      setSkippedCount(0);
      setErrorCount(0);
      const extractStartTime = Date.now();
      setStartTime(extractStartTime);
      setEstimatedTimeRemaining('');
      await ipcRenderer.invoke('prevent-sleep');

      const controller = new AbortController();
      abortControllerRef.current = controller;

      const response = await fetch(`${API_BASE_URL}/bulk/extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId,
          outputFolder,
          skipBlackClips: settings.skipBlackClips
        }),
        signal: controller.signal
      });

      if (!response.body) {
        throw new Error('No response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const progress: ExtractProgress = JSON.parse(line.slice(6));

              if (progress.type === 'progress') {
                setCurrentClip(progress.clip || 0);
                setTotalClips(progress.total || 0);
                setCurrentFile(progress.file || '');
                updateTimeEstimate(progress.clip || 0, progress.total || 0, extractStartTime);

                if (progress.status === 'skipped_black') {
                  setSkippedCount(prev => prev + 1);
                } else if (progress.status === 'error') {
                  setErrorCount(prev => prev + 1);
                }
              } else if (progress.type === 'complete') {
                setExtractedCount(progress.extracted || 0);
                setSkippedCount(progress.skipped || 0);
                setErrorCount(progress.errors || 0);
                setEstimatedTimeRemaining('');
              }

              onProgress?.(progress);
            } catch {
              // Ignore parse errors
            }
          }
        }
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        setEstimatedTimeRemaining('');
        return;
      }
      const message = err instanceof Error ? err.message : 'Failed to extract clips';
      setError(message);
      throw err;
    } finally {
      abortControllerRef.current = null;
      setIsExtracting(false);
      await ipcRenderer.invoke('allow-sleep');
    }
  }, [settings.skipBlackClips, updateTimeEstimate]);

  // Create timelines from extracted clips
  const createTimelines = useCallback(async (
    extractedFolder: string,
    sessionId?: string
  ): Promise<TimelineInfo[]> => {
    try {
      setError(null);

      const response = await fetch(`${API_BASE_URL}/bulk/create-timelines`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ extractedFolder, sessionId })
      });

      const data: BulkCreateTimelinesResponse = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Failed to create timelines');
      }

      return data.timelines || [];
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create timelines';
      setError(message);
      throw err;
    }
  }, []);

  // Process all sessions in batch
  const processAll = useCallback(async (
    sourceFolder: string,
    outputFolder: string,
    onProgress?: (progress: BatchProgress) => void,
    resume: boolean = false
  ): Promise<{ extracted: number; skipped: number; skippedExisting: number; errors: number } | undefined> => {
    let localExtracted = 0;
    let localSkipped = 0;
    let localSkippedExisting = 0;
    let localErrors = 0;

    try {
      setIsExtracting(true);
      setIsPaused(false);
      setError(null);
      setExtractedCount(0);
      setSkippedCount(0);
      setSkippedExistingCount(0);
      setErrorCount(0);
      workStartTimeRef.current = null;
      workDoneRef.current = 0;
      const processStartTime = Date.now();
      setStartTime(processStartTime);
      setEstimatedTimeRemaining('');
      await ipcRenderer.invoke('prevent-sleep');

      const controller = new AbortController();
      abortControllerRef.current = controller;

      const response = await fetch(`${API_BASE_URL}/bulk/process-all`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sourceFolder,
          outputFolder,
          settings,
          sessionIds: Array.from(selectedSessionIds),
          resume
        }),
        signal: controller.signal
      });

      if (!response.body) {
        throw new Error('No response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const progress: BatchProgress = JSON.parse(line.slice(6));

              if (progress.type === 'progress') {
                const isSkippedExisting = progress.status === 'skipped_existing';
                setCurrentClip(progress.clip || 0);
                setTotalClips(progress.total || 0);
                setCurrentFile(progress.file || '');
                updateTimeEstimate(progress.clip || 0, progress.total || 0, processStartTime, isSkippedExisting);

                if (progress.status === 'skipped_black') {
                  localSkipped++;
                  setSkippedCount(prev => prev + 1);
                } else if (isSkippedExisting) {
                  localSkippedExisting++;
                  setSkippedExistingCount(prev => prev + 1);
                } else if (progress.status === 'error') {
                  localErrors++;
                  setErrorCount(prev => prev + 1);
                } else if (progress.status === 'extracted') {
                  localExtracted++;
                  setExtractedCount(prev => prev + 1);
                }
              } else if (progress.type === 'batch_complete') {
                setEstimatedTimeRemaining('');
              }

              onProgress?.(progress);
            } catch {
              // Ignore parse errors
            }
          }
        }
      }

      return { extracted: localExtracted, skipped: localSkipped, skippedExisting: localSkippedExisting, errors: localErrors };
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        setEstimatedTimeRemaining('');
        return;
      }
      const message = err instanceof Error ? err.message : 'Failed to process sessions';
      setError(message);
      throw err;
    } finally {
      abortControllerRef.current = null;
      setIsExtracting(false);
      await ipcRenderer.invoke('allow-sleep');
    }
  }, [settings, selectedSessionIds, updateTimeEstimate]);

  // Selection helpers
  const toggleSessionSelection = useCallback((sessionId: string) => {
    setSelectedSessionIds(prev => {
      const next = new Set(prev);
      if (next.has(sessionId)) {
        next.delete(sessionId);
      } else {
        next.add(sessionId);
      }
      return next;
    });
  }, []);

  const selectAllSessions = useCallback(() => {
    setSelectedSessionIds(new Set(sessions.map(s => s.id)));
  }, [sessions]);

  const clearSelection = useCallback(() => {
    setSelectedSessionIds(new Set());
  }, []);

  const updateSettings = useCallback((updates: Partial<BulkSettings>) => {
    setSettings(prev => ({ ...prev, ...updates }));
  }, []);

  const toggleEventType = useCallback((eventType: string) => {
    setSettings(prev => {
      const current = prev.enabledEventTypes;
      const newTypes = current.includes(eventType)
        ? current.filter(t => t !== eventType)
        : [...current, eventType];
      return { ...prev, enabledEventTypes: newTypes };
    });
  }, []);

  const enableAllEventTypes = useCallback(() => {
    setSettings(prev => ({ ...prev, enabledEventTypes: Object.keys(availableEventTypes) }));
  }, [availableEventTypes]);

  const disableAllEventTypes = useCallback(() => {
    setSettings(prev => ({ ...prev, enabledEventTypes: [] }));
  }, []);

  const pauseProcessing = useCallback(async () => {
    try {
      await fetch(`${API_BASE_URL}/bulk/pause`, { method: 'POST' });
      setIsPaused(true);
    } catch (err) {
      console.error('Failed to pause:', err);
    }
  }, []);

  const resumeProcessing = useCallback(async () => {
    try {
      await fetch(`${API_BASE_URL}/bulk/resume`, { method: 'POST' });
      setIsPaused(false);
    } catch (err) {
      console.error('Failed to resume:', err);
    }
  }, []);

  const cancelProcessing = useCallback(async () => {
    // Ensure we unpause first so the server-side loop can exit
    try {
      await fetch(`${API_BASE_URL}/bulk/resume`, { method: 'POST' });
    } catch { /* ignore */ }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsPaused(false);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const reset = useCallback(() => {
    setSessions([]);
    setSelectedSessionIds(new Set());
    setAnalyzedSessions(new Map());
    setTotalSize('');
    setEstimatedOutputSize('');
    setEstimatedReduction('');
    setCurrentSession(0);
    setTotalSessions(0);
    setCurrentClip(0);
    setTotalClips(0);
    setCurrentFile('');
    setExtractedCount(0);
    setSkippedCount(0);
    setSkippedExistingCount(0);
    setErrorCount(0);
    setIsPaused(false);
    setStartTime(null);
    workStartTimeRef.current = null;
    workDoneRef.current = 0;
    setEstimatedTimeRemaining('');
    setError(null);
  }, []);

  return {
    // State
    isScanning,
    sessions,
    totalSize,
    selectedSessionIds,
    isAnalyzing,
    analyzedSessions,
    estimatedOutputSize,
    estimatedReduction,
    isExtracting,
    isPaused,
    currentSession,
    totalSessions,
    currentClip,
    totalClips,
    currentFile,
    extractedCount,
    skippedCount,
    skippedExistingCount,
    errorCount,
    estimatedTimeRemaining,
    settings,
    error,

    // Event types
    availableEventTypes,

    // Actions
    scanFolder,
    analyzeSession,
    extractSession,
    createTimelines,
    processAll,
    pauseProcessing,
    resumeProcessing,
    cancelProcessing,
    toggleSessionSelection,
    selectAllSessions,
    clearSelection,
    updateSettings,
    toggleEventType,
    enableAllEventTypes,
    disableAllEventTypes,
    clearError,
    reset
  };
};
