export interface Marker {
  id: number;
  timecode: string;
  timestampSeconds: number;
  color: string | null;
  rawText: string;
  text: string;
  instance: string | null;
  type: string;
  subtype: string;
  duration: number;
}

export interface MarkerFilter {
  search?: string;
  exclude?: string;
  eventTypes?: string[];
  instances?: string[];
  timeRangeStart?: number;
  timeRangeEnd?: number;
}

export interface EventStatistics {
  [eventType: string]: number;
}
