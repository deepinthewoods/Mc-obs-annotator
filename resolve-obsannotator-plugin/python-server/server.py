from flask import Flask, request, jsonify
from flask_cors import CORS

try:
    import DaVinciResolveScript as dvr_script
except ImportError:
    print("Warning: DaVinciResolveScript module not found")
    print("This is normal if you're setting up the project")
    print("The module will be available when running from within DaVinci Resolve's Python environment")
    dvr_script = None

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

    if dvr_script is None:
        return False

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
