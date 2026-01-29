# Bulk Import Feature - Implementation Plan

## Overview

Add a "Bulk Import" tab to the existing DaVinci Resolve companion plugin that:
1. Scans a folder of MKV recordings + matching EDL files
2. Extracts relevant clips based on marker types
3. Filters out black frames (AFK/alt-tab footage)
4. Creates organized Resolve timelines

## Requirements Summary

### Input
- **Source folder**: External drive with MKV files + matching EDL files
- **Output folder**: SSD for extracted clips
- **Video formats**: MKV (h.264 and h.265 mix)
- **Scale**: 10-50 recording sessions

### Extraction Rules

| Marker Type | Extraction Rule |
|-------------|-----------------|
| Regular chapter markers (Combat, Boss, etc.) | 0.5s before + 0.5s after, merge overlapping |
| Start → End pairs | Find "End", look back for most recent "Start", extract full range |
| POI A / POI B | 3 minutes before marker, ending at marker |

### Output
- **Extraction**: Lossless trim (FFmpeg `-c copy`, accepts keyframe-aligned cuts)
- **Black filter**: Skip clips that are 100% black frames
- **Folder structure**: `output/{video_name}/chapters/`, `recordings/`, `pois/`
- **Resolve integration**: Create timelines via Resolve API

### Output Timelines (per source video)
1. **Chapters Timeline**: All 0.5s chapter clips concatenated (for supercut generation)
2. **Recordings Timeline(s)**: One timeline per Start→End recording
3. **POI Timeline(s)**: One timeline per POI marker

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Electron App (React)                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    BulkImportPanel.tsx                       │   │
│  │  - Source/output folder selection                            │   │
│  │  - Scan results display                                      │   │
│  │  - Progress tracking                                         │   │
│  │  - Settings (buffer times, marker types)                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP API
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Python Flask Server                            │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐   │
│  │ bulk_scanner.py│  │clip_extractor.py│  │timeline_creator.py │   │
│  │                │  │                │  │                    │   │
│  │ - Find MKV+EDL │  │ - FFmpeg trim  │  │ - Resolve API      │   │
│  │ - Parse markers│  │ - Black detect │  │ - Create timelines │   │
│  │ - Build clips  │  │ - Merge regions│  │ - Import media     │   │
│  └────────────────┘  └────────────────┘  └────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## API Specification

### `POST /api/bulk/scan`
Scan source folder for video+EDL pairs.

**Request:**
```json
{
  "sourceFolder": "E:/recordings",
  "recursive": false
}
```

**Response:**
```json
{
  "success": true,
  "sessions": [
    {
      "id": "session_001",
      "videoFile": "E:/recordings/gameplay_2024_01_15.mkv",
      "edlFile": "E:/recordings/gameplay_2024_01_15.edl",
      "videoSize": 5368709120,
      "duration": 7200.5,
      "markerSummary": {
        "total": 156,
        "chapters": 142,
        "startEndPairs": 5,
        "pois": 9
      }
    }
  ],
  "totalSize": "45.2 GB",
  "totalSessions": 12
}
```

### `POST /api/bulk/analyze`
Analyze a session and calculate clip regions.

**Request:**
```json
{
  "sessionId": "session_001",
  "settings": {
    "chapterBuffer": 0.5,
    "poiDuration": 180,
    "mergeOverlapping": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "sessionId": "session_001",
  "clipRegions": {
    "chapters": [
      {"start": 120.5, "end": 121.5, "markers": ["Combat - Killed Zombie"]},
      {"start": 125.0, "end": 126.2, "markers": ["Combat - Killed Skeleton", "Combat - Killed Spider"]}
    ],
    "recordings": [
      {"start": 500.0, "end": 650.0, "startMarker": "Start", "endMarker": "End"}
    ],
    "pois": [
      {"start": 1620.0, "end": 1800.0, "marker": "POI A"}
    ]
  },
  "estimatedOutputSize": "1.2 GB",
  "estimatedReduction": "78%"
}
```

### `POST /api/bulk/extract`
Extract clips from a session.

**Request:**
```json
{
  "sessionId": "session_001",
  "outputFolder": "D:/extracted",
  "skipBlackClips": true
}
```

**Response (streaming progress):**
```json
{"type": "progress", "clip": 1, "total": 15, "status": "extracting", "file": "chapter_001.mkv"}
{"type": "progress", "clip": 2, "total": 15, "status": "skipped_black", "file": "chapter_002.mkv"}
...
{"type": "complete", "extracted": 14, "skipped": 1, "outputFolder": "D:/extracted/gameplay_2024_01_15"}
```

### `POST /api/bulk/create-timelines`
Create Resolve timelines from extracted clips.

**Request:**
```json
{
  "sessionId": "session_001",
  "extractedFolder": "D:/extracted/gameplay_2024_01_15"
}
```

**Response:**
```json
{
  "success": true,
  "timelines": [
    {"name": "gameplay_2024_01_15 - Chapters", "clips": 142, "duration": "2:15"},
    {"name": "gameplay_2024_01_15 - Recording 1", "clips": 1, "duration": "2:30"},
    {"name": "gameplay_2024_01_15 - POI A", "clips": 1, "duration": "3:00"}
  ]
}
```

### `POST /api/bulk/process-all`
Process all sessions in batch.

**Request:**
```json
{
  "sourceFolder": "E:/recordings",
  "outputFolder": "D:/extracted",
  "settings": {
    "chapterBuffer": 0.5,
    "poiDuration": 180,
    "skipBlackClips": true,
    "createTimelines": true
  }
}
```

---

## Implementation Tasks

### Agent 1: Python Backend - Core Processing (bulk_scanner.py, clip_extractor.py)

**Files to create:**
- `python-server/bulk_scanner.py` - Scan folders, pair files, parse EDLs
- `python-server/clip_extractor.py` - FFmpeg extraction, black detection, region merging

**Key functions:**

```python
# bulk_scanner.py
class BulkScanner:
    def scan_folder(self, source_folder: str, recursive: bool = False) -> List[Session]
    def parse_session(self, video_file: str, edl_file: str) -> Session
    def categorize_markers(self, markers: List[Marker]) -> CategorizedMarkers
    def build_clip_regions(self, markers: CategorizedMarkers, settings: Settings) -> ClipRegions
    def merge_overlapping_regions(self, regions: List[Region]) -> List[Region]
    def pair_start_end_markers(self, markers: List[Marker]) -> List[StartEndPair]

# clip_extractor.py
class ClipExtractor:
    def extract_clip(self, video_file: str, start: float, end: float, output: str) -> bool
    def detect_black_frames(self, video_file: str, start: float, end: float) -> float
    def is_entirely_black(self, video_file: str, start: float, end: float, threshold: float = 0.99) -> bool
    def extract_session(self, session: Session, output_folder: str, progress_callback) -> ExtractResult
```

**Dependencies:**
- Existing `edl_parser.py` (reuse)
- FFmpeg (subprocess calls)

---

### Agent 2: Python Backend - Resolve Integration (timeline_creator.py)

**Files to create:**
- `python-server/timeline_creator.py` - Create timelines, import media

**Key functions:**

```python
class TimelineCreator:
    def __init__(self, resolve, project):
        self.resolve = resolve
        self.project = project
        self.media_pool = project.GetMediaPool()

    def import_clips_to_pool(self, clip_folder: str) -> List[MediaPoolItem]
    def create_timeline(self, name: str, clips: List[MediaPoolItem]) -> Timeline
    def create_session_timelines(self, session_folder: str, session_name: str) -> List[Timeline]
    def add_clips_to_timeline(self, timeline: Timeline, clips: List[MediaPoolItem]) -> int
```

**Dependencies:**
- DaVinciResolveScript module
- Existing `server.py` patterns for Resolve API usage

---

### Agent 3: Flask API Endpoints (server.py additions)

**Files to modify:**
- `python-server/server.py` - Add bulk import endpoints

**Endpoints to add:**
- `POST /api/bulk/scan`
- `POST /api/bulk/analyze`
- `POST /api/bulk/extract` (with SSE progress streaming)
- `POST /api/bulk/create-timelines`
- `POST /api/bulk/process-all`

**Key considerations:**
- Long-running operations need progress streaming (Server-Sent Events)
- Error handling for partial failures
- Session state management between API calls

---

### Agent 4: React Frontend - BulkImportPanel Component

**Files to create:**
- `src/renderer/components/BulkImportPanel.tsx` - Main panel component
- `src/renderer/components/SessionList.tsx` - Display scanned sessions
- `src/renderer/components/ExtractionProgress.tsx` - Progress display
- `src/renderer/hooks/useBulkImport.ts` - API integration hook
- `src/renderer/types/bulk.ts` - TypeScript types

**Files to modify:**
- `src/renderer/App.tsx` - Add tab navigation, include BulkImportPanel

**UI Layout:**

```
┌─────────────────────────────────────────────────────────────────┐
│  [Single Import]  [Bulk Import]  [Supercut Generator]           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Source Folder: [E:/recordings                    ] [Browse]    │
│  Output Folder: [D:/extracted                     ] [Browse]    │
│                                                                 │
│  Settings:                                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Chapter buffer:  [0.5] seconds                          │   │
│  │ POI duration:    [180] seconds (3 minutes)              │   │
│  │ [x] Merge overlapping clips                             │   │
│  │ [x] Skip entirely black clips                           │   │
│  │ [x] Create Resolve timelines                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  [Scan Folder]                                                  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  Sessions Found: 12 (45.2 GB total)                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ [x] gameplay_2024_01_15.mkv    5.0 GB   156 markers     │   │
│  │ [x] gameplay_2024_01_16.mkv    3.2 GB   98 markers      │   │
│  │ [x] gameplay_2024_01_17.mkv    4.8 GB   134 markers     │   │
│  │ ...                                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Estimated output: 8.4 GB (81% reduction)                       │
│                                                                 │
│  [Process Selected]                [Process All]                │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  Progress:                                                      │
│  Session 3/12: gameplay_2024_01_17.mkv                         │
│  ████████████░░░░░░░░░░░░░░░░░░░░ 35%                          │
│  Extracting clip 45/134: chapter_045.mkv                        │
│                                                                 │
│  Completed: 2 sessions | Extracted: 254 clips | Skipped: 12    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Task Dependencies

```
Agent 1 (bulk_scanner.py, clip_extractor.py)
    │
    ├──► Agent 3 (server.py endpoints) ◄── Agent 2 (timeline_creator.py)
    │                │
    │                ▼
    └──────────► Agent 4 (React frontend)
```

**Parallelizable:**
- Agent 1 and Agent 2 can work in parallel (no dependencies)
- Agent 4 can start immediately with mock data

**Sequential:**
- Agent 3 depends on Agent 1 + Agent 2 for the actual implementation imports
- Final integration testing requires all agents complete

---

## File Changes Summary

### New Files
| File | Agent | Description |
|------|-------|-------------|
| `python-server/bulk_scanner.py` | 1 | Scan folders, parse EDLs, build clip regions |
| `python-server/clip_extractor.py` | 1 | FFmpeg extraction, black detection |
| `python-server/timeline_creator.py` | 2 | Resolve API timeline creation |
| `src/renderer/components/BulkImportPanel.tsx` | 4 | Main bulk import UI |
| `src/renderer/components/SessionList.tsx` | 4 | Session list display |
| `src/renderer/components/ExtractionProgress.tsx` | 4 | Progress tracking UI |
| `src/renderer/hooks/useBulkImport.ts` | 4 | API integration hook |
| `src/renderer/types/bulk.ts` | 4 | TypeScript types |

### Modified Files
| File | Agent | Changes |
|------|-------|---------|
| `python-server/server.py` | 3 | Add bulk import endpoints |
| `src/renderer/App.tsx` | 4 | Add tab navigation |
| `src/renderer/styles/globals.css` | 4 | Add bulk import styles |

---

## FFmpeg Commands Reference

### Lossless clip extraction
```bash
ffmpeg -ss {start} -i "{input}" -t {duration} -c copy -avoid_negative_ts make_zero "{output}"
```

### Black frame detection
```bash
ffmpeg -ss {start} -i "{input}" -t {duration} -vf "blackdetect=d=0.1:pix_th=0.1" -f null - 2>&1
```
Parse output for `black_start`, `black_end`, `black_duration` to calculate black percentage.

### Get video duration
```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{input}"
```

---

## Testing Plan

1. **Unit tests** for clip region merging logic
2. **Unit tests** for Start→End pairing logic
3. **Integration test** with sample MKV + EDL
4. **Manual test** with real recording folder

---

## Notes

- FFmpeg lossless cuts align to keyframes; actual cut points may be ±1-2 seconds
- MKV format supports both h.264 and h.265; `-c copy` preserves original codec
- Resolve API requires Studio version; check for this gracefully
- Progress streaming uses Server-Sent Events for real-time updates
- Session state persists in memory between API calls (scan → analyze → extract → create)
