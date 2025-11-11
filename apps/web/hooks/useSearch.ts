/**
 * useSearch Hook
 *
 * React Query-based hook for searching flight schools with caching,
 * pagination, and error handling.
 */

import { useQuery, useInfiniteQuery, useQueryClient } from '@tanstack/react-query';
import { searchSchools, getSearchAggregations } from '@/lib/Newsearch';
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
        // Use the OpenSearch client
        const result = await searchSchools({
          query: params.query,
          location: params.location ? {
            lat: params.location.latitude,
            lon: params.location.longitude,
            distance: `${params.location.radiusMiles || 100}mi`
          } : undefined,
          filters: {
            state: params.filters?.state,
            vaApproved: params.filters?.vaApproved,
            minRating: params.filters?.minRating,
            specialties: params.filters?.specialties,
            accreditationTypes: params.filters?.accreditationTypes,
          },
          sort: params.sort ? {
            field: params.sort.field === 'relevance' ? '_score' :
                   params.sort.field === 'rating' ? 'googleRating' :
                   params.sort.field === 'name' ? 'name.keyword' : '_score',
            order: params.sort.order
          } : undefined,
          pagination: params.pagination
        });

        return {
          schools: result.schools,
          total: result.total,
          page: result.page,
          limit: result.limit,
          took: result.took
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

      const result = await searchSchools({
        query: params.query,
        location: params.location ? {
          lat: params.location.latitude,
          lon: params.location.longitude,
          distance: `${params.location.radiusMiles || 100}mi`
        } : undefined,
        filters: {
          state: params.filters?.state,
          vaApproved: params.filters?.vaApproved,
          minRating: params.filters?.minRating,
          specialties: params.filters?.specialties,
          accreditationTypes: params.filters?.accreditationTypes,
        },
        sort: params.sort ? {
          field: params.sort.field === 'relevance' ? '_score' :
                 params.sort.field === 'rating' ? 'googleRating' :
                 params.sort.field === 'name' ? 'name.keyword' : '_score',
          order: params.sort.order
        } : undefined,
        pagination: params.pagination
      });

      return {
        schools: result.schools,
        total: result.total,
        page: result.page,
        limit: result.limit,
        took: result.took
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
        const aggregations = await getSearchAggregations();
        return {
          states: aggregations.states,
          cities: [], // Would need additional aggregation
          accreditationTypes: aggregations.accreditationTypes,
          specialties: aggregations.specialties,
          vaApproved: {
            approved: aggregations.vaApproved.true,
            notApproved: aggregations.vaApproved.false,
          },
          ratingRanges: aggregations.ratingRanges.map(range => ({
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
        const result = await searchSchools({
          query: params.query,
          location: params.location ? {
            lat: params.location.latitude,
            lon: params.location.longitude,
            distance: `${params.location.radiusMiles || 100}mi`
          } : undefined,
          filters: params.filters,
          sort: params.sort ? {
            field: params.sort.field === 'relevance' ? '_score' :
                   params.sort.field === 'rating' ? 'googleRating' :
                   params.sort.field === 'name' ? 'name.keyword' : '_score',
            order: params.sort.order
          } : undefined,
          pagination: params.pagination
        });

        return {
          schools: result.schools,
          total: result.total,
          page: result.page,
          limit: result.limit,
          took: result.took
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
