import { useState, useCallback } from 'react';
import { Marker } from '../types/marker';
import { EdlParseResult } from '../types/edl';

const API_BASE_URL = 'http://localhost:8765/api';

export const useEdlParser = () => {
  const [markers, setMarkers] = useState<Marker[]>([]);
  const [statistics, setStatistics] = useState<{ [key: string]: number }>({});
  const [title, setTitle] = useState<string>('');
  const [framerate, setFramerate] = useState<number>(30);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const parseEdl = useCallback(async (edlFilePath: string) => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/parse-edl`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ edlFilePath }),
      });

      const data: EdlParseResult = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Failed to parse EDL');
      }

      setMarkers(data.markers || []);
      setStatistics(data.statistics || {});
      setTitle(data.title || '');
      setFramerate(data.framerate || 30);

      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to parse EDL file';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearData = useCallback(() => {
    setMarkers([]);
    setStatistics({});
    setTitle('');
    setFramerate(30);
    setError(null);
  }, []);

  return {
    markers,
    statistics,
    title,
    framerate,
    loading,
    error,
    parseEdl,
    clearData,
  };
};
