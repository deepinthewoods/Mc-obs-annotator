"""
Timeline Creator - Create DaVinci Resolve timelines from extracted clips.
"""

import json
import os
from typing import List, Dict, Optional, Any


class TimelineCreator:
    """Create DaVinci Resolve timelines from extracted clips."""

    def __init__(self, resolve, project):
        """
        Initialize timeline creator.

        Args:
            resolve: DaVinci Resolve scripting app
            project: Current Resolve project
        """
        self.resolve = resolve
        self.project = project
        self.media_pool = project.GetMediaPool()

    def import_clips_to_pool(
        self,
        clip_folder: str,
        create_bin: bool = True,
        bin_name: Optional[str] = None
    ) -> List[Any]:
        """
        Import clips from a folder into the media pool.

        Args:
            clip_folder: Path to folder containing clips
            create_bin: Whether to create a bin for the clips
            bin_name: Name for the bin (defaults to folder name)

        Returns:
            List of MediaPoolItem objects
        """
        if not os.path.isdir(clip_folder):
            return []

        # Get all video files in folder (including subfolders)
        video_files = []
        for root, dirs, files in os.walk(clip_folder):
            for file in files:
                if file.lower().endswith(('.mkv', '.mp4', '.mov', '.avi')):
                    video_files.append(os.path.join(root, file))

        if not video_files:
            return []

        # Create or select bin
        if create_bin:
            root_folder = self.media_pool.GetRootFolder()
            actual_bin_name = bin_name or os.path.basename(clip_folder)

            # Try to create bin (will use existing if same name)
            bin_folder = self.media_pool.AddSubFolder(root_folder, actual_bin_name)
            if bin_folder:
                self.media_pool.SetCurrentFolder(bin_folder)

        # Import all clips
        items = self.media_pool.ImportMedia(video_files)
        return items if items else []

    def create_timeline(
        self,
        name: str,
        clips: List[Any],
        framerate: float = 30.0
    ) -> Optional[Any]:
        """
        Create a timeline with the given clips.

        Args:
            name: Timeline name
            clips: List of MediaPoolItem objects
            framerate: Timeline framerate

        Returns:
            Timeline object or None
        """
        if not clips:
            return None

        # Create empty timeline
        timeline = self.media_pool.CreateEmptyTimeline(name)
        if not timeline:
            return None

        # Add clips to timeline in order
        self.add_clips_to_timeline(timeline, clips)

        return timeline

    def add_clips_to_timeline(
        self,
        timeline,
        clips: List[Any],
        track_index: int = 1
    ) -> int:
        """
        Add clips to a timeline sequentially.

        Args:
            timeline: Timeline object
            clips: List of MediaPoolItem objects
            track_index: Video track index (1-based)

        Returns:
            Number of clips successfully added
        """
        added = 0

        for clip in clips:
            clip_info = {
                "mediaPoolItem": clip,
                "trackIndex": track_index
            }

            result = self.media_pool.AppendToTimeline([clip_info])
            if result:
                added += 1

        return added

    @staticmethod
    def _load_clip_metadata(clip_path: str) -> Optional[Dict]:
        """Load sidecar JSON metadata for a clip file."""
        sidecar_path = os.path.splitext(clip_path)[0] + '.json'
        if not os.path.isfile(sidecar_path):
            return None
        try:
            with open(sidecar_path, 'r') as f:
                return json.load(f)
        except Exception:
            return None

    def add_clips_to_timeline_trimmed(
        self,
        timeline,
        clips: List[Any],
        clip_paths: List[str],
        target_duration: float,
        track_index: int = 1
    ) -> int:
        """
        Add clips trimmed to target_duration centered on the event marker.

        Args:
            timeline: Timeline object
            clips: List of MediaPoolItem objects
            clip_paths: Corresponding file paths for sidecar lookup
            target_duration: Desired clip duration in seconds
            track_index: Video track index (1-based)

        Returns:
            Number of clips successfully added
        """
        added = 0
        framerate = float(timeline.GetSetting('timelineFrameRate'))
        half_dur = target_duration / 2.0
        timeline_frame_cursor = 0

        for clip, path in zip(clips, clip_paths):
            meta = self._load_clip_metadata(path)
            marker_offset = meta.get('markerOffset', 0.0) if meta else 0.0

            # Calculate trim window centered on the event
            event_sec = marker_offset
            trim_start = max(0.0, event_sec - half_dur)
            trim_end = trim_start + target_duration

            start_frame = int(trim_start * framerate)
            end_frame = int(trim_end * framerate)

            clip_info = {
                "mediaPoolItem": clip,
                "startFrame": start_frame,
                "endFrame": end_frame,
                "trackIndex": track_index
            }

            result = self.media_pool.AppendToTimeline([clip_info])
            if result:
                added += 1

                # Add a red marker at the event point on the timeline
                event_frame_in_clip = int(event_sec * framerate) - start_frame
                marker_frame_on_timeline = timeline_frame_cursor + event_frame_in_clip
                label = meta.get('label', '') if meta else ''
                timeline.AddMarker(
                    frameId=marker_frame_on_timeline,
                    color='Red',
                    name=label,
                    note=f"Event: {label}",
                    duration=1
                )

                # Advance cursor by the trimmed clip length
                timeline_frame_cursor += (end_frame - start_frame)

        return added

    def create_session_timelines(
        self,
        session_folder: str,
        session_name: str,
        chapter_buffer: float = 0.5
    ) -> List[Dict]:
        """
        Create all timelines for a session's extracted clips.

        Creates:
        - Chapters timeline (all chapter clips concatenated)
        - Recording timelines (one per recording)
        - POI timelines (one per POI)

        Args:
            session_folder: Path to extracted clips folder (with chapters/, recordings/, pois/ subfolders)
            session_name: Base name for timelines

        Returns:
            List of dicts with timeline info
        """
        timelines_created = []

        # Create bin for this session
        root_folder = self.media_pool.GetRootFolder()
        session_bin = self.media_pool.AddSubFolder(root_folder, session_name)
        if session_bin:
            self.media_pool.SetCurrentFolder(session_bin)

        # 1. Import and create Chapters timeline
        chapters_folder = os.path.join(session_folder, "chapters")
        if os.path.isdir(chapters_folder):
            # Create parent chapters bin
            chapters_bin = self.media_pool.AddSubFolder(session_bin, "Chapters")
            if chapters_bin:
                self.media_pool.SetCurrentFolder(chapters_bin)

            # Detect event-type subdirectories
            subdirs = [d for d in os.listdir(chapters_folder)
                       if os.path.isdir(os.path.join(chapters_folder, d))]

            all_chapter_items = []
            if subdirs:
                # Import clips per event-type subdirectory into sub-bins
                subdirs.sort()
                for subdir in subdirs:
                    subdir_path = os.path.join(chapters_folder, subdir)
                    sub_files = self._get_sorted_clips(subdir_path)
                    if sub_files and chapters_bin:
                        sub_bin = self.media_pool.AddSubFolder(chapters_bin, subdir)
                        if sub_bin:
                            self.media_pool.SetCurrentFolder(sub_bin)
                        items = self.media_pool.ImportMedia(sub_files)
                        if items:
                            all_chapter_items.extend(items)
            else:
                # Flat chapters folder (legacy)
                chapter_files = self._get_sorted_clips(chapters_folder)
                if chapter_files:
                    all_chapter_items = self.media_pool.ImportMedia(chapter_files) or []

            if all_chapter_items:
                # Set current folder back to chapters bin for timeline creation
                if chapters_bin:
                    self.media_pool.SetCurrentFolder(chapters_bin)

                # Collect all chapter clip paths for sidecar lookup
                all_chapter_paths = []
                if subdirs:
                    for subdir in subdirs:
                        subdir_path = os.path.join(chapters_folder, subdir)
                        all_chapter_paths.extend(self._get_sorted_clips(subdir_path))
                else:
                    all_chapter_paths = self._get_sorted_clips(chapters_folder)

                timeline_name = f"{session_name} - Chapters"
                target_duration = 2 * chapter_buffer  # e.g. 1.0s for 0.5s buffer
                timeline = self.media_pool.CreateEmptyTimeline(timeline_name)
                if timeline:
                    self.add_clips_to_timeline_trimmed(
                        timeline,
                        all_chapter_items,
                        all_chapter_paths,
                        target_duration
                    )
                    duration = self._get_timeline_duration(timeline)
                    timelines_created.append({
                        "name": timeline_name,
                        "clips": len(all_chapter_items),
                        "duration": self._format_duration(duration)
                    })

        # 2. Import and create Falls timeline (separate from chapters, not in supercuts)
        falls_folder = os.path.join(session_folder, "falls")
        if os.path.isdir(falls_folder):
            falls_bin = self.media_pool.AddSubFolder(session_bin, "Falls")
            if falls_bin:
                self.media_pool.SetCurrentFolder(falls_bin)

            # Detect event-type subdirectories under falls/
            fall_subdirs = [d for d in os.listdir(falls_folder)
                           if os.path.isdir(os.path.join(falls_folder, d))]

            all_fall_items = []
            all_fall_paths = []
            if fall_subdirs:
                fall_subdirs.sort()
                for subdir in fall_subdirs:
                    subdir_path = os.path.join(falls_folder, subdir)
                    sub_files = self._get_sorted_clips(subdir_path)
                    if sub_files and falls_bin:
                        sub_bin = self.media_pool.AddSubFolder(falls_bin, subdir)
                        if sub_bin:
                            self.media_pool.SetCurrentFolder(sub_bin)
                        items = self.media_pool.ImportMedia(sub_files)
                        if items:
                            all_fall_items.extend(items)
                            all_fall_paths.extend(sub_files)
            else:
                fall_files = self._get_sorted_clips(falls_folder)
                if fall_files:
                    all_fall_items = self.media_pool.ImportMedia(fall_files) or []
                    all_fall_paths = fall_files

            if all_fall_items:
                if falls_bin:
                    self.media_pool.SetCurrentFolder(falls_bin)

                timeline_name = f"{session_name} - Falls"
                # Use full clip duration for falls (no trimming)
                timeline = self.media_pool.CreateEmptyTimeline(timeline_name)
                if timeline:
                    self.add_clips_to_timeline(timeline, all_fall_items)
                    duration = self._get_timeline_duration(timeline)
                    timelines_created.append({
                        "name": timeline_name,
                        "clips": len(all_fall_items),
                        "duration": self._format_duration(duration)
                    })

        # 3. Import and create Recording timelines
        recordings_folder = os.path.join(session_folder, "recordings")
        if os.path.isdir(recordings_folder):
            recording_files = self._get_sorted_clips(recordings_folder)

            if recording_files:
                # Create recordings bin
                recordings_bin = self.media_pool.AddSubFolder(session_bin, "Recordings")
                if recordings_bin:
                    self.media_pool.SetCurrentFolder(recordings_bin)

                for i, recording_file in enumerate(recording_files, 1):
                    items = self.media_pool.ImportMedia([recording_file])
                    if items:
                        timeline_name = f"{session_name} - Recording {i}"
                        timeline = self.create_timeline(timeline_name, items)
                        if timeline:
                            duration = self._get_timeline_duration(timeline)
                            timelines_created.append({
                                "name": timeline_name,
                                "clips": 1,
                                "duration": self._format_duration(duration)
                            })

        # 3. Import and create POI timelines
        pois_folder = os.path.join(session_folder, "pois")
        if os.path.isdir(pois_folder):
            poi_files = self._get_sorted_clips(pois_folder)

            if poi_files:
                # Create POIs bin
                pois_bin = self.media_pool.AddSubFolder(session_bin, "POIs")
                if pois_bin:
                    self.media_pool.SetCurrentFolder(pois_bin)

                for i, poi_file in enumerate(poi_files, 1):
                    items = self.media_pool.ImportMedia([poi_file])
                    if items:
                        timeline_name = f"{session_name} - POI {i}"
                        timeline = self.create_timeline(timeline_name, items)
                        if timeline:
                            duration = self._get_timeline_duration(timeline)
                            timelines_created.append({
                                "name": timeline_name,
                                "clips": 1,
                                "duration": self._format_duration(duration)
                            })

        return timelines_created

    def _get_sorted_clips(self, folder: str) -> List[str]:
        """Get clip files from a folder, sorted by name."""
        if not os.path.isdir(folder):
            return []

        files = []
        for file in os.listdir(folder):
            if file.lower().endswith(('.mkv', '.mp4', '.mov', '.avi')):
                files.append(os.path.join(folder, file))

        files.sort()
        return files

    def _get_timeline_duration(self, timeline) -> float:
        """Get timeline duration in seconds."""
        try:
            framerate = float(timeline.GetSetting('timelineFrameRate'))
            # Get end frame of last clip
            clips = timeline.GetItemListInTrack("video", 1)
            if clips:
                last_clip = clips[-1]
                end_frame = last_clip.GetEnd()
                return end_frame / framerate
        except Exception:
            pass
        return 0.0

    def _format_duration(self, seconds: float) -> str:
        """Format seconds as MM:SS."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"

    def create_combined_timeline(
        self,
        session_folder: str,
        session_name: str,
        include_chapters: bool = True,
        include_recordings: bool = True,
        include_pois: bool = True
    ) -> Optional[Dict]:
        """
        Create a single combined timeline with all clip types.

        Args:
            session_folder: Path to extracted clips folder
            session_name: Base name for timeline
            include_chapters: Whether to include chapter clips
            include_recordings: Whether to include recording clips
            include_pois: Whether to include POI clips

        Returns:
            Dict with timeline info or None
        """
        all_files = []

        if include_chapters:
            chapters_folder = os.path.join(session_folder, "chapters")
            all_files.extend(self._get_sorted_clips(chapters_folder))

        if include_recordings:
            recordings_folder = os.path.join(session_folder, "recordings")
            all_files.extend(self._get_sorted_clips(recordings_folder))

        if include_pois:
            pois_folder = os.path.join(session_folder, "pois")
            all_files.extend(self._get_sorted_clips(pois_folder))

        if not all_files:
            return None

        # Create bin
        root_folder = self.media_pool.GetRootFolder()
        session_bin = self.media_pool.AddSubFolder(root_folder, session_name)
        if session_bin:
            self.media_pool.SetCurrentFolder(session_bin)

        # Import all clips
        items = self.media_pool.ImportMedia(all_files)
        if not items:
            return None

        # Create timeline
        timeline_name = f"{session_name} - Combined"
        timeline = self.create_timeline(timeline_name, items)
        if not timeline:
            return None

        duration = self._get_timeline_duration(timeline)

        return {
            "name": timeline_name,
            "clips": len(items),
            "duration": self._format_duration(duration)
        }
