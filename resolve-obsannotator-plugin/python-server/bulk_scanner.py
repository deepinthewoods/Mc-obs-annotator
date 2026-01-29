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
    pois: List[Dict]  # "POI A" and "POI B" markers
    falls: List[Dict]  # "Fall Landed" markers


@dataclass
class ClipRegions:
    """All clip regions for a session."""
    chapters: List[ClipRegion] = field(default_factory=list)
    recordings: List[ClipRegion] = field(default_factory=list)
    pois: List[ClipRegion] = field(default_factory=list)
    falls: List[ClipRegion] = field(default_factory=list)


@dataclass
class Session:
    """A video+EDL session."""
    id: str
    video_file: str
    edl_file: str
    video_size: int = 0
    duration: float = 0.0
    markers: List[Dict] = field(default_factory=list)
    marker_summary: Dict = field(default_factory=dict)
    clip_regions: Optional[ClipRegions] = None


@dataclass
class ScanSettings:
    """Settings for clip extraction."""
    chapter_buffer: float = 0.5  # Seconds before/after chapter markers
    poi_duration: float = 180.0  # 3 minutes for POI markers
    merge_overlapping: bool = True
    enabled_event_types: Optional[List[str]] = None  # None means all enabled
    fall_buffer_extra: float = 2.0  # Extra seconds before/after fall duration


class BulkScanner:
    """Scan folders for video+EDL pairs and build clip regions."""

    def __init__(self):
        self.parser = EdlParser()
        self.sessions: Dict[str, Session] = {}  # Session cache

    def scan_folder(self, source_folder: str, recursive: bool = False) -> List[Session]:
        """
        Scan a folder for MKV+EDL pairs.

        Args:
            source_folder: Path to folder containing recordings
            recursive: Whether to search subdirectories

        Returns:
            List of Session objects
        """
        sessions = []

        if recursive:
            for root, dirs, files in os.walk(source_folder):
                sessions.extend(self._scan_directory(root, files))
        else:
            files = os.listdir(source_folder)
            sessions.extend(self._scan_directory(source_folder, files))

        # Cache sessions
        for session in sessions:
            self.sessions[session.id] = session

        return sessions

    def _scan_directory(self, directory: str, files: List[str]) -> List[Session]:
        """Scan a single directory for MKV+EDL pairs."""
        sessions = []

        # Find all video files
        video_files = [f for f in files if f.lower().endswith(('.mkv', '.mp4', '.mov'))]

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
                'eventTypeCounts': event_type_counts
            }

            session = Session(
                id=f"session_{uuid.uuid4().hex[:8]}",
                video_file=video_file,
                edl_file=edl_file,
                video_size=video_size,
                duration=duration,
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

        for marker in markers:
            marker_type = marker.get('type', '').strip().lower()
            marker_text = marker.get('text', '').strip().lower()

            # Check for Start/End markers
            if marker_type == 'start' or marker_text == 'start':
                start_markers.append(marker)
            elif marker_type == 'end' or marker_text == 'end':
                end_markers.append(marker)
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
            falls=falls
        )

    def build_clip_regions(self, markers: List[Dict], settings: ScanSettings) -> ClipRegions:
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

        # Build POI regions (3 minutes before marker)
        poi_regions = self._build_poi_regions(
            categorized.pois,
            settings.poi_duration
        )

        # Build fall regions (duration-aware buffer)
        fall_regions = self._build_fall_regions(
            categorized.falls,
            settings.fall_buffer_extra
        )

        return ClipRegions(
            chapters=chapter_regions,
            recordings=recording_regions,
            pois=poi_regions,
            falls=fall_regions
        )

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
        pois: List[Dict],
        poi_duration: float
    ) -> List[ClipRegion]:
        """Build POI regions (duration before marker)."""
        regions = []

        for marker in pois:
            timestamp = marker['timestampSeconds']
            start = max(0, timestamp - poi_duration)
            end = timestamp

            regions.append(ClipRegion(
                start=start,
                end=end,
                markers=[marker['text']],
                region_type="poi",
                label=marker['text']
            ))

        return regions

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

            # Find the most recent Start marker before this End
            best_start = None
            for start_marker in reversed(starts):
                start_time = start_marker['timestampSeconds']
                start_id = id(start_marker)

                if start_time < end_time and start_id not in used_starts:
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
        clip_regions = self.build_clip_regions(session.markers, settings)
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
                'falls': [self._region_to_dict(r) for r in clip_regions.falls]
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

    def _format_size(self, size_bytes: int) -> str:
        """Format bytes as human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    def session_to_dict(self, session: Session) -> Dict:
        """Convert Session to dict for JSON serialization."""
        return {
            'id': session.id,
            'videoFile': session.video_file,
            'edlFile': session.edl_file,
            'videoSize': session.video_size,
            'duration': session.duration,
            'markerSummary': session.marker_summary
        }
