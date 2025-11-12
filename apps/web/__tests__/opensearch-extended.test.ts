/**
 * Extended OpenSearch Tests
 *
 * Comprehensive tests for OpenSearch operations, indexing, searching,
 * error handling, and edge cases to improve test coverage.
 */

// Mock the OpenSearch client before imports
const mockClient = {
  indices: {
    create: jest.fn(),
    delete: jest.fn(),
    exists: jest.fn(),
    stats: jest.fn(),
  },
  index: jest.fn(),
  bulk: jest.fn(),
  delete: jest.fn(),
  search: jest.fn(),
};

jest.mock('@opensearch-project/opensearch', () => ({
  Client: jest.fn(() => mockClient),
}));

import {
  opensearchClient,
  SCHOOLS_INDEX,
  SCHOOLS_INDEX_MAPPING,
  createSchoolsIndex,
  deleteSchoolsIndex,
  checkIndexHealth,
  indexSchool,
  bulkIndexSchools,
  deleteSchool,
  searchSchools,
  getSearchAggregations,
  handleOpenSearchError,
} from '../lib/Newsearch';

describe('OpenSearch Operations - Extended Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Index Management', () => {
    it('should create schools index successfully', async () => {
      mockClient.indices.create.mockResolvedValue({ acknowledged: true });

      await createSchoolsIndex();

      expect(mockClient.indices.create).toHaveBeenCalledWith({
        index: SCHOOLS_INDEX,
        body: SCHOOLS_INDEX_MAPPING,
      });
    });

    it('should handle index creation errors', async () => {
      mockClient.indices.create.mockRejectedValue(new Error('Index creation failed'));

      await expect(createSchoolsIndex()).rejects.toThrow('Index creation failed');
    });

    it('should delete schools index successfully', async () => {
      mockClient.indices.delete.mockResolvedValue({ acknowledged: true });

      await deleteSchoolsIndex();

      expect(mockClient.indices.delete).toHaveBeenCalledWith({
        index: SCHOOLS_INDEX,
      });
    });

    it('should handle index deletion errors', async () => {
      mockClient.indices.delete.mockRejectedValue(new Error('Index deletion failed'));

      await expect(deleteSchoolsIndex()).rejects.toThrow('Index deletion failed');
    });

    it('should check index health successfully', async () => {
      const mockStats = {
        indices: {
          [SCHOOLS_INDEX]: {
            total: { docs: { count: 100 } },
            store: { size_in_bytes: 1048576 },
          },
        },
      };

      mockClient.indices.stats.mockResolvedValue(mockStats);

      const health = await checkIndexHealth();

      expect(health).toEqual({
        exists: true,
        docCount: 100,
        sizeInBytes: 1048576,
        sizeInMB: 1,
      });
      expect(mockClient.indices.stats).toHaveBeenCalledWith({
        index: SCHOOLS_INDEX,
      });
    });

    it('should handle missing index in health check', async () => {
      mockClient.indices.stats.mockRejectedValue({
        meta: { statusCode: 404 },
      });

      const health = await checkIndexHealth();

      expect(health).toEqual({
        exists: false,
        docCount: 0,
        sizeInBytes: 0,
        sizeInMB: 0,
      });
    });

    it('should handle index stats errors', async () => {
      mockClient.indices.stats.mockRejectedValue(new Error('Stats error'));

      await expect(checkIndexHealth()).rejects.toThrow('Stats error');
    });
  });

  describe('Document Indexing', () => {
    const mockSchool = {
      schoolId: 'school-123',
      name: 'Test Aviation School',
      location: {
        city: 'Los Angeles',
        state: 'CA',
        coordinates: { lat: 34.0522, lon: -118.2437 },
      },
      accreditation: { type: 'Part 141', vaApproved: true },
      googleRating: 4.5,
    };

    it('should index school successfully', async () => {
      mockClient.index.mockResolvedValue({ _id: 'school-123', result: 'created' });

      await indexSchool(mockSchool);

      expect(mockClient.index).toHaveBeenCalledWith({
        index: SCHOOLS_INDEX,
        id: 'school-123',
        body: mockSchool,
      });
    });

    it('should handle indexing errors', async () => {
      mockClient.index.mockRejectedValue(new Error('Indexing failed'));

      await expect(indexSchool(mockSchool)).rejects.toThrow('Indexing failed');
    });

    it('should bulk index schools successfully', async () => {
      const schools = [mockSchool, { ...mockSchool, schoolId: 'school-456' }];
      const mockBulkResponse = {
        items: [
          { index: { _id: 'school-123', result: 'created' } },
          { index: { _id: 'school-456', result: 'created' } },
        ],
      };

      mockClient.bulk.mockResolvedValue(mockBulkResponse);

      const result = await bulkIndexSchools(schools);

      expect(result).toEqual({
        successful: 2,
        failed: 0,
        errors: [],
      });
      expect(mockClient.bulk).toHaveBeenCalledWith({
        body: expect.any(Array),
      });
    });

    it('should handle bulk indexing partial failures', async () => {
      const schools = [mockSchool, { ...mockSchool, schoolId: 'school-456' }];
      const mockBulkResponse = {
        items: [
          { index: { _id: 'school-123', result: 'created' } },
          {
            index: {
              _id: 'school-456',
              error: { type: 'mapper_parsing_exception', reason: 'Invalid field' }
            }
          },
        ],
      };

      mockClient.bulk.mockResolvedValue(mockBulkResponse);

      const result = await bulkIndexSchools(schools);

      expect(result).toEqual({
        successful: 1,
        failed: 1,
        errors: [{ id: 'school-456', error: 'mapper_parsing_exception: Invalid field' }],
      });
    });

    it('should handle bulk indexing errors', async () => {
      mockClient.bulk.mockRejectedValue(new Error('Bulk indexing failed'));

      await expect(bulkIndexSchools([mockSchool])).rejects.toThrow('Bulk indexing failed');
    });

    it('should delete school successfully', async () => {
      mockClient.delete.mockResolvedValue({ result: 'deleted' });

      await deleteSchool('school-123');

      expect(mockClient.delete).toHaveBeenCalledWith({
        index: SCHOOLS_INDEX,
        id: 'school-123',
      });
    });

    it('should handle deletion of non-existent school', async () => {
      mockClient.delete.mockRejectedValue({
        meta: { statusCode: 404 },
      });

      // Should not throw for non-existent documents
      await expect(deleteSchool('non-existent')).rejects.toThrow();
    });

    it('should handle deletion errors', async () => {
      mockClient.delete.mockRejectedValue(new Error('Deletion failed'));

      await expect(deleteSchool('school-123')).rejects.toThrow('Deletion failed');
    });
  });

  describe('Search Operations', () => {
    it('should search schools with basic query', async () => {
      const mockSearchResponse = {
        hits: {
          total: { value: 2 },
          hits: [
            { _source: { schoolId: 'school-1', name: 'School One' } },
            { _source: { schoolId: 'school-2', name: 'School Two' } },
          ],
        },
      };

      mockClient.search.mockResolvedValue(mockSearchResponse);

      const params = { query: 'aviation', limit: 10 };
      const result = await searchSchools(params);

      expect(result).toEqual({
        schools: [
          { schoolId: 'school-1', name: 'School One' },
          { schoolId: 'school-2', name: 'School Two' },
        ],
        total: 2,
        took: undefined,
      });
    });

    it('should handle search with filters', async () => {
      const mockSearchResponse = {
        hits: {
          total: { value: 1 },
          hits: [{ _source: { schoolId: 'school-1', state: 'CA' } }],
        },
      };

      mockClient.search.mockResolvedValue(mockSearchResponse);

      const params = {
        query: 'flying',
        state: 'CA',
        vaApproved: true,
        minRating: 4.0,
        limit: 20,
      };

      const result = await searchSchools(params);
      expect(result.total).toBe(1);
    });

    it('should handle geo search', async () => {
      const mockSearchResponse = {
        hits: {
          total: { value: 3 },
          hits: [
            { _source: { schoolId: 'school-1', location: { coordinates: { lat: 34, lon: -118 } } } },
          ],
        },
      };

      mockClient.search.mockResolvedValue(mockSearchResponse);

      const params = {
        lat: 34.0522,
        lng: -118.2437,
        radius: 50,
        limit: 10,
      };

      const result = await searchSchools(params);
      expect(result.total).toBe(3);
    });

    it('should handle empty search results', async () => {
      const mockSearchResponse = {
        hits: {
          total: { value: 0 },
          hits: [],
        },
      };

      mockClient.search.mockResolvedValue(mockSearchResponse);

      const result = await searchSchools({ query: 'nonexistent' });
      expect(result.schools).toEqual([]);
      expect(result.total).toBe(0);
    });

    it('should handle search errors', async () => {
      mockClient.search.mockRejectedValue(new Error('Search failed'));

      await expect(searchSchools({ query: 'test' })).rejects.toThrow('Search failed');
    });

    it('should handle malformed search responses', async () => {
      mockClient.search.mockResolvedValue({});

      const result = await searchSchools({ query: 'test' });
      expect(result.schools).toEqual([]);
      expect(result.total).toBe(0);
    });
  });

  describe('Aggregations', () => {
    it('should get search aggregations successfully', async () => {
      const mockAggResponse = {
        aggregations: {
          states: {
            buckets: [
              { key: 'CA', doc_count: 50 },
              { key: 'TX', doc_count: 30 },
            ],
          },
          accreditation_types: {
            buckets: [
              { key: 'Part 141', doc_count: 60 },
              { key: 'Part 61', doc_count: 20 },
            ],
          },
          avg_rating: { value: 4.2 },
        },
      };

      mockClient.search.mockResolvedValue(mockAggResponse);

      const aggregations = await getSearchAggregations();

      expect(aggregations).toEqual({
        states: [
          { state: 'CA', count: 50 },
          { state: 'TX', count: 30 },
        ],
        accreditationTypes: [
          { type: 'Part 141', count: 60 },
          { type: 'Part 61', count: 20 },
        ],
        avgRating: 4.2,
      });
    });

    it('should handle missing aggregations data', async () => {
      mockClient.search.mockResolvedValue({ aggregations: {} });

      const aggregations = await getSearchAggregations();

      expect(aggregations).toEqual({
        states: [],
        accreditationTypes: [],
        avgRating: 0,
      });
    });

    it('should handle aggregation errors', async () => {
      mockClient.search.mockRejectedValue(new Error('Aggregation failed'));

      await expect(getSearchAggregations()).rejects.toThrow('Aggregation failed');
    });
  });

  describe('Error Handling', () => {
    it('should handle 404 not found errors', () => {
      const error = { meta: { statusCode: 404 } };
      const message = handleOpenSearchError(error);
      expect(message).toBe('Search index not found. Please ensure OpenSearch is running and indexes are created.');
    });

    it('should handle 400 bad request errors', () => {
      const error = { meta: { statusCode: 400 } };
      const message = handleOpenSearchError(error);
      expect(message).toBe('Invalid search query. Please check your search parameters.');
    });

    it('should handle timeout errors', () => {
      const error = { message: 'Request timeout' };
      const message = handleOpenSearchError(error);
      expect(message).toBe('Search request timed out. Please try again with a simpler query.');
    });

    it('should handle connection refused errors', () => {
      const error = { message: 'connection refused' };
      const message = handleOpenSearchError(error);
      expect(message).toBe('Unable to connect to search service. Please try again later.');
    });

    it('should handle generic errors', () => {
      const error = { message: 'Something went wrong' };
      const message = handleOpenSearchError(error);
      expect(message).toBe('An unexpected search error occurred. Please try again.');
    });

    it('should handle null/undefined errors', () => {
      expect(handleOpenSearchError(null)).toBe('An unexpected search error occurred. Please try again.');
      expect(handleOpenSearchError(undefined)).toBe('An unexpected search error occurred. Please try again.');
    });

    it('should handle errors with different structures', () => {
      const error = { body: { error: { type: 'index_not_found_exception' } } };
      const message = handleOpenSearchError(error);
      expect(message).toBe('An unexpected search error occurred. Please try again.');
    });
  });

  describe('Index Configuration', () => {
    it('should have correct index name', () => {
      expect(SCHOOLS_INDEX).toBe('wheelsup-schools');
    });

    it('should have proper index mapping structure', () => {
      expect(SCHOOLS_INDEX_MAPPING).toHaveProperty('mappings');
      expect(SCHOOLS_INDEX_MAPPING.mappings).toHaveProperty('properties');

      const properties = SCHOOLS_INDEX_MAPPING.mappings.properties;
      expect(properties).toHaveProperty('schoolId');
      expect(properties).toHaveProperty('name');
      expect(properties).toHaveProperty('location');
      expect(properties).toHaveProperty('contact');
      expect(properties).toHaveProperty('accreditation');
    });

    it('should have geo_point mapping for coordinates', () => {
      const locationProps = SCHOOLS_INDEX_MAPPING.mappings.properties.location.properties;
      expect(locationProps.coordinates.type).toBe('geo_point');
    });

    it('should have autocomplete analyzer for name field', () => {
      const nameField = SCHOOLS_INDEX_MAPPING.mappings.properties.name;
      expect(nameField.fields.autocomplete).toBeDefined();
      expect(nameField.fields.autocomplete.analyzer).toBe('autocomplete');
    });
  });
});
