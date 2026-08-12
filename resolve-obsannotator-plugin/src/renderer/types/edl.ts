import { Marker } from './marker';

export interface EdlParseResult {
  success: boolean;
  title?: string;
  framerate?: number;
  markers?: Marker[];
  statistics?: { [key: string]: number };
  total_count?: number;
  error?: string;
}
