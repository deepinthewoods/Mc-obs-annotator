import json
import sys
import os
import threading
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

# Add DaVinci Resolve scripting module to Python path
resolve_script_dirs = [
    os.path.join(os.environ.get("PROGRAMDATA", "C:\\ProgramData"),
                 "Blackmagic Design", "DaVinci Resolve", "Support", "Developer", "Scripting", "Modules"),
    os.path.join(os.environ.get("APPDATA", ""),
                 "Blackmagic Design", "DaVinci Resolve", "Support", "Developer", "Scripting", "Modules"),
]
for d in resolve_script_dirs:
    if os.path.isdir(d) and d not in sys.path:
        sys.path.insert(0, d)

# Import is deferred to init_resolve() because fusionscript.dll crashes
# the process if DaVinci Resolve is not running.
dvr_script = None


def _check_resolve_available():
    """Check if DaVinci Resolve scripting is available by testing in a subprocess."""
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path[:0] = %r; import DaVinciResolveScript" % [d for d in resolve_script_dirs if os.path.isdir(d)]],
            capture_output=True, timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, Exception):
        return False


def _try_import_resolve_script():
    """Try to import DaVinciResolveScript. Returns the module or None.

    Tests in a subprocess first to avoid crashes from fusionscript.dll
    when DaVinci Resolve is not running.
    """
    global dvr_script
    if dvr_script is not None:
        return dvr_script

    if not _check_resolve_available():
        print("DaVinci Resolve scripting not available (Resolve may not be running)")
        return None

    try:
        import DaVinciResolveScript as _dvr
        dvr_script = _dvr
        return dvr_script
    except (ImportError, OSError) as e:
        print(f"Warning: DaVinciResolveScript not available: {e}")
        return None

from edl_parser import EdlParser
from marker_filter import MarkerFilter
from supercut_generator import SupercutGenerator
from bulk_scanner import BulkScanner, ScanSettings
from clip_extractor import ClipExtractor
from timeline_creator import TimelineCreator

app = Flask(__name__)
CORS(app)  # Allow Electron app to connect

# Initialize DaVinci Resolve API
resolve = None
project = None

# Initialize bulk import components
bulk_scanner = BulkScanner()
clip_extractor = ClipExtractor()

# Pause event for bulk processing (set = running, clear = paused)
bulk_pause_event = threading.Event()
bulk_pause_event.set()  # Start in running state


def init_resolve():
    """Initialize connection to DaVinci Resolve."""
    global resolve, project

    script = _try_import_resolve_script()
    if script is None:
        return False

    try:
        resolve = script.scriptapp("Resolve")
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


# ============================================================================
# Bulk Import Endpoints
# ============================================================================

@app.route('/api/bulk/scan', methods=['POST'])
def bulk_scan():
    """Scan source folder for video+EDL pairs."""
    try:
        data = request.json
        source_folder = data['sourceFolder']
        recursive = data.get('recursive', False)

        sessions = bulk_scanner.scan_folder(source_folder, recursive)

        # Calculate total size
        total_size = sum(s.video_size for s in sessions)

        def format_size(size_bytes):
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.1f} PB"

        return jsonify({
            'success': True,
            'sessions': [bulk_scanner.session_to_dict(s) for s in sessions],
            'totalSize': format_size(total_size),
            'totalSessions': len(sessions)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/bulk/analyze', methods=['POST'])
def bulk_analyze():
    """Analyze a session and calculate clip regions."""
    try:
        data = request.json
        session_id = data['sessionId']
        settings_data = data.get('settings', {})

        enabled_types = settings_data.get('enabledEventTypes', None)

        settings = ScanSettings(
            chapter_buffer=settings_data.get('chapterBuffer', 0.5),
            poi_duration=settings_data.get('poiDuration', 180.0),
            merge_overlapping=settings_data.get('mergeOverlapping', True),
            enabled_event_types=enabled_types if enabled_types else None
        )

        result = bulk_scanner.analyze_session(session_id, settings)

        if result:
            return jsonify({
                'success': True,
                **result
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/bulk/extract', methods=['POST'])
def bulk_extract():
    """Extract clips from a session with streaming progress."""
    try:
        data = request.json
        session_id = data['sessionId']
        output_folder = data['outputFolder']
        skip_black_clips = data.get('skipBlackClips', True)

        session = bulk_scanner.get_session(session_id)
        if not session:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404

        # Make sure we have clip regions
        if not session.clip_regions:
            settings = ScanSettings()
            bulk_scanner.analyze_session(session_id, settings)
            session = bulk_scanner.get_session(session_id)

        def generate():
            """Generator for SSE streaming."""
            for progress in clip_extractor.extract_session_streaming(
                session,
                output_folder,
                skip_black_clips
            ):
                yield f"data: {json.dumps(progress)}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/bulk/create-timelines', methods=['POST'])
def bulk_create_timelines():
    """Create Resolve timelines from extracted clips."""
    try:
        if not resolve or not project:
            if not init_resolve():
                return jsonify({
                    'success': False,
                    'error': 'Not connected to DaVinci Resolve'
                }), 500

        data = request.json
        session_id = data.get('sessionId')
        extracted_folder = data['extractedFolder']

        # Get session name
        session = bulk_scanner.get_session(session_id) if session_id else None
        if session:
            import os
            session_name = os.path.splitext(os.path.basename(session.video_file))[0]
        else:
            import os
            session_name = os.path.basename(extracted_folder)

        chapter_buffer = data.get('chapterBuffer', 0.5)

        creator = TimelineCreator(resolve, project)
        timelines = creator.create_session_timelines(extracted_folder, session_name, chapter_buffer)

        return jsonify({
            'success': True,
            'timelines': timelines
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/bulk/pause', methods=['POST'])
def bulk_pause():
    """Pause bulk processing."""
    bulk_pause_event.clear()
    return jsonify({'success': True, 'paused': True})


@app.route('/api/bulk/resume', methods=['POST'])
def bulk_resume():
    """Resume bulk processing."""
    bulk_pause_event.set()
    return jsonify({'success': True, 'paused': False})


@app.route('/api/bulk/process-all', methods=['POST'])
def bulk_process_all():
    """Process all sessions in batch with streaming progress."""
    try:
        data = request.json
        source_folder = data['sourceFolder']
        output_folder = data['outputFolder']
        settings_data = data.get('settings', {})
        session_ids = data.get('sessionIds', [])

        enabled_types = settings_data.get('enabledEventTypes', None)

        settings = ScanSettings(
            chapter_buffer=settings_data.get('chapterBuffer', 0.5),
            poi_duration=settings_data.get('poiDuration', 180.0),
            merge_overlapping=settings_data.get('mergeOverlapping', True),
            enabled_event_types=enabled_types if enabled_types else None
        )
        skip_black_clips = settings_data.get('skipBlackClips', True)
        create_timelines = settings_data.get('createTimelines', True)
        resume_processing = data.get('resume', False)

        # Ensure pause event is set (running) at start of new batch
        bulk_pause_event.set()

        # Use selected sessions if provided, otherwise scan folder
        if session_ids:
            sessions = []
            for sid in session_ids:
                s = bulk_scanner.get_session(sid)
                if s:
                    sessions.append(s)
        else:
            sessions = bulk_scanner.scan_folder(source_folder, recursive=False)

        def generate():
            """Generator for SSE streaming."""
            # Analyze all sessions first to compute total clip count
            for session in sessions:
                bulk_scanner.analyze_session(session.id, settings)

            total_clips_all = 0
            for session in sessions:
                if session.clip_regions:
                    total_clips_all += (
                        len(session.clip_regions.chapters)
                        + len(session.clip_regions.recordings)
                        + len(session.clip_regions.pois)
                        + len(session.clip_regions.falls)
                    )

            # Shared output folder — all clips go here (no per-video subfolder)
            shared_folder = output_folder

            # Counters that carry across sessions
            from clip_extractor import _sanitize_filename
            chapter_label_offsets = {}
            recording_offset = 0
            poi_offset = 0
            global_clip_offset = 0

            for session in sessions:
                # Extract clips into the shared folder
                for progress in clip_extractor.extract_session_streaming(
                    session,
                    output_folder,
                    skip_black_clips,
                    shared_folder=shared_folder,
                    chapter_label_offsets=chapter_label_offsets,
                    recording_offset=recording_offset,
                    poi_offset=poi_offset,
                    global_clip_offset=global_clip_offset,
                    global_clip_total=total_clips_all,
                    resume=resume_processing,
                    pause_event=bulk_pause_event
                ):
                    yield f"data: {json.dumps(progress)}\n\n"

                # Update offsets for the next session
                if session.clip_regions:
                    local_clips = (
                        len(session.clip_regions.chapters)
                        + len(session.clip_regions.recordings)
                        + len(session.clip_regions.pois)
                        + len(session.clip_regions.falls)
                    )
                    global_clip_offset += local_clips
                    recording_offset += len(session.clip_regions.recordings)
                    poi_offset += len(session.clip_regions.pois)

                    for r in session.clip_regions.chapters:
                        sanitized = _sanitize_filename(r.label)
                        chapter_label_offsets[sanitized] = chapter_label_offsets.get(sanitized, 0) + 1

            # Create timelines once at the end across all extracted clips
            if create_timelines:
                if resolve and project:
                    # Use source folder basename as the combined session name
                    combined_name = os.path.basename(source_folder.rstrip('/\\')) or 'Combined'

                    creator = TimelineCreator(resolve, project)
                    timelines = creator.create_session_timelines(shared_folder, combined_name, settings.chapter_buffer)

                    yield f"data: {json.dumps({'type': 'timelines_created', 'timelines': timelines})}\n\n"

            yield f"data: {json.dumps({'type': 'batch_complete', 'totalClips': total_clips_all})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


# ============================================================================
# Timeline Supercut Endpoints
# ============================================================================

@app.route('/api/timeline/clips', methods=['GET'])
def get_timeline_clips():
    """Read all clips from the current Resolve timeline."""
    try:
        if not resolve or not project:
            if not init_resolve():
                return jsonify({
                    'success': False,
                    'error': 'Not connected to DaVinci Resolve'
                }), 500

        timeline = project.GetCurrentTimeline()
        if not timeline:
            return jsonify({
                'success': False,
                'error': 'No timeline is currently open'
            }), 400

        framerate = float(timeline.GetSetting('timelineFrameRate'))
        generator = SupercutGenerator(resolve, project)
        clips = generator.read_timeline_clips(timeline)

        return jsonify({
            'success': True,
            'timelineName': timeline.GetName(),
            'framerate': framerate,
            'clips': clips
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/timeline/supercut-from-clips', methods=['POST'])
def supercut_from_clips():
    """Generate a BPM-synced supercut from selected timeline clips."""
    try:
        if not resolve or not project:
            if not init_resolve():
                return jsonify({
                    'success': False,
                    'error': 'Not connected to DaVinci Resolve'
                }), 500

        timeline = project.GetCurrentTimeline()
        if not timeline:
            return jsonify({
                'success': False,
                'error': 'No timeline is currently open'
            }), 400

        data = request.json
        clip_indices = data['clipIndices']
        bpm = data['bpm']
        note_division = data['noteDivision']
        options = data.get('options', {})

        framerate = float(timeline.GetSetting('timelineFrameRate'))

        generator = SupercutGenerator(resolve, project)
        result = generator.generate_from_timeline_clips(
            source_timeline=timeline,
            clip_indices=clip_indices,
            bpm=bpm,
            note_division=note_division,
            options=options,
            framerate=framerate
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
        print("[OK] Connected to DaVinci Resolve")
        if project:
            print(f"[OK] Project open: {project.GetName()}")
    else:
        print("[WARNING] Could not connect to DaVinci Resolve")
        print("  Make sure Resolve is running and a project is open")

    print("\nServer running on http://localhost:8765")
    app.run(host='127.0.0.1', port=8765, debug=False)
