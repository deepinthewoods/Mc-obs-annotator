/**
 * Types for Bulk Import feature
 */

export interface MarkerSummary {
  total: number;
  chapters: number;
  startEndPairs: number;
  pois: number;
  eventTypeCounts?: { [key: string]: number };
}

export interface Session {
  id: string;
  videoFile: string;
  edlFile: string;
  videoSize: number;
  duration: number;
  markerSummary: MarkerSummary;
}

export interface ClipRegion {
  start: number;
  end: number;
  markers: string[];
  type: 'chapter' | 'recording' | 'poi';
  label: string;
}

export interface ClipRegions {
  chapters: ClipRegion[];
  recordings: ClipRegion[];
  pois: ClipRegion[];
}

export interface BulkScanRequest {
  sourceFolder: string;
  recursive?: boolean;
}

export interface BulkScanResponse {
  success: boolean;
  sessions?: Session[];
  totalSize?: string;
  totalSessions?: number;
  error?: string;
}

export interface BulkAnalyzeRequest {
  sessionId: string;
  settings?: BulkSettings;
}

export interface BulkAnalyzeResponse {
  success: boolean;
  sessionId?: string;
  clipRegions?: ClipRegions;
  estimatedOutputSize?: string;
  estimatedReduction?: string;
  error?: string;
}

export interface BulkExtractRequest {
  sessionId: string;
  outputFolder: string;
  skipBlackClips?: boolean;
}

export interface ExtractProgress {
  type: 'progress' | 'complete' | 'error';
  clip?: number;
  total?: number;
  status?: 'extracting' | 'extracted' | 'skipped_black' | 'skipped_existing' | 'error';
  file?: string;
  extracted?: number;
  skipped?: number;
  errors?: number;
  outputFolder?: string;
}

export interface BulkCreateTimelinesRequest {
  sessionId?: string;
  extractedFolder: string;
}

export interface TimelineInfo {
  name: string;
  clips: number;
  duration: string;
}

export interface BulkCreateTimelinesResponse {
  success: boolean;
  timelines?: TimelineInfo[];
  error?: string;
}

export interface SilenceRemovalSettings {
  enabled: boolean;
  silenceThresholdDb: number;
  minSilenceDuration: number;
  padding: number;
  maxSilenceForReset: number;
}

export interface BulkSettings {
  chapterBuffer: number;
  mergeOverlapping: boolean;
  skipBlackClips: boolean;
  createTimelines: boolean;
  enabledEventTypes: string[];
  silenceRemoval: SilenceRemovalSettings;
}

export interface BulkProcessAllRequest {
  sourceFolder: string;
  outputFolder: string;
  settings?: BulkSettings;
}

export interface BatchProgress {
  type: 'session_start' | 'progress' | 'complete' | 'timelines_created' | 'batch_complete';
  session?: number;
  totalSessions?: number;
  totalClipsAllSessions?: number;
  name?: string;
  clip?: number;
  total?: number;
  status?: string;
  file?: string;
  extracted?: number;
  skipped?: number;
  errors?: number;
  outputFolder?: string;
  timelines?: TimelineInfo[];
}

export interface BulkImportState {
  // Scanning
  isScanning: boolean;
  sessions: Session[];
  totalSize: string;

  // Selection
  selectedSessionIds: Set<string>;

  // Analysis
  isAnalyzing: boolean;
  analyzedSessions: Map<string, ClipRegions>;
  estimatedOutputSize: string;
  estimatedReduction: string;

  // Extraction
  isExtracting: boolean;
  currentSession: number;
  totalSessions: number;
  currentClip: number;
  totalClips: number;
  currentFile: string;
  extractedCount: number;
  skippedCount: number;
  errorCount: number;

  // Errors
  error: string | null;
}

// Timeline Supercut types

export interface TimelineClipMarker {
  frame: number;
  name: string;
  color: string;
  note: string;
}

export interface TimelineClip {
  index: number;
  name: string;
  eventType: string;
  startFrame: number;
  endFrame: number;
  duration: number;
  markers: TimelineClipMarker[];
}

export interface TimelineClipsResponse {
  success: boolean;
  timelineName?: string;
  framerate?: number;
  clips?: TimelineClip[];
  error?: string;
}

export interface SupercutFromClipsRequest {
  clipIndices: number[];
  bpm: number;
  noteDivision: string;
  options?: {
    randomize?: boolean;
    add_crossfades?: boolean;
    crossfade_duration?: number;
    add_beat_markers?: boolean;
    output_timeline_name?: string;
  };
}

export const DEFAULT_SILENCE_REMOVAL_SETTINGS: SilenceRemovalSettings = {
  enabled: false,
  silenceThresholdDb: -30,
  minSilenceDuration: 0.8,
  padding: 0.15,
  maxSilenceForReset: 15.0
};

export const DEFAULT_BULK_SETTINGS: BulkSettings = {
  chapterBuffer: 0.5,
  mergeOverlapping: true,
  skipBlackClips: true,
  createTimelines: true,
  enabledEventTypes: [],
  silenceRemoval: { ...DEFAULT_SILENCE_REMOVAL_SETTINGS }
};
