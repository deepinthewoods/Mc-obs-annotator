# DaVinci Resolve Companion Plugin - Design Document (Revised)

## Overview
This document outlines the design for a DaVinci Resolve companion system that works with your **existing** Minecraft ObsAnnotator mod and OBS StreamUP Chapter Marker Manager to enable powerful video editing workflows including automated marker import, filtering, and BPM-synchronized supercut generation.

---

## Current Architecture Understanding

### What You Already Have

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
│   + StreamUP    │  - Receives annotations via vendor request
│   Chapter       │  - Creates chapter markers during recording
│   Manager       │  - Stores markers in memory
└────────┬────────┘
         │ Records video
         ▼
┌─────────────────┐      ┌──────────────────┐
│   Video File    │      │  StreamUP Export │
│    (.mp4)       │      │  (Text/XML)      │
└─────────────────┘      └──────────────────┘
                          (Manual export after recording)
```

### What Works Now
✅ Minecraft mod connects to OBS WebSocket
✅ Events are sent in real-time to StreamUP
✅ StreamUP creates chapter markers during recording
✅ StreamUP can export markers to text/XML after recording
✅ Config file supports event toggles and cooldowns

---

## What We Need to Add

### New Architecture

```
┌─────────────────┐
│   Minecraft     │
│  ObsAnnotator   │
│      Mod        │
└────────┬────┬───┘
         │    │
         │    └──────────────┐
         │ WebSocket         │ NEW: Write EDL file directly
         ▼                   ▼
┌─────────────────┐    ┌──────────────────┐
│   OBS Studio    │    │  Annotation File │
│   + StreamUP    │    │    (EDL Format)  │
└────────┬────────┘    └────────┬─────────┘
         │                      │
         │ Records Video        │ Saved alongside
         ▼                      │
┌─────────────────┐            │
│   Video File    │            │
│    (.mp4)       │            │
└────────┬────────┘            │
         │                      │
         └────────┬─────────────┘
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

### Key Changes

1. **Minecraft Mod Enhancement:** Add EDL file writing alongside WebSocket sending
2. **No OBS Script Needed:** Your mod already communicates with StreamUP perfectly
3. **EDL Format:** Use DaVinci Resolve's native Timeline Markers EDL format
4. **DaVinci Plugin:** Same as before - Electron app for filtering and supercut generation

---

## Component 1: EDL File Format (DaVinci Resolve Native)

### File Specification

**Filename Convention:**
```
{recording_name}.edl
Example: 2024-01-15_Minecraft_Stream.edl
```

**File Location:** Same directory as the recorded video file

### EDL Format Structure

DaVinci Resolve uses CMX3600 EDL format with marker extensions:

```edl
TITLE: Minecraft Stream 2024-01-15
FCM: NON-DROP FRAME

001 001 V C 00:00:15:13 00:00:15:14 00:00:15:13 00:00:15:14
|C:ResolveColorRed
|M:Combat - Entity Attacked
|D:1

002 001 V C 00:03:22:03 00:03:22:04 00:03:22:03 00:03:22:04
|C:ResolveColorCyan
|M:Block - Diamond Ore Mined
|D:1

003 001 V C 00:15:30:00 00:15:30:01 00:15:30:00 00:15:30:01
|C:ResolveColorPurple
|M:Boss - Ender Dragon Spawned
|D:1

004 001 V C 00:45:12:24 00:45:12:25 00:45:12:24 00:45:12:25
|C:ResolveColorYellow
|M:Manual - POI A
|D:1
```

### EDL Field Descriptions

**Header:**
- `TITLE:` - Recording session name
- `FCM:` - Frame count mode (NON-DROP FRAME for 30fps, 60fps; DROP FRAME for 29.97fps, 59.94fps)

**Event Line:**
```
001 001 V C 00:00:15:13 00:00:15:14 00:00:15:13 00:00:15:14
│   │   │ │ │           │           │           └─ Record Out (marker time + 1 frame)
│   │   │ │ │           │           └─ Record In (marker time)
│   │   │ │ │           └─ Source Out (marker time + 1 frame)
│   │   │ │ └─ Source In (marker time)
│   │   │ └─ Edit type (C=Cut)
│   │   └─ Track (V=Video)
│   └─ Reel number (001 for single video file)
└─ Event number (sequential)
```

**Marker Metadata:**
- `|C:` - Color (ResolveColorRed, ResolveColorBlue, ResolveColorCyan, ResolveColorGreen, ResolveColorYellow, ResolveColorPurple, ResolveColorPink, ResolveColorOrange)
- `|M:` - Marker text (the annotation)
- `|D:` - Duration in frames (1 for single-frame markers)

### Color Mapping

```java
Map<String, String> eventTypeColors = Map.of(
    "Combat", "ResolveColorRed",
    "Boss", "ResolveColorPurple",
    "Block", "ResolveColorCyan",
    "Item", "ResolveColorGreen",
    "Exploration", "ResolveColorBlue",
    "Achievement", "ResolveColorYellow",
    "Fall Damage", "ResolveColorOrange",
    "Explosion", "ResolveColorOrange",
    "Manual", "ResolveColorYellow"
);
```

### Timecode Calculation

```java
// For 30fps non-drop frame:
// Seconds to timecode: HH:MM:SS:FF
// Example: 15.45 seconds at 30fps
// = 0 hours + 0 minutes + 15 seconds + (0.45 * 30) frames
// = 00:00:15:13

String secondsToTimecode(double seconds, int framerate) {
    int totalFrames = (int)(seconds * framerate);
    int hours = totalFrames / (framerate * 3600);
    int minutes = (totalFrames % (framerate * 3600)) / (framerate * 60);
    int secs = (totalFrames % (framerate * 60)) / framerate;
    int frames = totalFrames % framerate;

    return String.format("%02d:%02d:%02d:%02d", hours, minutes, secs, frames);
}
```

---

## Component 2: Enhanced Minecraft Mod - EDL File Writer

### New Class: `EdlFileWriter.java`

```java
package ninja.trek.obsannotator;

import ninja.trek.obsannotator.config.ObsAnnotatorConfig;
import java.io.*;
import java.nio.file.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Map;

public class EdlFileWriter {
    private static final Map<String, String> EVENT_TYPE_COLORS = Map.of(
        "Combat", "ResolveColorRed",
        "Boss", "ResolveColorPurple",
        "Block", "ResolveColorCyan",
        "Item", "ResolveColorGreen",
        "Exploration", "ResolveColorBlue",
        "Achievement", "ResolveColorYellow",
        "Fall Damage", "ResolveColorOrange",
        "Explosion", "ResolveColorOrange",
        "Manual", "ResolveColorYellow"
    );

    private final ObsAnnotatorConfig config;
    private BufferedWriter writer;
    private Path edlFilePath;
    private int eventCounter = 1;
    private long recordingStartTime;

    public EdlFileWriter(ObsAnnotatorConfig config) {
        this.config = config;
    }

    /**
     * Start a new EDL file for recording session
     */
    public void startRecording(String outputDirectory, String videoFilename) {
        try {
            // Generate EDL filename (replace .mp4 with .edl)
            String edlFilename = videoFilename.replaceAll("\\.(mp4|mkv|mov)$", ".edl");
            edlFilePath = Paths.get(outputDirectory, edlFilename);

            // Create parent directories if needed
            Files.createDirectories(edlFilePath.getParent());

            // Open file for writing
            writer = Files.newBufferedWriter(edlFilePath,
                StandardOpenOption.CREATE,
                StandardOpenOption.TRUNCATE_EXISTING);

            // Write EDL header
            String sessionName = generateSessionName();
            writer.write("TITLE: " + sessionName + "\n");

            // Determine frame count mode based on framerate
            String fcm = (config.framerate == 29.97 || config.framerate == 59.94)
                ? "DROP FRAME"
                : "NON-DROP FRAME";
            writer.write("FCM: " + fcm + "\n");
            writer.write("\n");
            writer.flush();

            recordingStartTime = System.currentTimeMillis();
            eventCounter = 1;

            System.out.println("[OBS Annotator] EDL file created: " + edlFilePath);

        } catch (IOException e) {
            System.err.println("[OBS Annotator] Failed to create EDL file: " + e.getMessage());
        }
    }

    /**
     * Write a marker to the EDL file
     */
    public void writeMarker(String eventType, String eventSubtype) {
        if (writer == null) {
            return;
        }

        try {
            // Calculate timestamp
            long currentTime = System.currentTimeMillis();
            double timestampSeconds = (currentTime - recordingStartTime) / 1000.0;

            // Convert to timecode
            String timecode = secondsToTimecode(timestampSeconds, config.framerate);
            String timecodeEnd = secondsToTimecode(timestampSeconds + (1.0 / config.framerate), config.framerate);

            // Get color for event type
            String color = EVENT_TYPE_COLORS.getOrDefault(eventType, "ResolveColorWhite");

            // Format marker text
            String markerText = eventType + " - " + eventSubtype;

            // Write EDL event
            writer.write(String.format("%03d 001 V C %s %s %s %s\n",
                eventCounter, timecode, timecodeEnd, timecode, timecodeEnd));
            writer.write("|C:" + color + "\n");
            writer.write("|M:" + markerText + "\n");
            writer.write("|D:1\n");
            writer.write("\n");
            writer.flush();

            eventCounter++;

        } catch (IOException e) {
            System.err.println("[OBS Annotator] Failed to write marker: " + e.getMessage());
        }
    }

    /**
     * Stop recording and close the EDL file
     */
    public void stopRecording() {
        if (writer != null) {
            try {
                writer.close();
                System.out.println("[OBS Annotator] EDL file closed: " + edlFilePath);
            } catch (IOException e) {
                System.err.println("[OBS Annotator] Error closing EDL file: " + e.getMessage());
            }
            writer = null;
        }
    }

    /**
     * Convert seconds to timecode string (HH:MM:SS:FF)
     */
    private String secondsToTimecode(double seconds, double framerate) {
        int totalFrames = (int)(seconds * framerate);
        int hours = totalFrames / ((int)framerate * 3600);
        int minutes = (totalFrames % ((int)framerate * 3600)) / ((int)framerate * 60);
        int secs = (totalFrames % ((int)framerate * 60)) / (int)framerate;
        int frames = totalFrames % (int)framerate;

        return String.format("%02d:%02d:%02d:%02d", hours, minutes, secs, frames);
    }

    /**
     * Generate a session name for the EDL title
     */
    private String generateSessionName() {
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
        return "Minecraft Stream " + LocalDateTime.now().format(formatter);
    }

    public boolean isRecording() {
        return writer != null;
    }
}
```

### Integration into ObsAnnotatorClient.java

Modify the client to create an EDL writer:

```java
public class ObsAnnotatorClient implements ClientModInitializer {
    public static ObsAnnotatorConfig CONFIG;
    public static ObsWebSocketClient WS_CLIENT;
    public static EventTracker EVENT_TRACKER;
    public static EdlFileWriter EDL_WRITER;  // NEW

    @Override
    public void onInitializeClient() {
        CONFIG = ObsAnnotatorConfig.load();
        EVENT_TRACKER = new EventTracker();
        EDL_WRITER = new EdlFileWriter(CONFIG);  // NEW

        initWebSocket();
        registerKeybindings();
        // ... rest of initialization
    }

    public static void sendAnnotation(String text) {
        // Existing WebSocket send
        if (WS_CLIENT != null && WS_CLIENT.isAuthenticated()) {
            WS_CLIENT.sendAnnotation(text);
        }

        // NEW: Also write to EDL file
        if (CONFIG.enableEdlExport && EDL_WRITER != null) {
            // Parse annotation text to extract type and subtype
            String[] parts = text.split(" - ", 2);
            String eventType = parts.length > 0 ? parts[0] : "Event";
            String eventSubtype = parts.length > 1 ? parts[1] : "";

            EDL_WRITER.writeMarker(eventType, eventSubtype);
        }
    }
}
```

### Handling Recording Start/Stop

We need to detect when OBS starts/stops recording. Options:

**Option 1: OBS WebSocket Events (RECOMMENDED)**
Listen for OBS recording events via WebSocket:

```java
// In ObsWebSocketClient.onMessage():
case 9: // Event
    JsonObject eventData = msg.getAsJsonObject("d");
    String eventType = eventData.get("eventType").getAsString();

    if ("RecordStateChanged".equals(eventType)) {
        JsonObject data = eventData.getAsJsonObject("eventData");
        String outputState = data.get("outputState").getAsString();

        if ("OBS_WEBSOCKET_OUTPUT_STARTED".equals(outputState)) {
            handleRecordingStarted(data);
        } else if ("OBS_WEBSOCKET_OUTPUT_STOPPED".equals(outputState)) {
            handleRecordingStopped();
        }
    }
    break;

private void handleRecordingStarted(JsonObject data) {
    String outputPath = data.get("outputPath").getAsString();
    Path videoPath = Paths.get(outputPath);
    String directory = videoPath.getParent().toString();
    String filename = videoPath.getFileName().toString();

    ObsAnnotatorClient.EDL_WRITER.startRecording(directory, filename);
}

private void handleRecordingStopped() {
    ObsAnnotatorClient.EDL_WRITER.stopRecording();
}
```

**Option 2: Manual Keybinds**
Add keybinds for starting/stopping EDL recording:

```java
private static KeyMapping keyStartRecording;
private static KeyMapping keyStopRecording;

// In registerKeybindings():
while (keyStartRecording.consumeClick()) {
    // Prompt for filename or auto-generate
    String filename = generateAutoFilename();
    EDL_WRITER.startRecording(CONFIG.edlOutputDirectory, filename);
}

while (keyStopRecording.consumeClick()) {
    EDL_WRITER.stopRecording();
}
```

**Option 3: Config File Path**
User manually sets the video filename in config before recording:

```json
{
  "edlOutputDirectory": "C:/Users/YourName/Videos/OBS",
  "currentRecordingFilename": "2024-01-15_Stream.mp4",
  "enableEdlExport": true
}
```

### Configuration Additions

Add to `ObsAnnotatorConfig.java`:

```java
// EDL Export Settings
public boolean enableEdlExport = true;
public String edlOutputDirectory = "";  // Empty = use OBS recording dir from WebSocket
public double framerate = 30.0;  // Must match OBS recording framerate
public boolean autoDetectFramerate = true;  // Try to detect from OBS WebSocket
```

---

## Component 3: DaVinci Resolve Workflow Integration Plugin

### Technology Stack

- **Frontend:** Electron + React + TypeScript
- **Backend:** Python Flask server + DaVinci Resolve Python API
- **Communication:** HTTP REST API between Electron and Python

### Plugin Architecture

Same as the original design (see previous document), with these key features:

1. **File Browser:** Load video file and matching EDL file
2. **Marker List:** Display all markers from EDL with metadata
3. **Filter Panel:** Text search, exclude, time range, event type checkboxes
4. **BPM Supercut Generator:** Input BPM, note division, generate beat-synced edits
5. **Timeline Integration:** Import filtered markers directly to Resolve timeline

### GUI Layout (Same as Before)

```
┌─────────────────────────────────────────────────────────────────┐
│  ObsAnnotator - DaVinci Resolve Companion            [_][□][×]  │
├─────────────────────────────────────────────────────────────────┤
│  📁 Files                                                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Video File:   [/path/to/my_stream.mp4          ] [Browse] │ │
│  │ EDL File:     [/path/to/my_stream.edl          ] [Browse] │ │
│  │ Framerate:    [30 fps] (auto-detected)                    │ │
│  │ Duration:     [01:02:45]                                   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  🔍 Filter Markers                                               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Search:   [dragon              ] (contains text)          │ │
│  │ Exclude:  [manual              ] (exclude text)           │ │
│  │                                                            │ │
│  │ Time Range: [00:00:00] ━━●━━━━━━━━━━━━━━━━━ [01:02:45]   │ │
│  │                                                            │ │
│  │ Event Types: (234 total markers, 89 visible after filter) │ │
│  │ ☑ Combat (45)        ☑ Boss (8)        ☑ Block (120)     │ │
│  │ ☑ Item (12)          ☑ Exploration (5) ☑ Achievement (3) │ │
│  │ ☐ Explosion (25)     ☐ Manual (16)                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  📋 Markers (89 visible)                    [Import to Timeline]│
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Time      │ Color  │ Type   │ Description                 │ │
│  ├───────────┼────────┼────────┼────────────────────────────-┤ │
│  │ 00:00:15  │ 🔴     │ Combat │ Entity Attacked             │ │
│  │ 00:15:30  │ 🟣     │ Boss   │ Ender Dragon Spawned        │ │
│  │ 00:18:45  │ 🟣     │ Boss   │ Ender Dragon Defeated       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  🎵 BPM Supercut Generator                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Song BPM:        [120]                                     │ │
│  │ Note Division:   (●) 1/2  ( ) 1/4  ( ) 1/8  ( ) 1/16      │ │
│  │ Clip Duration:   [1.00] seconds (auto-calculated)         │ │
│  │                                                            │ │
│  │ Event Filter: Use filtered markers above (89 events)      │ │
│  │ Estimated timeline: [01:29] (89 clips × 1.0s)            │ │
│  │                                                            │ │
│  │ Options:                                                   │ │
│  │ ☑ Add crossfade transitions (0.2s)                        │ │
│  │ ☑ Sort chronologically                                    │ │
│  │ ☑ Skip duplicates within 3 seconds                        │ │
│  │                                                            │ │
│  │ Output Timeline: [BPM_Supercut_120]                       │ │
│  │                                                            │ │
│  │                   [Generate Supercut]                      │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### Key Workflows

#### Workflow 1: Import Markers
1. User records gameplay in Minecraft with OBS
2. EDL file is automatically created alongside video
3. User opens DaVinci Resolve and the ObsAnnotator plugin
4. User browses to video + EDL files (or auto-detects matching files)
5. Plugin parses EDL and displays markers
6. User applies filters (e.g., only Boss events, exclude Manual markers)
7. User clicks "Import to Timeline"
8. Filtered markers appear on Resolve timeline with correct colors

#### Workflow 2: BPM Supercut
1. User loads video + EDL (same as Workflow 1)
2. User filters for specific events (e.g., "Combat - Entity Attacked" + "Block - Diamond Ore")
3. User enters song BPM (e.g., 120) and note division (e.g., 1/4 notes)
4. Plugin calculates clip duration: 60/120 * (4/4) = 0.5 seconds per clip
5. User clicks "Generate Supercut"
6. Plugin creates new timeline:
   - Extracts 0.25s before + 0.25s after each marker
   - Places clips so events land on beats (0.0s, 0.5s, 1.0s, ...)
   - Adds crossfade transitions
   - Creates new markers on beats
7. User reviews timeline and adds music track
8. User renders final video

---

## Component 4: Python API Server & Supercut Generator

### Core Functionality

**EDL Parser:**
```python
class EdlParser:
    def parse(self, edl_file_path):
        """Parse EDL file and return list of markers."""
        markers = []

        with open(edl_file_path, 'r') as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check for event line (starts with digit)
            if line and line[0].isdigit():
                parts = line.split()
                event_num = int(parts[0])
                timecode_in = parts[4]  # Record In timecode

                # Read metadata lines
                color = None
                text = None
                duration = 1

                for j in range(i+1, min(i+4, len(lines))):
                    meta_line = lines[j].strip()
                    if meta_line.startswith('|C:'):
                        color = meta_line[3:]
                    elif meta_line.startswith('|M:'):
                        text = meta_line[3:]
                    elif meta_line.startswith('|D:'):
                        duration = int(meta_line[3:])

                markers.append({
                    'id': event_num,
                    'timecode': timecode_in,
                    'timestampSeconds': self.timecode_to_seconds(timecode_in, framerate),
                    'color': color,
                    'text': text,
                    'duration': duration,
                    'type': text.split(' - ')[0] if ' - ' in text else 'Unknown',
                    'subtype': text.split(' - ')[1] if ' - ' in text else text
                })

                i += 4  # Skip to next event
            else:
                i += 1

        return markers

    def timecode_to_seconds(self, timecode, framerate):
        """Convert HH:MM:SS:FF to seconds."""
        parts = timecode.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        frames = int(parts[3])

        return hours * 3600 + minutes * 60 + seconds + (frames / framerate)
```

**BPM Supercut Generator:**
(Same algorithm as in original design document - see previous document for full pseudocode)

Key algorithm:
```python
def generate_bpm_supercut(markers, bpm, note_division, options):
    beat_interval = 60.0 / bpm
    clip_duration = calculate_clip_duration(bpm, note_division)
    half_duration = clip_duration / 2.0

    timeline = create_new_timeline(options['timeline_name'])
    beat_position = 0

    for marker in markers:
        # Extract clip centered on event
        source_start = marker['timestampSeconds'] - half_duration
        source_end = marker['timestampSeconds'] + half_duration

        # Add clip to timeline at beat position
        add_clip_to_timeline(timeline, source_start, source_end, beat_position)

        # Add marker at beat
        timeline.add_marker(beat_position, marker['text'], marker['color'])

        # Move to next beat
        beat_position += beat_interval

    return timeline
```

---

## Installation & Setup

### 1. Minecraft Mod Setup

**Modify existing mod:**

1. Add `EdlFileWriter.java` to the project
2. Modify `ObsAnnotatorClient.java` to instantiate EDL writer
3. Modify `sendAnnotation()` to call `EDL_WRITER.writeMarker()`
4. Subscribe to OBS recording events (recommended) or add manual keybinds
5. Rebuild and reinstall mod

**Update config file (`.minecraft/config/obsannotator.json`):**

```json
{
  "obsHost": "localhost",
  "obsPort": 4455,
  "obsPassword": "",
  "enableEdlExport": true,
  "edlOutputDirectory": "C:/Users/YourName/Videos/OBS",
  "framerate": 30.0,
  "autoDetectFramerate": true,
  "enableCombatEvents": true,
  ...
}
```

### 2. OBS Setup

**No changes needed!** Your existing StreamUP Chapter Marker Manager setup continues to work.

### 3. DaVinci Resolve Plugin Setup

(Same as original design - see full installation section in previous document)

**Quick summary:**
1. Install Python dependencies (`pip install flask DaVinciResolveScript`)
2. Build Electron app (`npm install && npm run build`)
3. Copy to Resolve Workflow Integration Plugins directory
4. Start Python API server
5. Open plugin in Resolve

---

## First-Time Workflow

```
1. Start Minecraft with ObsAnnotator mod (updated version)
2. Start OBS Studio (StreamUP already running)
3. Press "Start Recording" in OBS
   → Mod detects recording started via WebSocket event
   → EDL file created: my_stream.edl
4. Play Minecraft (events tracked)
   → Events sent to StreamUP (existing behavior)
   → Events written to EDL file (NEW)
5. Press "Stop Recording" in OBS
   → Mod detects recording stopped
   → EDL file closed
6. Files created:
   - my_stream.mp4 (video)
   - my_stream.edl (markers for Resolve)
7. Open DaVinci Resolve
8. Open ObsAnnotator plugin panel
9. Browse to my_stream.mp4 and my_stream.edl
10. Filter markers as desired
11. Click "Import to Timeline" or "Generate Supercut"
```

---

## Technical Considerations

### Handling OBS Recording Events

To detect when OBS starts/stops recording, we need to:

1. **Enable Recording Events in WebSocket**

In `ObsWebSocketClient.java`, after authentication, subscribe to recording events:

```java
private void subscribeToEvents() {
    try {
        JsonObject request = new JsonObject();
        request.addProperty("op", 6); // Request

        JsonObject requestData = new JsonObject();
        requestData.addProperty("requestType", "SetOutputSettings");
        requestData.addProperty("requestId", UUID.randomUUID().toString());

        // Subscribe to Output events (includes RecordStateChanged)
        JsonObject eventSubscriptions = new JsonObject();
        eventSubscriptions.addProperty("eventSubscription", 64); // Output events = bit 6 = 64

        requestData.add("requestData", eventSubscriptions);
        request.add("d", requestData);

        send(GSON.toJson(request));
    } catch (Exception e) {
        System.err.println("[OBS Annotator] Failed to subscribe to events: " + e.getMessage());
    }
}
```

2. **Handle RecordStateChanged Event**

Update `onMessage()` to handle recording state changes:

```java
case 9: // Event
    JsonObject eventData = msg.getAsJsonObject("d");
    String eventType = eventData.get("eventType").getAsString();

    if ("RecordStateChanged".equals(eventType)) {
        handleRecordingStateChanged(eventData.getAsJsonObject("eventData"));
    }
    break;
```

### Framerate Auto-Detection

Query OBS for recording settings:

```java
private void detectFramerate() {
    // Send GetRecordingSettings request
    // Parse response and extract framerate
    // Update config.framerate
}
```

### Error Handling

**Missing output directory:**
- Fallback to user's Videos folder
- Log warning message

**Unable to detect recording start:**
- Provide manual keybind option
- Show in-game message prompting user

**Framerate mismatch:**
- Warn user if EDL framerate doesn't match video
- Offer to recalculate markers

---

## Future Enhancements

### Phase 1 Extensions

1. **Metadata Enrichment**
   - Capture player health, position, biome in EDL comments
   - Use metadata for advanced filtering

2. **Multi-Session Support**
   - Combine markers from multiple recordings
   - Generate compilation videos from multiple sessions

3. **Custom Supercut Types**
   - "Best Moments" (boss fights + achievements)
   - "Near-Death Compilation" (only near-death moments)
   - "Progression Video" (achievements chronologically)

4. **Auto-Music Sync**
   - Detect music BPM in Resolve timeline
   - Auto-generate beat markers
   - Sync supercut to existing music track

### Phase 2 Extensions

1. **AI-Enhanced Filtering**
   - Analyze audio for exciting moments (shouting, excitement)
   - Visual analysis (detect explosions, boss health bars)
   - Sentiment analysis of commentary

2. **Template System**
   - Pre-built supercut templates
   - Intro/outro clip insertion
   - Automatic title card generation

3. **Collaboration Features**
   - Share marker files with editors
   - Cloud sync for annotation files
   - Multi-player perspective sync

---

## Summary of Changes from Original Design

### What's Different

1. ✅ **No OBS Script Needed** - Your mod already talks to OBS perfectly
2. ✅ **EDL Format Instead of JSON** - Native Resolve format, no conversion needed
3. ✅ **Direct File Writing** - Mod writes EDL alongside recording
4. ✅ **Simpler Architecture** - Fewer components, less complexity
5. ✅ **Preserves Existing Workflow** - StreamUP continues to work as-is

### What's the Same

1. ✅ **DaVinci Resolve Plugin** - Same Electron app design
2. ✅ **BPM Supercut Algorithm** - Same beat-sync logic
3. ✅ **Filtering System** - Same UI and functionality
4. ✅ **Python API Server** - Same architecture

### Key Advantages

- **Simpler:** Direct EDL export from mod, no intermediate formats
- **Faster:** No conversion step needed
- **Native:** EDL is DaVinci Resolve's native marker format
- **Reliable:** Fewer points of failure
- **Backwards Compatible:** StreamUP still works for live annotations

---

## Next Steps

### Immediate Actions

1. **Review this design** - Confirm it matches your expectations
2. **Clarify questions:**
   - Should we use OBS WebSocket recording events or manual keybinds?
   - What framerate do you typically record at?
   - Where do you want EDL files saved?

3. **Begin implementation:**
   - Phase 1: Add `EdlFileWriter` to Minecraft mod
   - Phase 2: Test EDL generation during recording
   - Phase 3: Build DaVinci Resolve plugin
   - Phase 4: Implement BPM supercut generator

### Questions Before Starting

1. **Recording Detection:** Prefer automatic (WebSocket events) or manual (keybind)?
2. **Output Directory:** Auto-detect from OBS or manually configure?
3. **Framerate:** Fixed 30fps or auto-detect from OBS?
4. **File Naming:** Auto-generate based on timestamp or let user specify?

Ready to start implementation once you confirm the approach!
