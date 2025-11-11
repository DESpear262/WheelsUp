/**
 * OpenSearch Client for WheelsUp
 *
 * This module provides a type-safe interface to Amazon OpenSearch Service
 * for searching and indexing flight school data.
 */

import { Client } from '@opensearch-project/opensearch';

// ============================================================================
// Configuration
// ============================================================================

/**
 * OpenSearch configuration
 */
const opensearchConfig = {
  node: process.env.OPENSEARCH_URL || 'http://localhost:9200',
  // For development, no authentication needed (security disabled in docker-compose)
  // For production AWS OpenSearch, use AWS IAM authentication
  ...(process.env.AWS_REGION && {
    auth: {
      // AWS IAM authentication would be configured here for production
    }
  }),
  requestTimeout: 60000,
  pingTimeout: 3000,
  ssl: {
    rejectUnauthorized: false, // For development only
  },
};

// ============================================================================
// Client Initialization
// ============================================================================

/**
 * OpenSearch client instance
 */
export const opensearchClient = new Client(opensearchConfig);

// ============================================================================
// Index Configuration
// ============================================================================

/**
 * Schools index name
 */
export const SCHOOLS_INDEX = 'wheelsup-schools';

/**
 * Schools index mapping for search optimization
 */
export const SCHOOLS_INDEX_MAPPING = {
  mappings: {
    properties: {
      // Primary identifiers
      schoolId: { type: 'keyword' },
      name: {
        type: 'text',
        analyzer: 'standard',
        fields: {
          keyword: { type: 'keyword' },
          autocomplete: {
            type: 'text',
            analyzer: 'autocomplete',
            search_analyzer: 'standard'
          }
        }
      },

      // Location data for geo queries
      location: {
        type: 'object',
        properties: {
          address: { type: 'text' },
          city: { type: 'keyword' },
          state: { type: 'keyword' },
          zipCode: { type: 'keyword' },
          country: { type: 'keyword' },
          coordinates: { type: 'geo_point' },
          nearestAirportIcao: { type: 'keyword' },
          nearestAirportName: { type: 'text' },
          airportDistanceMiles: { type: 'float' }
        }
      },

      // Contact information
      contact: {
        type: 'object',
        properties: {
          phone: { type: 'keyword' },
          email: { type: 'keyword' },
          website: { type: 'keyword' }
        }
      },

      // Accreditation and operations
      accreditation: {
        type: 'object',
        properties: {
          type: { type: 'keyword' },
          certificateNumber: { type: 'keyword' },
          vaApproved: { type: 'boolean' }
        }
      },

      operations: {
        type: 'object',
        properties: {
          foundedYear: { type: 'integer' },
          employeeCount: { type: 'integer' },
          fleetSize: { type: 'integer' },
          studentCapacity: { type: 'integer' }
        }
      },

      // Searchable content
      description: { type: 'text', analyzer: 'standard' },
      specialties: { type: 'keyword' },

      // Ratings and metrics
      googleRating: { type: 'float' },
      googleReviewCount: { type: 'integer' },
      yelpRating: { type: 'float' },

      // Provenance
      sourceType: { type: 'keyword' },
      sourceUrl: { type: 'keyword' },
      extractedAt: { type: 'date' },
      confidence: { type: 'float' },
      extractorVersion: { type: 'keyword' },
      snapshotId: { type: 'keyword' },

      // Metadata
      lastUpdated: { type: 'date' },
      isActive: { type: 'boolean' }
    }
  },
  settings: {
    analysis: {
      analyzer: {
        autocomplete: {
          type: 'custom',
          tokenizer: 'autocomplete',
          filter: ['lowercase']
        }
      },
      tokenizer: {
        autocomplete: {
          type: 'edge_ngram',
          min_gram: 2,
          max_gram: 10,
          token_chars: ['letter', 'digit']
        }
      }
    }
  }
};

// ============================================================================
// Index Management
// ============================================================================

/**
 * Create the schools index with proper mapping
 */
export async function createSchoolsIndex(): Promise<void> {
  try {
    const exists = await opensearchClient.indices.exists({ index: SCHOOLS_INDEX });

    if (!exists.body) {
      await opensearchClient.indices.create({
        index: SCHOOLS_INDEX,
        body: SCHOOLS_INDEX_MAPPING
      });
      console.log(`Created OpenSearch index: ${SCHOOLS_INDEX}`);
    } else {
      console.log(`OpenSearch index ${SCHOOLS_INDEX} already exists`);
    }
  } catch (error) {
    console.error('Error creating schools index:', error);
    throw new OpenSearchError('Failed to create schools index', error);
  }
}

/**
 * Delete the schools index (for testing/reset purposes)
 */
export async function deleteSchoolsIndex(): Promise<void> {
  try {
    await opensearchClient.indices.delete({ index: SCHOOLS_INDEX });
    console.log(`Deleted OpenSearch index: ${SCHOOLS_INDEX}`);
  } catch (error) {
    console.error('Error deleting schools index:', error);
    throw new OpenSearchError('Failed to delete schools index', error);
  }
}

/**
 * Check index health and mapping consistency
 */
export async function checkIndexHealth(): Promise<{
  exists: boolean;
  documentCount: number;
  health: any;
}> {
  try {
    const exists = await opensearchClient.indices.exists({ index: SCHOOLS_INDEX });
    const health = await opensearchClient.cluster.health({ index: SCHOOLS_INDEX });

    let documentCount = 0;
    if (exists.body) {
      const count = await opensearchClient.count({ index: SCHOOLS_INDEX });
      documentCount = count.body.count;
    }

    return {
      exists: exists.body,
      documentCount,
      health: health.body
    };
  } catch (error) {
    console.error('Error checking index health:', error);
    throw new OpenSearchError('Failed to check index health', error);
  }
}

// ============================================================================
// Document Operations
// ============================================================================

/**
 * Index a single school document
 */
export async function indexSchool(school: any): Promise<void> {
  try {
    // Transform school data for search optimization
    const searchDocument = {
      ...school,
      // Flatten location for easier querying
      location: {
        ...school.location,
        coordinates: school.location?.latitude && school.location?.longitude
          ? [school.location.longitude, school.location.latitude]
          : undefined
      },
      // Ensure arrays are properly handled
      specialties: Array.isArray(school.specialties) ? school.specialties : [],
    };

    await opensearchClient.index({
      index: SCHOOLS_INDEX,
      id: school.schoolId,
      body: searchDocument,
      refresh: true // Make document immediately searchable
    });
  } catch (error) {
    console.error('Error indexing school:', error);
    throw new OpenSearchError('Failed to index school', error);
  }
}

/**
 * Index multiple schools in bulk
 */
export async function bulkIndexSchools(schools: any[]): Promise<void> {
  try {
    const body = schools.flatMap(school => {
      const searchDocument = {
        ...school,
        location: {
          ...school.location,
          coordinates: school.location?.latitude && school.location?.longitude
            ? [school.location.longitude, school.location.latitude]
            : undefined
        },
        specialties: Array.isArray(school.specialties) ? school.specialties : [],
      };

      return [
        { index: { _index: SCHOOLS_INDEX, _id: school.schoolId } },
        searchDocument
      ];
    });

    const response = await opensearchClient.bulk({ body, refresh: true });

    if (response.body.errors) {
      console.error('Bulk indexing errors:', response.body.items);
      throw new OpenSearchError('Some documents failed to index');
    }

    console.log(`Successfully indexed ${schools.length} schools`);
  } catch (error) {
    console.error('Error bulk indexing schools:', error);
    throw new OpenSearchError('Failed to bulk index schools', error);
  }
}

/**
 * Delete a school document by ID
 */
export async function deleteSchool(schoolId: string): Promise<void> {
  try {
    await opensearchClient.delete({
      index: SCHOOLS_INDEX,
      id: schoolId,
      refresh: true
    });
  } catch (error) {
    console.error('Error deleting school:', error);
    throw new OpenSearchError('Failed to delete school', error);
  }
}

// ============================================================================
// Search Operations
// ============================================================================

/**
 * Search schools with filters and pagination
 */
export async function searchSchools(params: {
  query?: string;
  location?: {
    lat: number;
    lon: number;
    distance?: string; // e.g., "50mi"
  };
  filters?: {
    state?: string;
    vaApproved?: boolean;
    minRating?: number;
    specialties?: string[];
    accreditationTypes?: string[];
  };
  sort?: {
    field: string;
    order: 'asc' | 'desc';
  };
  pagination?: {
    page: number;
    limit: number;
  };
}): Promise<{
  schools: any[];
  total: number;
  page: number;
  limit: number;
  took: number;
}> {
  try {
    const {
      query,
      location,
      filters = {},
      sort,
      pagination = { page: 1, limit: 20 }
    } = params;

    const from = (pagination.page - 1) * pagination.limit;

    // Build search query
    const searchQuery: any = {
      bool: {
        must: [],
        filter: [],
        should: []
      }
    };

    // Text search
    if (query) {
      searchQuery.bool.must.push({
        multi_match: {
          query,
          fields: ['name^3', 'description', 'location.city', 'location.state'],
          fuzziness: 'AUTO'
        }
      });
    }

    // Geo distance filter
    if (location) {
      searchQuery.bool.filter.push({
        geo_distance: {
          distance: location.distance || '100mi',
          'location.coordinates': {
            lat: location.lat,
            lon: location.lon
          }
        }
      });
    }

    // Additional filters
    if (filters.state) {
      searchQuery.bool.filter.push({
        term: { 'location.state': filters.state }
      });
    }

    if (filters.vaApproved !== undefined) {
      searchQuery.bool.filter.push({
        term: { 'accreditation.vaApproved': filters.vaApproved }
      });
    }

    if (filters.minRating) {
      searchQuery.bool.filter.push({
        range: { googleRating: { gte: filters.minRating } }
      });
    }

    if (filters.specialties?.length) {
      searchQuery.bool.filter.push({
        terms: { specialties: filters.specialties }
      });
    }

    if (filters.accreditationTypes?.length) {
      searchQuery.bool.filter.push({
        terms: { 'accreditation.type': filters.accreditationTypes }
      });
    }

    // Build search request
    const searchRequest: any = {
      index: SCHOOLS_INDEX,
      body: {
        query: searchQuery,
        from,
        size: pagination.limit,
        sort: sort ? [{ [sort.field]: sort.order }] : [{ _score: 'desc' }],
        _source: true
      }
    };

    const response = await opensearchClient.search(searchRequest);

    return {
      schools: response.body.hits.hits.map((hit: any) => ({
        ...hit._source,
        _score: hit._score,
        _id: hit._id
      })),
      total: response.body.hits.total.value,
      page: pagination.page,
      limit: pagination.limit,
      took: response.body.took
    };
  } catch (error) {
    console.error('Error searching schools:', error);
    throw new OpenSearchError('Failed to search schools', error);
  }
}

// ============================================================================
// Aggregation Operations
// ============================================================================

/**
 * Get search aggregations for faceted search
 */
export async function getSearchAggregations(): Promise<{
  states: Array<{ key: string; count: number }>;
  accreditationTypes: Array<{ key: string; count: number }>;
  specialties: Array<{ key: string; count: number }>;
  vaApproved: { true: number; false: number };
  ratingRanges: Array<{ key: string; count: number }>;
}> {
  try {
    const response = await opensearchClient.search({
      index: SCHOOLS_INDEX,
      body: {
        size: 0,
        aggs: {
          states: {
            terms: { field: 'location.state', size: 50 }
          },
          accreditationTypes: {
            terms: { field: 'accreditation.type', size: 20 }
          },
          specialties: {
            terms: { field: 'specialties', size: 50 }
          },
          vaApproved: {
            terms: { field: 'accreditation.vaApproved' }
          },
          ratingRanges: {
            range: {
              field: 'googleRating',
              ranges: [
                { to: 2.0, key: '0-2' },
                { from: 2.0, to: 3.0, key: '2-3' },
                { from: 3.0, to: 4.0, key: '3-4' },
                { from: 4.0, to: 5.0, key: '4-5' }
              ]
            }
          }
        }
      }
    });

    const aggs = response.body.aggregations;
    return {
      states: aggs.states.buckets,
      accreditationTypes: aggs.accreditationTypes.buckets,
      specialties: aggs.specialties.buckets,
      vaApproved: {
        true: aggs.vaApproved.buckets.find((b: any) => b.key === 1)?.doc_count || 0,
        false: aggs.vaApproved.buckets.find((b: any) => b.key === 0)?.doc_count || 0
      },
      ratingRanges: aggs.ratingRanges.buckets
    };
  } catch (error) {
    console.error('Error getting search aggregations:', error);
    throw new OpenSearchError('Failed to get search aggregations', error);
  }
}

// ============================================================================
// Error Handling
// ============================================================================

/**
 * Custom OpenSearch error class
 */
export class OpenSearchError extends Error {
  constructor(message: string, public originalError?: any) {
    super(message);
    this.name = 'OpenSearchError';
  }
}

/**
 * Handle OpenSearch errors with user-friendly messages
 */
export function handleOpenSearchError(error: any): string {
  console.error('OpenSearch error:', error);

  if (error?.meta?.statusCode === 404) {
    return 'Search index not found. Please ensure OpenSearch is running and indexes are created.';
  }

  if (error?.meta?.statusCode === 400) {
    return 'Invalid search query. Please check your search parameters.';
  }

  if (error?.message?.includes('timeout')) {
    return 'Search request timed out. Please try again.';
  }

  if (error?.message?.includes('connection')) {
    return 'Unable to connect to search service. Please check your configuration.';
  }

  return 'An unexpected search error occurred';
}
