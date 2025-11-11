# ObsAnnotator - DaVinci Resolve Companion Plugin

A powerful desktop application that helps you import and manage Minecraft ObsAnnotator event markers in DaVinci Resolve, with advanced filtering and BPM-synchronized supercut generation.

## Overview

This plugin works with your existing Minecraft ObsAnnotator mod and OBS StreamUP Chapter Marker Manager to provide:

- **Marker Preview** - See all events before importing
- **Powerful Filtering** - Search, exclude, filter by type and time range
- **Direct Import** - Import markers directly to Resolve timelines
- **BPM Supercuts** - Auto-generate beat-synchronized video edits
- **Color Coding** - Auto-assign colors by event type
- **Statistics** - View event distribution and counts

## Prerequisites

### Required Software

1. **DaVinci Resolve Studio 18+** (Studio version required for Python API)
2. **Python 3.10+**
3. **Node.js 18+**

### Existing Setup (Already Working)

- Minecraft with ObsAnnotator mod
- OBS Studio with StreamUP Chapter Marker Manager
- Configured to send events via OBS WebSocket

## Installation

### 1. Clone or Download

```bash
cd /path/to/Mc-obs-annotator/davinci
```

### 2. Install Python Dependencies

```bash
cd python-server

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

### 3. Install Node.js Dependencies

```bash
cd ..  # Back to davinci folder
npm install
```

### 4. Build the Application

```bash
npm run build
```

## Usage

### Starting the Plugin

You need to start both the Python server and the Electron app.

#### Option 1: Manual Start (Recommended for Development)

**Terminal 1 - Start Python Server:**
```bash
cd python-server
# Activate venv if not already active
source venv/bin/activate  # or venv\Scripts\activate on Windows
python server.py
```

Wait for the message: `✓ Connected to DaVinci Resolve`

**Terminal 2 - Start Electron App:**
```bash
# From davinci folder
npm start
```

#### Option 2: Using Launcher Scripts

**Windows - Create `start-plugin.bat`:**
```batch
@echo off
echo Starting ObsAnnotator Plugin...

start "Python Server" cmd /k "cd python-server && venv\Scripts\activate && python server.py"
timeout /t 3 /nobreak > nul
start "ObsAnnotator Plugin" cmd /k "npm start"
```

**Mac/Linux - Create `start-plugin.sh`:**
```bash
#!/bin/bash
echo "Starting ObsAnnotator Plugin..."

cd python-server
source venv/bin/activate
python server.py &
sleep 3
cd ..
npm start
```

Make executable: `chmod +x start-plugin.sh`

### Workflow

#### 1. Export EDL from StreamUP

After recording gameplay with ObsAnnotator events:

1. In OBS, go to **File > Export > EDL**
2. Save to the same directory as your video file
3. Files should be named matching: `my_stream.mp4` and `my_stream.edl`

#### 2. Load Files in Plugin

1. Click **Browse** next to Video File
2. Select your recorded video (`.mp4`, `.mov`, etc.)
3. The plugin will auto-detect the matching `.edl` file if it exists
4. If not found, manually browse for the EDL file
5. Click **Load Files**

#### 3. Filter Markers (Optional)

Use the filter panel to refine which markers you want:

- **Search**: Filter markers containing specific text
- **Exclude**: Remove markers containing specific text
- **Event Types**: Select which event types to include
- **Time Range**: Filter by video timestamp

#### 4. Import to DaVinci Resolve

**Option A: Import Selected**
- Check/uncheck markers in the list
- Click **Import Selected to Timeline**

**Option B: Import All Filtered**
- Click **Import All Filtered** to import all visible markers

**Requirements:**
- DaVinci Resolve must be running
- A project must be open
- A timeline must be active

#### 5. Generate BPM Supercut (Optional)

Create a beat-synchronized montage of your filtered events:

1. Set **Song BPM** (use a BPM detector tool if needed)
2. Choose **Note Division** (half notes, quarter notes, etc.)
3. Configure **Options**:
   - Add crossfade transitions
   - Sort chronologically or randomize
   - Skip duplicate events
   - Add beat markers
4. Set **Output Timeline Name**
5. Click **Generate Supercut**

The plugin will create a new timeline with clips extracted around each marker, perfectly aligned to the beat!

## Troubleshooting

### Python Server Won't Connect to Resolve

**Problem:** Server shows `⚠ Could not connect to DaVinci Resolve`

**Solutions:**
1. Make sure DaVinci Resolve Studio is running (not the free version)
2. Open a project in Resolve
3. Check that the DaVinciResolveScript module is available:
   - Windows: `C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\`
   - Mac: `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/`
   - Linux: `/opt/resolve/Developer/Scripting/`
4. You may need to add the script path to your Python environment

### EDL Parse Error

**Problem:** "Failed to parse EDL" error

**Solutions:**
1. Make sure the file is a valid EDL file exported from StreamUP
2. Check that the EDL contains marker data (`|M:` lines)
3. Try opening the EDL in a text editor to verify the format

### No Timeline Open Error

**Problem:** "No timeline is currently open"

**Solutions:**
1. Create or open a timeline in DaVinci Resolve
2. Make sure the timeline is active (visible in the timeline panel)

### Import Fails Silently

**Problem:** Markers don't appear on timeline

**Solutions:**
1. Check that you're on the correct timeline
2. Verify the timeline framerate matches the video
3. Try importing fewer markers to test
4. Check the Resolve console for error messages

## Development

### Project Structure

```
davinci/
├── python-server/          # Flask API backend
│   ├── server.py           # Main Flask app
│   ├── edl_parser.py       # EDL file parser
│   ├── marker_filter.py    # Marker filtering logic
│   ├── supercut_generator.py  # BPM supercut creation
│   └── requirements.txt    # Python dependencies
├── src/
│   ├── main/               # Electron main process
│   │   ├── index.ts        # Main process entry
│   │   └── preload.ts      # Preload script
│   └── renderer/           # React frontend
│       ├── App.tsx         # Main app component
│       ├── components/     # UI components
│       ├── hooks/          # React hooks
│       ├── types/          # TypeScript types
│       └── styles/         # CSS styles
├── package.json
├── tsconfig.json
└── webpack.renderer.config.js
```

### Building for Distribution

```bash
npm run package
```

This creates platform-specific installers in the `release/` folder.

## Technical Details

### EDL Format

The plugin parses CMX 3600 EDL format with Resolve marker extensions:

```edl
001 001 V C 00:00:15:13 00:00:15:14 00:00:15:13 00:00:15:14
|C:ResolveColorRed
|M:Combat - Entity Attacked
|D:1
```

### API Endpoints

The Python server provides these endpoints:

- `GET /api/health` - Check server and Resolve connection
- `POST /api/parse-edl` - Parse EDL file and return markers
- `POST /api/filter-markers` - Apply filters to markers
- `POST /api/import-markers` - Import markers to timeline
- `POST /api/generate-supercut` - Generate BPM supercut

### Marker Format

Markers from ObsAnnotator follow the format:
```
{EventType} - {EventSubtype}
```

Examples:
- `Combat - Entity Attacked`
- `Boss - Ender Dragon Spawned`
- `Block - Diamond Ore Mined`
- `Achievement - Advancement Unlocked`

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

### Development Mode

```bash
# Terminal 1 - Python server
cd python-server
source venv/bin/activate
python server.py

# Terminal 2 - Electron app (with hot reload)
npm start
```

## License

MIT License - See LICENSE file for details

## Credits

- Built for the Minecraft ObsAnnotator mod
- Uses DaVinci Resolve Python API
- Integrates with OBS StreamUP Chapter Marker Manager

## Support

For issues and feature requests, please visit:
https://github.com/deepinthewoods/Mc-obs-annotator/issues
