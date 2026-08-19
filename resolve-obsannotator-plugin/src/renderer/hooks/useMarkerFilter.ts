import { useState, useCallback, useMemo } from 'react';
import { Marker, MarkerFilter } from '../types/marker';

export const useMarkerFilter = (allMarkers: Marker[]) => {
  const [filters, setFilters] = useState<MarkerFilter>({
    search: '',
    exclude: '',
    eventTypes: [],
    instances: [],
    timeRangeStart: undefined,
    timeRangeEnd: undefined,
  });

  const [selectedMarkerIds, setSelectedMarkerIds] = useState<Set<number>>(new Set());

  const filteredMarkers = useMemo(() => {
    let result = [...allMarkers];

    // Text search filter
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      result = result.filter(
        m =>
          m.text.toLowerCase().includes(searchTerm) ||
          m.type.toLowerCase().includes(searchTerm) ||
          m.subtype.toLowerCase().includes(searchTerm) ||
          (m.instance || 'Untagged').toLowerCase().includes(searchTerm)
      );
    }

    // Exclude filter
    if (filters.exclude) {
      const excludeTerm = filters.exclude.toLowerCase();
      result = result.filter(
        m =>
          !m.text.toLowerCase().includes(excludeTerm) &&
          !m.type.toLowerCase().includes(excludeTerm) &&
          !m.subtype.toLowerCase().includes(excludeTerm) &&
          !(m.instance || 'Untagged').toLowerCase().includes(excludeTerm)
      );
    }

    // Event type filter
    if (filters.eventTypes && filters.eventTypes.length > 0) {
      const allowedTypes = new Set(filters.eventTypes);
      result = result.filter(m => allowedTypes.has(m.text));
    }

    // Minecraft instance filter. Older EDLs are grouped as Untagged.
    if (filters.instances && filters.instances.length > 0) {
      const allowedInstances = new Set(filters.instances);
      result = result.filter(m => allowedInstances.has(m.instance || 'Untagged'));
    }

    // Time range filter
    if (filters.timeRangeStart !== undefined) {
      result = result.filter(m => m.timestampSeconds >= filters.timeRangeStart!);
    }

    if (filters.timeRangeEnd !== undefined) {
      result = result.filter(m => m.timestampSeconds <= filters.timeRangeEnd!);
    }

    return result;
  }, [allMarkers, filters]);

  const eventTypes = useMemo(() => {
    const types = new Set<string>();
    allMarkers.forEach(m => types.add(m.text));
    return Array.from(types).sort();
  }, [allMarkers]);

  const instances = useMemo(() => {
    const values = new Set<string>();
    allMarkers.forEach(m => values.add(m.instance || 'Untagged'));
    return Array.from(values).sort();
  }, [allMarkers]);

  const filteredStatistics = useMemo(() => {
    const stats: { [key: string]: number } = {};
    filteredMarkers.forEach(marker => {
      stats[marker.text] = (stats[marker.text] || 0) + 1;
    });
    return stats;
  }, [filteredMarkers]);

  const updateFilter = useCallback((key: keyof MarkerFilter, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({
      search: '',
      exclude: '',
      eventTypes: [],
      instances: [],
      timeRangeStart: undefined,
      timeRangeEnd: undefined,
    });
  }, []);

  const toggleMarkerSelection = useCallback((markerId: number) => {
    setSelectedMarkerIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(markerId)) {
        newSet.delete(markerId);
      } else {
        newSet.add(markerId);
      }
      return newSet;
    });
  }, []);

  const selectAllFiltered = useCallback(() => {
    setSelectedMarkerIds(new Set(filteredMarkers.map(m => m.id)));
  }, [filteredMarkers]);

  const clearSelection = useCallback(() => {
    setSelectedMarkerIds(new Set());
  }, []);

  const selectedMarkers = useMemo(() => {
    return filteredMarkers.filter(m => selectedMarkerIds.has(m.id));
  }, [filteredMarkers, selectedMarkerIds]);

  return {
    filters,
    filteredMarkers,
    filteredStatistics,
    eventTypes,
    instances,
    selectedMarkerIds,
    selectedMarkers,
    updateFilter,
    clearFilters,
    toggleMarkerSelection,
    selectAllFiltered,
    clearSelection,
  };
};
