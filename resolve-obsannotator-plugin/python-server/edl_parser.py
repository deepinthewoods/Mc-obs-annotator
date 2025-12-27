import re
from typing import List, Dict, Optional


class EdlParser:
    """Parse CMX 3600 EDL files with Resolve marker extensions."""

    def __init__(self):
        self.framerate = 30.0  # Default, can be overridden

    def parse(self, edl_file_path: str) -> Dict:
        """
        Parse EDL file and return structured data.

        Returns:
            {
                'title': str,
                'framerate': float,
                'fcm': str,
                'markers': List[Dict]
            }
        """
        markers = []
        last_marker = None
        title = ""
        fcm = "NON-DROP FRAME"

        with open(edl_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Parse header
            if line.startswith('TITLE:'):
                title = line[6:].strip()
            elif line.startswith('FCM:'):
                fcm = line[4:].strip()
                # Detect framerate from FCM
                if 'DROP' in fcm:
                    self.framerate = 29.97
                else:
                    self.framerate = 30.0

            # Parse event line (starts with digit)
            elif line and line[0].isdigit():
                marker = self._parse_event(lines, i)
                if marker and not self._is_duplicate_marker(marker, last_marker):
                    markers.append(marker)
                    last_marker = marker

            i += 1

        return {
            'title': title,
            'framerate': self.framerate,
            'fcm': fcm,
            'markers': markers
        }

    def _parse_event(self, lines: List[str], start_idx: int) -> Optional[Dict]:
        """Parse a single event entry."""
        line = lines[start_idx].strip()
        parts = line.split()

        if len(parts) < 9:
            return None

        event_num = int(parts[0])
        # Timecode is at parts[4] (Record In)
        timecode = parts[4]

        # Parse metadata lines (|C:, |M:, |D:)
        color = None
        text = None
        duration = 1

        for j in range(start_idx + 1, min(start_idx + 10, len(lines))):
            meta_line = lines[j].strip()

            if meta_line.startswith('|C:'):
                color = meta_line[3:].strip()
            elif meta_line.startswith('|M:'):
                text = meta_line[3:].strip()
            elif meta_line.startswith('|D:'):
                duration = int(meta_line[3:].strip())
            elif not meta_line or (meta_line[0].isdigit() and j > start_idx + 1):
                # Next event or empty line, stop parsing metadata
                break

        if not text:
            return None

        # Parse event type and subtype from text
        # Format: "EventType - EventSubtype"
        type_parts = text.split(' - ', 1)
        event_type = type_parts[0].strip() if len(type_parts) > 0 else "Unknown"
        event_subtype = type_parts[1].strip() if len(type_parts) > 1 else ""

        return {
            'id': event_num,
            'timecode': timecode,
            'timestampSeconds': self.timecode_to_seconds(timecode),
            'color': color,
            'text': text,
            'type': event_type,
            'subtype': event_subtype,
            'duration': duration
        }

    def _is_duplicate_marker(self, marker: Dict, last_marker: Optional[Dict]) -> bool:
        if not last_marker:
            return False

        return (
            marker['timecode'] == last_marker['timecode'] and
            marker['text'] == last_marker['text'] and
            marker.get('color') == last_marker.get('color') and
            marker.get('duration', 1) == last_marker.get('duration', 1)
        )

    def timecode_to_seconds(self, timecode: str) -> float:
        """
        Convert timecode HH:MM:SS:FF to seconds.

        Args:
            timecode: String in format "HH:MM:SS:FF"

        Returns:
            Timestamp in seconds (float)
        """
        parts = timecode.split(':')
        if len(parts) != 4:
            return 0.0

        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2])
        frames = int(parts[3])

        total_seconds = (
            hours * 3600 +
            minutes * 60 +
            seconds +
            (frames / self.framerate)
        )

        return total_seconds

    def seconds_to_timecode(self, seconds: float) -> str:
        """
        Convert seconds to timecode HH:MM:SS:FF.

        Args:
            seconds: Timestamp in seconds

        Returns:
            Timecode string "HH:MM:SS:FF"
        """
        total_frames = int(seconds * self.framerate)
        hours = total_frames // (int(self.framerate) * 3600)
        minutes = (total_frames % (int(self.framerate) * 3600)) // (int(self.framerate) * 60)
        secs = (total_frames % (int(self.framerate) * 60)) // int(self.framerate)
        frames = total_frames % int(self.framerate)

        return f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}"
