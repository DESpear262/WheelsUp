/**
 * Search Utilities for WheelsUp
 *
 * Helper functions for building search queries, handling pagination,
 * and processing search results.
 */

import type { School, Program, Pricing } from './db';

// ============================================================================
// Search Query Builders
// ============================================================================

/**
 * Search parameters interface
 */
export interface SearchParams {
  query?: string;
  location?: {
    latitude: number;
    longitude: number;
    radiusMiles?: number;
  };
  filters?: {
    state?: string;
    city?: string;
    vaApproved?: boolean;
    minRating?: number;
    maxRating?: number;
    accreditationTypes?: string[];
    specialties?: string[];
    minFleetSize?: number;
    maxCost?: number;
    programTypes?: string[];
  };
  sort?: {
    field: 'relevance' | 'rating' | 'distance' | 'name' | 'cost';
    order: 'asc' | 'desc';
  };
  pagination?: {
    page: number;
    limit: number;
  };
}

/**
 * Build OpenSearch query from search parameters
 */
export function buildSearchQuery(params: SearchParams): any {
  const { query, location, filters = {} } = params;

  const searchQuery: any = {
    bool: {
      must: [],
      filter: [],
      should: []
    }
  };

  // Text search with relevance boosting
  if (query?.trim()) {
    searchQuery.bool.must.push({
      multi_match: {
        query: query.trim(),
        fields: [
          'name^3',           // Boost school names
          'description^2',    // Boost descriptions
          'location.city^2',  // Boost city names
          'specialties',      // Include specialties
          'accreditation.type'
        ],
        fuzziness: 'AUTO',
        operator: 'and'
      }
    });
  }

  // Geo distance filter
  if (location) {
    searchQuery.bool.filter.push({
      geo_distance: {
        distance: `${location.radiusMiles || 100}mi`,
        'location.coordinates': {
          lat: location.latitude,
          lon: location.longitude
        }
      }
    });
  }

  // State filter
  if (filters.state) {
    searchQuery.bool.filter.push({
      term: { 'location.state': filters.state }
    });
  }

  // City filter
  if (filters.city) {
    searchQuery.bool.filter.push({
      term: { 'location.city': filters.city }
    });
  }

  // VA approved filter
  if (filters.vaApproved !== undefined) {
    searchQuery.bool.filter.push({
      term: { 'accreditation.vaApproved': filters.vaApproved }
    });
  }

  // Rating range filter
  if (filters.minRating !== undefined || filters.maxRating !== undefined) {
    const ratingRange: any = { 'googleRating': {} };
    if (filters.minRating !== undefined) ratingRange['googleRating'].gte = filters.minRating;
    if (filters.maxRating !== undefined) ratingRange['googleRating'].lte = filters.maxRating;
    searchQuery.bool.filter.push({ range: ratingRange });
  }

  // Accreditation types filter
  if (filters.accreditationTypes?.length) {
    searchQuery.bool.filter.push({
      terms: { 'accreditation.type': filters.accreditationTypes }
    });
  }

  // Specialties filter
  if (filters.specialties?.length) {
    searchQuery.bool.filter.push({
      terms: { specialties: filters.specialties }
    });
  }

  // Fleet size filter
  if (filters.minFleetSize !== undefined) {
    searchQuery.bool.filter.push({
      range: { 'operations.fleetSize': { gte: filters.minFleetSize } }
    });
  }

  // Only search active schools
  searchQuery.bool.filter.push({
    term: { isActive: true }
  });

  return searchQuery;
}

/**
 * Build sort configuration from search parameters
 */
export function buildSortConfig(sort?: SearchParams['sort']): any[] {
  if (!sort) {
    return [{ _score: 'desc' }];
  }

  switch (sort.field) {
    case 'rating':
      return [{ googleRating: sort.order }];
    case 'name':
      return [{ 'name.keyword': sort.order }];
    case 'distance':
      // Distance sorting requires location context
      return [{ _score: 'desc' }];
    case 'cost':
      // Cost sorting would require pricing data aggregation
      return [{ _score: 'desc' }];
    case 'relevance':
    default:
      return [{ _score: sort.order }];
  }
}

/**
 * Calculate pagination parameters
 */
export function calculatePagination(pagination?: SearchParams['pagination']): {
  from: number;
  size: number;
  page: number;
  limit: number;
} {
  const page = Math.max(1, pagination?.page || 1);
  const limit = Math.min(100, Math.max(1, pagination?.limit || 20)); // Max 100, min 1
  const from = (page - 1) * limit;

  return { from, size: limit, page, limit };
}

// ============================================================================
// Result Processing
// ============================================================================

/**
 * Search result interface
 */
export interface SearchResult {
  schools: SchoolSearchResult[];
  total: number;
  page: number;
  limit: number;
  took: number;
  aggregations?: SearchAggregations;
}

/**
 * Individual school search result
 */
export interface SchoolSearchResult {
  school: School;
  programs?: Program[];
  pricing?: Pricing;
  distance?: number;
  relevanceScore: number;
  _id?: string;
}

/**
 * Search aggregations for faceted search
 */
export interface SearchAggregations {
  states: Array<{ key: string; count: number; }>;
  cities: Array<{ key: string; count: number; }>;
  accreditationTypes: Array<{ key: string; count: number; }>;
  specialties: Array<{ key: string; count: number; }>;
  vaApproved: { approved: number; notApproved: number; };
  ratingRanges: Array<{ key: string; from?: number; to?: number; count: number; }>;
  fleetSizeRanges: Array<{ key: string; min?: number; max?: number; count: number; }>;
}

/**
 * Process raw OpenSearch results into structured search results
 */
export function processSearchResults(
  opensearchResponse: any,
  searchParams: SearchParams
): SearchResult {
  const { hits, aggregations } = opensearchResponse.body;

  const schools: SchoolSearchResult[] = hits.hits.map((hit: any) => ({
    school: {
      ...hit._source,
      // Restore proper date objects
      extractedAt: new Date(hit._source.extractedAt),
      lastUpdated: new Date(hit._source.lastUpdated),
    },
    relevanceScore: hit._score || 0,
    // Distance calculation would be done here if needed
  }));

  return {
    schools,
    total: hits.total.value,
    page: searchParams.pagination?.page || 1,
    limit: searchParams.pagination?.limit || 20,
    took: opensearchResponse.body.took,
    aggregations: aggregations ? processAggregations(aggregations) : undefined
  };
}

/**
 * Process OpenSearch aggregations into structured format
 */
function processAggregations(aggregations: any): SearchAggregations {
  return {
    states: aggregations.states?.buckets || [],
    cities: aggregations.cities?.buckets || [],
    accreditationTypes: aggregations.accreditationTypes?.buckets || [],
    specialties: aggregations.specialties?.buckets || [],
    vaApproved: {
      approved: aggregations.vaApproved?.buckets?.find((b: any) => b.key === 1)?.doc_count || 0,
      notApproved: aggregations.vaApproved?.buckets?.find((b: any) => b.key === 0)?.doc_count || 0,
    },
    ratingRanges: aggregations.ratingRanges?.buckets?.map((bucket: any) => ({
      key: bucket.key,
      from: bucket.from,
      to: bucket.to,
      count: bucket.doc_count
    })) || [],
    fleetSizeRanges: aggregations.fleetSizeRanges?.buckets?.map((bucket: any) => ({
      key: bucket.key,
      min: bucket.from,
      max: bucket.to,
      count: bucket.doc_count
    })) || []
  };
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Validate search parameters
 */
export function validateSearchParams(params: SearchParams): { isValid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (params.query && params.query.length > 200) {
    errors.push('Search query too long (max 200 characters)');
  }

  if (params.location) {
    const { latitude, longitude, radiusMiles } = params.location;
    if (latitude < -90 || latitude > 90) {
      errors.push('Invalid latitude (must be between -90 and 90)');
    }
    if (longitude < -180 || longitude > 180) {
      errors.push('Invalid longitude (must be between -180 and 180)');
    }
    if (radiusMiles && (radiusMiles < 1 || radiusMiles > 500)) {
      errors.push('Invalid radius (must be between 1 and 500 miles)');
    }
  }

  if (params.pagination) {
    const { page, limit } = params.pagination;
    if (page < 1) {
      errors.push('Page must be greater than 0');
    }
    if (limit < 1 || limit > 100) {
      errors.push('Limit must be between 1 and 100');
    }
  }

  if (params.filters?.minRating !== undefined &&
      (params.filters.minRating < 0 || params.filters.minRating > 5)) {
    errors.push('Minimum rating must be between 0 and 5');
  }

  if (params.filters?.maxRating !== undefined &&
      (params.filters.maxRating < 0 || params.filters.maxRating > 5)) {
    errors.push('Maximum rating must be between 0 and 5');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}

/**
 * Sanitize search query to prevent injection
 */
export function sanitizeSearchQuery(query: string): string {
  // Remove potentially dangerous characters
  return query
    .replace(/[<>]/g, '') // Remove angle brackets
    .replace(/[\/\\]/g, '') // Remove slashes and backslashes
    .replace(/[\x00-\x1F\x7F]/g, '') // Remove control characters
    .trim();
}

/**
 * Generate search suggestions based on partial input
 */
export function generateSearchSuggestions(partial: string): string[] {
  if (!partial || partial.length < 2) return [];

  // Common search suggestions for flight schools
  const suggestions = [
    'flight school',
    'pilot training',
    'private pilot',
    'commercial pilot',
    'CFI training',
    'instrument rating',
    'multi-engine',
    'VA approved'
  ];

  return suggestions.filter(suggestion =>
    suggestion.toLowerCase().includes(partial.toLowerCase())
  );
}

/**
 * Calculate distance between two coordinates using Haversine formula
 */
export function calculateDistance(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number,
  unit: 'miles' | 'kilometers' = 'miles'
): number {
  const R = unit === 'miles' ? 3959 : 6371; // Earth's radius
  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lon2 - lon1);

  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function toRadians(degrees: number): number {
  return degrees * (Math.PI / 180);
}

// ============================================================================
// Export Types
// ============================================================================

export type { SearchParams, SearchResult, SchoolSearchResult, SearchAggregations };
