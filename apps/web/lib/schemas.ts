/**
 * Zod Validation Schemas for WheelsUp API
 *
 * These schemas validate API inputs and outputs, ensuring type safety
 * and data integrity for the Next.js API routes.
 */

import { z } from 'zod';

// ============================================================================
// Base Schemas and Enums
// ============================================================================

const AccreditationTypeSchema = z.enum(['Part 61', 'Part 141', 'Part 142']);

const AircraftCategorySchema = z.enum([
  'single_engine_land',
  'multi_engine_land',
  'single_engine_sea',
  'multi_engine_sea',
  'rotorcraft',
  'glider',
  'lighter_than_air'
]);

const CurrencySchema = z.enum(['USD']);

const CostBandSchema = z.enum([
  'budget',
  '$5k-$10k',
  '$10k-$15k',
  '$15k-$25k',
  '$25k+'
]);

// ============================================================================
// Contact and Location Schemas
// ============================================================================

const ContactInfoSchema = z.object({
  phone: z.string().regex(/^\+?[\d\s\-()]{10,20}$/).optional(),
  email: z.string().email().optional(),
  website: z.string().url().optional(),
});

const LocationInfoSchema = z.object({
  address: z.string().optional(),
  city: z.string().optional(),
  state: z.string().optional(),
  zipCode: z.string().optional(),
  country: z.string().default('United States'),
  latitude: z.number().min(-90).max(90).optional(),
  longitude: z.number().min(-180).max(180).optional(),
  nearestAirportIcao: z.string().optional(),
  nearestAirportName: z.string().optional(),
  airportDistanceMiles: z.number().positive().optional(),
});

// ============================================================================
// Accreditation and Operations Schemas
// ============================================================================

const AccreditationInfoSchema = z.object({
  type: AccreditationTypeSchema.optional(),
  certificateNumber: z.string().optional(),
  inspectionDate: z.string().datetime().optional(),
  vaApproved: z.boolean().optional(),
});

const OperationalInfoSchema = z.object({
  foundedYear: z.number().int().min(1900).max(new Date().getFullYear()).optional(),
  employeeCount: z.number().int().positive().optional(),
  fleetSize: z.number().int().nonnegative().optional(),
  studentCapacity: z.number().int().positive().optional(),
});

// ============================================================================
// Program Schemas
// ============================================================================

const ProgramTypeSchema = z.enum([
  'Private Pilot License',
  'Instrument Rating',
  'Commercial Pilot License',
  'Certified Flight Instructor',
  'Certified Flight Instructor - Instrument',
  'Multi-Engine Instructor',
  'Airline Transport Pilot',
  'Sport Pilot',
  'Rotorcraft Helicopter',
  'Seaplane Rating',
  'Tailwheel Endorsement'
]);

const ProgramDurationSchema = z.object({
  hoursMin: z.number().int().positive().optional(),
  hoursMax: z.number().int().positive().optional(),
  hoursTypical: z.number().int().positive().optional(),
  weeksMin: z.number().int().positive().optional(),
  weeksMax: z.number().int().positive().optional(),
  weeksTypical: z.number().int().positive().optional(),
}).refine((data) => {
  // Validate that max >= min when both are present
  if (data.hoursMin && data.hoursMax && data.hoursMax < data.hoursMin) return false;
  if (data.weeksMin && data.weeksMax && data.weeksMax < data.weeksMin) return false;
  return true;
}, 'Maximum values must be >= minimum values');

const ProgramRequirementsSchema = z.object({
  ageMinimum: z.number().int().min(14).max(100).optional(),
  englishProficiency: z.boolean().optional(),
  medicalCertificateClass: z.string().optional(),
  priorCertifications: z.array(z.string()),
  flightExperienceHours: z.number().nonnegative().optional(),
});

const ProgramDetailsSchema = z.object({
  programType: ProgramTypeSchema,
  name: z.string().min(1).max(200),
  description: z.string().max(1000).optional(),
  duration: ProgramDurationSchema,
  requirements: ProgramRequirementsSchema,
  includesGroundSchool: z.boolean().optional(),
  includesCheckride: z.boolean().optional(),
  aircraftTypes: z.array(z.string()),
  part61Available: z.boolean().default(true),
  part141Available: z.boolean().default(false),
  isPopular: z.boolean().optional(),
});

// ============================================================================
// Pricing Schemas
// ============================================================================

const HourlyRateSchema = z.object({
  aircraftCategory: AircraftCategorySchema,
  ratePerHour: z.number().positive(),
  includesInstructor: z.boolean().default(true),
  includesFuel: z.boolean().optional(),
  blockHoursMin: z.number().int().positive().optional(),
  blockHoursMax: z.number().int().positive().optional(),
});

const PackagePricingSchema = z.object({
  programType: z.string(),
  packageName: z.string().min(1).max(200),
  totalCost: z.number().positive(),
  flightHoursIncluded: z.number().int().nonnegative().optional(),
  groundHoursIncluded: z.number().int().nonnegative().optional(),
  includesMaterials: z.boolean().default(false),
  validForMonths: z.number().int().positive().optional(),
  completionDeadlineMonths: z.number().int().positive().optional(),
});

const ProgramCostEstimateSchema = z.object({
  programType: z.string(),
  costBand: CostBandSchema,
  estimatedTotalMin: z.number().nonnegative().optional(),
  estimatedTotalMax: z.number().nonnegative().optional(),
  estimatedTotalTypical: z.number().nonnegative().optional(),
  flightCostEstimate: z.number().nonnegative().optional(),
  groundCostEstimate: z.number().nonnegative().optional(),
  materialsCostEstimate: z.number().nonnegative().optional(),
  examFeesEstimate: z.number().nonnegative().optional(),
  assumptions: z.record(z.string(), z.any()),
}).refine((data) => {
  // Validate that max >= min when both are present
  if (data.estimatedTotalMin && data.estimatedTotalMax && data.estimatedTotalMax < data.estimatedTotalMin) {
    return false;
  }
  return true;
}, 'Maximum cost cannot be less than minimum cost');

const AdditionalFeesSchema = z.object({
  checkrideFee: z.number().nonnegative().optional(),
  medicalExamFee: z.number().nonnegative().optional(),
  knowledgeTestFee: z.number().nonnegative().optional(),
  membershipFee: z.number().nonnegative().optional(),
  multiEngineSurcharge: z.number().nonnegative().optional(),
  nightSurcharge: z.number().nonnegative().optional(),
  weekendSurcharge: z.number().nonnegative().optional(),
  enrollmentDeposit: z.number().nonnegative().optional(),
  paymentPlansAvailable: z.boolean().optional(),
});

// ============================================================================
// Provenance Schema (used by all entities)
// ============================================================================

export const ProvenanceSchema = z.object({
  sourceType: z.string().min(1).max(50),
  sourceUrl: z.string().url(),
  extractedAt: z.string().datetime().default(() => new Date().toISOString()),
  confidence: z.number().min(0).max(1),
  extractorVersion: z.string().min(1).max(20),
  snapshotId: z.string().min(1).max(50),
});

// ============================================================================
// Main Entity Schemas
// ============================================================================

export const SchoolSchema = z.object({
  // Core identifiers
  schoolId: z.string().regex(/^[a-zA-Z0-9_-]{8,50}$/, 'Invalid school ID format'),
  name: z.string().min(1).max(200),

  // Descriptive information
  description: z.string().max(2000).optional(),
  specialties: z.array(z.string()).default([]),

  // Contact and location
  contact: ContactInfoSchema.optional().default({}),
  location: LocationInfoSchema.optional().default({
    country: 'United States'
  }),

  // Accreditation and operations
  accreditation: AccreditationInfoSchema.default({}),
  operations: OperationalInfoSchema.default({}),

  // External references
  googleRating: z.number().min(1).max(5).optional(),
  googleReviewCount: z.number().int().nonnegative().optional(),
  yelpRating: z.number().min(1).max(5).optional(),

  // Provenance
  ...ProvenanceSchema.shape,

  // Metadata
  lastUpdated: z.string().datetime().default(() => new Date().toISOString()),
  isActive: z.boolean().default(true),
});

export const ProgramSchema = z.object({
  programId: z.string().regex(/^[a-zA-Z0-9_-]{8,50}$/, 'Invalid program ID format'),
  schoolId: z.string().regex(/^[a-zA-Z0-9_-]{8,50}$/, 'Invalid school ID format'),

  // Program details
  details: ProgramDetailsSchema,

  // Operational info
  isActive: z.boolean().default(true),
  seasonalAvailability: z.string().optional(),

  // Provenance
  ...ProvenanceSchema.shape,

  // Metadata
  lastUpdated: z.string().datetime().default(() => new Date().toISOString()),
});

export const PricingSchema = z.object({
  schoolId: z.string().regex(/^[a-zA-Z0-9_-]{8,50}$/, 'Invalid school ID format'),

  // Pricing structures
  hourlyRates: z.array(HourlyRateSchema).default([]),
  packagePricing: z.array(PackagePricingSchema).default([]),
  programCosts: z.array(ProgramCostEstimateSchema).default([]),
  additionalFees: AdditionalFeesSchema.default({}),

  // Pricing metadata
  currency: CurrencySchema.default('USD'),
  priceLastUpdated: z.string().datetime().optional(),
  valueInclusions: z.array(z.string()).default([]),
  scholarshipsAvailable: z.boolean().optional(),

  // Provenance
  ...ProvenanceSchema.shape,

  // Metadata
  lastUpdated: z.string().datetime().default(() => new Date().toISOString()),
});

export const MetricsSchema = z.object({
  schoolId: z.string().regex(/^[a-zA-Z0-9_-]{8,50}$/, 'Invalid school ID format'),

  // Metric categories
  training: z.object({
    averageCompletionMonths: z.number().positive().optional(),
    completionRatePercent: z.number().min(0).max(100).optional(),
    passRateFirstAttempt: z.number().min(0).max(100).optional(),
    averageHoursPerMonth: z.number().positive().optional(),
    soloRatePercent: z.number().min(0).max(100).optional(),
    dropoutRatePercent: z.number().min(0).max(100).optional(),
  }).optional(),

  operational: z.object({
    cancellationRatePercent: z.number().min(0).max(100).optional(),
    noShowRatePercent: z.number().min(0).max(100).optional(),
    aircraftUtilizationPercent: z.number().min(0).max(100).optional(),
    averageBookingLeadDays: z.number().positive().optional(),
  }).optional(),

  experience: z.object({
    npsScore: z.number().min(-100).max(100).optional(),
    satisfactionRating: z.number().min(1).max(5).optional(),
    repeatCustomerRate: z.number().min(0).max(100).optional(),
    referralRatePercent: z.number().min(0).max(100).optional(),
  }).optional(),

  accreditation: z.object({
    inspectionScore: z.number().min(0).max(100).optional(),
    complianceViolationsCount: z.number().int().nonnegative().optional(),
    safetyIncidentCount: z.number().int().nonnegative().optional(),
  }).optional(),

  financial: z.object({
    yearsInOperation: z.number().int().nonnegative().optional(),
    valueScore: z.number().min(0).max(10).optional(),
    fleetAgeAverageYears: z.number().positive().optional(),
  }).optional(),

  // Metrics metadata
  metricsLastUpdated: z.string().datetime().optional(),
  dataSources: z.array(z.string()).default([]),
  sampleSize: z.number().int().nonnegative().optional(),
  overallReliabilityScore: z.number().min(0).max(10).optional(),
  overallQualityScore: z.number().min(0).max(10).optional(),

  // Provenance
  ...ProvenanceSchema.shape,

  // Metadata
  lastUpdated: z.string().datetime().default(() => new Date().toISOString()),
  isCurrent: z.boolean().default(true),
});

export const AttributesSchema = z.object({
  schoolId: z.string().regex(/^[a-zA-Z0-9_-]{8,50}$/, 'Invalid school ID format'),

  // Facilities and amenities
  amenities: z.array(z.object({
    type: z.string(),
    name: z.string().min(1).max(100),
    description: z.string().max(500).optional(),
    available: z.boolean().default(true),
  })).default([]),

  equipment: z.array(z.object({
    type: z.string(),
    name: z.string().min(1).max(100),
    description: z.string().max(500).optional(),
    available: z.boolean().default(true),
    quantity: z.number().int().positive().optional(),
  })).default([]),

  // Programs and offerings
  specialPrograms: z.array(z.object({
    type: z.string(),
    name: z.string().min(1).max(200),
    description: z.string().max(1000).optional(),
    active: z.boolean().default(true),
  })).default([]),

  certifications: z.array(z.object({
    name: z.string().min(1).max(200),
    issuer: z.string().min(1).max(100),
    issueDate: z.string().datetime().optional(),
    expiryDate: z.string().datetime().optional(),
    isActive: z.boolean().default(true),
  })).default([]),

  // Business relationships
  partnerships: z.array(z.object({
    partnerName: z.string().min(1).max(200),
    partnershipType: z.string().min(1).max(100),
    description: z.string().max(500).optional(),
    active: z.boolean().default(true),
  })).default([]),

  awards: z.array(z.object({
    name: z.string().min(1).max(200),
    issuer: z.string().min(1).max(100),
    year: z.number().int().min(1900).max(new Date().getFullYear()),
    description: z.string().max(500).optional(),
  })).default([]),

  // Flexible data
  customAttributes: z.record(z.string(), z.any()).default({}),
  socialMedia: z.record(z.string(), z.string()).default({}),
  onlinePresence: z.record(z.string(), z.any()).default({}),
  operationalNotes: z.array(z.string()).default([]),

  // Provenance
  ...ProvenanceSchema.shape,

  // Metadata
  lastUpdated: z.string().datetime().default(() => new Date().toISOString()),
});

// ============================================================================
// API Response Schemas
// ============================================================================

export const SchoolResponseSchema = SchoolSchema.extend({
  id: z.number().int().positive(),
});

export const ProgramResponseSchema = ProgramSchema.extend({
  id: z.number().int().positive(),
});

export const PricingResponseSchema = PricingSchema.extend({
  id: z.number().int().positive(),
});

export const MetricsResponseSchema = MetricsSchema.extend({
  id: z.number().int().positive(),
});

export const AttributesResponseSchema = AttributesSchema.extend({
  id: z.number().int().positive(),
});

// ============================================================================
// API Query Parameter Schemas
// ============================================================================

export const SchoolsQuerySchema = z.object({
  // Location filters
  city: z.string().optional(),
  state: z.string().optional(),
  lat: z.number().min(-90).max(90).optional(),
  lng: z.number().min(-180).max(180).optional(),
  radius: z.number().positive().optional(), // miles

  // Accreditation filters
  accreditation: z.enum(['Part 61', 'Part 141']).optional(),
  vaApproved: z.boolean().optional(),

  // Cost filters
  maxCost: z.number().positive().optional(),
  costBand: CostBandSchema.optional(),

  // Rating filters
  minRating: z.number().min(1).max(5).optional(),

  // Pagination
  page: z.number().int().min(1).default(1),
  limit: z.number().int().min(1).max(100).default(20),

  // Sorting
  sortBy: z.enum(['name', 'rating', 'cost', 'distance']).default('name'),
  sortOrder: z.enum(['asc', 'desc']).default('asc'),
});

export const SchoolDetailQuerySchema = z.object({
  includePrograms: z.boolean().default(true),
  includePricing: z.boolean().default(true),
  includeMetrics: z.boolean().default(false),
  includeAttributes: z.boolean().default(false),
});

// ============================================================================
// Type Exports
// ============================================================================

export type School = z.infer<typeof SchoolSchema>;
export type Program = z.infer<typeof ProgramSchema>;
export type Pricing = z.infer<typeof PricingSchema>;
export type Metrics = z.infer<typeof MetricsSchema>;
export type Attributes = z.infer<typeof AttributesSchema>;

export type SchoolResponse = z.infer<typeof SchoolResponseSchema>;
export type ProgramResponse = z.infer<typeof ProgramResponseSchema>;
export type PricingResponse = z.infer<typeof PricingResponseSchema>;
export type MetricsResponse = z.infer<typeof MetricsResponseSchema>;
export type AttributesResponse = z.infer<typeof AttributesResponseSchema>;

export type SchoolsQuery = z.infer<typeof SchoolsQuerySchema>;
export type SchoolDetailQuery = z.infer<typeof SchoolDetailQuerySchema>;
