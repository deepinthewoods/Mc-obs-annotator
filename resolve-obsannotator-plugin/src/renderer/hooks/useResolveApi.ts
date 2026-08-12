import { useState, useCallback } from 'react';
import {
  HealthCheckResponse,
  ImportMarkersRequest,
  ImportMarkersResponse,
  GenerateSupercutRequest,
  GenerateSupercutResponse
} from '../types/api';
import { Marker } from '../types/marker';

const API_BASE_URL = 'http://localhost:8765/api';

export const useResolveApi = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [projectOpen, setProjectOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/health`);
      const data: HealthCheckResponse = await response.json();

      setIsConnected(data.resolve_connected);
      setProjectOpen(data.project_open);

      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to connect to server';
      setError(message);
      setIsConnected(false);
      setProjectOpen(false);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const importMarkers = useCallback(async (markers: Marker[]): Promise<ImportMarkersResponse> => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/import-markers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ markers }),
      });

      const data: ImportMarkersResponse = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Failed to import markers');
      }

      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to import markers';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const generateSupercut = useCallback(async (
    request: GenerateSupercutRequest
  ): Promise<GenerateSupercutResponse> => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/generate-supercut`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      const data: GenerateSupercutResponse = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Failed to generate supercut');
      }

      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to generate supercut';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    isConnected,
    projectOpen,
    loading,
    error,
    checkHealth,
    importMarkers,
    generateSupercut,
  };
};
