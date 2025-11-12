/**
 * useSearch Hook
 *
 * React Query-based hook for searching flight schools with caching,
 * pagination, and error handling.
 */

import { useQuery, useInfiniteQuery, useQueryClient } from '@tanstack/react-query';
import { SearchParams, SearchResult, SearchAggregations } from '@/lib/search_utils';

// ============================================================================
// Query Keys
// ============================================================================

export const searchKeys = {
  all: ['search'] as const,
  schools: (params: SearchParams) => ['search', 'schools', params] as const,
  aggregations: () => ['search', 'aggregations'] as const,
};

// ============================================================================
// Main Search Hook
// ============================================================================

/**
 * Hook for searching flight schools
 */
export function useSearch(params: SearchParams, enabled = true) {
  return useQuery({
    queryKey: searchKeys.schools(params),
    queryFn: async (): Promise<SearchResult> => {
      try {
        // Build API URL with query parameters
        const searchParams = new URLSearchParams();

        if (params.query) searchParams.set('q', params.query);
        if (params.filters?.state) searchParams.set('state', params.filters.state);
        if (params.location) {
          searchParams.set('lat', params.location.latitude.toString());
          searchParams.set('lng', params.location.longitude.toString());
          searchParams.set('radius', (params.location.radiusMiles || 100).toString());
        }
        if (params.filters?.vaApproved !== undefined) searchParams.set('vaApproved', params.filters.vaApproved.toString());
        if (params.filters?.minRating) searchParams.set('minRating', params.filters.minRating.toString());
        if (params.filters?.accreditationTypes?.length) searchParams.set('accreditation', params.filters.accreditationTypes[0]);
        if (params.filters?.specialties?.length) searchParams.set('specialties', params.filters.specialties.join(','));
        if (params.sort) {
          searchParams.set('sort', params.sort.field);
          searchParams.set('order', params.sort.order);
        }
        if (params.pagination) {
          searchParams.set('page', params.pagination.page.toString());
          searchParams.set('limit', params.pagination.limit.toString());
        }

        const response = await fetch(`/api/search?${searchParams.toString()}`);

        if (!response.ok) {
          throw new Error(`Search API error: ${response.status}`);
        }

        const data = await response.json();

        return {
          schools: data.schools,
          total: data.pagination.total,
          page: data.pagination.page,
          limit: data.pagination.limit,
          took: data.metadata.took
        };
      } catch (error) {
        console.error('Search error:', error);
        throw new Error('Failed to search flight schools. Please try again.');
      }
    },
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    retry: (failureCount, error) => {
      // Don't retry on 4xx errors
      if (error instanceof Error && error.message.includes('Invalid')) {
        return false;
      }
      return failureCount < 3;
    },
  });
}

// ============================================================================
// Infinite Search Hook
// ============================================================================

/**
 * Hook for infinite scrolling search results
 */
export function useInfiniteSearch(initialParams: Omit<SearchParams, 'pagination'>) {
  return useInfiniteQuery({
    queryKey: ['search', 'infinite', initialParams],
    initialPageParam: 1,
    queryFn: async ({ pageParam = 1 }): Promise<SearchResult> => {
      const params: SearchParams = {
        ...initialParams,
        pagination: { page: pageParam, limit: 20 }
      };

      // Build API URL with query parameters
      const searchParams = new URLSearchParams();

      if (params.query) searchParams.set('q', params.query);
      if (params.filters?.state) searchParams.set('state', params.filters.state);
      if (params.location) {
        searchParams.set('lat', params.location.latitude.toString());
        searchParams.set('lng', params.location.longitude.toString());
        searchParams.set('radius', (params.location.radiusMiles || 100).toString());
      }
      if (params.filters?.vaApproved !== undefined) searchParams.set('vaApproved', params.filters.vaApproved.toString());
      if (params.filters?.minRating) searchParams.set('minRating', params.filters.minRating.toString());
      if (params.filters?.accreditationTypes?.length) searchParams.set('accreditation', params.filters.accreditationTypes[0]);
      if (params.filters?.specialties?.length) searchParams.set('specialties', params.filters.specialties.join(','));
      if (params.sort) {
        searchParams.set('sort', params.sort.field);
        searchParams.set('order', params.sort.order);
      }
      searchParams.set('page', params.pagination.page.toString());
      searchParams.set('limit', params.pagination.limit.toString());

      const response = await fetch(`/api/search?${searchParams.toString()}`);

      if (!response.ok) {
        throw new Error(`Search API error: ${response.status}`);
      }

      const data = await response.json();

      return {
        schools: data.schools,
        total: data.pagination.total,
        page: data.pagination.page,
        limit: data.pagination.limit,
        took: data.metadata.took
      };
    },
    getNextPageParam: (lastPage, pages) => {
      const totalPages = Math.ceil(lastPage.total / lastPage.limit);
      if (lastPage.page < totalPages) {
        return lastPage.page + 1;
      }
      return undefined;
    },
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  });
}

// ============================================================================
// Search Aggregations Hook
// ============================================================================

/**
 * Hook for fetching search aggregations (facets)
 */
export function useSearchAggregations(enabled = true) {
  return useQuery({
    queryKey: searchKeys.aggregations(),
    queryFn: async (): Promise<SearchAggregations> => {
      try {
        const response = await fetch('/api/search/aggregations');

        if (!response.ok) {
          throw new Error(`Aggregations API error: ${response.status}`);
        }

        const aggregations = await response.json();

        return {
          states: aggregations.states || [],
          cities: [], // Would need additional aggregation
          accreditationTypes: aggregations.accreditationTypes || [],
          specialties: aggregations.specialties || [],
          vaApproved: {
            approved: aggregations.vaApproved?.true || 0,
            notApproved: aggregations.vaApproved?.false || 0,
          },
          ratingRanges: (aggregations.ratingRanges || []).map((range: any) => ({
            key: range.key,
            from: range.key === '0-2' ? 0 : range.key === '2-3' ? 2 : range.key === '3-4' ? 3 : 4,
            to: range.key === '0-2' ? 2 : range.key === '2-3' ? 3 : range.key === '3-4' ? 4 : 5,
            count: range.count
          })),
          fleetSizeRanges: [], // Would need additional aggregation
        };
      } catch (error) {
        console.error('Aggregations error:', error);
        throw new Error('Failed to load search filters. Please try again.');
      }
    },
    enabled,
    staleTime: 15 * 60 * 1000, // 15 minutes - aggregations don't change often
    gcTime: 30 * 60 * 1000, // 30 minutes
  });
}

// ============================================================================
// Search Prefetch Hook
// ============================================================================

/**
 * Hook for prefetching search results
 */
export function usePrefetchSearch() {
  const queryClient = useQueryClient();

  const prefetchSearch = (params: SearchParams) => {
    queryClient.prefetchQuery({
      queryKey: searchKeys.schools(params),
      queryFn: async () => {
        // Build API URL with query parameters
        const searchParams = new URLSearchParams();

        if (params.query) searchParams.set('q', params.query);
        if (params.filters?.state) searchParams.set('state', params.filters.state);
        if (params.location) {
          searchParams.set('lat', params.location.latitude.toString());
          searchParams.set('lng', params.location.longitude.toString());
          searchParams.set('radius', (params.location.radiusMiles || 100).toString());
        }
        if (params.filters?.vaApproved !== undefined) searchParams.set('vaApproved', params.filters.vaApproved.toString());
        if (params.filters?.minRating) searchParams.set('minRating', params.filters.minRating.toString());
        if (params.filters?.accreditationTypes?.length) searchParams.set('accreditation', params.filters.accreditationTypes[0]);
        if (params.filters?.specialties?.length) searchParams.set('specialties', params.filters.specialties.join(','));
        if (params.sort) {
          searchParams.set('sort', params.sort.field);
          searchParams.set('order', params.sort.order);
        }
        if (params.pagination) {
          searchParams.set('page', params.pagination.page.toString());
          searchParams.set('limit', params.pagination.limit.toString());
        }

        const response = await fetch(`/api/search?${searchParams.toString()}`);

        if (!response.ok) {
          throw new Error(`Search API error: ${response.status}`);
        }

        const data = await response.json();

        return {
          schools: data.schools,
          total: data.pagination.total,
          page: data.pagination.page,
          limit: data.pagination.limit,
          took: data.metadata.took
        };
      },
      staleTime: 5 * 60 * 1000,
    });
  };

  return { prefetchSearch };
}

// ============================================================================
// Search Cache Management
// ============================================================================

/**
 * Hook for clearing search cache
 */
export function useClearSearchCache() {
  const queryClient = useQueryClient();

  const clearSearchCache = () => {
    queryClient.invalidateQueries({ queryKey: searchKeys.all });
  };

  return { clearSearchCache };
}
