/**
 * Unit tests for OpenSearch client functionality
 */

import {
  buildSearchQuery,
  buildSortConfig,
  calculatePagination,
  validateSearchParams,
  sanitizeSearchQuery,
  generateSearchSuggestions,
  calculateDistance,
  processSearchResults,
} from '../lib/search_utils';
import {
  SCHOOLS_INDEX,
  SCHOOLS_INDEX_MAPPING,
  OpenSearchError,
  handleOpenSearchError,
} from '../lib/Newsearch';

describe('OpenSearch Client', () => {
  // Sample search data
  const sampleSearchParams = {
    query: 'flight school',
    location: {
      latitude: 34.0522,
      longitude: -118.2437,
      radiusMiles: 50
    },
    filters: {
      state: 'CA',
      vaApproved: true,
      minRating: 4.0,
      accreditationTypes: ['FAA Part 141'],
      specialties: ['PPL', 'IR']
    },
    sort: {
      field: 'rating' as const,
      order: 'desc' as const
    },
    pagination: {
      page: 2,
      limit: 10
    }
  };

  const sampleSchool = {
    schoolId: 'test-school-001',
    name: 'Test Flight School',
    description: 'A test flight school for unit testing',
    location: {
      city: 'Los Angeles',
      state: 'CA',
      coordinates: [-118.2437, 34.0522]
    },
    accreditation: {
      vaApproved: true,
      type: 'FAA Part 141'
    },
    googleRating: 4.5,
    specialties: ['PPL', 'IR'],
    isActive: true,
    extractedAt: '2024-01-01T00:00:00Z',
    lastUpdated: '2024-01-01T00:00:00Z'
  };

  describe('Search Query Building', () => {
    test('buildSearchQuery creates proper OpenSearch query', () => {
      const query = buildSearchQuery(sampleSearchParams);

      expect(query.bool.must).toHaveLength(1); // Text search
      expect(query.bool.filter).toHaveLength(7); // Geo + state + vaApproved + rating + accreditationTypes + specialties + active
      expect(query.bool.must[0].multi_match).toBeDefined();
      expect(query.bool.filter[0].geo_distance).toBeDefined();
    });

    test('buildSearchQuery handles empty parameters', () => {
      const query = buildSearchQuery({});

      expect(query.bool.must).toHaveLength(0);
      expect(query.bool.filter).toHaveLength(1); // Only active check
    });

    test('buildSearchQuery handles geo-only search', () => {
      const params = {
        location: { latitude: 34.0522, longitude: -118.2437 }
      };
      const query = buildSearchQuery(params);

      expect(query.bool.filter).toHaveLength(2); // Geo + active
      expect(query.bool.filter[0].geo_distance.distance).toBe('100mi'); // Default radius
    });
  });

  describe('Sort Configuration', () => {
    test('buildSortConfig handles rating sort', () => {
      const sort = buildSortConfig({ field: 'rating', order: 'desc' });
      expect(sort).toEqual([{ googleRating: 'desc' }]);
    });

    test('buildSortConfig handles name sort', () => {
      const sort = buildSortConfig({ field: 'name', order: 'asc' });
      expect(sort).toEqual([{ 'name.keyword': 'asc' }]);
    });

    test('buildSortConfig defaults to relevance', () => {
      const sort = buildSortConfig();
      expect(sort).toEqual([{ _score: 'desc' }]);
    });

    test('buildSortConfig handles relevance sort', () => {
      const sort = buildSortConfig({ field: 'relevance', order: 'asc' });
      expect(sort).toEqual([{ _score: 'asc' }]);
    });
  });

  describe('Pagination', () => {
    test('calculatePagination handles normal case', () => {
      const result = calculatePagination({ page: 2, limit: 10 });
      expect(result).toEqual({
        from: 10,
        size: 10,
        page: 2,
        limit: 10
      });
    });

    test('calculatePagination enforces limits', () => {
      const result = calculatePagination({ page: 0, limit: 200 });
      expect(result.page).toBe(1);
      expect(result.limit).toBe(100);
    });

    test('calculatePagination provides defaults', () => {
      const result = calculatePagination();
      expect(result).toEqual({
        from: 0,
        size: 20,
        page: 1,
        limit: 20
      });
    });
  });

  describe('Parameter Validation', () => {
    test('validateSearchParams accepts valid parameters', () => {
      const result = validateSearchParams(sampleSearchParams);
      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    test('validateSearchParams rejects invalid coordinates', () => {
      const invalidParams = {
        location: { latitude: 100, longitude: -118.2437 } // Invalid latitude
      };
      const result = validateSearchParams(invalidParams);
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Invalid latitude (must be between -90 and 90)');
    });

    test('validateSearchParams rejects invalid rating range', () => {
      const invalidParams = {
        filters: { minRating: -1, maxRating: 6 }
      };
      const result = validateSearchParams(invalidParams);
      expect(result.isValid).toBe(false);
      expect(result.errors).toHaveLength(2);
    });

    test('validateSearchParams rejects invalid pagination', () => {
      const invalidParams = {
        pagination: { page: 0, limit: 150 }
      };
      const result = validateSearchParams(invalidParams);
      expect(result.isValid).toBe(false);
      expect(result.errors).toHaveLength(2);
    });
  });

  describe('Query Sanitization', () => {
    test('sanitizeSearchQuery removes dangerous characters', () => {
      const dangerous = '<script>alert("xss")</script>Hello\x00World\x01';
      const sanitized = sanitizeSearchQuery(dangerous);
      expect(sanitized).toBe('scriptalert("xss")scriptHelloWorld');
    });

    test('sanitizeSearchQuery trims whitespace', () => {
      const spaced = '  hello world  ';
      const sanitized = sanitizeSearchQuery(spaced);
      expect(sanitized).toBe('hello world');
    });
  });

  describe('Search Suggestions', () => {
    test('generateSearchSuggestions returns relevant suggestions', () => {
      const suggestions = generateSearchSuggestions('flight');
      expect(suggestions).toContain('flight school');
      expect(suggestions.length).toBeGreaterThan(0);
    });

    test('generateSearchSuggestions handles short input', () => {
      const suggestions = generateSearchSuggestions('f');
      expect(suggestions).toHaveLength(0);
    });

    test('generateSearchSuggestions is case insensitive', () => {
      const suggestions = generateSearchSuggestions('FLIGHT');
      expect(suggestions.length).toBeGreaterThan(0);
    });
  });

  describe('Distance Calculation', () => {
    test('calculateDistance calculates correctly in miles', () => {
      // Distance from LA to NYC (approximate)
      const distance = calculateDistance(34.0522, -118.2437, 40.7128, -74.0060, 'miles');
      expect(distance).toBeGreaterThan(2400); // Should be around 2450 miles
      expect(distance).toBeLessThan(2500);
    });

    test('calculateDistance calculates correctly in kilometers', () => {
      const distance = calculateDistance(34.0522, -118.2437, 40.7128, -74.0060, 'kilometers');
      expect(distance).toBeGreaterThan(3900); // Should be around 3950 km
      expect(distance).toBeLessThan(4000);
    });

    test('calculateDistance handles same location', () => {
      const distance = calculateDistance(34.0522, -118.2437, 34.0522, -118.2437);
      expect(distance).toBe(0);
    });
  });

  describe('Result Processing', () => {
    const mockOpenSearchResponse = {
      body: {
        hits: {
          hits: [
            {
              _source: sampleSchool,
              _score: 0.95,
              _id: 'test-school-001'
            }
          ],
          total: { value: 1 }
        },
        took: 15,
        aggregations: {
          states: { buckets: [{ key: 'CA', doc_count: 150 }] },
          accreditationTypes: { buckets: [{ key: 'FAA Part 141', doc_count: 200 }] }
        }
      }
    };

    test('processSearchResults transforms OpenSearch response', () => {
      const result = processSearchResults(mockOpenSearchResponse, sampleSearchParams);

      expect(result.schools).toHaveLength(1);
      expect(result.total).toBe(1);
      expect(result.took).toBe(15);
      expect(result.schools[0].school.schoolId).toBe('test-school-001');
      expect(result.schools[0].relevanceScore).toBe(0.95);
      expect(result.schools[0].school.extractedAt).toBeInstanceOf(Date);
    });

    test('processSearchResults handles empty results', () => {
      const emptyResponse = {
        body: {
          hits: { hits: [], total: { value: 0 } },
          took: 5
        }
      };
      const result = processSearchResults(emptyResponse, {});

      expect(result.schools).toHaveLength(0);
      expect(result.total).toBe(0);
    });
  });

  describe('Index Configuration', () => {
    test('SCHOOLS_INDEX has correct name', () => {
      expect(SCHOOLS_INDEX).toBe('wheelsup-schools');
    });

    test('SCHOOLS_INDEX_MAPPING has required structure', () => {
      expect(SCHOOLS_INDEX_MAPPING.mappings.properties).toBeDefined();
      expect(SCHOOLS_INDEX_MAPPING.mappings.properties.name).toBeDefined();
      expect(SCHOOLS_INDEX_MAPPING.mappings.properties.location).toBeDefined();
      expect(SCHOOLS_INDEX_MAPPING.settings.analysis).toBeDefined();
    });

    test('SCHOOLS_INDEX_MAPPING includes geo_point for location', () => {
      const locationMapping = SCHOOLS_INDEX_MAPPING.mappings.properties.location.properties.coordinates;
      expect(locationMapping.type).toBe('geo_point');
    });
  });

  describe('Error Handling', () => {
    test('OpenSearchError constructor works', () => {
      const originalError = new Error('Connection failed');
      const osError = new OpenSearchError('Custom message', originalError);
      expect(osError.message).toBe('Custom message');
      expect(osError.name).toBe('OpenSearchError');
      expect(osError.originalError).toBe(originalError);
    });

    test('handleOpenSearchError provides user-friendly messages', () => {
      // Test 404 error
      const notFoundError = { meta: { statusCode: 404 } };
      expect(handleOpenSearchError(notFoundError)).toContain('Search index not found');

      // Test 400 error
      const badRequestError = { meta: { statusCode: 400 } };
      expect(handleOpenSearchError(badRequestError)).toContain('Invalid search query');

      // Test timeout error
      const timeoutError = { message: 'Request timeout' };
      expect(handleOpenSearchError(timeoutError)).toContain('timed out');

      // Test connection error
      const connectionError = { message: 'connection refused' };
      expect(handleOpenSearchError(connectionError)).toContain('Unable to connect');

      // Test unknown error
      const unknownError = { message: 'Something went wrong' };
      expect(handleOpenSearchError(unknownError)).toContain('unexpected search error');
    });
  });

  describe('Constants and Configuration', () => {
    test('Index name is properly defined', () => {
      expect(SCHOOLS_INDEX).toBe('wheelsup-schools');
    });

    test('Index mapping includes all required fields', () => {
      const props = SCHOOLS_INDEX_MAPPING.mappings.properties;
      const requiredFields = [
        'schoolId', 'name', 'location', 'contact', 'accreditation',
        'operations', 'googleRating', 'sourceType', 'extractedAt', 'isActive'
      ];

      requiredFields.forEach(field => {
        expect(props).toHaveProperty(field);
      });
    });

    test('Autocomplete analyzer is configured', () => {
      const analysis = SCHOOLS_INDEX_MAPPING.settings.analysis;
      expect(analysis.analyzer.autocomplete).toBeDefined();
      expect(analysis.tokenizer.autocomplete).toBeDefined();
    });
  });
});
