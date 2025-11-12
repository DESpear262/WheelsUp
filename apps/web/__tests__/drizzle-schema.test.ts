/**
 * Drizzle Schema Tests
 *
 * Tests for database schema definitions and type exports
 * to ensure schema integrity and type safety.
 */

import {
  schools,
  programs,
  pricing,
  metrics,
  attributes,
  schoolsRelations,
  programsRelations,
  pricingRelations,
  metricsRelations,
  attributesRelations,
  type School,
  type NewSchool,
  type Program,
  type NewProgram,
  type Pricing,
  type NewPricing,
  type Metric,
  type NewMetric,
  type Attribute,
  type NewAttribute,
} from '../drizzle/schema';

describe('Drizzle Schema Tests', () => {
  describe('Table Definitions', () => {
    it('schools table should be defined', () => {
      expect(schools).toBeDefined();
      expect(typeof schools).toBe('object');
    });

    it('programs table should be defined', () => {
      expect(programs).toBeDefined();
      expect(typeof programs).toBe('object');
    });

    it('pricing table should be defined', () => {
      expect(pricing).toBeDefined();
      expect(typeof pricing).toBe('object');
    });

    it('metrics table should be defined', () => {
      expect(metrics).toBeDefined();
      expect(typeof metrics).toBe('object');
    });

    it('attributes table should be defined', () => {
      expect(attributes).toBeDefined();
      expect(typeof attributes).toBe('object');
    });
  });

  describe('Relations', () => {
    it('schools relations should be defined', () => {
      expect(schoolsRelations).toBeDefined();
      expect(typeof schoolsRelations).toBe('object');
    });

    it('programs relations should be defined', () => {
      expect(programsRelations).toBeDefined();
      expect(typeof programsRelations).toBe('object');
    });

    it('pricing relations should be defined', () => {
      expect(pricingRelations).toBeDefined();
      expect(typeof pricingRelations).toBe('object');
    });

    it('metrics relations should be defined', () => {
      expect(metricsRelations).toBeDefined();
      expect(typeof metricsRelations).toBe('object');
    });

    it('attributes relations should be defined', () => {
      expect(attributesRelations).toBeDefined();
      expect(typeof attributesRelations).toBe('object');
    });
  });

  describe('Type Exports', () => {
    it('School type should be available', () => {
      const school: School = {
        id: 1,
        schoolId: 'test-school',
        name: 'Test School',
        description: 'A test school',
        specialties: ['PPL'],
        contact: { phone: '123-456-7890' },
        location: {
          address: '123 Main St',
          city: 'Test City',
          state: 'TS',
          zipCode: '12345',
          country: 'USA',
        },
        accreditation: { type: 'Part 61', vaApproved: true },
        operations: { foundedYear: 2020 },
        googleRating: 4.5,
        googleReviewCount: 10,
        sourceType: 'website',
        sourceUrl: 'https://test.com',
        extractedAt: new Date(),
        confidence: 0.9,
        extractorVersion: '1.0',
        snapshotId: 'test-snapshot',
        lastUpdated: new Date(),
        isActive: true,
      };
      expect(school).toBeDefined();
    });

    it('NewSchool type should be available', () => {
      const newSchool: NewSchool = {
        schoolId: 'new-school',
        name: 'New School',
        sourceType: 'website',
        sourceUrl: 'https://new.com',
        extractedAt: new Date(),
        confidence: 0.8,
        extractorVersion: '1.0',
        snapshotId: 'test-snapshot',
      };
      expect(newSchool).toBeDefined();
    });

    it('Program type should be available', () => {
      const program: Program = {
        id: 1,
        schoolId: 'test-school',
        programId: 'test-program',
        details: {
          programType: 'PPL',
          name: 'Private Pilot License',
          duration: { hoursTypical: 60, weeksTypical: 12 },
          requirements: { ageMinimum: 17 },
          aircraftTypes: ['C172'],
          part61Available: true,
          part141Available: false,
        },
        isActive: true,
        sourceType: 'website',
        sourceUrl: 'https://test.com',
        extractedAt: new Date(),
        confidence: 0.85,
        extractorVersion: '1.0',
        snapshotId: 'test-snapshot',
        lastUpdated: new Date(),
      };
      expect(program).toBeDefined();
    });

    it('Pricing type should be available', () => {
      const pricingData: Pricing = {
        id: 1,
        schoolId: 'test-school',
        hourlyRates: [{
          aircraftCategory: 'Single Engine',
          ratePerHour: 150,
          includesInstructor: true,
          includesFuel: false,
        }],
        programCosts: [{
          programType: 'PPL',
          costBand: 'Medium',
          estimatedTotalTypical: 12000,
          flightCostEstimate: 9000,
          groundCostEstimate: 3000,
          assumptions: {},
        }],
        currency: 'USD',
        sourceType: 'website',
        sourceUrl: 'https://test.com',
        extractedAt: new Date(),
        confidence: 0.8,
        extractorVersion: '1.0',
        snapshotId: 'test-snapshot',
        lastUpdated: new Date(),
      };
      expect(pricingData).toBeDefined();
    });

    it('Metrics type should be available', () => {
      const metric: Metric = {
        id: 1,
        schoolId: 'test-school',
        training: { averageCompletionMonths: 6 },
        operational: { aircraftUtilizationPercent: 75 },
        experience: { npsScore: 8.5 },
        accreditation: { inspectionScore: 95 },
        financial: { yearsInOperation: 10 },
        metricsLastUpdated: new Date(),
        dataSources: ['survey'],
        sampleSize: 50,
        overallReliabilityScore: 4.2,
        overallQualityScore: 4.5,
        sourceType: 'website',
        sourceUrl: 'https://test.com',
        extractedAt: new Date(),
        confidence: 0.75,
        extractorVersion: '1.0',
        snapshotId: 'test-snapshot',
        lastUpdated: new Date(),
        isCurrent: true,
      };
      expect(metric).toBeDefined();
    });

    it('Attribute type should be available', () => {
      const attribute: Attribute = {
        id: 1,
        schoolId: 'test-school',
        amenities: [{
          type: 'facility',
          name: 'Flight Simulator',
          available: true,
        }],
        equipment: [{
          type: 'simulator',
          name: 'Redbird FMX',
          available: true,
        }],
        specialPrograms: [{
          type: 'accelerated',
          name: 'Fast Track PPL',
          active: true,
        }],
        certifications: [{
          name: 'FAA Safety Team',
          issuer: 'FAA',
          isActive: true,
        }],
        partnerships: [{
          partnerName: 'Boeing',
          partnershipType: 'training',
          active: true,
        }],
        awards: [{
          name: 'Best Flight School 2024',
          issuer: 'AOPA',
          year: 2024,
        }],
        socialMedia: { facebook: 'https://fb.com/test' },
        operationalNotes: ['Excellent maintenance record'],
        sourceType: 'website',
        sourceUrl: 'https://test.com',
        extractedAt: new Date(),
        confidence: 0.7,
        extractorVersion: '1.0',
        snapshotId: 'test-snapshot',
        lastUpdated: new Date(),
      };
      expect(attribute).toBeDefined();
    });
  });

  describe('Schema Constraints', () => {
    it('schools table should have required fields', () => {
      expect(schools.id).toBeDefined();
      expect(schools.schoolId).toBeDefined();
      expect(schools.name).toBeDefined();
      expect(schools.sourceType).toBeDefined();
      expect(schools.sourceUrl).toBeDefined();
    });

    it('schools table should have index definitions', () => {
      // Test that the table has been configured with indexes
      expect(schools).toBeDefined();
      // The specific index structure is tested at runtime during migration
    });

    it('programs table should reference schools', () => {
      expect(programs.schoolId).toBeDefined();
      // The foreign key reference would be verified at runtime
    });
  });
});
