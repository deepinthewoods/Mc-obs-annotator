"""
Bulk Scanner - Scan folders for MKV+EDL pairs and build clip regions.
"""

import os
import re
import uuid
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field, asdict
from edl_parser import EdlParser


@dataclass
class ClipRegion:
    """A region to extract from a video."""
    start: float
    end: float
    markers: List[str] = field(default_factory=list)
    region_type: str = "chapter"  # "chapter", "recording", "poi"
    label: str = ""
    marker_offset: float = 0.0  # Marker's exact time relative to clip start


@dataclass
class StartEndPair:
    """A Start→End marker pair."""
    start_time: float
    end_time: float
    start_marker: str
    end_marker: str


@dataclass
class CategorizedMarkers:
    """Markers categorized by type."""
    chapters: List[Dict]  # Regular chapter markers (Combat, Boss, etc.)
    start_markers: List[Dict]  # "Start" markers
    end_markers: List[Dict]  # "End" markers
    pois: List[Dict]  # POI markers (e.g. "POI 1m", "POI 3m", "POI 5m")
    falls: List[Dict]  # "Fall Landed" markers
    new_section_markers: List[Dict] = field(default_factory=list)  # "New Section" markers
    camera_markers: List[Dict] = field(default_factory=list)
    timelapse_build_markers: List[Dict] = field(default_factory=list)


@dataclass
class CameraRegion:
    """A camera-mode span reconstructed from consecutive director markers."""
    start: float
    end: float
    mode: str
    node_id: Optional[str] = None
    build_id: Optional[str] = None
    build_mode: Optional[str] = None
    expected_frames: Optional[int] = None
    actual_frames: Optional[int] = None
    render_frames: Optional[int] = None
    marker_sequence: Optional[int] = None
    render_sequence: Optional[int] = None
    open_ended: bool = False


@dataclass
class CameraDiagnostic:
    """A recoverable marker timing or lifecycle issue for editor review."""
    code: str
    severity: str
    message: str
    timestamp: float
    node_id: Optional[str] = None
    build_id: Optional[str] = None
    expected_frames: Optional[int] = None
    actual_frames: Optional[int] = None


@dataclass
class ClipRegions:
    """All clip regions for a session."""
    chapters: List[ClipRegion] = field(default_factory=list)
    recordings: List[ClipRegion] = field(default_factory=list)
    pois: List[ClipRegion] = field(default_factory=list)
    falls: List[ClipRegion] = field(default_factory=list)
    camera_modes: List[CameraRegion] = field(default_factory=list)
    camera_diagnostics: List[CameraDiagnostic] = field(default_factory=list)
    timelapse_build_events: List[Dict] = field(default_factory=list)


@dataclass
class MulticamConfig:
    """Mapping of filename prefixes to camera numbers."""
    enabled: bool = False
    # List of {"prefix": "spec1", "trackName": "Spectator 1", "cameraNumber": 2}
    tracks: List[Dict] = field(default_factory=list)


@dataclass
class Session:
    """A video+EDL session."""
    id: str
    video_file: str
    edl_file: str
    video_size: int = 0
    duration: float = 0.0
    framerate: float = 30.0
    markers: List[Dict] = field(default_factory=list)
    marker_summary: Dict = field(default_factory=dict)
    clip_regions: Optional[ClipRegions] = None
    # Spectator camera files grouped with this session
    # Each entry: {"prefix": "spec1", "file": "/path/to/spec1_timestamp.mkv", "cameraNumber": 2}
    multicam_files: List[Dict] = field(default_factory=list)


@dataclass
class ScanSettings:
    """Settings for clip extraction."""
    chapter_buffer: float = 0.5  # Seconds before/after chapter markers
    merge_overlapping: bool = True
    enabled_event_types: Optional[List[str]] = None  # None means all enabled
    fall_buffer_extra: float = 2.0  # Extra seconds before/after fall duration


class BulkScanner:
    """Scan folders for video+EDL pairs and build clip regions."""

    def __init__(self):
        self.parser = EdlParser()
        self.sessions: Dict[str, Session] = {}  # Session cache

    def scan_folder(self, source_folder: str, recursive: bool = False,
                     multicam_config: Optional[MulticamConfig] = None) -> List[Session]:
        """
        Scan a folder for MKV+EDL pairs.

        Args:
            source_folder: Path to folder containing recordings
            recursive: Whether to search subdirectories
            multicam_config: Optional multicam configuration for grouping spectator files

        Returns:
            List of Session objects
        """
        sessions = []

        if recursive:
            for root, dirs, files in os.walk(source_folder):
                sessions.extend(self._scan_directory(root, files, multicam_config))
        else:
            files = os.listdir(source_folder)
            sessions.extend(self._scan_directory(source_folder, files, multicam_config))

        # Cache sessions
        for session in sessions:
            self.sessions[session.id] = session

        return sessions

    def _scan_directory(self, directory: str, files: List[str],
                         multicam_config: Optional[MulticamConfig] = None) -> List[Session]:
        """Scan a single directory for MKV+EDL pairs."""
        sessions = []

        # Find all video files
        video_files = [f for f in files if f.lower().endswith(('.mkv', '.mp4', '.mov'))]

        if multicam_config and multicam_config.enabled and multicam_config.tracks:
            prefixes = [t['prefix'] for t in multicam_config.tracks]

            # Separate main files from spectator files
            main_files = []
            spec_files: Dict[str, List[str]] = {}  # prefix -> list of filenames

            for vf in video_files:
                matched_prefix = None
                for prefix in prefixes:
                    if vf.lower().startswith(prefix.lower()):
                        matched_prefix = prefix
                        break
                if matched_prefix:
                    spec_files.setdefault(matched_prefix, []).append(vf)
                else:
                    main_files.append(vf)

            # For each main file, find matching spec files by timestamp/suffix
            for video_file in main_files:
                video_path = os.path.join(directory, video_file)
                base_name = os.path.splitext(video_file)[0]

                # Look for matching EDL file
                edl_path = None
                for suffix in ['.edl', '_chapters.edl']:
                    candidate = os.path.join(directory, base_name + suffix)
                    if os.path.exists(candidate):
                        edl_path = candidate
                        break

                if edl_path:
                    session = self.parse_session(video_path, edl_path)
                    if session:
                        # Match spectator files by comparing the non-prefix part
                        main_suffix = self._extract_suffix(video_file)
                        for prefix in prefixes:
                            for sf in spec_files.get(prefix, []):
                                spec_suffix = self._extract_suffix(sf, prefix)
                                if spec_suffix == main_suffix:
                                    track = next((t for t in multicam_config.tracks
                                                 if t['prefix'] == prefix), None)
                                    session.multicam_files.append({
                                        'prefix': prefix,
                                        'file': os.path.join(directory, sf),
                                        'cameraNumber': track['cameraNumber'] if track else 0
                                    })
                        sessions.append(session)
        else:
            # Non-multicam logic (original)
            for video_file in video_files:
                video_path = os.path.join(directory, video_file)
                base_name = os.path.splitext(video_file)[0]

                # Look for matching EDL file (try both "name.edl" and "name_chapters.edl")
                edl_path = None
                for suffix in ['.edl', '_chapters.edl']:
                    candidate = os.path.join(directory, base_name + suffix)
                    if os.path.exists(candidate):
                        edl_path = candidate
                        break

                if edl_path:
                    session = self.parse_session(video_path, edl_path)
                    if session:
                        sessions.append(session)

        return sessions

    def _extract_suffix(self, filename: str, prefix: str = "") -> str:
        """Extract the part of filename after the prefix for matching.

        e.g. 'spec1_2026-01-15 13-09-49.mkv' with prefix 'spec1' -> '_2026-01-15 13-09-49'
             '2026-01-15 13-09-49.mkv' with prefix '' -> '2026-01-15 13-09-49'
        """
        base = os.path.splitext(filename)[0]
        if prefix and base.lower().startswith(prefix.lower()):
            return base[len(prefix):]
        return base

    def parse_session(self, video_file: str, edl_file: str) -> Optional[Session]:
        """
        Parse a video+EDL pair into a Session.

        Args:
            video_file: Path to video file
            edl_file: Path to EDL file

        Returns:
            Session object or None if parsing fails
        """
        try:
            # Parse EDL file
            result = self.parser.parse(edl_file)
            markers = result['markers']

            # Get video file size
            video_size = os.path.getsize(video_file)

            # Get video duration (estimate from last marker if no probe available)
            duration = 0.0
            if markers:
                duration = max(m['timestampSeconds'] for m in markers) + 60  # Add buffer

            # Categorize markers for summary
            categorized = self.categorize_markers(markers)

            # Count event types among chapter markers (by full text e.g. "Combat - Player Death")
            event_type_counts = {}
            for m in categorized.chapters:
                t = m.get('text', '').strip()
                if t:
                    event_type_counts[t] = event_type_counts.get(t, 0) + 1
            for m in categorized.falls:
                t = m.get('text', '').strip()
                if t:
                    event_type_counts[t] = event_type_counts.get(t, 0) + 1

            # Build marker summary
            marker_summary = {
                'total': len(markers),
                'chapters': len(categorized.chapters),
                'startEndPairs': min(len(categorized.start_markers), len(categorized.end_markers)),
                'pois': len(categorized.pois),
                'falls': len(categorized.falls),
                'cameraMarkers': len(categorized.camera_markers),
                'timelapseBuildMarkers': len(categorized.timelapse_build_markers),
                'eventTypeCounts': event_type_counts
            }

            session = Session(
                id=f"session_{uuid.uuid4().hex[:8]}",
                video_file=video_file,
                edl_file=edl_file,
                video_size=video_size,
                duration=duration,
                framerate=result.get('framerate', 30.0),
                markers=markers,
                marker_summary=marker_summary
            )

            return session

        except Exception as e:
            print(f"Error parsing session {video_file}: {e}")
            return None

    def categorize_markers(self, markers: List[Dict]) -> CategorizedMarkers:
        """
        Categorize markers by type.

        Args:
            markers: List of marker dicts from EDL parser

        Returns:
            CategorizedMarkers with markers sorted by type
        """
        chapters = []
        start_markers = []
        end_markers = []
        pois = []
        falls = []
        new_section_markers = []
        camera_markers = []
        timelapse_build_markers = []

        for marker in markers:
            marker_type = marker.get('type', '').strip().lower()
            marker_text = marker.get('text', '').strip().lower()

            # Director/build markers are analysis metadata, not extractable chapters.
            if marker_type == 'camera':
                camera_markers.append(marker)
            elif marker_type == 'timelapse build':
                timelapse_build_markers.append(marker)
            # Check for Start/End markers
            elif marker_type == 'start' or marker_text == 'start':
                start_markers.append(marker)
            elif marker_type == 'end' or marker_text == 'end':
                end_markers.append(marker)
            # Check for New Section markers
            elif marker_text == 'new section':
                new_section_markers.append(marker)
            # Check for POI markers
            elif 'poi' in marker_type or 'poi' in marker_text:
                pois.append(marker)
            # Check for Fall Landed markers
            elif marker_text.startswith('fall landed'):
                falls.append(marker)
            # Everything else is a chapter marker
            else:
                chapters.append(marker)

        return CategorizedMarkers(
            chapters=chapters,
            start_markers=start_markers,
            end_markers=end_markers,
            pois=pois,
            falls=falls,
            new_section_markers=new_section_markers,
            camera_markers=camera_markers,
            timelapse_build_markers=timelapse_build_markers
        )

    def build_clip_regions(self, markers: List[Dict], settings: ScanSettings,
                           framerate: float = 30.0) -> ClipRegions:
        """
        Build clip regions from markers based on extraction rules.

        Args:
            markers: List of marker dicts
            settings: Extraction settings

        Returns:
            ClipRegions with all regions to extract
        """
        categorized = self.categorize_markers(markers)

        # Filter chapter markers by enabled event types
        chapters = categorized.chapters
        if settings.enabled_event_types is not None:
            chapters = [
                m for m in chapters
                if m.get('text', '').strip() in settings.enabled_event_types
            ]

        # Build chapter regions (buffer before/after, merge overlapping)
        chapter_regions = self._build_chapter_regions(
            chapters,
            settings.chapter_buffer,
            settings.merge_overlapping
        )

        # Build recording regions (Start→End pairs)
        recording_regions = self._build_recording_regions(
            categorized.start_markers,
            categorized.end_markers
        )

        # Build POI regions (duration parsed from marker text)
        poi_regions = self._build_poi_regions(
            categorized.pois
        )

        # Build fall regions (duration-aware buffer)
        fall_regions = self._build_fall_regions(
            categorized.falls,
            settings.fall_buffer_extra
        )

        camera_regions, camera_diagnostics = self._build_camera_regions(
            categorized.camera_markers,
            framerate
        )
        build_events, build_diagnostics = self._build_timelapse_build_events(
            categorized.timelapse_build_markers
        )

        return ClipRegions(
            chapters=chapter_regions,
            recordings=recording_regions,
            pois=poi_regions,
            falls=fall_regions,
            camera_modes=camera_regions,
            camera_diagnostics=camera_diagnostics + build_diagnostics,
            timelapse_build_events=build_events
        )

    def _build_camera_regions(
        self,
        camera_markers: List[Dict],
        framerate: float
    ) -> Tuple[List[CameraRegion], List[CameraDiagnostic]]:
        """Reconstruct mode spans and flag one-frame marker discrepancies."""
        markers = sorted(camera_markers, key=lambda marker: marker['timestampSeconds'])
        regions = []
        diagnostics = []
        fps = framerate if framerate > 0 else 30.0
        previous_sequence = None
        previous_render = None

        for index, marker in enumerate(markers):
            payload = marker.get('structured') or {}
            mode = payload.get('mode', '').lower()
            timestamp = marker['timestampSeconds']
            if mode not in ('normal', 'face', 'timelapse'):
                diagnostics.append(CameraDiagnostic(
                    code='invalid_camera_marker',
                    severity='warning',
                    message=f"Camera marker has unknown mode '{mode or 'missing'}'",
                    timestamp=timestamp,
                    node_id=payload.get('node'),
                    build_id=payload.get('build')
                ))
                continue

            sequence = self._optional_int(payload.get('seq'))
            render_sequence = self._optional_int(payload.get('render'))
            expected_frames = self._optional_int(payload.get('expectedFrames'))
            if mode == 'timelapse' and expected_frames is None:
                expected_frames = 1

            if sequence is not None and previous_sequence is not None \
                    and sequence != previous_sequence + 1:
                diagnostics.append(CameraDiagnostic(
                    code='camera_sequence_gap',
                    severity='warning',
                    message=f"Camera marker sequence jumped from {previous_sequence} to {sequence}",
                    timestamp=timestamp,
                    node_id=payload.get('node'),
                    build_id=payload.get('build')
                ))
            if render_sequence is not None and previous_render is not None \
                    and render_sequence <= previous_render:
                diagnostics.append(CameraDiagnostic(
                    code='non_monotonic_render_sequence',
                    severity='warning',
                    message=f"Render sequence did not advance after {previous_render}",
                    timestamp=timestamp,
                    node_id=payload.get('node'),
                    build_id=payload.get('build')
                ))

            next_marker = markers[index + 1] if index + 1 < len(markers) else None
            end = next_marker['timestampSeconds'] if next_marker else timestamp
            actual_frames = max(0, round((end - timestamp) * fps)) if next_marker else None
            next_payload = next_marker.get('structured') or {} if next_marker else {}
            next_render = self._optional_int(next_payload.get('render'))
            render_frames = (next_render - render_sequence) \
                if render_sequence is not None and next_render is not None else None

            region = CameraRegion(
                start=timestamp,
                end=end,
                mode=mode,
                node_id=payload.get('node'),
                build_id=payload.get('build'),
                build_mode=payload.get('buildMode'),
                expected_frames=expected_frames,
                actual_frames=actual_frames,
                render_frames=render_frames,
                marker_sequence=sequence,
                render_sequence=render_sequence,
                open_ended=next_marker is None
            )
            regions.append(region)

            if mode == 'timelapse':
                if next_marker is None:
                    diagnostics.append(CameraDiagnostic(
                        code='missing_camera_return_marker',
                        severity='warning',
                        message='Timelapse marker has no following camera-mode marker',
                        timestamp=timestamp,
                        node_id=payload.get('node'),
                        build_id=payload.get('build'),
                        expected_frames=expected_frames
                    ))
                else:
                    if render_frames is not None and render_frames != expected_frames:
                        diagnostics.append(CameraDiagnostic(
                            code='render_frame_span_mismatch',
                            severity='warning',
                            message=f"Timelapse spans {render_frames} render frames; expected {expected_frames}",
                            timestamp=timestamp,
                            node_id=payload.get('node'),
                            build_id=payload.get('build'),
                            expected_frames=expected_frames,
                            actual_frames=render_frames
                        ))
                    if actual_frames != expected_frames:
                        diagnostics.append(CameraDiagnostic(
                            code='marker_timecode_span_mismatch',
                            severity='warning',
                            message=(f"EDL markers span {actual_frames} frames at {fps:g} fps; "
                                     f"expected {expected_frames}"),
                            timestamp=timestamp,
                            node_id=payload.get('node'),
                            build_id=payload.get('build'),
                            expected_frames=expected_frames,
                            actual_frames=actual_frames
                        ))

            if sequence is not None:
                previous_sequence = sequence
            if render_sequence is not None:
                previous_render = render_sequence

        return regions, diagnostics

    def _build_timelapse_build_events(
        self,
        markers: List[Dict]
    ) -> Tuple[List[Dict], List[CameraDiagnostic]]:
        """Normalize golem lifecycle markers and validate reconstructable transitions."""
        events = []
        diagnostics = []
        lifecycle_by_build = {}
        allowed_transitions = {
            'start': {'pause', 'complete', 'stop'},
            'resume': {'pause', 'complete', 'stop'},
            'pause': {'resume', 'stop'},
            'complete': set(),
            'stop': set()
        }

        for marker in sorted(markers, key=lambda item: item['timestampSeconds']):
            payload = marker.get('structured') or {}
            timestamp = marker['timestampSeconds']
            state = payload.get('state', '').lower()
            build_id = payload.get('build')
            node_id = payload.get('node')
            if state not in allowed_transitions or not build_id:
                diagnostics.append(CameraDiagnostic(
                    code='invalid_build_marker',
                    severity='warning',
                    message='Timelapse build marker is missing a valid state or build id',
                    timestamp=timestamp,
                    node_id=node_id,
                    build_id=build_id
                ))
                continue

            previous = lifecycle_by_build.get(build_id)
            if previous and state not in allowed_transitions[previous['state']]:
                diagnostics.append(CameraDiagnostic(
                    code='invalid_build_transition',
                    severity='warning',
                    message=f"Build state changed from {previous['state']} to {state}",
                    timestamp=timestamp,
                    node_id=node_id,
                    build_id=build_id
                ))
            if previous and previous.get('nodeId') and node_id and previous['nodeId'] != node_id:
                diagnostics.append(CameraDiagnostic(
                    code='build_node_changed',
                    severity='warning',
                    message='Build session changed timelapse node id',
                    timestamp=timestamp,
                    node_id=node_id,
                    build_id=build_id
                ))

            event = {
                'timestamp': timestamp,
                'state': state,
                'buildId': build_id,
                'nodeId': node_id,
                'buildMode': payload.get('mode')
            }
            events.append(event)
            lifecycle_by_build[build_id] = event

        for build_id, event in lifecycle_by_build.items():
            if event['state'] in ('start', 'resume'):
                diagnostics.append(CameraDiagnostic(
                    code='open_build_session',
                    severity='info',
                    message='Build session has no pause, completion, or stop marker before the EDL ends',
                    timestamp=event['timestamp'],
                    node_id=event.get('nodeId'),
                    build_id=build_id
                ))

        return events, diagnostics

    @staticmethod
    def _optional_int(value) -> Optional[int]:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def _build_chapter_regions(
        self,
        chapters: List[Dict],
        buffer: float,
        merge_overlapping: bool
    ) -> List[ClipRegion]:
        """Build chapter clip regions with buffer and optional merging."""
        if not chapters:
            return []

        # Create initial regions with buffer
        regions = []
        for marker in chapters:
            timestamp = marker['timestampSeconds']
            start = max(0, timestamp - buffer)
            end = timestamp + buffer

            regions.append(ClipRegion(
                start=start,
                end=end,
                markers=[marker['text']],
                region_type="chapter",
                label=marker['text'],
                marker_offset=timestamp - start
            ))

        # Sort by start time
        regions.sort(key=lambda r: r.start)

        return regions

    def _build_recording_regions(
        self,
        start_markers: List[Dict],
        end_markers: List[Dict]
    ) -> List[ClipRegion]:
        """Build recording regions from Start→End pairs."""
        pairs = self.pair_start_end_markers(start_markers, end_markers)

        regions = []
        for i, pair in enumerate(pairs):
            regions.append(ClipRegion(
                start=pair.start_time,
                end=pair.end_time,
                markers=[pair.start_marker, pair.end_marker],
                region_type="recording",
                label=f"Recording {i + 1}"
            ))

        return regions

    def _build_poi_regions(
        self,
        pois: List[Dict]
    ) -> List[ClipRegion]:
        """Build POI regions with duration parsed from marker text.

        Parses "POI Xm" to get X minutes. Falls back to 180s (3 min).
        After building individual regions, merges overlapping ones.
        """
        regions = []

        for marker in pois:
            timestamp = marker['timestampSeconds']
            text = marker.get('text', '')

            # Parse duration from text: "POI 1m", "POI 3m", "POI 5m", etc.
            match = re.search(r'POI\s+(\d+)m', text, re.IGNORECASE)
            duration = float(match.group(1)) * 60 if match else 180.0

            start = max(0, timestamp - duration)
            end = timestamp

            regions.append(ClipRegion(
                start=start,
                end=end,
                markers=[text],
                region_type="poi",
                label=text
            ))

        if not regions:
            return regions

        # Sort by start time and merge overlapping regions
        regions.sort(key=lambda r: r.start)
        merged = [regions[0]]
        for current in regions[1:]:
            last = merged[-1]
            if current.start <= last.end:
                last.end = max(last.end, current.end)
                last.markers.extend(current.markers)
                last.label = " + ".join(last.markers)
            else:
                merged.append(current)

        return merged

    def _build_fall_regions(
        self,
        falls: List[Dict],
        extra_buffer: float
    ) -> List[ClipRegion]:
        """Build fall clip regions with duration-aware buffering.

        Parses the fall duration from marker text like "Fall Landed (3.0s)"
        and creates a clip that covers the full fall plus extra context.
        """
        if not falls:
            return []

        regions = []
        for marker in falls:
            timestamp = marker['timestampSeconds']
            text = marker.get('text', '')

            # Parse fall duration from text: "Fall Landed (X.Xs)"
            match = re.search(r'\(([\d.]+)s\)', text)
            fall_duration = float(match.group(1)) if match else 3.0

            # Clip: fall_duration + extra before landing, extra after landing
            start = max(0, timestamp - fall_duration - extra_buffer)
            end = timestamp + extra_buffer

            regions.append(ClipRegion(
                start=start,
                end=end,
                markers=[text],
                region_type="fall",
                label=text,
                marker_offset=timestamp - start
            ))

        regions.sort(key=lambda r: r.start)
        return regions

    def merge_overlapping_regions(self, regions: List[ClipRegion]) -> List[ClipRegion]:
        """
        Merge overlapping clip regions.

        Args:
            regions: List of ClipRegion objects (must be sorted by start time)

        Returns:
            List of merged ClipRegion objects
        """
        if not regions:
            return []

        merged = [regions[0]]

        for current in regions[1:]:
            last = merged[-1]

            # Check if regions overlap or touch
            if current.start <= last.end:
                # Merge: extend end time and combine markers
                last.end = max(last.end, current.end)
                last.markers.extend(current.markers)
                last.label = f"{len(last.markers)} markers"
            else:
                merged.append(current)

        return merged

    def pair_start_end_markers(
        self,
        start_markers: List[Dict],
        end_markers: List[Dict]
    ) -> List[StartEndPair]:
        """
        Pair Start markers with their corresponding End markers.

        For each End marker, look back for the most recent Start marker.

        Args:
            start_markers: List of Start marker dicts
            end_markers: List of End marker dicts

        Returns:
            List of StartEndPair objects
        """
        if not start_markers or not end_markers:
            return []

        # Sort both lists by timestamp
        starts = sorted(start_markers, key=lambda m: m['timestampSeconds'])
        ends = sorted(end_markers, key=lambda m: m['timestampSeconds'])

        pairs = []
        used_starts = set()

        for end_marker in ends:
            end_time = end_marker['timestampSeconds']
            end_instance = end_marker.get('instance')

            # Find the most recent Start marker before this End from the same
            # Minecraft instance. Legacy untagged markers pair with each other.
            best_start = None
            for start_marker in reversed(starts):
                start_time = start_marker['timestampSeconds']
                start_id = id(start_marker)

                if (start_marker.get('instance') == end_instance and
                        start_time < end_time and start_id not in used_starts):
                    best_start = start_marker
                    break

            if best_start:
                used_starts.add(id(best_start))
                pairs.append(StartEndPair(
                    start_time=best_start['timestampSeconds'],
                    end_time=end_time,
                    start_marker=best_start['text'],
                    end_marker=end_marker['text']
                ))

        # Sort pairs by start time
        pairs.sort(key=lambda p: p.start_time)

        return pairs

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a cached session by ID."""
        return self.sessions.get(session_id)

    def analyze_session(self, session_id: str, settings: ScanSettings) -> Optional[Dict]:
        """
        Analyze a session and calculate clip regions.

        Args:
            session_id: Session ID from scan
            settings: Extraction settings

        Returns:
            Dict with clip regions and estimates
        """
        session = self.get_session(session_id)
        if not session:
            return None

        # Build clip regions
        clip_regions = self.build_clip_regions(session.markers, settings, session.framerate)
        session.clip_regions = clip_regions

        # Calculate estimates
        total_chapter_duration = sum(r.end - r.start for r in clip_regions.chapters)
        total_recording_duration = sum(r.end - r.start for r in clip_regions.recordings)
        total_poi_duration = sum(r.end - r.start for r in clip_regions.pois)
        total_fall_duration = sum(r.end - r.start for r in clip_regions.falls)
        total_extract_duration = total_chapter_duration + total_recording_duration + total_poi_duration + total_fall_duration

        # Estimate output size (rough: same bitrate as original)
        if session.duration > 0:
            bytes_per_second = session.video_size / session.duration
            estimated_output_size = int(total_extract_duration * bytes_per_second)
            reduction_percent = 100 * (1 - total_extract_duration / session.duration)
        else:
            estimated_output_size = 0
            reduction_percent = 0

        return {
            'sessionId': session_id,
            'clipRegions': {
                'chapters': [self._region_to_dict(r) for r in clip_regions.chapters],
                'recordings': [self._region_to_dict(r) for r in clip_regions.recordings],
                'pois': [self._region_to_dict(r) for r in clip_regions.pois],
                'falls': [self._region_to_dict(r) for r in clip_regions.falls],
                'cameraModes': [self._camera_region_to_dict(r) for r in clip_regions.camera_modes],
                'cameraDiagnostics': [self._camera_diagnostic_to_dict(d)
                                      for d in clip_regions.camera_diagnostics],
                'timelapseBuildEvents': clip_regions.timelapse_build_events
            },
            'estimatedOutputSize': self._format_size(estimated_output_size),
            'estimatedReduction': f"{reduction_percent:.0f}%"
        }

    def _region_to_dict(self, region: ClipRegion) -> Dict:
        """Convert ClipRegion to dict for JSON serialization."""
        return {
            'start': region.start,
            'end': region.end,
            'markers': region.markers,
            'type': region.region_type,
            'label': region.label,
            'markerOffset': region.marker_offset
        }

    def _camera_region_to_dict(self, region: CameraRegion) -> Dict:
        return {
            'start': region.start,
            'end': region.end,
            'mode': region.mode,
            'nodeId': region.node_id,
            'buildId': region.build_id,
            'buildMode': region.build_mode,
            'expectedFrames': region.expected_frames,
            'actualFrames': region.actual_frames,
            'renderFrames': region.render_frames,
            'markerSequence': region.marker_sequence,
            'renderSequence': region.render_sequence,
            'openEnded': region.open_ended
        }

    def _camera_diagnostic_to_dict(self, diagnostic: CameraDiagnostic) -> Dict:
        return {
            'code': diagnostic.code,
            'severity': diagnostic.severity,
            'message': diagnostic.message,
            'timestamp': diagnostic.timestamp,
            'nodeId': diagnostic.node_id,
            'buildId': diagnostic.build_id,
            'expectedFrames': diagnostic.expected_frames,
            'actualFrames': diagnostic.actual_frames
        }

    def _format_size(self, size_bytes: int) -> str:
        """Format bytes as human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    def session_to_dict(self, session: Session) -> Dict:
        """Convert Session to dict for JSON serialization."""
        d = {
            'id': session.id,
            'videoFile': session.video_file,
            'edlFile': session.edl_file,
            'videoSize': session.video_size,
            'duration': session.duration,
            'framerate': session.framerate,
            'markerSummary': session.marker_summary
        }
        if session.multicam_files:
            d['multicamFiles'] = session.multicam_files
        return d
