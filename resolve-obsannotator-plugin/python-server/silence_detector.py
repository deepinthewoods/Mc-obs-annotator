"""
Silence Detector - Detect speech/silence ranges in audio using FFmpeg silencedetect.
"""

import re
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SilenceSettings:
    """Settings for silence detection."""
    silence_threshold_db: float = -30.0   # dB level to count as silence
    min_silence_duration: float = 0.8     # shortest silence to detect (seconds)
    padding: float = 0.15                 # buffer around speech edges (seconds)
    max_silence_for_reset: float = 15.0   # auto section-break threshold (seconds)


@dataclass
class SpeechSegment:
    """A segment of detected speech."""
    start: float   # seconds
    end: float     # seconds


@dataclass
class SilenceResult:
    """Result of silence detection."""
    speech_segments: List[SpeechSegment] = field(default_factory=list)
    total_speech_duration: float = 0.0
    total_silence_removed: float = 0.0


def get_duration(file_path: str, ffprobe_path: str = "ffprobe") -> float:
    """Get the duration of a media file using ffprobe."""
    cmd = [
        ffprobe_path,
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        file_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return float(result.stdout.strip())
    except Exception:
        pass
    return 0.0


def detect_silences(
    file_path: str,
    settings: Optional[SilenceSettings] = None,
    ffmpeg_path: str = "ffmpeg",
    ffprobe_path: str = "ffprobe"
) -> SilenceResult:
    """
    Detect speech and silence ranges in a media file.

    Uses FFmpeg's silencedetect filter to find silence ranges,
    then inverts them to get speech ranges.

    Args:
        file_path: Path to the media file
        settings: Silence detection settings
        ffmpeg_path: Path to ffmpeg binary
        ffprobe_path: Path to ffprobe binary

    Returns:
        SilenceResult with speech segments and statistics
    """
    if settings is None:
        settings = SilenceSettings()

    # Get file duration
    file_duration = get_duration(file_path, ffprobe_path)
    if file_duration <= 0:
        return SilenceResult()

    # Run silencedetect
    cmd = [
        ffmpeg_path,
        '-i', file_path,
        '-af', f'silencedetect=noise={settings.silence_threshold_db}dB:d={settings.min_silence_duration}',
        '-f', 'null',
        '-'
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout for long files
        )
    except subprocess.TimeoutExpired:
        print(f"Silence detection timed out for {file_path}")
        return SilenceResult()
    except Exception as e:
        print(f"Silence detection error for {file_path}: {e}")
        return SilenceResult()

    # Parse silence ranges from stderr
    silence_ranges = _parse_silence_ranges(result.stderr, file_duration)

    # Invert silence ranges to get speech ranges
    speech_segments = _invert_to_speech(silence_ranges, file_duration)

    # Apply padding
    speech_segments = _apply_padding(speech_segments, settings.padding, file_duration)

    # Merge overlapping segments
    speech_segments = _merge_overlapping(speech_segments)

    # Calculate statistics
    total_speech = sum(s.end - s.start for s in speech_segments)
    total_silence = file_duration - total_speech

    return SilenceResult(
        speech_segments=speech_segments,
        total_speech_duration=round(total_speech, 3),
        total_silence_removed=round(total_silence, 3)
    )


def _parse_silence_ranges(stderr: str, file_duration: float) -> List[tuple]:
    """Parse silence_start/silence_end from FFmpeg stderr output."""
    starts = []
    ends = []

    for match in re.finditer(r'silence_start:\s*([\d.]+)', stderr):
        starts.append(float(match.group(1)))

    for match in re.finditer(r'silence_end:\s*([\d.]+)', stderr):
        ends.append(float(match.group(1)))

    # Pair them up
    ranges = []
    for i, start in enumerate(starts):
        if i < len(ends):
            ranges.append((start, ends[i]))
        else:
            # Silence extends to end of file
            ranges.append((start, file_duration))

    return ranges


def _invert_to_speech(silence_ranges: List[tuple], file_duration: float) -> List[SpeechSegment]:
    """Invert silence ranges to get speech segments."""
    if not silence_ranges:
        # No silence found — entire file is speech
        return [SpeechSegment(start=0.0, end=file_duration)]

    speech = []
    prev_end = 0.0

    for silence_start, silence_end in silence_ranges:
        if silence_start > prev_end:
            speech.append(SpeechSegment(start=prev_end, end=silence_start))
        prev_end = silence_end

    # Add trailing speech after last silence
    if prev_end < file_duration:
        speech.append(SpeechSegment(start=prev_end, end=file_duration))

    return speech


def _apply_padding(segments: List[SpeechSegment], padding: float, file_duration: float) -> List[SpeechSegment]:
    """Expand each speech segment by padding on each side, clamped to file bounds."""
    if padding <= 0:
        return segments

    padded = []
    for seg in segments:
        padded.append(SpeechSegment(
            start=max(0.0, seg.start - padding),
            end=min(file_duration, seg.end + padding)
        ))
    return padded


def _merge_overlapping(segments: List[SpeechSegment]) -> List[SpeechSegment]:
    """Merge overlapping or adjacent speech segments."""
    if not segments:
        return []

    # Sort by start time
    sorted_segs = sorted(segments, key=lambda s: s.start)
    merged = [SpeechSegment(start=sorted_segs[0].start, end=sorted_segs[0].end)]

    for seg in sorted_segs[1:]:
        last = merged[-1]
        if seg.start <= last.end:
            last.end = max(last.end, seg.end)
        else:
            merged.append(SpeechSegment(start=seg.start, end=seg.end))

    return merged
