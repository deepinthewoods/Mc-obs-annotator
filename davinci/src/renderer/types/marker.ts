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

export interface MarkerStatistics {
  [eventType: string]: number;
}
