import { useState, useEffect } from 'react';
import { Marker } from '../types/marker';
import { FilterOptions } from '../types/api';

export const useMarkerFilter = (allMarkers: Marker[]) => {
  const [filteredMarkers, setFilteredMarkers] = useState<Marker[]>(allMarkers);
  const [filters, setFilters] = useState<FilterOptions>({});

  useEffect(() => {
    // Apply filters client-side for immediate feedback
    let result = [...allMarkers];

    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      result = result.filter(
        (m) =>
          m.text.toLowerCase().includes(searchTerm) ||
          m.type.toLowerCase().includes(searchTerm) ||
          m.subtype.toLowerCase().includes(searchTerm)
      );
    }

    if (filters.exclude) {
      const excludeTerm = filters.exclude.toLowerCase();
      result = result.filter(
        (m) =>
          !m.text.toLowerCase().includes(excludeTerm) &&
          !m.type.toLowerCase().includes(excludeTerm) &&
          !m.subtype.toLowerCase().includes(excludeTerm)
      );
    }

    if (filters.eventTypes && filters.eventTypes.length > 0) {
      const allowedTypes = new Set(filters.eventTypes);
      result = result.filter((m) => allowedTypes.has(m.type));
    }

    if (filters.timeRangeStart !== undefined) {
      result = result.filter((m) => m.timestampSeconds >= filters.timeRangeStart!);
    }

    if (filters.timeRangeEnd !== undefined) {
      result = result.filter((m) => m.timestampSeconds <= filters.timeRangeEnd!);
    }

    setFilteredMarkers(result);
  }, [allMarkers, filters]);

  return {
    filteredMarkers,
    filters,
    setFilters,
    filterCount: filteredMarkers.length,
    totalCount: allMarkers.length,
  };
};
