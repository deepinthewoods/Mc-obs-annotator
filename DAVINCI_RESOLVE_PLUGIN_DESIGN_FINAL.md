# DaVinci Resolve Companion Plugin - Final Design Document

## Overview
This document outlines the design for a DaVinci Resolve companion plugin that works with your **existing** Minecraft ObsAnnotator mod and OBS StreamUP Chapter Marker Manager to enable powerful video editing workflows including marker filtering, preview, and BPM-synchronized supercut generation.

---

## Current Architecture (No Changes Needed!)

```
┌─────────────────┐
│   Minecraft     │
│  ObsAnnotator   │  - Tracks 20+ event types
│      Mod        │  - Combat, Boss, Block, Item, etc.
└────────┬────────┘
         │ OBS WebSocket (port 4455)
         │ CallVendorRequest to "streamup-chapter-manager"
         │ Sends: "Combat - Entity Attacked", etc.
         ▼
┌─────────────────┐
│   OBS Studio    │
│   + StreamUP    │  - Receives annotations via WebSocket
│   Chapter       │  - Creates chapter markers during recording
│   Manager       │  - Stores markers in memory
└────────┬────────┘
         │
         │ Records video
         ▼
┌─────────────────┐
│   Video File    │
│    (.mp4)       │
└─────────────────┘

After Recording:
┌─────────────────┐
│   StreamUP      │  - Export markers as EDL file
│   EDL Export    │  - File > Export > EDL
└─────────────────┘
```

### What Works Now
✅ Minecraft mod connects to OBS WebSocket
✅ Events are sent in real-time to StreamUP
✅ StreamUP creates chapter markers during recording
✅ StreamUP can export markers to **EDL format**
✅ Config file supports event toggles and cooldowns

**Nothing needs to change in your existing mod!**

---

## What We're Adding: DaVinci Resolve Companion Plugin

```
After Recording:

┌─────────────────┐      ┌──────────────────┐
│   Video File    │      │   StreamUP EDL   │
│    (.mp4)       │      │   Export (.edl)  │
└─────────┬───────┘      └────────┬─────────┘
          │                       │
          └────────┬──────────────┘
                   │
          ┌────────▼───────────────────────┐
          │  DaVinci Resolve               │
          │                                 │
          │  Option A: Direct Import        │
          │  - Right-click timeline         │
          │  - Import > Timeline Markers    │
          │    from EDL                     │
          │                                 │
          │  Option B: Use Plugin (NEW)     │
          │  ┌────────────────────────────┐ │
          │  │ ObsAnnotator Plugin        │ │
          │  │ - Filter markers           │ │
          │  │ - Preview before import    │ │
          │  │ - Generate BPM supercuts   │ │
          │  └────────────────────────────┘ │
          └─────────────────────────────────┘
```

### Plugin Value Proposition

Users can import EDL directly in Resolve, but our plugin adds:

1. **Marker Preview** - See all markers before importing
2. **Filtering** - Only import markers you want (search, exclude, event types, time range)
3. **Color Coding** - Auto-assign colors by event type
4. **BPM Supercuts** - Auto-generate beat-synced video edits
5. **Batch Operations** - Process multiple recording sessions
6. **Statistics** - View event counts and distribution

---

## Component 1: Understanding StreamUP EDL Export Format

### EDL Format (CMX 3600)

StreamUP exports in standard CMX 3600 EDL format with marker extensions:

```edl
TITLE: Recording Title
FCM: NON-DROP FRAME

001 001 V C 00:00:15:13 00:00:15:14 00:00:15:13 00:00:15:14
* FROM CLIP NAME: recording.mp4
|C:ResolveColorRed
|M:Combat - Entity Attacked
|D:1

002 001 V C 00:03:22:03 00:03:22:04 00:03:22:03 00:03:22:04
* FROM CLIP NAME: recording.mp4
|C:ResolveColorCyan
|M:Block - Diamond Ore Mined
|D:1

003 001 V C 00:15:30:00 00:15:30:01 00:15:30:00 00:15:30:01
* FROM CLIP NAME: recording.mp4
|C:ResolveColorPurple
|M:Boss - Ender Dragon Spawned
|D:1
```

### EDL Structure

**Header:**
- `TITLE:` - Recording session name
- `FCM:` - Frame count mode (NON-DROP FRAME or DROP FRAME)

**Event Entry:**
```
001 001 V C 00:00:15:13 00:00:15:14 00:00:15:13 00:00:15:14
│   │   │ │ │           │           │           └─ Record Out
│   │   │ │ │           │           └─ Record In (marker timecode)
│   │   │ │ │           └─ Source Out
│   │   │ │ └─ Source In
│   │   │ └─ Edit type (C=Cut)
│   │   └─ Track (V=Video)
│   └─ Reel/Clip number
└─ Event number
```

**Marker Metadata:**
- `|C:` - Color (ResolveColorRed, ResolveColorBlue, etc.)
- `|M:` - Marker text (the annotation from your mod)
- `|D:` - Duration in frames (typically 1 for point markers)

### Marker Text Format

From your mod, annotations are sent as:
```
"Combat - Entity Attacked"
"Boss - Ender Dragon Spawned"
"Block - Diamond Ore Mined"
"Achievement - Advancement Unlocked"
"Manual - POI A"
```

Format: `{EventType} - {EventSubtype}`

This makes parsing and filtering straightforward!

---

## Component 2: DaVinci Resolve Workflow Integration Plugin

### Technology Stack

**Frontend:**
- Electron (desktop app framework)
- React + TypeScript (UI components)
- Tailwind CSS (styling)

**Backend:**
- Python Flask server (API for Resolve)
- DaVinci Resolve Python API (timeline manipulation)

**Communication:**
- HTTP REST API between Electron and Python
- Python server runs on localhost:8765

### Architecture

```
┌─────────────────────────────────────────┐
│   Electron App (Main Process)           │
│   ┌─────────────────────────────────┐  │
│   │  React UI                       │  │
│   │  ┌───────────────────────────┐ │  │
│   │  │ File Browser             │ │  │
│   │  │ - Video file selector    │ │  │
│   │  │ - EDL file selector      │ │  │
│   │  └───────────────────────────┘ │  │
│   │                                 │  │
│   │  ┌───────────────────────────┐ │  │
│   │  │ Marker List              │ │  │
│   │  │ - Sortable table         │ │  │
│   │  │ - Color indicators       │ │  │
│   │  │ - Event statistics       │ │  │
│   │  └───────────────────────────┘ │  │
│   │                                 │  │
│   │  ┌───────────────────────────┐ │  │
│   │  │ Filter Panel             │ │  │
│   │  │ - Text search            │ │  │
│   │  │ - Exclude filter         │ │  │
│   │  │ - Event type checkboxes  │ │  │
│   │  │ - Time range slider      │ │  │
│   │  └───────────────────────────┘ │  │
│   │                                 │  │
│   │  ┌───────────────────────────┐ │  │
│   │  │ BPM Supercut Generator   │ │  │
│   │  │ - BPM input              │ │  │
│   │  │ - Note division selector │ │  │
│   │  │ - Options                │ │  │
│   │  └───────────────────────────┘ │  │
│   └─────────────────────────────────┘  │
│              │                          │
│              │ IPC Bridge               │
│              ▼                          │
│   ┌─────────────────────────────────┐  │
│   │  API Client (fetch/axios)       │  │
│   └──────────┬──────────────────────┘  │
└──────────────┼──────────────────────────┘
               │ HTTP (localhost:8765)
               ▼
┌─────────────────────────────────────────┐
│   Python Flask Server                   │
│   ┌─────────────────────────────────┐  │
│   │  REST API Endpoints             │  │
│   │  - POST /api/parse-edl          │  │
│   │  - POST /api/import-markers     │  │
│   │  - POST /api/generate-supercut  │  │
│   │  - GET  /api/timeline/info      │  │
│   └──────────┬──────────────────────┘  │
│              │                          │
│   ┌──────────▼──────────────────────┐  │
│   │  EDL Parser                     │  │
│   │  - Parse CMX 3600 format        │  │
│   │  - Extract markers              │  │
│   │  - Convert timecodes            │  │
│   └──────────┬──────────────────────┘  │
│              │                          │
│   ┌──────────▼──────────────────────┐  │
│   │  Marker Filter                  │  │
│   │  - Apply search/exclude         │  │
│   │  - Filter by type               │  │
│   │  - Filter by time range         │  │
│   └──────────┬──────────────────────┘  │
│              │                          │
│   ┌──────────▼──────────────────────┐  │
│   │  DaVinci Resolve API            │  │
│   │  - Import markers to timeline   │  │
│   │  - Create new timelines         │  │
│   │  - Generate supercuts           │  │
│   └─────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### File Structure

```
resolve-obsannotator-plugin/
├── package.json
├── electron-main.js                 # Electron entry point
├── tsconfig.json
├── webpack.config.js
├── src/
│   ├── renderer/                    # React app
│   │   ├── App.tsx                  # Main component
│   │   ├── index.tsx                # Entry point
│   │   ├── components/
│   │   │   ├── FileBrowser.tsx
│   │   │   ├── MarkerList.tsx
│   │   │   ├── FilterPanel.tsx
│   │   │   ├── SupercutPanel.tsx
│   │   │   ├── StatusBar.tsx
│   │   │   └── EventStatistics.tsx
│   │   ├── hooks/
│   │   │   ├── useEdlParser.ts
│   │   │   ├── useMarkerFilter.ts
│   │   │   └── useResolveApi.ts
│   │   ├── types/
│   │   │   ├── marker.ts
│   │   │   ├── edl.ts
│   │   │   └── api.ts
│   │   └── styles/
│   │       └── globals.css
│   └── main/                        # Electron main process
│       ├── index.ts
│       └── preload.ts
├── python-server/
│   ├── server.py                    # Flask app
│   ├── edl_parser.py                # EDL parsing
│   ├── marker_filter.py             # Filtering logic
│   ├── supercut_generator.py       # BPM supercut
│   ├── resolve_api.py               # Resolve integration
│   └── requirements.txt
└── README.md
```

---

## Component 3: GUI Design

### Main Window Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  ObsAnnotator - DaVinci Resolve Companion             [_][□][×]  │
├──────────────────────────────────────────────────────────────────┤
│  📁 Load Files                                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Video File:  [C:/Videos/2024-01-15_Stream.mp4    ] [Browse]│ │
│  │ EDL File:    [C:/Videos/2024-01-15_Stream.edl    ] [Browse]│ │
│  │                                                              │ │
│  │ ℹ️  Video: 1920x1080, 30fps, 01:02:45 duration               │ │
│  │ ℹ️  Markers: 234 total events                                │ │
│  │                                                              │ │
│  │ [Auto-detect matching EDL] [Load Files]                    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  📊 Event Statistics                                              │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ 🔴 Combat: 45    🟣 Boss: 8       🔵 Block: 120            │ │
│  │ 🟢 Item: 12      🔵 Explore: 5    🟡 Achievement: 3        │ │
│  │ 🟠 Explosion: 25 🟡 Manual: 16    Total: 234               │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  🔍 Filter Markers                                                │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Search:   [dragon              ] (contains text)           │ │
│  │ Exclude:  [manual              ] (exclude text)            │ │
│  │                                                             │ │
│  │ Time Range:                                                 │ │
│  │ [00:00:00] ━━━━●━━━━━━━━━━━━━━━━━━━━━━━ [01:02:45]        │ │
│  │            └─ 0:00           Current: 15:30      End ─┘    │ │
│  │                                                             │ │
│  │ Event Types:                                                │ │
│  │ ☑ Combat (45)      ☑ Boss (8)         ☑ Block (120)       │ │
│  │ ☑ Item (12)        ☑ Exploration (5)  ☑ Achievement (3)   │ │
│  │ ☐ Explosion (25)   ☐ Manual (16)                          │ │
│  │                                                             │ │
│  │ [Clear All Filters] [Reset]                                │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  📋 Filtered Markers (3 visible / 234 total)                     │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ ⬜ Time      │ Color │ Type │ Description                   │ │
│  │ ├───────────┼───────┼──────┼──────────────────────────────┤ │
│  │ ☑ 00:15:30  │  🟣   │ Boss │ Ender Dragon Spawned         │ │
│  │ ☑ 00:18:45  │  🟣   │ Boss │ Ender Dragon Defeated        │ │
│  │ ☑ 00:22:10  │  🟡   │ Ach. │ Advancement: Free the End    │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  [Import Selected to Timeline (3)]  [Import All Filtered (3)]   │
│                                                                   │
│  🎵 BPM Supercut Generator                                        │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Song BPM:         [120]  ℹ️ Use a BPM detector if unsure    │ │
│  │                                                              │ │
│  │ Note Division:                                               │ │
│  │ ( ) Whole  (●) Half  ( ) Quarter  ( ) Eighth  ( ) Sixteenth│ │
│  │                                                              │ │
│  │ Clip Duration: [1.00] seconds (auto-calculated from BPM)   │ │
│  │                                                              │ │
│  │ Source: Use filtered markers above (3 events)               │ │
│  │ Estimated supercut length: [00:03] (3 clips × 1.0s)        │ │
│  │                                                              │ │
│  │ Options:                                                     │ │
│  │ ☑ Add crossfade transitions ([0.2] seconds)                │ │
│  │ ☑ Sort clips chronologically                                │ │
│  │ ☐ Randomize clip order                                      │ │
│  │ ☑ Skip duplicate events within [3.0] seconds               │ │
│  │ ☑ Add beat markers to timeline                              │ │
│  │                                                              │ │
│  │ Output Timeline Name: [Supercut_Boss_120BPM]               │ │
│  │                                                              │ │
│  │               [Generate Supercut]                            │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Status: ✅ Connected to DaVinci Resolve | 3 markers ready       │
└───────────────────────────────────────────────────────────────────┘
```

### Key UI Features

**1. Smart File Detection**
- When user selects video file, auto-search for matching .edl file
- Match by filename: `recording.mp4` → `recording.edl`
- Show warning if EDL not found

**2. Real-time Filtering**
- Filter updates immediately as user types
- Show filtered count vs total count
- Visual feedback on which markers are visible

**3. Event Type Checkboxes**
- Show count next to each type
- Update counts when filters change
- Color-coded to match Resolve colors

**4. Time Range Slider**
- Visual timeline representation
- Drag handles to set start/end
- Show timecode at current position

**5. Marker List**
- Sortable by time, type, description
- Checkboxes for selective import
- Color indicators matching Resolve
- Click to jump to timecode in preview

**6. BPM Calculator**
- Auto-calculate clip duration from BPM
- Show estimated output length
- Preview beat grid

---

## Component 4: Python Backend Implementation

### EDL Parser

**File:** `python-server/edl_parser.py`

```python
import re
from typing import List, Dict, Optional

class EdlParser:
    """Parse CMX 3600 EDL files with Resolve marker extensions."""

    def __init__(self):
        self.framerate = 30.0  # Default, can be overridden

    def parse(self, edl_file_path: str) -> Dict:
        """
        Parse EDL file and return structured data.

        Returns:
            {
                'title': str,
                'framerate': float,
                'fcm': str,
                'markers': List[Dict]
            }
        """
        markers = []
        title = ""
        fcm = "NON-DROP FRAME"

        with open(edl_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Parse header
            if line.startswith('TITLE:'):
                title = line[6:].strip()
            elif line.startswith('FCM:'):
                fcm = line[4:].strip()
                # Detect framerate from FCM
                if 'DROP' in fcm:
                    self.framerate = 29.97
                else:
                    self.framerate = 30.0

            # Parse event line (starts with digit)
            elif line and line[0].isdigit():
                marker = self._parse_event(lines, i)
                if marker:
                    markers.append(marker)

            i += 1

        return {
            'title': title,
            'framerate': self.framerate,
            'fcm': fcm,
            'markers': markers
        }

    def _parse_event(self, lines: List[str], start_idx: int) -> Optional[Dict]:
        """Parse a single event entry."""
        line = lines[start_idx].strip()
        parts = line.split()

        if len(parts) < 9:
            return None

        event_num = int(parts[0])
        # Timecode is at parts[4] (Record In)
        timecode = parts[4]

        # Parse metadata lines (|C:, |M:, |D:)
        color = None
        text = None
        duration = 1

        for j in range(start_idx + 1, min(start_idx + 10, len(lines))):
            meta_line = lines[j].strip()

            if meta_line.startswith('|C:'):
                color = meta_line[3:].strip()
            elif meta_line.startswith('|M:'):
                text = meta_line[3:].strip()
            elif meta_line.startswith('|D:'):
                duration = int(meta_line[3:].strip())
            elif not meta_line or (meta_line[0].isdigit() and j > start_idx + 1):
                # Next event or empty line, stop parsing metadata
                break

        if not text:
            return None

        # Parse event type and subtype from text
        # Format: "EventType - EventSubtype"
        type_parts = text.split(' - ', 1)
        event_type = type_parts[0].strip() if len(type_parts) > 0 else "Unknown"
        event_subtype = type_parts[1].strip() if len(type_parts) > 1 else ""

        return {
            'id': event_num,
            'timecode': timecode,
            'timestampSeconds': self.timecode_to_seconds(timecode),
            'color': color,
            'text': text,
            'type': event_type,
            'subtype': event_subtype,
            'duration': duration
        }

    def timecode_to_seconds(self, timecode: str) -> float:
        """
        Convert timecode HH:MM:SS:FF to seconds.

        Args:
            timecode: String in format "HH:MM:SS:FF"

        Returns:
            Timestamp in seconds (float)
        """
        parts = timecode.split(':')
        if len(parts) != 4:
            return 0.0

        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        frames = int(parts[3])

        total_seconds = (
            hours * 3600 +
            minutes * 60 +
            seconds +
            (frames / self.framerate)
        )

        return total_seconds

    def seconds_to_timecode(self, seconds: float) -> str:
        """
        Convert seconds to timecode HH:MM:SS:FF.

        Args:
            seconds: Timestamp in seconds

        Returns:
            Timecode string "HH:MM:SS:FF"
        """
        total_frames = int(seconds * self.framerate)
        hours = total_frames // (int(self.framerate) * 3600)
        minutes = (total_frames % (int(self.framerate) * 3600)) // (int(self.framerate) * 60)
        secs = (total_frames % (int(self.framerate) * 60)) // int(self.framerate)
        frames = total_frames % int(self.framerate)

        return f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}"
```

### Marker Filter

**File:** `python-server/marker_filter.py`

```python
from typing import List, Dict, Set

class MarkerFilter:
    """Filter markers based on user criteria."""

    @staticmethod
    def apply_filters(markers: List[Dict], filters: Dict) -> List[Dict]:
        """
        Apply all filters to marker list.

        Args:
            markers: List of marker dicts
            filters: {
                'search': str (optional),
                'exclude': str (optional),
                'eventTypes': List[str] (optional),
                'timeRangeStart': float (optional),
                'timeRangeEnd': float (optional)
            }

        Returns:
            Filtered list of markers
        """
        filtered = markers.copy()

        # Text search filter
        if filters.get('search'):
            search_term = filters['search'].lower()
            filtered = [
                m for m in filtered
                if search_term in m['text'].lower() or
                   search_term in m['type'].lower() or
                   search_term in m['subtype'].lower()
            ]

        # Exclude filter
        if filters.get('exclude'):
            exclude_term = filters['exclude'].lower()
            filtered = [
                m for m in filtered
                if exclude_term not in m['text'].lower() and
                   exclude_term not in m['type'].lower() and
                   exclude_term not in m['subtype'].lower()
            ]

        # Event type filter
        if filters.get('eventTypes'):
            allowed_types = set(filters['eventTypes'])
            filtered = [
                m for m in filtered
                if m['type'] in allowed_types
            ]

        # Time range filter
        if filters.get('timeRangeStart') is not None:
            start = filters['timeRangeStart']
            filtered = [
                m for m in filtered
                if m['timestampSeconds'] >= start
            ]

        if filters.get('timeRangeEnd') is not None:
            end = filters['timeRangeEnd']
            filtered = [
                m for m in filtered
                if m['timestampSeconds'] <= end
            ]

        return filtered

    @staticmethod
    def get_event_statistics(markers: List[Dict]) -> Dict[str, int]:
        """
        Count markers by event type.

        Returns:
            {'Combat': 45, 'Boss': 8, ...}
        """
        stats = {}
        for marker in markers:
            event_type = marker['type']
            stats[event_type] = stats.get(event_type, 0) + 1

        return stats
```

### BPM Supercut Generator

**File:** `python-server/supercut_generator.py`

```python
import random
from typing import List, Dict, Any

class SupercutGenerator:
    """Generate BPM-synchronized supercut timelines."""

    def __init__(self, resolve, project):
        self.resolve = resolve
        self.project = project
        self.media_pool = project.GetMediaPool()

    def generate(
        self,
        video_file: str,
        markers: List[Dict],
        bpm: int,
        note_division: str,
        options: Dict
    ) -> Dict[str, Any]:
        """
        Generate a BPM-synchronized supercut.

        Args:
            video_file: Path to source video
            markers: List of marker dicts (already filtered)
            bpm: Beats per minute (e.g., 120)
            note_division: 'whole', 'half', 'quarter', 'eighth', 'sixteenth'
            options: {
                'sort_chronologically': bool,
                'randomize': bool,
                'skip_duplicates_within_seconds': float,
                'add_crossfades': bool,
                'crossfade_duration': float,
                'add_beat_markers': bool,
                'output_timeline_name': str
            }

        Returns:
            {
                'success': bool,
                'timeline_name': str,
                'clips_added': int,
                'duration_seconds': float,
                'error': str (optional)
            }
        """
        # 1. Calculate timing parameters
        beat_interval = 60.0 / bpm
        clip_duration = self._calculate_clip_duration(bpm, note_division)
        half_duration = clip_duration / 2.0

        # 2. Prepare markers
        working_markers = markers.copy()

        if options.get('sort_chronologically', True):
            working_markers.sort(key=lambda m: m['timestampSeconds'])
        elif options.get('randomize', False):
            random.shuffle(working_markers)

        if options.get('skip_duplicates_within_seconds'):
            working_markers = self._remove_nearby_duplicates(
                working_markers,
                options['skip_duplicates_within_seconds']
            )

        if not working_markers:
            return {'success': False, 'error': 'No markers after filtering'}

        # 3. Import source video
        media_item = self._import_media(video_file)
        if not media_item:
            return {'success': False, 'error': 'Failed to import video file'}

        # 4. Create new timeline
        timeline_name = options.get('output_timeline_name', f'Supercut_{bpm}BPM')
        timeline = self.media_pool.CreateEmptyTimeline(timeline_name)
        if not timeline:
            return {'success': False, 'error': 'Failed to create timeline'}

        # 5. Add clips to timeline
        beat_position = 0
        clips_added = 0
        framerate = float(timeline.GetSetting('timelineFrameRate'))

        for marker in working_markers:
            # Calculate source clip boundaries
            # Event should land on beat, so extract:
            # [marker_time - half_duration] to [marker_time + half_duration]
            source_start = marker['timestampSeconds'] - half_duration
            source_end = marker['timestampSeconds'] + half_duration

            # Handle edge cases (don't go before 0)
            if source_start < 0:
                source_start = 0
                source_end = clip_duration

            # Convert to frames
            source_start_frame = int(source_start * framerate)
            source_end_frame = int(source_end * framerate)

            # Add clip to timeline at beat position
            success = self._add_clip_to_timeline(
                timeline,
                media_item,
                source_start_frame,
                source_end_frame,
                beat_position,
                framerate
            )

            if success:
                clips_added += 1

                # Add marker at beat position
                if options.get('add_beat_markers', True):
                    beat_frame = int(beat_position * framerate)
                    timeline.AddMarker(
                        frameId=beat_frame,
                        color=marker.get('color', 'Blue'),
                        name=marker['text'],
                        note=f"Beat {clips_added}",
                        duration=1
                    )

            # Move to next beat
            beat_position += beat_interval

        # 6. Add crossfades if requested
        if options.get('add_crossfades', False):
            self._add_crossfades(
                timeline,
                options.get('crossfade_duration', 0.2),
                framerate
            )

        return {
            'success': True,
            'timeline_name': timeline_name,
            'clips_added': clips_added,
            'duration_seconds': beat_position,
            'markers_used': len(working_markers)
        }

    def _calculate_clip_duration(self, bpm: int, note_division: str) -> float:
        """
        Calculate clip duration based on BPM and note division.

        Examples:
            120 BPM, half note = 1.0s
            120 BPM, quarter note = 0.5s
            120 BPM, eighth note = 0.25s
        """
        note_multipliers = {
            'whole': 4.0,
            'half': 2.0,
            'quarter': 1.0,
            'eighth': 0.5,
            'sixteenth': 0.25
        }

        beat_duration = 60.0 / bpm
        return beat_duration * note_multipliers.get(note_division, 1.0)

    def _remove_nearby_duplicates(
        self,
        markers: List[Dict],
        threshold: float
    ) -> List[Dict]:
        """
        Remove markers that are within threshold seconds of each other.
        Keeps the first occurrence.
        """
        if not markers:
            return []

        filtered = [markers[0]]
        last_timestamp = markers[0]['timestampSeconds']

        for marker in markers[1:]:
            if marker['timestampSeconds'] - last_timestamp >= threshold:
                filtered.append(marker)
                last_timestamp = marker['timestampSeconds']

        return filtered

    def _import_media(self, file_path: str):
        """Import media file into media pool."""
        root_folder = self.media_pool.GetRootFolder()
        items = self.media_pool.ImportMedia([file_path])
        return items[0] if items else None

    def _add_clip_to_timeline(
        self,
        timeline,
        media_item,
        source_start_frame: int,
        source_end_frame: int,
        record_time_seconds: float,
        framerate: float
    ) -> bool:
        """Add a clip to the timeline at specified position."""
        record_frame = int(record_time_seconds * framerate)

        # Use AppendToTimeline with clip info
        clip_info = {
            "mediaPoolItem": media_item,
            "startFrame": source_start_frame,
            "endFrame": source_end_frame,
            "trackIndex": 1,
            "recordFrame": record_frame
        }

        return timeline.AppendToTimeline([clip_info])

    def _add_crossfades(self, timeline, duration_seconds: float, framerate: float):
        """Add crossfade transitions between all clips."""
        transition_frames = int(duration_seconds * framerate)

        # Get clips from track 1
        clips = timeline.GetItemListInTrack("video", 1)

        for i in range(len(clips) - 1):
            timeline.AddTransition(
                transitionType="Cross Dissolve",
                trackIndex=1,
                clipIndex=i,
                duration=transition_frames
            )
```

### Flask API Server

**File:** `python-server/server.py`

```python
from flask import Flask, request, jsonify
from flask_cors import CORS
import DaVinciResolveScript as dvr_script

from edl_parser import EdlParser
from marker_filter import MarkerFilter
from supercut_generator import SupercutGenerator

app = Flask(__name__)
CORS(app)  # Allow Electron app to connect

# Initialize DaVinci Resolve API
resolve = None
project = None

def init_resolve():
    """Initialize connection to DaVinci Resolve."""
    global resolve, project
    try:
        resolve = dvr_script.scriptapp("Resolve")
        if resolve:
            project_manager = resolve.GetProjectManager()
            project = project_manager.GetCurrentProject()
            return True
    except Exception as e:
        print(f"Failed to connect to Resolve: {e}")
    return False

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check if server and Resolve are connected."""
    resolve_connected = init_resolve() if not resolve else True

    return jsonify({
        'server': 'running',
        'resolve_connected': resolve_connected,
        'project_open': project is not None
    })

@app.route('/api/parse-edl', methods=['POST'])
def parse_edl():
    """Parse EDL file and return markers."""
    try:
        data = request.json
        edl_file = data['edlFilePath']

        parser = EdlParser()
        result = parser.parse(edl_file)

        # Calculate statistics
        stats = MarkerFilter.get_event_statistics(result['markers'])

        return jsonify({
            'success': True,
            'title': result['title'],
            'framerate': result['framerate'],
            'markers': result['markers'],
            'statistics': stats,
            'total_count': len(result['markers'])
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/filter-markers', methods=['POST'])
def filter_markers():
    """Apply filters to marker list."""
    try:
        data = request.json
        markers = data['markers']
        filters = data['filters']

        filtered = MarkerFilter.apply_filters(markers, filters)
        stats = MarkerFilter.get_event_statistics(filtered)

        return jsonify({
            'success': True,
            'markers': filtered,
            'statistics': stats,
            'count': len(filtered)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/import-markers', methods=['POST'])
def import_markers():
    """Import markers to current Resolve timeline."""
    try:
        if not resolve or not project:
            if not init_resolve():
                return jsonify({
                    'success': False,
                    'error': 'Not connected to DaVinci Resolve'
                }), 500

        data = request.json
        markers = data['markers']

        timeline = project.GetCurrentTimeline()
        if not timeline:
            return jsonify({
                'success': False,
                'error': 'No timeline is currently open'
            }), 400

        # Get timeline framerate
        framerate = float(timeline.GetSetting('timelineFrameRate'))

        # Import each marker
        imported_count = 0
        for marker in markers:
            frame = int(marker['timestampSeconds'] * framerate)

            success = timeline.AddMarker(
                frameId=frame,
                color=marker.get('color', 'Blue'),
                name=marker['text'],
                note=f"{marker['type']} - {marker['subtype']}",
                duration=marker.get('duration', 1)
            )

            if success:
                imported_count += 1

        return jsonify({
            'success': True,
            'imported': imported_count,
            'total': len(markers)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate-supercut', methods=['POST'])
def generate_supercut():
    """Generate BPM-synchronized supercut timeline."""
    try:
        if not resolve or not project:
            if not init_resolve():
                return jsonify({
                    'success': False,
                    'error': 'Not connected to DaVinci Resolve'
                }), 500

        data = request.json
        video_file = data['videoFile']
        markers = data['markers']
        bpm = data['bpm']
        note_division = data['noteDivision']
        options = data.get('options', {})

        generator = SupercutGenerator(resolve, project)
        result = generator.generate(
            video_file=video_file,
            markers=markers,
            bpm=bpm,
            note_division=note_division,
            options=options
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("Starting ObsAnnotator Python server...")
    print("Connecting to DaVinci Resolve...")

    if init_resolve():
        print("✓ Connected to DaVinci Resolve")
        if project:
            print(f"✓ Project open: {project.GetName()}")
    else:
        print("⚠ Could not connect to DaVinci Resolve")
        print("  Make sure Resolve is running and a project is open")

    print("\nServer running on http://localhost:8765")
    app.run(host='127.0.0.1', port=8765, debug=False)
```

---

## Component 5: User Workflows

### Workflow 1: Simple Marker Import

```
1. Record gameplay
   → Minecraft mod sends events to StreamUP ✅

2. After recording, in OBS:
   → File > Export > EDL
   → Save to same directory as video
   → my_stream.mp4 + my_stream.edl created

3. In DaVinci Resolve:
   → Right-click timeline
   → Timelines > Import > Timeline Markers from EDL
   → Select my_stream.edl
   → All markers appear on timeline ✅

Done! No plugin needed for basic import.
```

### Workflow 2: Filtered Marker Import (Using Plugin)

```
1. Record gameplay
   → Minecraft mod sends events to StreamUP ✅

2. Export from StreamUP
   → File > Export > EDL
   → my_stream.edl created

3. Open DaVinci Resolve
   → Start Python server (python server.py)
   → Open ObsAnnotator plugin

4. In plugin:
   → Load my_stream.mp4 and my_stream.edl
   → Plugin shows all 234 markers
   → Apply filters:
     * Search: "boss"
     * Uncheck: Explosion, Manual
     * Time range: 00:10:00 to 00:30:00
   → Now showing 8 markers (only Boss events)

5. Click "Import Filtered to Timeline"
   → Only 8 Boss markers appear on Resolve timeline ✅

Perfect for focusing on specific content!
```

### Workflow 3: BPM Supercut Generation

```
1. Record gameplay + export EDL (same as above)

2. Open DaVinci Resolve + Plugin

3. In plugin:
   → Load video + EDL
   → Filter for combat events:
     * Check: Combat
     * Search: "attacked"
     * Result: 45 markers

4. BPM Supercut Generator:
   → BPM: 140
   → Note division: Quarter notes
   → Clip duration: 0.43s (auto-calculated)
   → Options:
     ☑ Add crossfades (0.2s)
     ☑ Sort chronologically
     ☑ Skip duplicates within 3s
   → Output: "Combat_Montage_140BPM"

5. Click "Generate Supercut"
   → Plugin creates new timeline
   → 45 clips, each 0.43s long
   → Events land exactly on beats
   → Crossfades between clips
   → Total: ~19 seconds of action

6. Add your music track (140 BPM)
   → Everything syncs perfectly! ✅

Perfect for montage videos!
```

---

## Component 6: Installation & Setup

### Prerequisites

**For Minecraft + OBS (Already have!):**
- ✅ Minecraft with ObsAnnotator mod
- ✅ OBS Studio with StreamUP Chapter Marker Manager
- ✅ Already configured and working

**For DaVinci Resolve Plugin:**
- DaVinci Resolve Studio 18+ (Studio version required for Python API)
- Python 3.10+
- Node.js 18+

### Installation Steps

#### 1. Install Python Dependencies

```bash
cd resolve-obsannotator-plugin/python-server

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**requirements.txt:**
```
flask==3.0.0
flask-cors==4.0.0
DaVinciResolveScript==1.0.0
```

#### 2. Build Electron App

```bash
cd resolve-obsannotator-plugin

# Install dependencies
npm install

# Build app
npm run build

# Output: dist/ folder with built app
```

#### 3. Run the Plugin

**Start Python server:**
```bash
cd python-server
python server.py

# Output:
# Starting ObsAnnotator Python server...
# Connecting to DaVinci Resolve...
# ✓ Connected to DaVinci Resolve
# ✓ Project open: My Project
# Server running on http://localhost:8765
```

**Start Electron app:**
```bash
# From another terminal
cd resolve-obsannotator-plugin
npm start

# Plugin window opens
```

#### 4. (Optional) Create Launcher Scripts

**Windows - `start-plugin.bat`:**
```batch
@echo off
echo Starting ObsAnnotator Plugin...

start "Python Server" cmd /k "cd python-server && python server.py"
timeout /t 3 /nobreak > nul
start "ObsAnnotator Plugin" cmd /k "npm start"
```

**Mac/Linux - `start-plugin.sh`:**
```bash
#!/bin/bash
echo "Starting ObsAnnotator Plugin..."

cd python-server
python server.py &
sleep 3
cd ..
npm start
```

---

## Component 7: Testing Plan

### Test Case 1: EDL Parsing

**Input:** Sample EDL file with various markers
**Expected:** All markers parsed correctly with types, timestamps, colors
**Verify:** Count matches, timecodes correct, event types extracted

### Test Case 2: Filtering

**Input:** 234 markers, filter "Boss" + time range 00:10:00-00:20:00
**Expected:** Only Boss events in that time range
**Verify:** Correct count, all matches criteria

### Test Case 3: Marker Import

**Input:** 8 filtered markers
**Expected:** 8 markers appear on Resolve timeline with correct colors
**Verify:** Timecodes match, colors match, descriptions correct

### Test Case 4: BPM Supercut

**Input:** 45 combat markers, 120 BPM, quarter notes
**Expected:** New timeline with 45 clips, each 0.5s, events on beats
**Verify:** Beat positions correct (0.0s, 0.5s, 1.0s...), clips centered on events

### Test Case 5: Edge Cases

- Empty EDL file
- EDL with no markers
- Video file not found
- Resolve not running
- No timeline open
- Very large EDL (1000+ markers)

---

## Component 8: Future Enhancements

### Phase 1: Core Features (MVP)
- [x] EDL parsing
- [x] Marker filtering (search, exclude, type, time range)
- [x] Import to Resolve timeline
- [x] BPM supercut generation
- [x] Basic UI

### Phase 2: Quality of Life
- [ ] Preset filters (save/load filter configurations)
- [ ] Batch processing (multiple EDL files)
- [ ] Export filtered markers as new EDL
- [ ] Video preview with marker navigation
- [ ] Keyboard shortcuts

### Phase 3: Advanced Features
- [ ] Multiple event type supercuts (e.g., Boss + Achievement)
- [ ] Variable clip durations (shorter for fast BPM)
- [ ] Audio analysis (detect music BPM automatically)
- [ ] Custom color schemes
- [ ] Marker statistics and visualizations

### Phase 4: Integration
- [ ] Auto-launch with Resolve (Workflow Integration Plugin)
- [ ] Embedded panel in Resolve UI
- [ ] Direct access from timeline context menu
- [ ] Sync with StreamUP in real-time during recording

### Phase 5: AI & Automation
- [ ] Auto-detect "exciting" moments (audio volume spikes)
- [ ] Suggest optimal BPM for footage
- [ ] Auto-generate titles and transitions
- [ ] Smart event grouping (cluster nearby events)

---

## Component 9: Technical Considerations

### Performance

**EDL Parsing:**
- 1000 markers = ~200 KB file
- Parse time: <100ms
- Memory: ~5 MB

**Marker Import:**
- Resolve API calls: ~50ms per marker
- 100 markers = ~5 seconds import time
- Acceptable for typical use

**Supercut Generation:**
- Depends on clip count and Resolve performance
- 100 clips = ~2-3 minutes generation time
- GPU acceleration helps rendering, not API calls

### Error Handling

**Common Issues:**

1. **Resolve Not Running**
   - Detection: API connection fails
   - Solution: Show error with instructions to start Resolve
   - Recovery: Retry connection button

2. **No Timeline Open**
   - Detection: GetCurrentTimeline() returns null
   - Solution: Prompt user to create/open timeline
   - Recovery: Offer to create new timeline

3. **EDL Parse Errors**
   - Detection: Malformed timecode or missing metadata
   - Solution: Show line number and error detail
   - Recovery: Skip invalid markers, continue parsing

4. **File Not Found**
   - Detection: Video or EDL file doesn't exist
   - Solution: Show file browser to locate file
   - Recovery: Remember last valid directory

5. **Framerate Mismatch**
   - Detection: EDL framerate ≠ video framerate
   - Solution: Warn user, offer to recalculate timecodes
   - Recovery: Auto-detect from video metadata

### Platform Compatibility

**Supported Platforms:**
- Windows 10/11
- macOS 12+
- Linux (Ubuntu 20.04+)

**DaVinci Resolve:**
- Studio version required (API access)
- Version 18+ (Python API stability)
- Earlier versions may have limited API support

---

## Component 10: Documentation

### User Guide Topics

1. **Quick Start**
   - Export EDL from StreamUP
   - Load files in plugin
   - Import markers

2. **Filtering Guide**
   - Text search syntax
   - Event type selection
   - Time range selection
   - Combining filters

3. **BPM Supercut Tutorial**
   - Finding song BPM
   - Choosing note division
   - Setting options
   - Editing generated timeline

4. **Troubleshooting**
   - Connection issues
   - Import failures
   - Performance optimization

### Developer Documentation

1. **Architecture Overview**
   - Component diagram
   - API reference
   - Data flow

2. **EDL Format Specification**
   - CMX 3600 standard
   - Resolve extensions
   - Parsing logic

3. **API Endpoints**
   - Request/response formats
   - Error codes
   - Examples

4. **Contributing Guide**
   - Setup development environment
   - Code style
   - Testing
   - Pull request process

---

## Summary

### What Makes This Design Work

1. **Zero Mod Changes** - Your Minecraft mod already does everything perfectly
2. **Simple Workflow** - Export EDL from StreamUP, load in plugin
3. **Native Format** - EDL is what Resolve expects, no conversion needed
4. **Optional Plugin** - Users can import EDL directly, plugin adds filtering & supercuts
5. **Clean Architecture** - Electron UI + Python API = familiar, maintainable stack

### Key Features Delivered

✅ **Marker Preview** - See all events before importing
✅ **Powerful Filtering** - Search, exclude, type, time range
✅ **Direct Import** - Python API imports to timeline
✅ **BPM Supercuts** - Auto-generate beat-synced edits
✅ **Color Coding** - Auto-assign colors by event type
✅ **Statistics** - View event distribution

### Development Effort Estimate

**Phase 1 (MVP):**
- Python backend: 2-3 days
- React frontend: 3-4 days
- Testing & debugging: 2 days
- **Total: ~7-9 days**

**Phase 2 (Polish):**
- UI improvements: 2 days
- Error handling: 1 day
- Documentation: 1 day
- **Total: ~4 days**

**Grand Total: ~2 weeks for production-ready v1.0**

---

## Next Steps

1. **Review & Approve** this design
2. **Set up development environment**
3. **Implement Python backend** (EDL parser, filters, API)
4. **Build React frontend** (UI components)
5. **Test with real recordings**
6. **Package & distribute**

Ready to start building! 🚀
