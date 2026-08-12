import os
import random
from typing import List, Dict, Any, Optional


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

    def read_timeline_clips(self, timeline) -> List[Dict]:
        """
        Read all clips from the current timeline with their markers and event info.

        Returns:
            List of clip dicts with index, name, event_type, marker info.
        """
        clips = timeline.GetItemListInTrack("video", 1)
        if not clips:
            return []

        framerate = float(timeline.GetSetting('timelineFrameRate'))
        result = []

        # Also read timeline markers
        timeline_markers = timeline.GetMarkers() or {}

        for idx, clip in enumerate(clips):
            clip_name = clip.GetName()
            start_frame = clip.GetStart()
            end_frame = clip.GetEnd()
            duration_frames = end_frame - start_frame
            duration_sec = duration_frames / framerate

            # Infer event type from filename
            # Filenames follow pattern: EventType_NNN.mkv
            base = os.path.splitext(clip_name)[0]
            # Strip trailing _NNN
            parts = base.rsplit('_', 1)
            event_type = parts[0] if len(parts) == 2 and parts[1].isdigit() else base

            # Check for markers within clip range
            clip_markers = []
            for frame_id, marker_data in timeline_markers.items():
                if start_frame <= frame_id < end_frame:
                    clip_markers.append({
                        'frame': frame_id,
                        'name': marker_data.get('name', ''),
                        'color': marker_data.get('color', ''),
                        'note': marker_data.get('note', '')
                    })

            result.append({
                'index': idx,
                'name': clip_name,
                'eventType': event_type,
                'startFrame': start_frame,
                'endFrame': end_frame,
                'duration': round(duration_sec, 3),
                'markers': clip_markers
            })

        return result

    def generate_from_timeline_clips(
        self,
        source_timeline,
        clip_indices: List[int],
        bpm: int,
        note_division: str,
        options: Dict,
        framerate: float
    ) -> Dict[str, Any]:
        """
        Generate a BPM-synced supercut from selected clips in an existing timeline.

        Args:
            source_timeline: The source Resolve timeline object
            clip_indices: Indices of clips to include
            bpm: Beats per minute
            note_division: Note division string
            options: Generation options
            framerate: Timeline framerate

        Returns:
            Result dict with success, timeline_name, clips_added, duration_seconds
        """
        beat_interval = 60.0 / bpm
        clip_duration = self._calculate_clip_duration(bpm, note_division)
        half_duration = clip_duration / 2.0

        # Get clips from source timeline
        all_clips = source_timeline.GetItemListInTrack("video", 1)
        if not all_clips:
            return {'success': False, 'error': 'No clips in source timeline'}

        # Get timeline markers for event center detection
        timeline_markers = source_timeline.GetMarkers() or {}

        # Gather selected clips with their media pool items and event center frames
        selected = []
        for idx in clip_indices:
            if idx < 0 or idx >= len(all_clips):
                continue
            clip = all_clips[idx]
            media_item = clip.GetMediaPoolItem()
            if not media_item:
                continue

            start_frame = clip.GetStart()
            end_frame = clip.GetEnd()
            clip_mid = (start_frame + end_frame) / 2.0

            # Look for a marker within the clip range; use it as event center
            event_frame = clip_mid  # default: clip center
            for frame_id, _ in timeline_markers.items():
                if start_frame <= frame_id < end_frame:
                    event_frame = frame_id
                    break

            # Compute the event position relative to clip's own media
            # source_in is the frame within the media pool item where the clip starts
            source_in = clip.GetLeftOffset()
            event_in_media = source_in + (event_frame - start_frame)

            selected.append({
                'media_item': media_item,
                'event_frame': event_in_media,
                'name': clip.GetName()
            })

        if options.get('randomize', False):
            random.shuffle(selected)

        if not selected:
            return {'success': False, 'error': 'No valid clips selected'}

        # Create new timeline
        timeline_name = options.get('output_timeline_name', f'Supercut_{bpm}BPM')
        new_timeline = self.media_pool.CreateEmptyTimeline(timeline_name)
        if not new_timeline:
            return {'success': False, 'error': 'Failed to create timeline'}

        new_framerate = float(new_timeline.GetSetting('timelineFrameRate'))
        clips_added = 0
        beat_position = 0.0

        for sel in selected:
            event_frame = sel['event_frame']
            start_f = int(event_frame - half_duration * new_framerate)
            end_f = int(event_frame + half_duration * new_framerate)
            if start_f < 0:
                start_f = 0
                end_f = int(clip_duration * new_framerate)

            clip_info = {
                "mediaPoolItem": sel['media_item'],
                "startFrame": start_f,
                "endFrame": end_f,
                "trackIndex": 1
            }

            result = self.media_pool.AppendToTimeline([clip_info])
            if result:
                clips_added += 1

                if options.get('add_beat_markers', True):
                    beat_frame = int(beat_position * new_framerate)
                    new_timeline.AddMarker(
                        frameId=beat_frame,
                        color='Blue',
                        name=sel['name'],
                        note=f"Beat {clips_added}",
                        duration=1
                    )

            beat_position += beat_interval

        if options.get('add_crossfades', False):
            self._add_crossfades(
                new_timeline,
                options.get('crossfade_duration', 0.2),
                new_framerate
            )

        return {
            'success': True,
            'timeline_name': timeline_name,
            'clips_added': clips_added,
            'duration_seconds': beat_position
        }
