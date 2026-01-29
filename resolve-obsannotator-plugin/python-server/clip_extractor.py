"""
Clip Extractor - Extract clips from videos using FFmpeg.
"""

import json
import os
import re
import subprocess
import threading
from typing import List, Dict, Optional, Callable, Generator
from dataclasses import dataclass

from bulk_scanner import Session, ClipRegion, ClipRegions


def _sanitize_filename(label: str) -> str:
    """Convert a label like 'Combat - Player Death' to 'Combat_Player_Death'."""
    # Replace common separators with underscores
    sanitized = re.sub(r'[\s\-/\\:]+', '_', label.strip())
    # Remove any characters not safe for filenames
    sanitized = re.sub(r'[^\w]', '', sanitized)
    # Collapse multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized).strip('_')
    return sanitized or 'clip'


@dataclass
class ExtractionProgress:
    """Progress update for extraction."""
    clip_index: int
    total_clips: int
    status: str  # "extracting", "skipped_black", "completed", "error"
    file_name: str
    message: str = ""


@dataclass
class ExtractResult:
    """Result of session extraction."""
    extracted: int
    skipped: int
    errors: int
    output_folder: str
    clips: List[str]
    chapter_label_counters: Optional[Dict[str, int]] = None
    recording_count: int = 0
    poi_count: int = 0
    local_clip_count: int = 0


class ClipExtractor:
    """Extract clips from videos using FFmpeg."""

    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path

    def extract_clip(
        self,
        video_file: str,
        start: float,
        end: float,
        output: str
    ) -> bool:
        """
        Extract a clip from a video file using lossless copy.

        Args:
            video_file: Source video path
            start: Start time in seconds
            end: End time in seconds
            output: Output file path

        Returns:
            True if extraction succeeded
        """
        duration = end - start

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output), exist_ok=True)

        cmd = [
            self.ffmpeg_path,
            '-y',  # Overwrite output
            '-ss', str(start),
            '-i', video_file,
            '-t', str(duration),
            '-c', 'copy',  # Lossless copy
            '-avoid_negative_ts', 'make_zero',
            output
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False
        except Exception as e:
            print(f"FFmpeg error: {e}")
            return False

    def get_video_duration(self, video_file: str) -> float:
        """
        Get video duration using ffprobe.

        Args:
            video_file: Path to video file

        Returns:
            Duration in seconds, or 0.0 if probe fails
        """
        cmd = [
            self.ffprobe_path,
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_file
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                return float(result.stdout.strip())
        except Exception:
            pass

        return 0.0

    def detect_black_frames(
        self,
        video_file: str,
        start: float,
        end: float
    ) -> float:
        """
        Detect black frames in a video segment.

        Args:
            video_file: Source video path
            start: Start time in seconds
            end: End time in seconds

        Returns:
            Percentage of video that is black (0.0 to 1.0)
        """
        duration = end - start
        if duration <= 0:
            return 0.0

        cmd = [
            self.ffmpeg_path,
            '-ss', str(start),
            '-i', video_file,
            '-t', str(duration),
            '-vf', 'blackdetect=d=0.1:pix_th=0.1',
            '-f', 'null',
            '-'
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )

            # Parse blackdetect output for black_duration values
            stderr = result.stderr
            total_black = 0.0

            # Pattern: black_start:X black_end:Y black_duration:Z
            pattern = r'black_duration:([\d.]+)'
            for match in re.finditer(pattern, stderr):
                total_black += float(match.group(1))

            return min(1.0, total_black / duration)

        except Exception:
            return 0.0

    def is_entirely_black(
        self,
        video_file: str,
        start: float,
        end: float,
        threshold: float = 0.99
    ) -> bool:
        """
        Check if a video segment is entirely black frames.

        Args:
            video_file: Source video path
            start: Start time in seconds
            end: End time in seconds
            threshold: Percentage threshold to consider "entirely black"

        Returns:
            True if black percentage exceeds threshold
        """
        black_percentage = self.detect_black_frames(video_file, start, end)
        return black_percentage >= threshold

    def _write_sidecar(self, clip_path: str, region: ClipRegion):
        """Write a JSON sidecar file alongside the extracted clip."""
        sidecar_path = os.path.splitext(clip_path)[0] + '.json'
        metadata = {
            'markerOffset': region.marker_offset,
            'label': region.label,
            'regionType': region.region_type,
            'regionStart': region.start,
            'regionEnd': region.end
        }
        try:
            with open(sidecar_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            print(f"Warning: failed to write sidecar {sidecar_path}: {e}")

    def extract_session(
        self,
        session: Session,
        output_folder: str,
        skip_black_clips: bool = True,
        progress_callback: Optional[Callable[[ExtractionProgress], None]] = None
    ) -> ExtractResult:
        """
        Extract all clips from a session.

        Args:
            session: Session object with clip_regions
            output_folder: Base output folder
            skip_black_clips: Whether to skip clips that are entirely black
            progress_callback: Optional callback for progress updates

        Returns:
            ExtractResult with extraction statistics
        """
        if not session.clip_regions:
            return ExtractResult(
                extracted=0,
                skipped=0,
                errors=0,
                output_folder=output_folder,
                clips=[]
            )

        # Create session output folder
        video_name = os.path.splitext(os.path.basename(session.video_file))[0]
        session_folder = os.path.join(output_folder, video_name)
        os.makedirs(session_folder, exist_ok=True)

        extracted = 0
        skipped = 0
        errors = 0
        clips = []

        # Gather all regions with their subfolder
        all_regions = []

        # Chapters: use per-label counters and event-type subdirectories
        chapter_label_counters: Dict[str, int] = {}
        for r in session.clip_regions.chapters:
            sanitized = _sanitize_filename(r.label)
            chapter_label_counters[sanitized] = chapter_label_counters.get(sanitized, 0) + 1
            idx = chapter_label_counters[sanitized]
            filename = f"{sanitized}_{idx:03d}.mkv"
            subfolder = os.path.join("chapters", sanitized)
            all_regions.append((r, subfolder, filename))

        # Falls: per-label subdirectories under falls/
        fall_label_counters: Dict[str, int] = {}
        for r in session.clip_regions.falls:
            sanitized = _sanitize_filename(r.label)
            fall_label_counters[sanitized] = fall_label_counters.get(sanitized, 0) + 1
            idx = fall_label_counters[sanitized]
            filename = f"{sanitized}_{idx:03d}.mkv"
            subfolder = os.path.join("falls", sanitized)
            all_regions.append((r, subfolder, filename))

        all_regions.extend([
            (r, "recordings", f"recording_{i:03d}.mkv")
            for i, r in enumerate(session.clip_regions.recordings, 1)
        ])
        all_regions.extend([
            (r, "pois", f"poi_{i:03d}.mkv")
            for i, r in enumerate(session.clip_regions.pois, 1)
        ])

        total_clips = len(all_regions)

        for i, (region, subfolder, filename) in enumerate(all_regions, 1):
            output_path = os.path.join(session_folder, subfolder, filename)

            # Check for black frames if requested
            if skip_black_clips:
                if self.is_entirely_black(session.video_file, region.start, region.end):
                    skipped += 1
                    if progress_callback:
                        progress_callback(ExtractionProgress(
                            clip_index=i,
                            total_clips=total_clips,
                            status="skipped_black",
                            file_name=filename,
                            message="Skipped: entirely black frames"
                        ))
                    continue

            # Report progress
            if progress_callback:
                progress_callback(ExtractionProgress(
                    clip_index=i,
                    total_clips=total_clips,
                    status="extracting",
                    file_name=filename,
                    message=f"Extracting {region.start:.1f}s - {region.end:.1f}s"
                ))

            # Extract clip
            success = self.extract_clip(
                session.video_file,
                region.start,
                region.end,
                output_path
            )

            if success:
                extracted += 1
                clips.append(output_path)
                # Write sidecar metadata
                self._write_sidecar(output_path, region)
            else:
                errors += 1
                if progress_callback:
                    progress_callback(ExtractionProgress(
                        clip_index=i,
                        total_clips=total_clips,
                        status="error",
                        file_name=filename,
                        message="FFmpeg extraction failed"
                    ))

        # Final progress update
        if progress_callback:
            progress_callback(ExtractionProgress(
                clip_index=total_clips,
                total_clips=total_clips,
                status="completed",
                file_name="",
                message=f"Completed: {extracted} extracted, {skipped} skipped, {errors} errors"
            ))

        return ExtractResult(
            extracted=extracted,
            skipped=skipped,
            errors=errors,
            output_folder=session_folder,
            clips=clips
        )

    def extract_session_streaming(
        self,
        session: Session,
        output_folder: str,
        skip_black_clips: bool = True,
        shared_folder: Optional[str] = None,
        chapter_label_offsets: Optional[Dict[str, int]] = None,
        recording_offset: int = 0,
        poi_offset: int = 0,
        global_clip_offset: int = 0,
        global_clip_total: int = 0,
        resume: bool = False,
        pause_event: Optional[threading.Event] = None
    ) -> Generator[Dict, None, ExtractResult]:
        """
        Extract all clips from a session, yielding progress as a generator.

        Args:
            session: Session object with clip_regions
            output_folder: Base output folder
            skip_black_clips: Whether to skip clips that are entirely black
            shared_folder: If provided, use this folder directly (no video_name subfolder)
            chapter_label_offsets: Starting counters per chapter label for continuous numbering
            recording_offset: Starting counter for recordings
            poi_offset: Starting counter for POIs
            global_clip_offset: Number of clips already processed across prior sessions
            global_clip_total: Total clips across all sessions (for progress reporting)

        Yields:
            Progress dict for each clip

        Returns:
            ExtractResult with extraction statistics
        """
        if not session.clip_regions:
            return ExtractResult(
                extracted=0,
                skipped=0,
                errors=0,
                output_folder=output_folder,
                clips=[]
            )

        # Use shared folder or create per-session subfolder
        if shared_folder:
            session_folder = shared_folder
        else:
            video_name = os.path.splitext(os.path.basename(session.video_file))[0]
            session_folder = os.path.join(output_folder, video_name)
        os.makedirs(session_folder, exist_ok=True)

        extracted = 0
        skipped = 0
        errors = 0
        clips = []

        # Gather all regions with their subfolder
        all_regions = []

        # Chapters: use per-label counters and event-type subdirectories
        chapter_label_counters: Dict[str, int] = dict(chapter_label_offsets) if chapter_label_offsets else {}
        for r in session.clip_regions.chapters:
            sanitized = _sanitize_filename(r.label)
            chapter_label_counters[sanitized] = chapter_label_counters.get(sanitized, 0) + 1
            idx = chapter_label_counters[sanitized]
            filename = f"{sanitized}_{idx:03d}.mkv"
            subfolder = os.path.join("chapters", sanitized)
            all_regions.append((r, subfolder, filename))

        # Falls: per-label subdirectories under falls/
        fall_label_counters: Dict[str, int] = {}
        for r in session.clip_regions.falls:
            sanitized = _sanitize_filename(r.label)
            fall_label_counters[sanitized] = fall_label_counters.get(sanitized, 0) + 1
            idx = fall_label_counters[sanitized]
            filename = f"{sanitized}_{idx:03d}.mkv"
            subfolder = os.path.join("falls", sanitized)
            all_regions.append((r, subfolder, filename))

        all_regions.extend([
            (r, "recordings", f"recording_{i:03d}.mkv")
            for i, r in enumerate(session.clip_regions.recordings, recording_offset + 1)
        ])
        all_regions.extend([
            (r, "pois", f"poi_{i:03d}.mkv")
            for i, r in enumerate(session.clip_regions.pois, poi_offset + 1)
        ])

        total_clips = len(all_regions)
        report_total = global_clip_total if global_clip_total > 0 else total_clips

        skipped_existing = 0

        for i, (region, subfolder, filename) in enumerate(all_regions, 1):
            global_i = global_clip_offset + i
            output_path = os.path.join(session_folder, subfolder, filename)
            sidecar_path = os.path.splitext(output_path)[0] + '.json'

            # Wait if paused
            if pause_event is not None:
                pause_event.wait()

            # Resume mode: skip clips that already exist with their sidecar
            if resume and os.path.isfile(output_path) and os.path.isfile(sidecar_path):
                skipped_existing += 1
                extracted += 1
                clips.append(output_path)
                yield {
                    "type": "progress",
                    "clip": global_i,
                    "total": report_total,
                    "status": "skipped_existing",
                    "file": filename
                }
                continue

            # Check for black frames if requested
            if skip_black_clips:
                if self.is_entirely_black(session.video_file, region.start, region.end):
                    skipped += 1
                    yield {
                        "type": "progress",
                        "clip": global_i,
                        "total": report_total,
                        "status": "skipped_black",
                        "file": filename
                    }
                    continue

            # Report progress
            yield {
                "type": "progress",
                "clip": global_i,
                "total": report_total,
                "status": "extracting",
                "file": filename
            }

            # Extract clip
            success = self.extract_clip(
                session.video_file,
                region.start,
                region.end,
                output_path
            )

            if success:
                extracted += 1
                clips.append(output_path)
                # Write sidecar metadata
                self._write_sidecar(output_path, region)
                yield {
                    "type": "progress",
                    "clip": global_i,
                    "total": report_total,
                    "status": "extracted",
                    "file": filename
                }
            else:
                errors += 1
                yield {
                    "type": "progress",
                    "clip": global_i,
                    "total": report_total,
                    "status": "error",
                    "file": filename
                }

        # Only yield completion if not in shared/merged mode (caller handles it)
        if not shared_folder:
            yield {
                "type": "complete",
                "extracted": extracted,
                "skipped": skipped,
                "errors": errors,
                "outputFolder": session_folder
            }

        return ExtractResult(
            extracted=extracted,
            skipped=skipped,
            errors=errors,
            output_folder=session_folder,
            clips=clips,
            chapter_label_counters=chapter_label_counters,
            recording_count=recording_offset + len(session.clip_regions.recordings),
            poi_count=poi_offset + len(session.clip_regions.pois),
            local_clip_count=total_clips
        )
