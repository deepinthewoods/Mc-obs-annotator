# ObsAnnotator - DaVinci Resolve Companion Plugin

A powerful companion plugin for DaVinci Resolve that works with the ObsAnnotator Minecraft mod and OBS StreamUP Chapter Marker Manager to enable advanced video editing workflows including marker filtering, preview, and BPM-synchronized supercut generation.

## Overview

This plugin allows you to:
- **Preview Markers** - See all markers from EDL files before importing
- **Filter Markers** - Search, exclude, filter by type, and time range
- **Import Selectively** - Only import the markers you want
- **Generate BPM Supercuts** - Auto-generate beat-synced montages
- **Color Coding** - Auto-assign colors by event type
- **Statistics** - View event counts and distribution

## Prerequisites

### Already Working (No Changes Needed!)
- ✅ Minecraft with ObsAnnotator mod
- ✅ OBS Studio with StreamUP Chapter Marker Manager
- ✅ Already configured and working

### Required for Plugin
- **DaVinci Resolve Studio 18+** (Studio version required for Python API)
- **Python 3.10+**
- **Node.js 18+**

## Installation

### 1. Install Python Dependencies

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

### 2. Build Electron App

```bash
cd resolve-obsannotator-plugin

# Install dependencies
npm install

# Build app
npm run build

# Or for development:
npm run dev
```

## Usage

### Starting the Plugin

**Option 1: Use Launcher Scripts**

Windows:
```bash
.\start-plugin.bat
```

Mac/Linux:
```bash
./start-plugin.sh
```

**Option 2: Manual Start**

Terminal 1 - Start Python server:
```bash
cd python-server
python server.py
```

Terminal 2 - Start Electron app:
```bash
npm start
```

### Workflow 1: Simple Marker Import (No Plugin Needed)

1. Record gameplay (Minecraft mod sends events to StreamUP automatically)
2. After recording in OBS: **File > Export > EDL**
3. Save EDL to same directory as video
4. In DaVinci Resolve:
   - Right-click timeline
   - Timelines > Import > Timeline Markers from EDL
   - Select your .edl file
   - All markers appear on timeline ✅

### Workflow 2: Filtered Marker Import (Using Plugin)

1. Record gameplay and export EDL from StreamUP
2. Open DaVinci Resolve and start the plugin
3. In plugin:
   - Load video file and EDL file
   - Plugin shows all markers with statistics
   - Apply filters:
     - Search: "boss"
     - Uncheck: Explosion, Manual
     - Time range: 00:10:00 to 00:30:00
   - Click "Import Filtered to Timeline"
   - Only filtered markers appear in Resolve ✅

### Workflow 3: BPM Supercut Generation

1. Record gameplay and export EDL
2. Open DaVinci Resolve and start the plugin
3. In plugin:
   - Load video and EDL files
   - Filter for specific events (e.g., Combat events)
   - Go to BPM Supercut Generator:
     - Set BPM: 140
     - Choose note division: Quarter notes
     - Enable options: crossfades, beat markers
     - Click "Generate Supercut"
4. Plugin creates new timeline with:
   - Events synced to beats
   - Crossfade transitions
   - Beat markers
5. Add your music track and enjoy perfect sync! ✅

## Features

### File Browser
- Select video and EDL files
- Auto-detection of matching files
- File information display

### Event Statistics
- Visual breakdown of event types
- Count per type
- Total event count

### Filter Panel
- **Text Search** - Find markers containing specific text
- **Exclude Filter** - Exclude markers with specific text
- **Event Type Selection** - Choose which event types to show
- **Time Range Slider** - Filter by timeline position

### Marker List
- Sortable table view
- Color indicators
- Checkbox selection
- Select all / Clear selection

### BPM Supercut Generator
- Set BPM and note division
- Auto-calculated clip durations
- Options:
  - Sort chronologically or randomize
  - Skip duplicate events
  - Add crossfade transitions
  - Add beat markers
- Estimated output length
- Custom timeline name

### Status Bar
- Connection status to DaVinci Resolve
- Current project status
- Error messages
- Marker count

## Project Structure

```
resolve-obsannotator-plugin/
├── python-server/
│   ├── server.py                 # Flask API server
│   ├── edl_parser.py             # EDL file parser
│   ├── marker_filter.py          # Marker filtering logic
│   ├── supercut_generator.py    # BPM supercut generator
│   └── requirements.txt          # Python dependencies
├── src/
│   ├── main/                     # Electron main process
│   │   ├── index.ts
│   │   └── preload.ts
│   └── renderer/                 # React application
│       ├── components/           # UI components
│       ├── hooks/                # React hooks
│       ├── types/                # TypeScript types
│       └── styles/               # CSS styles
├── package.json
├── tsconfig.json
├── webpack.config.js
└── README.md
```

## Troubleshooting

### Plugin won't connect to DaVinci Resolve
- Make sure DaVinci Resolve Studio is running
- Ensure a project is open in Resolve
- Check that the Python server is running
- Verify DaVinciResolveScript module is available

### EDL file won't parse
- Make sure the file is in CMX 3600 EDL format
- Check that the file was exported from StreamUP
- Verify the file path is correct

### Markers not importing
- Ensure a timeline is open in DaVinci Resolve
- Check that markers are selected
- Verify the timeline framerate matches the EDL

### Supercut generation fails
- Make sure the video file path is correct
- Verify markers are filtered and available
- Check that DaVinci Resolve has the video in its media pool
- Ensure sufficient disk space

## Development

### Running in Development Mode

```bash
# Terminal 1: Python server
cd python-server
python server.py

# Terminal 2: React dev server + Electron
npm run dev
```

### Building for Production

```bash
# Build everything
npm run build
npm run build:electron

# Package as installer
npm run package
```

## API Endpoints

The Python Flask server exposes the following API endpoints:

- `GET /api/health` - Check server and Resolve connection status
- `POST /api/parse-edl` - Parse EDL file and return markers
- `POST /api/filter-markers` - Apply filters to marker list
- `POST /api/import-markers` - Import markers to Resolve timeline
- `POST /api/generate-supercut` - Generate BPM-synchronized supercut

## Technologies Used

- **Frontend**: Electron, React, TypeScript
- **Backend**: Python, Flask, DaVinci Resolve API
- **Build Tools**: Webpack, TypeScript Compiler
- **Styling**: CSS (custom dark theme)

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on the GitHub repository.
