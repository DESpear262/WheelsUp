/**
 * Search Utilities Tests
 *
 * Comprehensive tests for search utility functions, query building,
 * result processing, and validation to improve test coverage.
 */

import {
  buildSearchQuery,
  buildSortConfig,
  calculatePagination,
  processSearchResults,
  validateSearchParams,
  sanitizeSearchQuery,
  generateSearchSuggestions,
  calculateDistance,
  SearchParams,
} from '../lib/search_utils';

describe('Search Utilities Tests', () => {
  describe('buildSearchQuery', () => {
    it('should build basic text query', () => {
      const params: SearchParams = {
        query: 'aviation school',
      };

      const query = buildSearchQuery(params);

      expect(query).toHaveProperty('query');
      expect(query.query).toHaveProperty('bool');
      expect(query.query.bool).toHaveProperty('must');
    });

    it('should build geo distance query', () => {
      const params: SearchParams = {
        location: {
          latitude: 34.0522,
          longitude: -118.2437,
          radiusMiles: 50,
        },
      };

      const query = buildSearchQuery(params);

      expect(query).toHaveProperty('query');
      expect(query.query.bool).toHaveProperty('filter');
      expect(query.query.bool.filter[0]).toHaveProperty('geo_distance');
    });

    it('should apply state filter', () => {
      const params: SearchParams = {
        filters: {
          state: 'CA',
        },
      };

      const query = buildSearchQuery(params);

      expect(query.query.bool.filter).toContainEqual({
        term: { 'location.state': 'CA' },
      });
    });

    it('should apply multiple filters', () => {
      const params: SearchParams = {
        filters: {
          state: 'CA',
          vaApproved: true,
          minRating: 4.0,
          accreditationTypes: ['Part 141', 'Part 61'],
        },
      };

      const query = buildSearchQuery(params);
      const filters = query.query.bool.filter;

      expect(filters).toContainEqual({
        term: { 'location.state': 'CA' },
      });
      expect(filters).toContainEqual({
        term: { 'accreditation.vaApproved': true },
      });
      expect(filters).toContainEqual({
        range: { googleRating: { gte: 4.0 } },
      });
    });

    it('should handle complex query combinations', () => {
      const params: SearchParams = {
        query: 'flight training',
        location: {
          latitude: 40.7128,
          longitude: -74.0060,
          radiusMiles: 25,
        },
        filters: {
          vaApproved: true,
          minRating: 4.5,
        },
      };

      const query = buildSearchQuery(params);

      expect(query.query.bool.must).toBeDefined();
      expect(query.query.bool.filter).toHaveLength(3); // geo + vaApproved + rating
    });
  });

  describe('buildSortConfig', () => {
    it('should build relevance sort by default', () => {
      const sort = buildSortConfig();
      expect(sort).toEqual([['_score', 'desc']]);
    });

    it('should build rating sort', () => {
      const sort = buildSortConfig({ field: 'rating', order: 'desc' });
      expect(sort).toEqual([
        [{ 'googleRating': 'desc' }, { 'yelpRating': 'desc' }],
        ['_score', 'desc'],
      ]);
    });

    it('should build distance sort', () => {
      const sort = buildSortConfig({ field: 'distance', order: 'asc' });
      expect(sort).toEqual([
        [{ '_geo_distance': { 'location.coordinates': [-118.2437, 34.0522], 'order': 'asc', 'unit': 'mi' } }],
        ['_score', 'desc'],
      ]);
    });

    it('should build name sort', () => {
      const sort = buildSortConfig({ field: 'name', order: 'asc' });
      expect(sort).toEqual([
        [{ 'name.keyword': 'asc' }],
        ['_score', 'desc'],
      ]);
    });

    it('should handle invalid sort fields', () => {
      const sort = buildSortConfig({ field: 'invalid' as any, order: 'asc' });
      expect(sort).toEqual([['_score', 'desc']]);
    });
  });

  describe('calculatePagination', () => {
    it('should calculate default pagination', () => {
      const pagination = calculatePagination();

      expect(pagination).toEqual({
        from: 0,
        size: 20,
        page: 1,
        limit: 20,
      });
    });

    it('should calculate custom pagination', () => {
      const pagination = calculatePagination({ page: 3, limit: 10 });

      expect(pagination).toEqual({
        from: 20, // (3-1) * 10
        size: 10,
        page: 3,
        limit: 10,
      });
    });

    it('should enforce maximum limit', () => {
      const pagination = calculatePagination({ page: 1, limit: 200 });

      expect(pagination.limit).toBe(100); // Max limit
      expect(pagination.size).toBe(100);
    });

    it('should handle edge cases', () => {
      const pagination1 = calculatePagination({ page: 0, limit: 1 });
      expect(pagination1.page).toBe(1); // Minimum page

      const pagination2 = calculatePagination({ page: 1000, limit: 10 });
      expect(pagination2.from).toBe(9990); // Large page numbers
    });
  });

  describe('processSearchResults', () => {
    const mockOpenSearchResponse = {
      hits: {
        total: { value: 25 },
        hits: [
          {
            _id: 'school-1',
            _score: 0.95,
            _source: {
              schoolId: 'school-1',
              name: 'Aviation Academy',
              location: { city: 'Los Angeles', state: 'CA' },
              googleRating: 4.5,
            },
            sort: [0.95],
          },
          {
            _id: 'school-2',
            _score: 0.87,
            _source: {
              schoolId: 'school-2',
              name: 'Flight Training Center',
              location: { city: 'Phoenix', state: 'AZ' },
              googleRating: 4.2,
            },
            sort: [0.87],
          },
        ],
      },
      aggregations: {
        states: {
          buckets: [
            { key: 'CA', doc_count: 15 },
            { key: 'AZ', doc_count: 10 },
          ],
        },
      },
      took: 45,
    };

    it('should process basic search results', () => {
      const result = processSearchResults(mockOpenSearchResponse);

      expect(result).toEqual({
        schools: [
          {
            id: 'school-1',
            score: 0.95,
            schoolId: 'school-1',
            name: 'Aviation Academy',
            location: { city: 'Los Angeles', state: 'CA' },
            googleRating: 4.5,
          },
          {
            id: 'school-2',
            score: 0.87,
            schoolId: 'school-2',
            name: 'Flight Training Center',
            location: { city: 'Phoenix', state: 'AZ' },
            googleRating: 4.2,
          },
        ],
        total: 25,
        aggregations: {
          states: [
            { key: 'CA', count: 15 },
            { key: 'AZ', count: 10 },
          ],
        },
        took: 45,
        page: 1,
        limit: 20,
      });
    });

    it('should handle empty results', () => {
      const emptyResponse = {
        hits: { total: { value: 0 }, hits: [] },
        took: 5,
      };

      const result = processSearchResults(emptyResponse);

      expect(result.schools).toEqual([]);
      expect(result.total).toBe(0);
    });

    it('should handle missing aggregations', () => {
      const noAggResponse = {
        hits: { total: { value: 5 }, hits: [] },
        took: 10,
      };

      const result = processSearchResults(noAggResponse);

      expect(result.aggregations).toEqual({});
    });

    it('should process different aggregation types', () => {
      const aggResponse = {
        hits: { total: { value: 10 }, hits: [] },
        aggregations: {
          avg_rating: { value: 4.3 },
          price_ranges: {
            buckets: [
              { key: '0-5000', doc_count: 5 },
              { key: '5000-10000', doc_count: 3 },
            ],
          },
        },
        took: 20,
      };

      const result = processSearchResults(aggResponse);

      expect(result.aggregations).toEqual({
        avg_rating: 4.3,
        price_ranges: [
          { key: '0-5000', count: 5 },
          { key: '5000-10000', count: 3 },
        ],
      });
    });
  });

  describe('validateSearchParams', () => {
    it('should validate valid search parameters', () => {
      const validParams: SearchParams = {
        query: 'flight school',
        location: {
          latitude: 34.0522,
          longitude: -118.2437,
          radiusMiles: 50,
        },
        filters: {
          state: 'CA',
          vaApproved: true,
          minRating: 4.0,
        },
        sort: {
          field: 'rating',
          order: 'desc',
        },
        pagination: {
          page: 1,
          limit: 20,
        },
      };

      const result = validateSearchParams(validParams);
      expect(result.isValid).toBe(true);
      expect(result.errors).toEqual([]);
    });

    it('should reject invalid coordinates', () => {
      const invalidParams: SearchParams = {
        location: {
          latitude: 91, // Invalid latitude
          longitude: -118.2437,
          radiusMiles: 50,
        },
      };

      const result = validateSearchParams(invalidParams);
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Invalid latitude: must be between -90 and 90');
    });

    it('should reject invalid pagination', () => {
      const invalidParams: SearchParams = {
        pagination: {
          page: 0, // Invalid page
          limit: 150, // Too high limit
        },
      };

      const result = validateSearchParams(invalidParams);
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Page must be at least 1');
      expect(result.errors).toContain('Limit must not exceed 100');
    });

    it('should reject invalid rating ranges', () => {
      const invalidParams: SearchParams = {
        filters: {
          minRating: -1, // Too low
          maxRating: 6, // Too high
        },
      };

      const result = validateSearchParams(invalidParams);
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Rating must be between 0 and 5');
    });

    it('should validate sort parameters', () => {
      const invalidParams: SearchParams = {
        sort: {
          field: 'invalid' as any,
          order: 'invalid' as any,
        },
      };

      const result = validateSearchParams(invalidParams);
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Invalid sort field');
      expect(result.errors).toContain('Invalid sort order');
    });
  });

  describe('sanitizeSearchQuery', () => {
    it('should sanitize basic queries', () => {
      expect(sanitizeSearchQuery('normal query')).toBe('normal query');
      expect(sanitizeSearchQuery('query with spaces')).toBe('query with spaces');
    });

    it('should remove dangerous characters', () => {
      expect(sanitizeSearchQuery('<script>alert("xss")</script>')).toBe('scriptalertxssscript');
      expect(sanitizeSearchQuery('query; DROP TABLE users;')).toBe('query DROP TABLE users');
    });

    it('should handle empty and null inputs', () => {
      expect(sanitizeSearchQuery('')).toBe('');
      expect(sanitizeSearchQuery('   ')).toBe('');
    });

    it('should trim whitespace', () => {
      expect(sanitizeSearchQuery('  query  ')).toBe('query');
    });

    it('should limit query length', () => {
      const longQuery = 'a'.repeat(300);
      const result = sanitizeSearchQuery(longQuery);
      expect(result.length).toBeLessThanOrEqual(200);
    });
  });

  describe('generateSearchSuggestions', () => {
    it('should generate basic suggestions', () => {
      const suggestions = generateSearchSuggestions('fly');
      expect(suggestions).toContain('flying school');
      expect(suggestions).toContain('flight training');
      expect(Array.isArray(suggestions)).toBe(true);
    });

    it('should handle empty input', () => {
      const suggestions = generateSearchSuggestions('');
      expect(suggestions).toEqual([]);
    });

    it('should handle short input', () => {
      const suggestions = generateSearchSuggestions('a');
      expect(suggestions.length).toBeGreaterThan(0);
    });

    it('should limit suggestions', () => {
      const suggestions = generateSearchSuggestions('flight');
      expect(suggestions.length).toBeLessThanOrEqual(10);
    });
  });

  describe('calculateDistance', () => {
    it('should calculate distance between coordinates', () => {
      // Los Angeles to New York (approximate)
      const distance = calculateDistance(34.0522, -118.2437, 40.7128, -74.0060);
      expect(distance).toBeGreaterThan(2400); // Roughly 2450 miles
      expect(distance).toBeLessThan(2500);
    });

    it('should handle same location', () => {
      const distance = calculateDistance(34.0522, -118.2437, 34.0522, -118.2437);
      expect(distance).toBe(0);
    });

    it('should handle north-south distance', () => {
      // North Pole to South Pole
      const distance = calculateDistance(90, 0, -90, 0);
      expect(distance).toBeGreaterThan(12400); // Roughly 12450 miles
    });

    it('should be symmetric', () => {
      const distance1 = calculateDistance(0, 0, 1, 1);
      const distance2 = calculateDistance(1, 1, 0, 0);
      expect(distance1).toBe(distance2);
    });
  });

  describe('Integration Tests', () => {
    it('should build complete search query with all parameters', () => {
      const complexParams: SearchParams = {
        query: 'private pilot license',
        location: {
          latitude: 34.0522,
          longitude: -118.2437,
          radiusMiles: 100,
        },
        filters: {
          state: 'CA',
          vaApproved: true,
          minRating: 4.0,
          accreditationTypes: ['Part 141'],
          specialties: ['PPL', 'IR'],
        },
        sort: {
          field: 'rating',
          order: 'desc',
        },
        pagination: {
          page: 2,
          limit: 10,
        },
      };

      const query = buildSearchQuery(complexParams);
      const sort = buildSortConfig(complexParams.sort);
      const pagination = calculatePagination(complexParams.pagination);

      expect(query).toHaveProperty('query');
      expect(query.query.bool).toHaveProperty('must');
      expect(query.query.bool).toHaveProperty('filter');
      expect(sort).toBeDefined();
      expect(pagination.from).toBe(10); // (page-1) * limit
    });

    it('should validate complex parameter combinations', () => {
      const complexParams: SearchParams = {
        query: 'advanced flight training',
        location: {
          latitude: 45.0,
          longitude: -90.0,
          radiusMiles: 200,
        },
        filters: {
          state: 'TX',
          city: 'Austin',
          vaApproved: true,
          minRating: 4.5,
          maxRating: 5.0,
          accreditationTypes: ['Part 141', 'Part 61'],
          specialties: ['CPL', 'CFI'],
          minFleetSize: 5,
          maxCost: 25000,
          programTypes: ['PPL', 'IR'],
        },
        sort: {
          field: 'distance',
          order: 'asc',
        },
        pagination: {
          page: 1,
          limit: 25,
        },
      };

      const validation = validateSearchParams(complexParams);
      expect(validation.isValid).toBe(true);
      expect(validation.errors).toEqual([]);
    });
  });
});
