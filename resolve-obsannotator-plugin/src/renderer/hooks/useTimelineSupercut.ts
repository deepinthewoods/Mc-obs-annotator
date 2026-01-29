import { useState, useCallback, useMemo } from 'react';
import { TimelineClip, TimelineClipsResponse } from '../types/bulk';

const API_BASE_URL = 'http://localhost:8765/api';

export const useTimelineSupercut = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [clips, setClips] = useState<TimelineClip[]>([]);
  const [timelineName, setTimelineName] = useState('');
  const [framerate, setFramerate] = useState(30);
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(new Set());
  const [enabledEventTypes, setEnabledEventTypes] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);

  // Derive available event types from clips
  const eventTypes = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const clip of clips) {
      counts[clip.eventType] = (counts[clip.eventType] || 0) + 1;
    }
    return counts;
  }, [clips]);

  // Filtered clips based on enabled event types
  const filteredClips = useMemo(() => {
    if (enabledEventTypes.size === 0) return clips;
    return clips.filter(c => enabledEventTypes.has(c.eventType));
  }, [clips, enabledEventTypes]);

  const readTimeline = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      setClips([]);
      setSelectedIndices(new Set());

      const response = await fetch(`${API_BASE_URL}/timeline/clips`);
      const data: TimelineClipsResponse = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Failed to read timeline');
      }

      const loadedClips = data.clips || [];
      setClips(loadedClips);
      setTimelineName(data.timelineName || '');
      setFramerate(data.framerate || 30);

      // Enable all event types by default
      const types = new Set(loadedClips.map(c => c.eventType));
      setEnabledEventTypes(types);

      // Select all by default
      setSelectedIndices(new Set(loadedClips.map(c => c.index)));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to read timeline';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const toggleClipSelection = useCallback((index: number) => {
    setSelectedIndices(prev => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  }, []);

  const selectAllFiltered = useCallback(() => {
    setSelectedIndices(new Set(filteredClips.map(c => c.index)));
  }, [filteredClips]);

  const clearSelection = useCallback(() => {
    setSelectedIndices(new Set());
  }, []);

  const toggleEventType = useCallback((eventType: string) => {
    setEnabledEventTypes(prev => {
      const next = new Set(prev);
      if (next.has(eventType)) {
        next.delete(eventType);
      } else {
        next.add(eventType);
      }
      return next;
    });
  }, []);

  const enableAllEventTypes = useCallback(() => {
    setEnabledEventTypes(new Set(Object.keys(eventTypes)));
  }, [eventTypes]);

  const disableAllEventTypes = useCallback(() => {
    setEnabledEventTypes(new Set());
  }, []);

  const generateSupercut = useCallback(async (
    bpm: number,
    noteDivision: string,
    options: Record<string, unknown> = {}
  ) => {
    try {
      setIsLoading(true);
      setError(null);

      // Only include selected clips that are also in the filtered set
      const filteredIndicesSet = new Set(filteredClips.map(c => c.index));
      const clipIndices = Array.from(selectedIndices).filter(i => filteredIndicesSet.has(i));

      if (clipIndices.length === 0) {
        throw new Error('No clips selected');
      }

      const response = await fetch(`${API_BASE_URL}/timeline/supercut-from-clips`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          clipIndices,
          bpm,
          noteDivision,
          options
        })
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Failed to generate supercut');
      }

      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to generate supercut';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [selectedIndices, filteredClips]);

  return {
    isLoading,
    clips,
    filteredClips,
    timelineName,
    framerate,
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
  };
};
