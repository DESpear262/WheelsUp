/**
 * Schema Validation Tests
 *
 * Tests for Zod schema validation and data transformation
 */

import { SchoolsQuerySchema, SchoolDetailQuerySchema } from '../lib/schemas';

describe('Schema Validation', () => {
  describe('SchoolsQuerySchema', () => {
    it('should validate valid query parameters', () => {
      const validData = {
        city: 'Los Angeles',
        state: 'CA',
        lat: 34.0522,
        lng: -118.2437,
        radius: 50,
        accreditation: 'Part 141',
        vaApproved: true,
        maxCost: 15000,
        costBand: '$10k-$15k',
        minRating: 4.0,
        page: 1,
        limit: 20,
        sortBy: 'name',
        sortOrder: 'asc',
      };

      const result = SchoolsQuerySchema.parse(validData);
      expect(result).toEqual(validData);
    });

    it('should provide default values for optional parameters', () => {
      const minimalData = {};

      const result = SchoolsQuerySchema.parse(minimalData);
      expect(result.page).toBe(1);
      expect(result.limit).toBe(20);
      expect(result.sortBy).toBe('name');
      expect(result.sortOrder).toBe('asc');
    });

    it('should reject invalid data types', () => {
      const invalidData = {
        page: 'not-a-number',
        limit: 150, // Too high
        lat: 'not-a-number',
      };

      expect(() => SchoolsQuerySchema.parse(invalidData)).toThrow();
    });

    it('should enforce limit constraints', () => {
      const tooHighLimit = { limit: 150 };
      expect(() => SchoolsQuerySchema.parse(tooHighLimit)).toThrow();

      const validLimit = { limit: 50 };
      const result = SchoolsQuerySchema.parse(validLimit);
      expect(result.limit).toBe(50);
    });

    it('should validate coordinate ranges', () => {
      const invalidLat = { lat: 91 }; // Invalid latitude
      expect(() => SchoolsQuerySchema.parse(invalidLat)).toThrow();

      const invalidLng = { lng: 181 }; // Invalid longitude
      expect(() => SchoolsQuerySchema.parse(invalidLng)).toThrow();

      const validCoords = { lat: 45, lng: -90 };
      const result = SchoolsQuerySchema.parse(validCoords);
      expect(result.lat).toBe(45);
      expect(result.lng).toBe(-90);
    });
  });

  describe('SchoolDetailQuerySchema', () => {
    it('should validate valid detail query parameters', () => {
      const validData = {
        includePrograms: true,
        includePricing: true,
        includeMetrics: false,
        includeAttributes: true,
      };

      const result = SchoolDetailQuerySchema.parse(validData);
      expect(result).toEqual(validData);
    });

    it('should provide correct default values', () => {
      const emptyData = {};

      const result = SchoolDetailQuerySchema.parse(emptyData);
      expect(result.includePrograms).toBe(true);
      expect(result.includePricing).toBe(true);
      expect(result.includeMetrics).toBe(false);
      expect(result.includeAttributes).toBe(false);
    });

    it('should parse boolean values correctly', () => {
      const booleanValues = {
        includePrograms: false,
        includePricing: true,
        includeMetrics: false,
        includeAttributes: true,
      };

      const result = SchoolDetailQuerySchema.parse(booleanValues);
      expect(result.includePrograms).toBe(false);
      expect(result.includePricing).toBe(true);
      expect(result.includeMetrics).toBe(false);
      expect(result.includeAttributes).toBe(true);
    });

    it('should reject invalid boolean values', () => {
      const invalidData = {
        includePrograms: 'maybe',
      };

      expect(() => SchoolDetailQuerySchema.parse(invalidData)).toThrow();
    });
  });
});
