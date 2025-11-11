import { Marker } from './marker';

export interface EdlData {
  title: string;
  framerate: number;
  fcm: string;
  markers: Marker[];
}

export interface EdlParseResult {
  success: boolean;
  title?: string;
  framerate?: number;
  markers?: Marker[];
  statistics?: { [eventType: string]: number };
  total_count?: number;
  error?: string;
}
