import re
from typing import List, Dict, Optional


class EdlParser:
    """Parse CMX 3600 EDL files with Resolve marker extensions."""

    INSTANCE_TAG_PATTERN = re.compile(
        r'^\[Instance:\s*([^\]\r\n|]+)\]\s*(.+)$',
        re.IGNORECASE
    )

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
        seen_markers = set()
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
                if marker and not self._is_duplicate_marker(marker, seen_markers):
                    markers.append(marker)

            i += 1

        # Subtract timeline start offset (DaVinci Resolve typically starts at 01:00:00:00)
        # Use the first marker's timestamp as the base offset
        if markers:
            base_offset = markers[0]['timestampSeconds']
            for marker in markers:
                marker['timestampSeconds'] = marker['timestampSeconds'] - base_offset

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

        if len(parts) < 5:
            return None

        event_num = int(parts[0])
        # Timecode is at parts[4] (Record In)
        timecode = parts[4]

        # Parse metadata lines (|C:, |M:, |D:)
        # Metadata can be on separate lines OR all on a single line like:
        #   Start |C:ResolveColorBlue |M:Start |D:1
        color = None
        text = None
        duration = 1

        for j in range(start_idx + 1, min(start_idx + 10, len(lines))):
            meta_line = lines[j].strip()

            if not meta_line or (meta_line[0].isdigit() and j > start_idx + 1):
                # Next event or empty line, stop parsing metadata
                break

            # Check if line has inline metadata (split on |)
            if '|' in meta_line:
                parts = meta_line.split('|')
                for part in parts:
                    part = part.strip()
                    if part.startswith('C:'):
                        color = part[2:].strip()
                    elif part.startswith('M:'):
                        text = part[2:].strip()
                    elif part.startswith('D:'):
                        try:
                            duration = int(part[2:].strip())
                        except ValueError:
                            pass
            elif meta_line.startswith('|C:'):
                color = meta_line[3:].strip()
            elif meta_line.startswith('|M:'):
                text = meta_line[3:].strip()
            elif meta_line.startswith('|D:'):
                duration = int(meta_line[3:].strip())

        if not text:
            return None

        # New recordings use a human-readable, machine-parseable instance tag:
        #   [Instance: Camera] EventType - EventSubtype
        # Keep `text` normalized so every existing consumer continues to see
        # the legacy event format, and preserve the OBS/EDL value as rawText.
        raw_text = text
        instance, text = self._split_instance_tag(text)

        # Parse event type and subtype from normalized text
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
            'rawText': raw_text,
            'instance': instance,
            'type': event_type,
            'subtype': event_subtype,
            'duration': duration
        }

    @classmethod
    def _split_instance_tag(cls, text: str):
        """Return (instance, legacy-compatible text) for an optional tag."""
        match = cls.INSTANCE_TAG_PATTERN.match(text.strip())
        if not match:
            return None, text.strip()

        instance = match.group(1).strip()
        marker_text = match.group(2).strip()
        if not instance or not marker_text:
            return None, text.strip()
        return instance, marker_text

    def _is_duplicate_marker(self, marker: Dict, seen_markers: set) -> bool:
        key = (
            marker['timecode'],
            marker['text'],
            marker.get('instance'),
            marker.get('color'),
            marker.get('duration', 1)
        )
        if key in seen_markers:
            return True
        seen_markers.add(key)
        return False

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
