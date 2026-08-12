# DaVinci Resolve Companion Plugin - Design Document

## Overview
This document outlines the design for a comprehensive workflow system that bridges Minecraft gameplay recording with OBS annotations and DaVinci Resolve video editing, featuring automated marker import, filtering, and BPM-synchronized supercut generation.

---

## System Architecture

```
┌─────────────────┐
│   Minecraft     │
│  + ObsAnnotator │
│      Mod        │
└────────┬────────┘
         │ WebSocket
         ▼
┌─────────────────┐      ┌──────────────────┐
│   OBS Studio    │─────▶│  Annotation File │
│  + Lua Script   │      │     (JSON)       │
└─────────────────┘      └────────┬─────────┘
         │                        │
         │ Records Video          │ Saved alongside
         ▼                        │
┌─────────────────┐              │
│   Video File    │              │
│    (.mp4)       │              │
└────────┬────────┘              │
         │                        │
         └────────┬───────────────┘
                  │ Both loaded by
                  ▼
         ┌─────────────────────────┐
         │  DaVinci Resolve        │
         │  Workflow Integration   │
         │  Plugin (Electron)      │
         └─────────────────────────┘
                  │
                  ├─▶ Import & Filter Markers
                  ├─▶ Generate BPM Supercuts
                  └─▶ Create Custom Edits
```

---

## Component 1: Annotation File Format

### File Specification

**Filename Convention:**
```
{recording_name}.json
Example: 2024-01-15_Minecraft_Stream_001.json
```

**File Location:**
Same directory as the recorded video file.

### JSON Structure

```json
{
  "version": "1.0",
  "metadata": {
    "sessionId": "2024-01-15-session-001",
    "recordingStartTime": "2024-01-15T14:30:00.000Z",
    "recordingEndTime": "2024-01-15T15:32:45.250Z",
    "videoDuration": 3765.25,
    "videoFile": "2024-01-15_Minecraft_Stream_001.mp4",
    "framerate": 30,
    "timecodeFormat": "HH:MM:SS.mmm"
  },
  "markers": [
    {
      "id": 1,
      "timestamp": "00:00:15.450",
      "timestampSeconds": 15.45,
      "frame": 463,
      "type": "Combat",
      "subtype": "Entity Attacked",
      "category": "combat_entity_attacked",
      "description": "Combat - Entity Attacked",
      "color": "Red",
      "metadata": {
        "playerHealth": 18.5,
        "entityType": "zombie",
        "biome": "plains"
      }
    },
    {
      "id": 2,
      "timestamp": "00:03:22.120",
      "timestampSeconds": 202.12,
      "frame": 6063,
      "type": "Block",
      "subtype": "Block Broken",
      "category": "block_broken",
      "description": "Block - Diamond Ore Mined",
      "color": "Cyan",
      "metadata": {
        "blockType": "diamond_ore",
        "toolUsed": "iron_pickaxe",
        "position": "X:245 Y:-52 Z:1023"
      }
    },
    {
      "id": 3,
      "timestamp": "00:15:30.000",
      "timestampSeconds": 930.0,
      "frame": 27900,
      "type": "Boss",
      "subtype": "Ender Dragon Spawned",
      "category": "boss_dragon_spawned",
      "description": "Boss - Ender Dragon Spawned",
      "color": "Purple",
      "metadata": {
        "dimension": "the_end"
      }
    },
    {
      "id": 4,
      "timestamp": "00:45:12.800",
      "timestampSeconds": 2712.8,
      "frame": 81384,
      "type": "Manual",
      "subtype": "POI Marker",
      "category": "manual_poi",
      "description": "Manual - Point of Interest",
      "color": "Yellow",
      "metadata": {
        "note": "User pressed Numpad 5"
      }
    }
  ],
  "eventCategories": {
    "Combat": ["Entity Attacked", "Entity Damaged", "Entity Died", "Player Near Death", "Player Respawned"],
    "Boss": ["Ender Dragon Spawned", "Ender Dragon Defeated", "Wither Spawned", "Wither Defeated"],
    "Block": ["Block Broken", "Block Left Clicked", "Block Right Clicked"],
    "Item": ["Rare Item Obtained", "Item Used"],
    "Exploration": ["Biome Changed", "New Biome Discovered"],
    "Achievement": ["Advancement Unlocked"],
    "Explosion": ["Explosion Detected"],
    "Manual": ["Start Marker", "End Marker", "POI Marker"]
  },
  "colorScheme": {
    "Combat": "Red",
    "Boss": "Purple",
    "Block": "Cyan",
    "Item": "Green",
    "Exploration": "Blue",
    "Achievement": "Gold",
    "Explosion": "Orange",
    "Manual": "Yellow"
  }
}
```

### Field Descriptions

- **version**: Schema version for future compatibility
- **metadata.sessionId**: Unique identifier for the recording session
- **metadata.recordingStartTime**: ISO 8601 timestamp of recording start
- **metadata.framerate**: FPS of the video (detected automatically by OBS script)
- **markers[].timestamp**: Timecode in HH:MM:SS.mmm format
- **markers[].timestampSeconds**: Decimal seconds from start (for calculations)
- **markers[].frame**: Frame number (calculated from timestamp × framerate)
- **markers[].category**: Machine-readable event identifier (for filtering)
- **markers[].description**: Human-readable description
- **markers[].color**: Marker color in Resolve
- **markers[].metadata**: Event-specific data

---

## Component 2: OBS Lua Script

### Purpose
Automatically create and populate annotation files during recording by listening to WebSocket messages from the Minecraft mod.

### Script Location
```
OBS Scripts folder: %AppData%\obs-studio\scripts\ (Windows)
                    ~/.config/obs-studio/scripts/ (Linux)
```

### Script Filename
`obsannotator_export.lua`

### Functionality

#### 1. Recording Lifecycle Management
```lua
-- When recording starts:
- Detect video filename and output path
- Detect video framerate from OBS settings
- Create new JSON annotation file with matching name
- Initialize metadata (sessionId, startTime)
- Reset marker array
- Start recording start time

-- When recording stops:
- Set recording end time
- Calculate total duration
- Write complete JSON file
- Close file handle
```

#### 2. WebSocket Message Handling
```lua
-- Connect to OBS WebSocket (port 4455 by default)
-- Listen for messages from StreamUP plugin
-- Parse incoming annotation messages
-- Format: "EventType - EventSubtype"

-- Extract:
- Current recording timestamp (from OBS API)
- Event type and subtype
- Convert to proper JSON marker entry

-- Append to markers array in memory
```

#### 3. Settings Panel
```lua
OBS Settings → Scripts → ObsAnnotator Export

[x] Enable Annotation Export
Output Directory: [Browse...] (default: same as recording)
WebSocket Port: [4455]
Annotation Format: [JSON v1.0]
[x] Also create EDL file (for compatibility)
[x] Include frame numbers
[x] Include extended metadata

[Test Connection]  [Save Settings]
```

#### 4. Real-time File Writing
```lua
-- Option A: Buffered writing
- Store markers in memory
- Write to file when recording stops
- Risk: Lose data if OBS crashes

-- Option B: Append mode (RECOMMENDED)
- Open file in append mode
- Write each marker immediately when received
- Add proper JSON formatting
- Risk-free, survives crashes
```

### Implementation Notes

**OBS Lua API calls needed:**
- `obs.obs_frontend_get_current_record_output()` - Get recording output
- `obs.obs_output_get_video_encoder()` - Get encoder settings (framerate)
- `obs.obs_frontend_get_recording_output()` - Get recording file path
- `obs.obs_frontend_recording_start()` / `stop()` - Hook recording events
- WebSocket client library (may need external lib like `lua-websocket`)

**Challenge:** OBS Lua may not have built-in WebSocket client. Solutions:
1. Use OBS WebSocket plugin's internal messaging (if accessible from Lua)
2. Monitor StreamUP's output log file instead
3. Have Minecraft mod write directly to a temp file that Lua script reads
4. Use a small Python helper script (OBS supports Python scripts better)

**RECOMMENDATION:** Use **Python script** instead of Lua for better WebSocket support.

---

## Component 3: Enhanced Minecraft Mod Export

### Modified `ObsAnnotatorClient.java`

Add a secondary export mechanism that writes directly to a JSON file alongside the WebSocket connection.

```java
public class AnnotationFileWriter {
    private File annotationFile;
    private BufferedWriter writer;
    private int markerId = 0;
    private long recordingStartTimeMs;

    public void startRecording(String outputDir, String videoFilename) {
        // Create annotation file: videoFilename.json
        String jsonFilename = videoFilename.replaceAll("\\.mp4$", ".json");
        annotationFile = new File(outputDir, jsonFilename);

        // Initialize JSON structure
        recordingStartTimeMs = System.currentTimeMillis();
        writeHeader();
    }

    public void writeMarker(EventType type, String subtype, Map<String, Object> metadata) {
        long currentTimeMs = System.currentTimeMillis();
        double timestampSeconds = (currentTimeMs - recordingStartTimeMs) / 1000.0;

        // Calculate timecode: HH:MM:SS.mmm
        String timecode = formatTimecode(timestampSeconds);

        // Calculate frame number (assume 30fps, read from config)
        int frameNumber = (int)(timestampSeconds * config.framerate);

        // Write marker JSON entry
        writeMarkerJson(markerId++, timecode, timestampSeconds, frameNumber,
                       type, subtype, metadata);
    }

    public void stopRecording() {
        // Write footer and close file
        writeFooter();
        writer.close();
    }
}
```

### Integration Points

Modify `EventTracker.java` to also call `AnnotationFileWriter.writeMarker()` whenever sending WebSocket message:

```java
public void trackEvent(String eventType, String eventSubtype, Map<String, Object> metadata) {
    // Existing WebSocket send
    obsClient.sendMarker(eventType, eventSubtype);

    // NEW: Also write to file
    if (config.enableFileExport) {
        annotationWriter.writeMarker(eventType, eventSubtype, metadata);
    }
}
```

### Configuration Addition

Add to `ObsAnnotatorConfig.java`:
```java
@ConfigEntry.Category("export")
@ConfigEntry.Gui.Tooltip
public boolean enableFileExport = true;

@ConfigEntry.Category("export")
public String exportDirectory = ""; // Default: use OBS recording dir

@ConfigEntry.Category("export")
public int framerate = 30; // Should match OBS setting
```

### User Workflow

1. User sets OBS recording directory in mod config (or auto-detect)
2. Start Minecraft and begin playing
3. Start OBS recording (video: `my_stream.mp4`)
4. Mod automatically creates `my_stream.json` in same directory
5. Events are written to both WebSocket (for live StreamUP) AND JSON file
6. Stop recording → JSON file is complete and ready for Resolve

---

## Component 4: DaVinci Resolve Workflow Integration Plugin

### Technology Stack

- **Frontend:** Electron + React + TypeScript
- **Styling:** CSS (or Tailwind/Material-UI)
- **Backend API Bridge:** Node.js talking to Resolve Python API via RPC
- **Data Handling:** JSON parsing, time calculations

### Architecture

```
┌─────────────────────────────────────┐
│   Electron App (UI)                 │
│   ┌─────────────────────────────┐  │
│   │  React Components           │  │
│   │  - File Browser             │  │
│   │  - Marker List & Filters    │  │
│   │  - BPM Supercut Controls    │  │
│   └──────────┬──────────────────┘  │
│              │                      │
│   ┌──────────▼──────────────────┐  │
│   │  Electron IPC Bridge        │  │
│   └──────────┬──────────────────┘  │
└──────────────┼──────────────────────┘
               │
               │ HTTP/WebSocket
               ▼
┌─────────────────────────────────────┐
│   Python API Server                 │
│   ┌─────────────────────────────┐  │
│   │  Flask/FastAPI Server       │  │
│   │  - /import_markers          │  │
│   │  - /generate_supercut       │  │
│   │  - /get_timeline_info       │  │
│   └──────────┬──────────────────┘  │
│              │                      │
│   ┌──────────▼──────────────────┐  │
│   │  DaVinci Resolve Python API │  │
│   │  - Timeline manipulation    │  │
│   │  - Marker creation          │  │
│   │  - Clip editing             │  │
│   └─────────────────────────────┘  │
└─────────────────────────────────────┘
```

### Plugin File Structure

```
resolve-obsannotator-plugin/
├── package.json
├── electron-main.js              # Electron entry point
├── src/
│   ├── ui/
│   │   ├── App.tsx              # Main React app
│   │   ├── components/
│   │   │   ├── FileBrowser.tsx  # Video + annotation file selector
│   │   │   ├── MarkerList.tsx   # Filterable marker list
│   │   │   ├── FilterPanel.tsx  # Search & filter controls
│   │   │   ├── SupercutPanel.tsx # BPM supercut generator
│   │   │   └── TimelineView.tsx # Visual timeline preview
│   │   └── styles/
│   ├── api/
│   │   ├── ipc-bridge.ts        # Electron IPC handlers
│   │   └── resolve-api.ts       # API call wrappers
│   └── utils/
│       ├── timecode.ts          # Timecode conversion utilities
│       ├── beat-calculator.ts   # BPM beat grid calculations
│       └── marker-parser.ts     # JSON annotation parser
├── python-server/
│   ├── resolve_server.py        # Python API server
│   ├── marker_importer.py       # Marker import logic
│   ├── supercut_generator.py   # Supercut generation logic
│   └── requirements.txt
└── manifest.json                # Workflow Integration manifest
```

### GUI Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  ObsAnnotator - DaVinci Resolve Companion            [_][□][×]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📁 Files                                                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Video File:   [/path/to/my_stream.mp4          ] [Browse] │ │
│  │ Annotations:  [/path/to/my_stream.json         ] [Browse] │ │
│  │ Framerate:    [30 fps] (auto-detected)                    │ │
│  │ Duration:     [01:02:45]                                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  🔍 Filter Markers                                               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Search:   [________________] (e.g., "dragon", "diamond")  │ │
│  │ Exclude:  [________________] (e.g., "manual")             │ │
│  │                                                            │ │
│  │ Time Range: [00:00:00] ━━●━━━━━━━━━━━━━━━━━ [01:02:45]   │ │
│  │             └─ Start           End ─┘                     │ │
│  │                                                            │ │
│  │ Event Types: (234 total markers, 89 visible)              │ │
│  │ ☑ Combat (45)        ☑ Boss (8)        ☑ Block (120)     │ │
│  │ ☑ Item (12)          ☑ Exploration (5) ☑ Achievement (3) │ │
│  │ ☐ Explosion (25)     ☐ Manual (16)                       │ │
│  │                                                            │ │
│  │ [Clear Filters] [Select All] [Select None]               │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  📋 Markers (89 visible)                    [Import to Timeline]│
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Time      │ Type        │ Description                      │ │
│  ├───────────┼─────────────┼─────────────────────────────────-┤ │
│  │ 00:00:15  │ Combat      │ Entity Attacked                  │ │
│  │ 00:03:22  │ Block       │ Diamond Ore Mined                │ │
│  │ 00:15:30  │ Boss        │ Ender Dragon Spawned             │ │
│  │ 00:18:45  │ Boss        │ Ender Dragon Defeated            │ │
│  │ 00:22:10  │ Achievement │ Advancement: Free the End        │ │
│  │ ...       │ ...         │ ...                              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  🎵 BPM Supercut Generator                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Song BPM:        [120]                                     │ │
│  │ Note Division:   ( ) Whole  (●) 1/2  ( ) 1/4  ( ) 1/8     │ │
│  │ Clip Duration:   [2.00] seconds (calculated)              │ │
│  │                                                            │ │
│  │ Event Filter: Use current filter above                    │ │
│  │ Markers to use: 89 events                                 │ │
│  │ Estimated length: [02:58] (89 clips × 2.0s)              │ │
│  │                                                            │ │
│  │ Advanced Options ▼                                         │ │
│  │ ☑ Add crossfade transitions (0.2s)                        │ │
│  │ ☑ Sort clips chronologically                              │ │
│  │ ☐ Randomize clip order                                    │ │
│  │ ☑ Skip duplicate events within 3 seconds                  │ │
│  │                                                            │ │
│  │ Output Timeline: [BPM_Supercut_2024-01-15]               │ │
│  │                                                            │ │
│  │            [Generate Supercut]                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Status: Ready                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Component 5: BPM Supercut Algorithm

### Mathematical Foundation

**Given:**
- BPM (beats per minute): e.g., 120
- Note division: e.g., 1/4 notes
- Marker timestamps: array of seconds

**Calculations:**

```javascript
// 1. Calculate beat interval (seconds per beat)
const beatInterval = 60 / bpm;  // 120 BPM = 0.5s per beat

// 2. Calculate clip duration based on note division
const noteDivisions = {
  whole: 1,
  half: 2,
  quarter: 4,
  eighth: 8
};
const clipDuration = (60 / bpm) * (4 / noteDivisions[noteType]);
// For 1/4 notes at 120 BPM: (60/120) * (4/4) = 0.5s

// 3. Calculate beat grid (positions where clips should land)
const beatGrid = [];
for (let i = 0; i < targetDuration; i += beatInterval) {
  beatGrid.push(i);
}
// Results in: [0, 0.5, 1.0, 1.5, 2.0, ...] for 120 BPM
```

### Algorithm Pseudocode

```python
def generate_bpm_supercut(markers, bpm, note_division, options):
    """
    Generate a beat-synchronized supercut from filtered markers.

    Args:
        markers: List of marker objects with timestamps
        bpm: Beats per minute (e.g., 120)
        note_division: 'whole', 'half', 'quarter', 'eighth'
        options: Dict with additional settings (crossfade, sort, etc.)

    Returns:
        Timeline object with generated supercut
    """

    # 1. Calculate timing parameters
    beat_interval = 60.0 / bpm
    clip_duration = calculate_clip_duration(bpm, note_division)
    half_duration = clip_duration / 2.0

    # 2. Prepare markers
    if options['sort_chronologically']:
        markers = sorted(markers, key=lambda m: m.timestamp_seconds)
    elif options['randomize']:
        random.shuffle(markers)

    # 3. Remove duplicates (if enabled)
    if options['skip_duplicates_within_seconds']:
        markers = remove_nearby_duplicates(markers,
                                          options['skip_duplicates_within_seconds'])

    # 4. Create new timeline
    timeline = resolve.create_new_timeline(options['output_timeline_name'])
    video_track = timeline.get_video_track(1)

    # 5. Load source media
    source_clip = resolve.import_media(options['video_file'])

    # 6. Generate beat grid
    beat_position = 0  # Current position on output timeline

    for marker in markers:
        # a) Calculate source clip boundaries
        # Event should land on beat, so:
        # Extract from [marker - half_duration] to [marker + half_duration]
        source_start = marker.timestamp_seconds - half_duration
        source_end = marker.timestamp_seconds + half_duration

        # b) Handle edge cases
        if source_start < 0:
            source_start = 0
            source_end = clip_duration
        if source_end > source_clip.duration:
            source_end = source_clip.duration
            source_start = source_end - clip_duration

        # c) Extract clip
        clip = extract_subclip(source_clip, source_start, source_end)

        # d) Calculate where event lands in extracted clip
        event_position_in_clip = marker.timestamp_seconds - source_start

        # e) Place clip on timeline such that event lands on beat
        # Beat is at beat_position, event is at event_position_in_clip
        # So clip starts at: beat_position - event_position_in_clip
        timeline_start = beat_position - event_position_in_clip

        # f) Add clip to timeline
        video_track.add_clip(clip, timeline_start)

        # g) Add marker at beat position (for reference)
        timeline.add_marker(beat_position, marker.description, marker.color)

        # h) Move to next beat
        beat_position += beat_interval

    # 7. Add crossfade transitions (if enabled)
    if options['add_crossfades']:
        add_crossfade_transitions(timeline, options['crossfade_duration'])

    # 8. Return timeline
    return timeline


def calculate_clip_duration(bpm, note_division):
    """
    Calculate clip duration based on BPM and note division.

    Examples:
        120 BPM, quarter note = 0.5s
        120 BPM, eighth note = 0.25s
        140 BPM, half note = 0.857s
    """
    note_multipliers = {
        'whole': 4.0,
        'half': 2.0,
        'quarter': 1.0,
        'eighth': 0.5
    }
    beat_duration = 60.0 / bpm
    return beat_duration * note_multipliers[note_division]


def remove_nearby_duplicates(markers, threshold_seconds):
    """
    Remove markers that are within threshold_seconds of each other.
    Keeps the first occurrence.
    """
    filtered = []
    last_timestamp = -999

    for marker in markers:
        if marker.timestamp_seconds - last_timestamp >= threshold_seconds:
            filtered.append(marker)
            last_timestamp = marker.timestamp_seconds

    return filtered


def extract_subclip(source_clip, start_seconds, end_seconds):
    """
    Extract a subclip from source media.
    Uses DaVinci Resolve API.
    """
    clip = source_clip.copy()
    clip.set_clip_property("Start", seconds_to_frames(start_seconds))
    clip.set_clip_property("End", seconds_to_frames(end_seconds))
    return clip


def add_crossfade_transitions(timeline, duration_seconds):
    """
    Add crossfade transitions between all clips on timeline.
    """
    clips = timeline.get_video_track(1).get_clips()

    for i in range(len(clips) - 1):
        current_clip = clips[i]
        next_clip = clips[i + 1]

        # Calculate overlap duration
        overlap = min(duration_seconds, current_clip.duration / 2,
                     next_clip.duration / 2)

        # Shift next clip to overlap
        next_clip.move_by(-overlap)

        # Add crossfade transition
        timeline.add_transition("Cross Dissolve",
                               current_clip.get_end_frame(),
                               seconds_to_frames(overlap))
```

### Timing Diagram

```
Example: 120 BPM, 1/4 notes (0.5s clips)

Source Timeline (original video):
0────────15.45s───────│──────30.2s────────│──────52.8s────────
                    Event 1           Event 2           Event 3
                    (marker)          (marker)          (marker)

Extract clips (0.25s before + 0.25s after each event):
Clip 1: [15.20s ─── 15.45s ─── 15.70s]  (0.5s total)
Clip 2: [29.95s ─── 30.20s ─── 30.45s]
Clip 3: [52.55s ─── 52.80s ─── 53.05s]

Output Timeline (supercut):
Beat:     0.0s        0.5s        1.0s        1.5s
          │           │           │           │
          ├───────────┤───────────┤───────────┤
          │  Clip 1   │  Clip 2   │  Clip 3   │
          │     ▲     │     ▲     │     ▲     │
          └─────┼─────┴─────┼─────┴─────┼─────
          Event lands    Event lands Event lands
          on beat       on beat      on beat
          (at 0.0s)     (at 0.5s)    (at 1.0s)

With crossfade (0.2s):
          │  Clip 1   │
          │         ╱─┼───────┤
          │       ╱   │ Clip 2│
          │     ╱     │     ╱─┼───────┤
          │   ╱       │   ╱   │ Clip 3│
          ├─╱─────────┼─╱─────┼───────┤
          0.0s        0.3s    0.8s    1.3s
          (Clips overlap by 0.2s each)
```

---

## Component 6: DaVinci Resolve Python API Bridge

### API Server Structure

**File:** `python-server/resolve_server.py`

```python
from flask import Flask, request, jsonify
import DaVinciResolveScript as dvr_script
import json

app = Flask(__name__)

# Initialize Resolve API
resolve = dvr_script.scriptapp("Resolve")
project_manager = resolve.GetProjectManager()
project = project_manager.GetCurrentProject()

@app.route('/api/timeline/current', methods=['GET'])
def get_current_timeline():
    """Get information about the currently open timeline."""
    timeline = project.GetCurrentTimeline()
    if not timeline:
        return jsonify({"error": "No timeline open"}), 404

    return jsonify({
        "name": timeline.GetName(),
        "framerate": timeline.GetSetting("timelineFrameRate"),
        "duration": timeline.GetEndFrame(),
        "videoTracks": timeline.GetTrackCount("video"),
        "audioTracks": timeline.GetTrackCount("audio")
    })


@app.route('/api/markers/import', methods=['POST'])
def import_markers():
    """Import markers from annotation JSON file."""
    data = request.json
    annotation_file = data['annotationFile']
    filters = data.get('filters', {})

    # Parse annotation file
    with open(annotation_file, 'r') as f:
        annotations = json.load(f)

    # Filter markers
    markers_to_import = filter_markers(annotations['markers'], filters)

    # Get current timeline
    timeline = project.GetCurrentTimeline()
    if not timeline:
        return jsonify({"error": "No timeline open"}), 404

    # Import markers
    imported_count = 0
    for marker in markers_to_import:
        frame = marker['frame']
        name = marker['description']
        color = marker['color']
        note = f"{marker['type']} - {marker['subtype']}"

        success = timeline.AddMarker(
            frameId=frame,
            color=color,
            name=name,
            note=note,
            duration=1
        )

        if success:
            imported_count += 1

    return jsonify({
        "success": True,
        "imported": imported_count,
        "total": len(markers_to_import)
    })


@app.route('/api/supercut/generate', methods=['POST'])
def generate_supercut():
    """Generate BPM-synchronized supercut."""
    data = request.json

    video_file = data['videoFile']
    annotation_file = data['annotationFile']
    bpm = data['bpm']
    note_division = data['noteDivision']
    filters = data.get('filters', {})
    options = data.get('options', {})

    # Import supercut generator
    from supercut_generator import SupercutGenerator

    generator = SupercutGenerator(resolve, project)
    result = generator.generate(
        video_file=video_file,
        annotation_file=annotation_file,
        bpm=bpm,
        note_division=note_division,
        filters=filters,
        options=options
    )

    return jsonify(result)


@app.route('/api/media/import', methods=['POST'])
def import_media():
    """Import media file into current project."""
    data = request.json
    file_path = data['filePath']

    media_pool = project.GetMediaPool()
    root_folder = media_pool.GetRootFolder()

    success = media_pool.ImportMedia([file_path])

    return jsonify({"success": bool(success)})


def filter_markers(markers, filters):
    """Apply filters to marker list."""
    filtered = markers

    # Text search
    if 'search' in filters and filters['search']:
        search_term = filters['search'].lower()
        filtered = [m for m in filtered
                   if search_term in m['description'].lower()
                   or search_term in m['type'].lower()]

    # Exclude text
    if 'exclude' in filters and filters['exclude']:
        exclude_term = filters['exclude'].lower()
        filtered = [m for m in filtered
                   if exclude_term not in m['description'].lower()
                   and exclude_term not in m['type'].lower()]

    # Time range
    if 'timeRangeStart' in filters:
        filtered = [m for m in filtered
                   if m['timestampSeconds'] >= filters['timeRangeStart']]

    if 'timeRangeEnd' in filters:
        filtered = [m for m in filtered
                   if m['timestampSeconds'] <= filters['timeRangeEnd']]

    # Event types
    if 'eventTypes' in filters and filters['eventTypes']:
        allowed_types = set(filters['eventTypes'])
        filtered = [m for m in filtered if m['type'] in allowed_types]

    return filtered


if __name__ == '__main__':
    # Run server on localhost
    app.run(host='127.0.0.1', port=8765)
```

### Supercut Generator Module

**File:** `python-server/supercut_generator.py`

```python
import json
import random
from typing import List, Dict, Any

class SupercutGenerator:
    def __init__(self, resolve, project):
        self.resolve = resolve
        self.project = project
        self.media_pool = project.GetMediaPool()

    def generate(self, video_file: str, annotation_file: str,
                bpm: int, note_division: str,
                filters: Dict, options: Dict) -> Dict[str, Any]:
        """
        Main supercut generation function.
        """

        # 1. Load and parse annotations
        with open(annotation_file, 'r') as f:
            annotations = json.load(f)

        framerate = annotations['metadata']['framerate']
        markers = self._filter_markers(annotations['markers'], filters)

        if not markers:
            return {"success": False, "error": "No markers match filters"}

        # 2. Calculate timing parameters
        beat_interval = 60.0 / bpm
        clip_duration = self._calculate_clip_duration(bpm, note_division)
        half_duration = clip_duration / 2.0

        # 3. Prepare markers
        if options.get('sort_chronologically', True):
            markers = sorted(markers, key=lambda m: m['timestampSeconds'])
        elif options.get('randomize', False):
            random.shuffle(markers)

        if options.get('skip_duplicates_within_seconds'):
            markers = self._remove_nearby_duplicates(
                markers,
                options['skip_duplicates_within_seconds']
            )

        # 4. Import source video
        media_item = self._import_media(video_file)
        if not media_item:
            return {"success": False, "error": "Failed to import video"}

        # 5. Create new timeline
        timeline_name = options.get('output_timeline_name',
                                    f"BPM_Supercut_{bpm}")
        timeline = self.media_pool.CreateEmptyTimeline(timeline_name)

        if not timeline:
            return {"success": False, "error": "Failed to create timeline"}

        # 6. Generate clips
        beat_position = 0
        clips_added = 0

        for marker in markers:
            # Calculate source clip boundaries
            source_start_sec = marker['timestampSeconds'] - half_duration
            source_end_sec = marker['timestampSeconds'] + half_duration

            # Convert to frames
            source_start_frame = self._seconds_to_frames(source_start_sec, framerate)
            source_end_frame = self._seconds_to_frames(source_end_sec, framerate)

            # Handle edge cases
            if source_start_frame < 0:
                source_start_frame = 0
                source_end_frame = self._seconds_to_frames(clip_duration, framerate)

            # Add clip to timeline
            # Note: Resolve API uses different methods depending on version
            success = timeline.AppendToTimeline([{
                "mediaPoolItem": media_item,
                "startFrame": source_start_frame,
                "endFrame": source_end_frame,
                "trackIndex": 1,
                "recordFrame": self._seconds_to_frames(beat_position, framerate)
            }])

            if success:
                clips_added += 1

                # Add marker at beat position
                beat_frame = self._seconds_to_frames(beat_position, framerate)
                timeline.AddMarker(
                    frameId=beat_frame,
                    color=marker['color'],
                    name=marker['description'],
                    note=f"Beat {clips_added}",
                    duration=1
                )

            beat_position += beat_interval

        # 7. Add crossfades (if enabled)
        if options.get('add_crossfades', False):
            self._add_crossfades(timeline,
                               options.get('crossfade_duration', 0.2),
                               framerate)

        return {
            "success": True,
            "timeline_name": timeline_name,
            "clips_added": clips_added,
            "duration_seconds": beat_position,
            "markers_used": len(markers)
        }

    def _calculate_clip_duration(self, bpm: int, note_division: str) -> float:
        """Calculate clip duration based on BPM and note division."""
        note_multipliers = {
            'whole': 4.0,
            'half': 2.0,
            'quarter': 1.0,
            'eighth': 0.5
        }
        beat_duration = 60.0 / bpm
        return beat_duration * note_multipliers[note_division]

    def _seconds_to_frames(self, seconds: float, framerate: int) -> int:
        """Convert seconds to frame number."""
        return int(seconds * framerate)

    def _filter_markers(self, markers: List[Dict], filters: Dict) -> List[Dict]:
        """Apply filters to markers (same logic as API server)."""
        # ... (same filtering logic as in resolve_server.py)
        pass

    def _remove_nearby_duplicates(self, markers: List[Dict],
                                  threshold: float) -> List[Dict]:
        """Remove markers within threshold seconds of each other."""
        filtered = []
        last_timestamp = -999

        for marker in markers:
            if marker['timestampSeconds'] - last_timestamp >= threshold:
                filtered.append(marker)
                last_timestamp = marker['timestampSeconds']

        return filtered

    def _import_media(self, file_path: str):
        """Import media file and return media pool item."""
        root_folder = self.media_pool.GetRootFolder()
        items = self.media_pool.ImportMedia([file_path])
        return items[0] if items else None

    def _add_crossfades(self, timeline, duration_seconds: float,
                       framerate: int):
        """Add crossfade transitions between clips."""
        # Get all clips on video track 1
        track_count = timeline.GetTrackCount("video")
        if track_count < 1:
            return

        clips = timeline.GetItemListInTrack("video", 1)

        for i in range(len(clips) - 1):
            # Add transition between clip i and i+1
            transition_frames = int(duration_seconds * framerate)
            timeline.AddTransition(
                transitionType="Cross Dissolve",
                trackIndex=1,
                clipIndex=i,
                duration=transition_frames
            )
```

---

## Component 7: Installation & Setup

### Prerequisites

**For OBS Script:**
- OBS Studio (latest version)
- Python 3.10+ (for OBS Python scripting)
- StreamUP Chapter Marker Manager plugin (already in use)

**For Minecraft Mod:**
- Java 17+
- Fabric Loader
- Existing ObsAnnotator mod installed

**For DaVinci Resolve Plugin:**
- DaVinci Resolve Studio (18+) - **Studio version required for scripting API**
- Node.js 18+
- Python 3.10+
- pip packages: `flask`, `DaVinciResolveScript`

### Installation Steps

#### 1. OBS Script Setup

```bash
# Windows
1. Copy obsannotator_export.py to:
   %AppData%\obs-studio\scripts\

2. Open OBS → Tools → Scripts
3. Click [+] and select obsannotator_export.py
4. Configure settings:
   - Enable: ✓
   - Output Directory: (same as recordings, or custom)
   - WebSocket Port: 4455
5. Click [Refresh Scripts]

# Linux/Mac
1. Copy to ~/.config/obs-studio/scripts/
2. Follow same OBS steps
```

#### 2. Minecraft Mod Configuration

```bash
# In-game, press the mod config key (default: K)
# Or edit: .minecraft/config/obsannotator.json

{
  "enableFileExport": true,
  "exportDirectory": "C:/Users/YourName/Videos/OBS",  # Match OBS output
  "framerate": 30,  # Match OBS recording framerate
  "enableWebSocket": true,
  "websocketHost": "localhost",
  "websocketPort": 4455
}
```

#### 3. DaVinci Resolve Plugin Installation

```bash
# 1. Install Python dependencies
cd resolve-obsannotator-plugin/python-server
pip install -r requirements.txt

# 2. Install Node.js dependencies
cd ../
npm install

# 3. Build Electron app
npm run build

# 4. Copy plugin to Resolve Workflow Integration directory
# Windows:
copy dist/ "C:\ProgramData\Blackmagic Design\DaVinci Resolve\Workflow Integration Plugins\ObsAnnotator\"

# Mac:
cp -r dist/ "/Library/Application Support/Blackmagic Design/DaVinci Resolve/Workflow Integration Plugins/ObsAnnotator/"

# Linux:
cp -r dist/ "/opt/resolve/Workflow Integration Plugins/ObsAnnotator/"

# 5. Start Python API server
python python-server/resolve_server.py
# Server will run on http://localhost:8765
```

#### 4. DaVinci Resolve Configuration

```
1. Open DaVinci Resolve
2. Go to: Workspace → Workflow Integrations
3. Enable "ObsAnnotator" plugin
4. Plugin panel should appear on right side
5. Test connection (plugin will auto-connect to localhost:8765)
```

### First-Time Workflow

```
1. Start Minecraft with ObsAnnotator mod
2. Start OBS Studio
3. Press "Start Recording" in OBS
4. Play Minecraft (events are tracked and written to JSON)
5. Press "Stop Recording" in OBS
6. Files created:
   - my_stream.mp4 (video)
   - my_stream.json (annotations)
7. Open DaVinci Resolve
8. Open ObsAnnotator plugin panel
9. Browse to my_stream.mp4 and my_stream.json
10. Filter markers as desired
11. Click "Import to Timeline" or "Generate Supercut"
```

---

## Component 8: Future Extension Ideas

### Additional Supercut Types

**1. "Best Moments" Montage**
- Filter by high-value events (boss fights, achievements, near-death)
- No BPM sync, just chronological compilation
- Add title cards between segments

**2. "Progression Timeline"**
- Show key milestones in order
- Add automatic captions with achievement names
- Slow motion on boss defeats

**3. "Chaos Compilation"**
- Filter for high-intensity events (explosions, combat, deaths)
- Fast cuts, no beat sync
- Add sound effects

**4. "Tutorial Builder"**
- Select specific event sequences (e.g., all diamond mining)
- Add text overlays explaining technique
- Slow down important moments

**5. "Highlight Reel"**
- Manually mark "star" events during gameplay
- Automatic best-of compilation
- Add intro/outro templates

### Enhanced Features

**Metadata-Based Filtering:**
- Filter by player health (near-death moments)
- Filter by biome (all Nether content)
- Filter by entity type (zombie kills vs skeleton kills)

**AI Integration:**
- Auto-detect "exciting" moments using audio analysis
- Face/emotion detection from webcam overlay
- Speech-to-text for commentary markers

**Multi-Stream Support:**
- Sync annotations from multiple perspectives (multiplayer)
- Generate split-screen comparisons
- Auto-switch between player perspectives

**Color Grading Automation:**
- Apply different grades based on event type
- Biome-based color palettes (Nether = red, End = purple)
- Mood-based grading (combat = desaturated, achievements = vibrant)

**Music Integration:**
- Auto-select music based on video pacing
- Detect existing music and sync cuts
- Generate beat markers from imported audio

---

## Technical Specifications Summary

### File Formats

| Component | Format | Location |
|-----------|--------|----------|
| Video | MP4 (H.264) | User-specified OBS output dir |
| Annotations | JSON | Same directory as video |
| Timeline | Resolve native | Project database |

### Performance Considerations

**Annotation File Size:**
- Approx. 200 bytes per marker
- 1-hour stream with 500 events = ~100 KB
- Negligible performance impact

**Supercut Generation Time:**
- Depends on clip count and Resolve hardware
- Estimate: ~1 second per clip (API overhead)
- 100 clips = ~2 minutes generation time
- GPU acceleration helps rendering, not API calls

**Memory Usage:**
- Electron app: ~200 MB
- Python server: ~50 MB
- Resolve: ~4 GB (normal operation)
- Total overhead: <300 MB

### Error Handling

**Common Issues:**

1. **Mismatched Framerate**
   - Detection: Compare annotation framerate vs video file
   - Solution: Ask user to confirm correct framerate
   - Fallback: Auto-detect from video file

2. **Missing Files**
   - Detection: Check file existence before operations
   - Solution: Show clear error message with path
   - Prevention: Auto-scan for matching JSON when video selected

3. **Timeline Not Open**
   - Detection: API returns null timeline
   - Solution: Prompt user to create/open timeline
   - Auto-fix: Offer to create new timeline

4. **API Server Disconnected**
   - Detection: HTTP request timeout
   - Solution: Show connection status indicator
   - Auto-fix: Restart server automatically

5. **Timestamp Drift**
   - Detection: Marker timestamp exceeds video duration
   - Solution: Warn user about potential recording restart
   - Workaround: Trim markers to video duration

---

## Development Roadmap

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] Design and implement annotation JSON schema
- [ ] Create OBS Python script for file export
- [ ] Modify Minecraft mod to write JSON files
- [ ] Test end-to-end annotation capture

### Phase 2: Basic Resolve Integration (Week 3-4)
- [ ] Set up Python API server
- [ ] Implement marker import functionality
- [ ] Create basic Electron app shell
- [ ] Build file browser and marker list UI

### Phase 3: Filtering System (Week 5)
- [ ] Implement text search/exclude filters
- [ ] Add time range slider
- [ ] Create event type checkboxes
- [ ] Test filter performance with large datasets

### Phase 4: BPM Supercut Generator (Week 6-7)
- [ ] Implement beat calculation algorithm
- [ ] Create supercut generation logic
- [ ] Build BPM UI panel
- [ ] Test with various BPM/note division combinations

### Phase 5: Polish & Testing (Week 8)
- [ ] Add error handling and validation
- [ ] Create installation documentation
- [ ] Record tutorial video
- [ ] Beta test with real streams

### Phase 6: Future Enhancements (Ongoing)
- [ ] Add additional supercut types
- [ ] Implement advanced metadata filtering
- [ ] Create preset system
- [ ] Add export templates

---

## Questions for Implementation

Before starting development, please clarify:

### 1. OBS Integration Approach

**Option A:** Python script that monitors WebSocket → Better WebSocket support
**Option B:** Lua script for native OBS integration → No external dependencies
**Option C:** Minecraft mod writes directly to file → Simplest, no OBS script needed

**Recommendation:** Option C initially, add OBS script later for validation

### 2. Resolve Plugin Distribution

**Question:** How should users install the plugin?
**Option A:** Manual copy to Workflow Integration folder
**Option B:** Installer executable
**Option C:** Resolve script that auto-installs

**Recommendation:** Option A for initial version

### 3. Python API Server

**Question:** Should it auto-start with Resolve or manual start?
**Option A:** Electron app starts Python server automatically
**Option B:** User starts server manually before opening Resolve

**Recommendation:** Option A for better UX

### 4. Metadata Expansion

**Question:** What additional metadata should we capture?
Current: playerHealth, entityType, biome, blockType, position

Potential additions:
- Player inventory state
- Game difficulty
- Time of day (in-game)
- Weather conditions
- Nearby players (multiplayer)

**Recommendation:** Start minimal, add based on user feedback

---

## Conclusion

This design provides a complete workflow from Minecraft gameplay to polished video edits in DaVinci Resolve. The key innovations are:

1. **Automatic annotation capture** alongside video recording
2. **Powerful filtering system** to find relevant moments
3. **Beat-synchronized supercut generation** for music video creation
4. **Extensible architecture** for future enhancement

The system respects professional video editing workflows while adding gaming-specific automation. All components are designed to work together seamlessly while remaining modular for independent improvements.

Next step: Review this document, answer clarifying questions, then begin Phase 1 implementation.
