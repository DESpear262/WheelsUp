/**
 * Extended Schema Validation Tests
 *
 * Comprehensive tests for all schema validations, edge cases,
 * type safety, and error handling to improve test coverage.
 */

import {
  SchoolSchema,
  ProgramSchema,
  PricingSchema,
  MetricsSchema,
  AttributesSchema,
  SchoolsQuerySchema,
  SchoolDetailQuerySchema,
  ProgramResponseSchema,
  PricingResponseSchema,
} from '../lib/schemas';

describe('Schema Validation - Extended Tests', () => {
  describe('SchoolSchema', () => {
    it('should validate complete school data', () => {
      const validSchool = {
        schoolId: 'school-123',
        name: 'Advanced Aviation Academy',
        description: 'Premier flight training facility',
        specialties: ['PPL', 'CPL', 'IR'],
        contact: {
          phone: '+1-555-123-4567',
          email: 'info@advancedaviation.com',
          website: 'https://advancedaviation.com',
        },
        location: {
          address: '123 Aviation Blvd',
          city: 'Phoenix',
          state: 'AZ',
          zipCode: '85001',
          country: 'USA',
          latitude: 33.4484,
          longitude: -112.0740,
          nearestAirportIcao: 'KPHX',
          nearestAirportName: 'Phoenix Sky Harbor International',
          airportDistanceMiles: 5.2,
        },
        accreditation: {
          type: 'Part 141',
          certificateNumber: 'ABC12345',
          inspectionDate: '2024-01-15',
          vaApproved: true,
        },
        operations: {
          foundedYear: 1995,
          employeeCount: 45,
          fleetSize: 12,
          studentCapacity: 150,
        },
        googleRating: 4.7,
        googleReviewCount: 89,
        yelpRating: 4.5,
        sourceType: 'scraped',
        sourceUrl: 'https://example.com/school-123',
        extractedAt: '2025-01-15T10:30:00Z',
        confidence: 0.95,
        extractorVersion: '2.1.0',
        snapshotId: '2025Q1-MVP',
        lastUpdated: '2025-01-15T10:30:00Z',
        isActive: true,
      };

      const result = SchoolSchema.parse(validSchool);
      expect(result).toEqual(validSchool);
    });

    it('should validate minimal school data', () => {
      const minimalSchool = {
        schoolId: 'school-min',
        name: 'Minimal School',
        sourceType: 'manual',
        sourceUrl: 'https://example.com',
        extractedAt: '2025-01-15T10:30:00Z',
        confidence: 0.8,
        extractorVersion: '1.0.0',
        snapshotId: '2025Q1-MVP',
      };

      const result = SchoolSchema.parse(minimalSchool);
      expect(result.schoolId).toBe('school-min');
      expect(result.isActive).toBe(true); // Default value
    });

    it('should reject invalid school IDs', () => {
      const invalidIds = [
        'too-short',
        'invalid@chars!',
        'way-way-way-way-too-long-school-id-that-exceeds-limits',
        '',
      ];

      invalidIds.forEach(id => {
        expect(() => SchoolSchema.parse({
          schoolId: id,
          name: 'Test School',
          sourceType: 'manual',
          sourceUrl: 'https://example.com',
          extractedAt: '2025-01-15T10:30:00Z',
          confidence: 0.8,
          extractorVersion: '1.0.0',
          snapshotId: '2025Q1-MVP',
        })).toThrow();
      });
    });

    it('should validate rating ranges', () => {
      // Valid ratings
      expect(() => SchoolSchema.parse({
        schoolId: 'school-123',
        name: 'Test School',
        googleRating: 4.5,
        sourceType: 'manual',
        sourceUrl: 'https://example.com',
        extractedAt: '2025-01-15T10:30:00Z',
        confidence: 0.8,
        extractorVersion: '1.0.0',
        snapshotId: '2025Q1-MVP',
      })).not.toThrow();

      // Invalid ratings
      expect(() => SchoolSchema.parse({
        schoolId: 'school-123',
        name: 'Test School',
        googleRating: 6.0, // Too high
        sourceType: 'manual',
        sourceUrl: 'https://example.com',
        extractedAt: '2025-01-15T10:30:00Z',
        confidence: 0.8,
        extractorVersion: '1.0.0',
        snapshotId: '2025Q1-MVP',
      })).toThrow();

      expect(() => SchoolSchema.parse({
        schoolId: 'school-123',
        name: 'Test School',
        googleRating: -1, // Too low
        sourceType: 'manual',
        sourceUrl: 'https://example.com',
        extractedAt: '2025-01-15T10:30:00Z',
        confidence: 0.8,
        extractorVersion: '1.0.0',
        snapshotId: '2025Q1-MVP',
      })).toThrow();
    });

    it('should validate confidence ranges', () => {
      // Valid confidence
      expect(() => SchoolSchema.parse({
        schoolId: 'school-123',
        name: 'Test School',
        confidence: 0.85,
        sourceType: 'manual',
        sourceUrl: 'https://example.com',
        extractedAt: '2025-01-15T10:30:00Z',
        extractorVersion: '1.0.0',
        snapshotId: '2025Q1-MVP',
      })).not.toThrow();

      // Invalid confidence
      expect(() => SchoolSchema.parse({
        schoolId: 'school-123',
        name: 'Test School',
        confidence: 1.5, // Too high
        sourceType: 'manual',
        sourceUrl: 'https://example.com',
        extractedAt: '2025-01-15T10:30:00Z',
        extractorVersion: '1.0.0',
        snapshotId: '2025Q1-MVP',
      })).toThrow();
    });

    it('should validate datetime formats', () => {
      // Valid datetime
      expect(() => SchoolSchema.parse({
        schoolId: 'school-123',
        name: 'Test School',
        extractedAt: '2025-01-15T10:30:00Z',
        sourceType: 'manual',
        sourceUrl: 'https://example.com',
        confidence: 0.8,
        extractorVersion: '1.0.0',
        snapshotId: '2025Q1-MVP',
      })).not.toThrow();

      // Invalid datetime
      expect(() => SchoolSchema.parse({
        schoolId: 'school-123',
        name: 'Test School',
        extractedAt: 'not-a-date',
        sourceType: 'manual',
        sourceUrl: 'https://example.com',
        confidence: 0.8,
        extractorVersion: '1.0.0',
        snapshotId: '2025Q1-MVP',
      })).toThrow();
    });
  });

  describe('ProgramSchema', () => {
    it('should validate complete program data', () => {
      const validProgram = {
        programId: 'ppl-12345678',
        schoolId: 'school-123',
        details: {
          name: 'Private Pilot License',
          programType: 'PPL',
          description: 'Complete PPL training program',
          duration: '6-8 months',
          requirements: ['Medical certificate', 'English proficiency'],
          aircraftTypes: ['C172', 'PA28'],
          part61Available: true,
          part141Available: true,
        },
        isActive: true,
        seasonalAvailability: 'Year-round',
        sourceType: 'scraped',
        sourceUrl: 'https://example.com/programs/ppl',
        extractedAt: '2025-01-15T10:30:00Z',
        confidence: 0.9,
        extractorVersion: '2.1.0',
        snapshotId: '2025Q1-MVP',
        lastUpdated: '2025-01-15T10:30:00Z',
      };

      const result = ProgramSchema.parse(validProgram);
      expect(result).toEqual(validProgram);
    });

    it('should validate program ID format', () => {
      // Valid IDs
      const validIds = ['ppl-12345678', 'cpl-ABCDEFGH', 'cfi-12345678'];

      validIds.forEach(id => {
        expect(() => ProgramSchema.parse({
          programId: id,
          schoolId: 'school-123',
          details: { name: 'Test Program' },
          sourceType: 'manual',
          sourceUrl: 'https://example.com',
          extractedAt: '2025-01-15T10:30:00Z',
          confidence: 0.8,
          extractorVersion: '1.0.0',
          snapshotId: '2025Q1-MVP',
        })).not.toThrow();
      });

      // Invalid IDs
      const invalidIds = ['short', 'invalid@chars', 'way-too-long-program-id'];

      invalidIds.forEach(id => {
        expect(() => ProgramSchema.parse({
          programId: id,
          schoolId: 'school-123',
          details: { name: 'Test Program' },
          sourceType: 'manual',
          sourceUrl: 'https://example.com',
          extractedAt: '2025-01-15T10:30:00Z',
          confidence: 0.8,
          extractorVersion: '1.0.0',
          snapshotId: '2025Q1-MVP',
        })).toThrow();
      });
    });
  });

  describe('PricingSchema', () => {
    it('should validate complete pricing data', () => {
      const validPricing = {
        schoolId: 'school-123',
        hourlyRates: [
          { aircraftType: 'C172', rate: 150, currency: 'USD' },
          { aircraftType: 'PA28', rate: 165, currency: 'USD' },
        ],
        packagePricing: [
          { name: 'PPL Package', totalCost: 15000, includes: ['Ground', 'Flight'] },
        ],
        programCosts: [
          { programType: 'PPL', estimatedCost: 12000, duration: '6 months' },
        ],
        additionalFees: {
          booksAndMaterials: 500,
          examFees: 300,
          medical: 150,
        },
        currency: 'USD',
        priceLastUpdated: '2025-01-15T10:30:00Z',
        valueInclusions: ['CFI checkride', 'Aircraft rental'],
        scholarshipsAvailable: true,
        sourceType: 'scraped',
        sourceUrl: 'https://example.com/pricing',
        extractedAt: '2025-01-15T10:30:00Z',
        confidence: 0.85,
        extractorVersion: '2.1.0',
        snapshotId: '2025Q1-MVP',
        lastUpdated: '2025-01-15T10:30:00Z',
      };

      const result = PricingSchema.parse(validPricing);
      expect(result).toEqual(validPricing);
    });

    it('should handle empty pricing arrays', () => {
      const minimalPricing = {
        schoolId: 'school-123',
        hourlyRates: [],
        packagePricing: [],
        programCosts: [],
        additionalFees: {},
        sourceType: 'manual',
        sourceUrl: 'https://example.com',
        extractedAt: '2025-01-15T10:30:00Z',
        confidence: 0.8,
        extractorVersion: '1.0.0',
        snapshotId: '2025Q1-MVP',
      };

      const result = PricingSchema.parse(minimalPricing);
      expect(result.hourlyRates).toEqual([]);
      expect(result.additionalFees).toEqual({});
    });
  });

  describe('MetricsSchema', () => {
    it('should validate metrics data', () => {
      const validMetrics = {
        schoolId: 'school-123',
        trainingVelocity: 85,
        cancellationRate: 5.2,
        completionRate: 92.5,
        studentSatisfaction: 4.3,
        lastCalculated: '2025-01-15T10:30:00Z',
        sourceType: 'calculated',
        sourceUrl: 'https://example.com/metrics',
        extractedAt: '2025-01-15T10:30:00Z',
        confidence: 0.95,
        extractorVersion: '2.1.0',
        snapshotId: '2025Q1-MVP',
        lastUpdated: '2025-01-15T10:30:00Z',
      };

      const result = MetricsSchema.parse(validMetrics);
      expect(result).toEqual(validMetrics);
    });
  });

  describe('AttributesSchema', () => {
    it('should validate attributes data', () => {
      const validAttributes = {
        schoolId: 'school-123',
        partnerships: ['Boeing', ' Cessna'],
        facilities: ['Hangar', 'Classroom'],
        amenities: ['WiFi', 'Cafeteria'],
        certifications: ['ISO 9001', 'FAA Approved'],
        additionalData: { customField: 'value' },
        sourceType: 'scraped',
        sourceUrl: 'https://example.com/attributes',
        extractedAt: '2025-01-15T10:30:00Z',
        confidence: 0.9,
        extractorVersion: '2.1.0',
        snapshotId: '2025Q1-MVP',
        lastUpdated: '2025-01-15T10:30:00Z',
      };

      const result = AttributesSchema.parse(validAttributes);
      expect(result).toEqual(validAttributes);
    });
  });

  describe('Query Schemas - Edge Cases', () => {
    it('should handle extreme pagination values', () => {
      // Test maximum limit
      const maxLimit = SchoolsQuerySchema.parse({ limit: 100 });
      expect(maxLimit.limit).toBe(100);

      // Test minimum values
      const minValues = SchoolsQuerySchema.parse({ page: 1, limit: 1 });
      expect(minValues.page).toBe(1);
      expect(minValues.limit).toBe(1);
    });

    it('should handle coordinate edge cases', () => {
      // Valid extreme coordinates
      const extremeCoords = SchoolsQuerySchema.parse({
        lat: 89.9999,
        lng: 179.9999,
        radius: 1000, // Large radius
      });
      expect(extremeCoords.lat).toBe(89.9999);
      expect(extremeCoords.lng).toBe(179.9999);

      // Invalid coordinates
      expect(() => SchoolsQuerySchema.parse({ lat: 91 })).toThrow();
      expect(() => SchoolsQuerySchema.parse({ lng: 181 })).toThrow();
    });

    it('should validate complex filter combinations', () => {
      const complexQuery = SchoolsQuerySchema.parse({
        city: 'Los Angeles',
        state: 'CA',
        lat: 34.0522,
        lng: -118.2437,
        radius: 50,
        accreditation: 'Part 141',
        vaApproved: true,
        maxCost: 20000,
        costBand: '$15k-$25k',
        minRating: 4.5,
        page: 2,
        limit: 25,
        sortBy: 'rating',
        sortOrder: 'desc',
      });

      expect(complexQuery).toBeDefined();
      expect(complexQuery.city).toBe('Los Angeles');
      expect(complexQuery.vaApproved).toBe(true);
      expect(complexQuery.sortBy).toBe('rating');
    });
  });

  describe('Response Schemas', () => {
    it('should validate program response format', () => {
      const programResponse = {
        id: 1,
        programId: 'ppl-12345678',
        name: 'Private Pilot License',
        programType: 'PPL',
        description: 'Complete PPL training',
        duration: '6 months',
        requirements: ['Medical certificate'],
        aircraftTypes: ['C172'],
        part61Available: true,
        part141Available: true,
        isActive: true,
        confidence: 0.9,
      };

      const result = ProgramResponseSchema.parse(programResponse);
      expect(result).toEqual(programResponse);
    });

    it('should validate pricing response format', () => {
      const pricingResponse = {
        id: 1,
        hourlyRates: { 'C172': 150 },
        packagePricing: [{ name: 'Full Package', totalCost: 15000 }],
        programCosts: [{ programType: 'PPL', estimatedCost: 12000 }],
        additionalFees: { books: 500 },
        currency: 'USD',
        priceLastUpdated: '2025-01-15T10:30:00Z',
        valueInclusions: ['Checkride'],
        scholarshipsAvailable: true,
        confidence: 0.85,
      };

      const result = PricingResponseSchema.parse(pricingResponse);
      expect(result).toEqual(pricingResponse);
    });
  });

  describe('Error Handling', () => {
    it('should provide detailed error messages', () => {
      // Test with invalid data to see error details
      try {
        SchoolSchema.parse({
          schoolId: 'invalid-id',
          name: 'Test',
          confidence: 2.0, // Invalid
          sourceType: 'manual',
          sourceUrl: 'https://example.com',
          extractedAt: '2025-01-15T10:30:00Z',
          extractorVersion: '1.0.0',
          snapshotId: '2025Q1-MVP',
        });
      } catch (error: any) {
        expect(error.errors).toBeDefined();
        expect(Array.isArray(error.errors)).toBe(true);
      }
    });

    it('should handle nested object validation', () => {
      // Test location object validation
      expect(() => SchoolSchema.parse({
        schoolId: 'school-123',
        name: 'Test School',
        location: {
          latitude: 91, // Invalid latitude
          longitude: -118.2437,
        },
        sourceType: 'manual',
        sourceUrl: 'https://example.com',
        extractedAt: '2025-01-15T10:30:00Z',
        confidence: 0.8,
        extractorVersion: '1.0.0',
        snapshotId: '2025Q1-MVP',
      })).toThrow();
    });
  });
});
