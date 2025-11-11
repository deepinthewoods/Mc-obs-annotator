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
