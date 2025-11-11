import { useState } from 'react';
import { Marker } from '../types/marker';
import {
  HealthCheckResponse,
  ImportMarkersResponse,
  GenerateSupercut Response,
  SupercutOptions,
} from '../types/api';

const API_BASE = 'http://localhost:8765/api';

export const useResolveApi = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = async (): Promise<boolean> => {
    try {
      const response = await fetch(`${API_BASE}/health`);
      const data: HealthCheckResponse = await response.json();
      setIsConnected(data.resolve_connected && data.project_open);
      return data.resolve_connected && data.project_open;
    } catch (err) {
      setIsConnected(false);
      return false;
    }
  };

  const importMarkers = async (markers: Marker[]): Promise<ImportMarkersResponse | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/import-markers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ markers }),
      });

      const data: ImportMarkersResponse = await response.json();

      if (!data.success) {
        setError(data.error || 'Failed to import markers');
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

  const generateSupercut = async (
    videoFile: string,
    markers: Marker[],
    bpm: number,
    noteDivision: string,
    options: SupercutOptions
  ): Promise<GenerateSupercut Response | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/generate-supercut`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          videoFile,
          markers,
          bpm,
          noteDivision,
          options,
        }),
      });

      const data: GenerateSupercut Response = await response.json();

      if (!data.success) {
        setError(data.error || 'Failed to generate supercut');
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

  return {
    isConnected,
    isLoading,
    error,
    checkHealth,
    importMarkers,
    generateSupercut,
  };
};
