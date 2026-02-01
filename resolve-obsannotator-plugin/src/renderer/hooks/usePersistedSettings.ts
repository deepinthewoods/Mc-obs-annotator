const STORAGE_KEY = 'obsAnnotator_settings';

interface PersistedSilenceRemoval {
  enabled?: boolean;
  silenceThresholdDb?: number;
  minSilenceDuration?: number;
  padding?: number;
  maxSilenceForReset?: number;
}

interface PersistedSettings {
  sourceFolder?: string;
  outputFolder?: string;
  enabledEventTypes?: string[];
  chapterBuffer?: number;
  mergeOverlapping?: boolean;
  skipBlackClips?: boolean;
  createTimelines?: boolean;
  silenceRemoval?: PersistedSilenceRemoval;
}

export function loadPersistedSettings(): PersistedSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      return JSON.parse(raw) as PersistedSettings;
    }
  } catch {
    // ignore corrupt data
  }
  return {};
}

export function savePersistedSettings(settings: PersistedSettings): void {
  try {
    const existing = loadPersistedSettings();
    const merged = { ...existing, ...settings };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
  } catch {
    // ignore storage errors
  }
}
