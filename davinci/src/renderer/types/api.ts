import { Marker } from './marker';

export interface FilterOptions {
  search?: string;
  exclude?: string;
  eventTypes?: string[];
  timeRangeStart?: number;
  timeRangeEnd?: number;
}

export interface SupercutOptions {
  sort_chronologically?: boolean;
  randomize?: boolean;
  skip_duplicates_within_seconds?: number;
  add_crossfades?: boolean;
  crossfade_duration?: number;
  add_beat_markers?: boolean;
  output_timeline_name?: string;
}

export interface HealthCheckResponse {
  server: string;
  resolve_connected: boolean;
  project_open: boolean;
}

export interface FilterMarkersResponse {
  success: boolean;
  markers?: Marker[];
  statistics?: { [eventType: string]: number };
  count?: number;
  error?: string;
}

export interface ImportMarkersResponse {
  success: boolean;
  imported?: number;
  total?: number;
  error?: string;
}

export interface GenerateSupercut Response {
  success: boolean;
  timeline_name?: string;
  clips_added?: number;
  duration_seconds?: number;
  markers_used?: number;
  error?: string;
}
