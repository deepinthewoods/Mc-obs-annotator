import { useState } from 'react';
import { Marker } from '../types/marker';
import { EdlParseResult } from '../types/edl';

const API_BASE = 'http://localhost:8765/api';

export const useEdlParser = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const parseEdl = async (edlFilePath: string): Promise<EdlParseResult | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/parse-edl`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ edlFilePath }),
      });

      const data: EdlParseResult = await response.json();

      if (!data.success) {
        setError(data.error || 'Failed to parse EDL');
        return null;
      }

      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return { parseEdl, isLoading, error };
};
