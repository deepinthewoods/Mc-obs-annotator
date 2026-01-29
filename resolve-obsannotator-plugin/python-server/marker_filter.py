from typing import List, Dict, Set


class MarkerFilter:
    """Filter markers based on user criteria."""

    @staticmethod
    def apply_filters(markers: List[Dict], filters: Dict) -> List[Dict]:
        """
        Apply all filters to marker list.

        Args:
            markers: List of marker dicts
            filters: {
                'search': str (optional),
                'exclude': str (optional),
                'eventTypes': List[str] (optional),
                'timeRangeStart': float (optional),
                'timeRangeEnd': float (optional)
            }

        Returns:
            Filtered list of markers
        """
        filtered = markers.copy()

        # Text search filter
        if filters.get('search'):
            search_term = filters['search'].lower()
            filtered = [
                m for m in filtered
                if search_term in m['text'].lower() or
                   search_term in m['type'].lower() or
                   search_term in m['subtype'].lower()
            ]

        # Exclude filter
        if filters.get('exclude'):
            exclude_term = filters['exclude'].lower()
            filtered = [
                m for m in filtered
                if exclude_term not in m['text'].lower() and
                   exclude_term not in m['type'].lower() and
                   exclude_term not in m['subtype'].lower()
            ]

        # Event type filter (match on full text e.g. "Combat - Player Death")
        if filters.get('eventTypes'):
            allowed_types = set(filters['eventTypes'])
            filtered = [
                m for m in filtered
                if m['text'] in allowed_types
            ]

        # Time range filter
        if filters.get('timeRangeStart') is not None:
            start = filters['timeRangeStart']
            filtered = [
                m for m in filtered
                if m['timestampSeconds'] >= start
            ]

        if filters.get('timeRangeEnd') is not None:
            end = filters['timeRangeEnd']
            filtered = [
                m for m in filtered
                if m['timestampSeconds'] <= end
            ]

        return filtered

    @staticmethod
    def get_event_statistics(markers: List[Dict]) -> Dict[str, int]:
        """
        Count markers by event type.

        Returns:
            {'Combat': 45, 'Boss': 8, ...}
        """
        stats = {}
        for marker in markers:
            event_type = marker['text']
            stats[event_type] = stats.get(event_type, 0) + 1

        return stats
