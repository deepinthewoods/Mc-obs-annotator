export interface Marker {
  id: number;
  timecode: string;
  timestampSeconds: number;
  color: string | null;
  text: string;
  type: string;
  subtype: string;
  duration: number;
}

export interface MarkerFilter {
  search?: string;
  exclude?: string;
  eventTypes?: string[];
  timeRangeStart?: number;
  timeRangeEnd?: number;
}

export interface EventStatistics {
  [eventType: string]: number;
}
