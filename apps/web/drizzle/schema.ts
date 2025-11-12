/**
 * Drizzle ORM Schema for WheelsUp Flight School Database
 *
 * This schema defines the PostgreSQL tables for storing flight school data,
 * including schools, programs, pricing, metrics, and attributes.
 *
 * All tables include provenance tracking for auditability and data freshness.
 */

import { pgTable, text, integer, real, boolean, timestamp, jsonb, serial, varchar, index, uniqueIndex } from 'drizzle-orm/pg-core';
import { relations } from 'drizzle-orm';

// ============================================================================
// Core Entity: Schools
// ============================================================================

export const schools = pgTable('schools', {
  // Primary key
  id: serial('id').primaryKey(),

  // Core identifiers
  schoolId: varchar('school_id', { length: 50 }).notNull().unique(),
  name: varchar('name', { length: 200 }).notNull(),

  // Descriptive information
  description: text('description'),
  specialties: jsonb('specialties').$type<string[]>(),

  // Contact information (stored as JSON for flexibility)
  contact: jsonb('contact').$type<{
    phone?: string;
    email?: string;
    website?: string;
  }>(),

  // Location information
  location: jsonb('location').$type<{
    address?: string;
    city?: string;
    state?: string;
    zipCode?: string;
    country: string;
    latitude?: number;
    longitude?: number;
    nearestAirportIcao?: string;
    nearestAirportName?: string;
    airportDistanceMiles?: number;
  }>(),

  // Accreditation and operations
  accreditation: jsonb('accreditation').$type<{
    type?: string;
    certificateNumber?: string;
    inspectionDate?: string;
    vaApproved?: boolean;
  }>(),

  operations: jsonb('operations').$type<{
    foundedYear?: number;
    employeeCount?: number;
    fleetSize?: number;
    studentCapacity?: number;
  }>(),

  // External references
  googleRating: real('google_rating'),
  googleReviewCount: integer('google_review_count'),
  yelpRating: real('yelp_rating'),

  // Provenance tracking (required for all records)
  sourceType: varchar('source_type', { length: 50 }).notNull(),
  sourceUrl: text('source_url').notNull(),
  extractedAt: timestamp('extracted_at', { withTimezone: true }).notNull().defaultNow(),
  confidence: real('confidence').notNull(),
  extractorVersion: varchar('extractor_version', { length: 20 }).notNull(),
  snapshotId: varchar('snapshot_id', { length: 50 }).notNull(),

  // Metadata
  lastUpdated: timestamp('last_updated', { withTimezone: true }).notNull().defaultNow(),
  isActive: boolean('is_active').notNull().default(true),
}, (table) => ({
  schoolIdIdx: uniqueIndex('schools_school_id_idx').on(table.schoolId),
  nameIdx: index('schools_name_idx').on(table.name),
  locationIdx: index('schools_location_idx').on(table.location),
  accreditationIdx: index('schools_accreditation_idx').on(table.accreditation),
  snapshotIdx: index('schools_snapshot_idx').on(table.snapshotId),
}));

// ============================================================================
// Programs Table
// ============================================================================

export const programs = pgTable('programs', {
  // Primary key
  id: serial('id').primaryKey(),

  // Foreign key to schools
  schoolId: varchar('school_id', { length: 50 }).notNull().references(() => schools.schoolId, { onDelete: 'cascade' }),

  // Program identifiers
  programId: varchar('program_id', { length: 50 }).notNull().unique(),
  details: jsonb('details').$type<{
    programType: string;
    name: string;
    description?: string;
    duration: {
      hoursMin?: number;
      hoursMax?: number;
      hoursTypical?: number;
      weeksMin?: number;
      weeksMax?: number;
      weeksTypical?: number;
    };
    requirements: {
      ageMinimum?: number;
      englishProficiency?: boolean;
      medicalCertificateClass?: string;
      priorCertifications: string[];
      flightExperienceHours?: number;
    };
    includesGroundSchool?: boolean;
    includesCheckride?: boolean;
    aircraftTypes: string[];
    part61Available: boolean;
    part141Available: boolean;
    isPopular?: boolean;
  }>().notNull(),

  // Operational info
  isActive: boolean('is_active').notNull().default(true),
  seasonalAvailability: text('seasonal_availability'),

  // Provenance tracking
  sourceType: varchar('source_type', { length: 50 }).notNull(),
  sourceUrl: text('source_url').notNull(),
  extractedAt: timestamp('extracted_at', { withTimezone: true }).notNull().defaultNow(),
  confidence: real('confidence').notNull(),
  extractorVersion: varchar('extractor_version', { length: 20 }).notNull(),
  snapshotId: varchar('snapshot_id', { length: 50 }).notNull(),

  // Metadata
  lastUpdated: timestamp('last_updated', { withTimezone: true }).notNull().defaultNow(),
}, (table) => ({
  programIdIdx: uniqueIndex('programs_program_id_idx').on(table.programId),
  schoolIdIdx: index('programs_school_id_idx').on(table.schoolId),
  programTypeIdx: index('programs_type_idx').on(table.details),
  snapshotIdx: index('programs_snapshot_idx').on(table.snapshotId),
}));

// ============================================================================
// Pricing Table
// ============================================================================

export const pricing = pgTable('pricing', {
  // Primary key
  id: serial('id').primaryKey(),

  // Foreign key to schools
  schoolId: varchar('school_id', { length: 50 }).notNull().references(() => schools.schoolId, { onDelete: 'cascade' }),

  // Pricing structures
  hourlyRates: jsonb('hourly_rates').$type<Array<{
    aircraftCategory: string;
    ratePerHour: number;
    includesInstructor: boolean;
    includesFuel?: boolean;
    blockHoursMin?: number;
    blockHoursMax?: number;
  }>>(),

  packagePricing: jsonb('package_pricing').$type<Array<{
    programType: string;
    packageName: string;
    totalCost: number;
    flightHoursIncluded?: number;
    groundHoursIncluded?: number;
    includesMaterials: boolean;
    validForMonths?: number;
    completionDeadlineMonths?: number;
  }>>(),

  // Normalized cost estimates
  programCosts: jsonb('program_costs').$type<Array<{
    programType: string;
    costBand: string;
    estimatedTotalMin?: number;
    estimatedTotalMax?: number;
    estimatedTotalTypical?: number;
    flightCostEstimate?: number;
    groundCostEstimate?: number;
    materialsCostEstimate?: number;
    examFeesEstimate?: number;
    assumptions: Record<string, any>;
  }>>(),

  // Additional fees
  additionalFees: jsonb('additional_fees').$type<{
    checkrideFee?: number;
    medicalExamFee?: number;
    knowledgeTestFee?: number;
    membershipFee?: number;
    multiEngineSurcharge?: number;
    nightSurcharge?: number;
    weekendSurcharge?: number;
    enrollmentDeposit?: number;
    paymentPlansAvailable?: boolean;
  }>(),

  // Pricing metadata
  currency: varchar('currency', { length: 3 }).notNull().default('USD'),
  priceLastUpdated: timestamp('price_last_updated', { withTimezone: true }),

  // Value propositions
  valueInclusions: jsonb('value_inclusions').$type<string[]>(),
  scholarshipsAvailable: boolean('scholarships_available'),

  // Provenance tracking
  sourceType: varchar('source_type', { length: 50 }).notNull(),
  sourceUrl: text('source_url').notNull(),
  extractedAt: timestamp('extracted_at', { withTimezone: true }).notNull().defaultNow(),
  confidence: real('confidence').notNull(),
  extractorVersion: varchar('extractor_version', { length: 20 }).notNull(),
  snapshotId: varchar('snapshot_id', { length: 50 }).notNull(),

  // Metadata
  lastUpdated: timestamp('last_updated', { withTimezone: true }).notNull().defaultNow(),
}, (table) => ({
  schoolIdIdx: index('pricing_school_id_idx').on(table.schoolId),
  snapshotIdx: index('pricing_snapshot_idx').on(table.snapshotId),
}));

// ============================================================================
// Metrics Table
// ============================================================================

export const metrics = pgTable('metrics', {
  // Primary key
  id: serial('id').primaryKey(),

  // Foreign key to schools
  schoolId: varchar('school_id', { length: 50 }).notNull().references(() => schools.schoolId, { onDelete: 'cascade' }),

  // Training metrics
  training: jsonb('training').$type<{
    averageCompletionMonths?: number;
    completionRatePercent?: number;
    passRateFirstAttempt?: number;
    averageHoursPerMonth?: number;
    soloRatePercent?: number;
    dropoutRatePercent?: number;
  }>(),

  // Operational metrics
  operational: jsonb('operational').$type<{
    cancellationRatePercent?: number;
    noShowRatePercent?: number;
    aircraftUtilizationPercent?: number;
    averageBookingLeadDays?: number;
  }>(),

  // Experience metrics
  experience: jsonb('experience').$type<{
    npsScore?: number;
    satisfactionRating?: number;
    repeatCustomerRate?: number;
    referralRatePercent?: number;
  }>(),

  // Accreditation metrics
  accreditation: jsonb('accreditation').$type<{
    inspectionScore?: number;
    complianceViolationsCount?: number;
    safetyIncidentCount?: number;
  }>(),

  // Financial metrics
  financial: jsonb('financial').$type<{
    yearsInOperation?: number;
    valueScore?: number;
    fleetAgeAverageYears?: number;
  }>(),

  // Metrics metadata
  metricsLastUpdated: timestamp('metrics_last_updated', { withTimezone: true }),
  dataSources: jsonb('data_sources').$type<string[]>(),
  sampleSize: integer('sample_size'),

  // Overall scores
  overallReliabilityScore: real('overall_reliability_score'),
  overallQualityScore: real('overall_quality_score'),

  // Provenance tracking
  sourceType: varchar('source_type', { length: 50 }).notNull(),
  sourceUrl: text('source_url').notNull(),
  extractedAt: timestamp('extracted_at', { withTimezone: true }).notNull().defaultNow(),
  confidence: real('confidence').notNull(),
  extractorVersion: varchar('extractor_version', { length: 20 }).notNull(),
  snapshotId: varchar('snapshot_id', { length: 50 }).notNull(),

  // Metadata
  lastUpdated: timestamp('last_updated', { withTimezone: true }).notNull().defaultNow(),
  isCurrent: boolean('is_current').notNull().default(true),
}, (table) => ({
  schoolIdIdx: index('metrics_school_id_idx').on(table.schoolId),
  snapshotIdx: index('metrics_snapshot_idx').on(table.snapshotId),
  reliabilityScoreIdx: index('metrics_reliability_score_idx').on(table.overallReliabilityScore),
  qualityScoreIdx: index('metrics_quality_score_idx').on(table.overallQualityScore),
}));

// ============================================================================
// Attributes Table (Semi-structured data)
// ============================================================================

export const attributes = pgTable('attributes', {
  // Primary key
  id: serial('id').primaryKey(),

  // Foreign key to schools
  schoolId: varchar('school_id', { length: 50 }).notNull().references(() => schools.schoolId, { onDelete: 'cascade' }),

  // Facilities and amenities
  amenities: jsonb('amenities').$type<Array<{
    type: string;
    name: string;
    description?: string;
    available: boolean;
  }>>(),

  equipment: jsonb('equipment').$type<Array<{
    type: string;
    name: string;
    description?: string;
    available: boolean;
    quantity?: number;
  }>>(),

  // Programs and offerings
  specialPrograms: jsonb('special_programs').$type<Array<{
    type: string;
    name: string;
    description?: string;
    active: boolean;
  }>>(),

  certifications: jsonb('certifications').$type<Array<{
    name: string;
    issuer: string;
    issueDate?: string;
    expiryDate?: string;
    isActive: boolean;
  }>>(),

  // Business relationships
  partnerships: jsonb('partnerships').$type<Array<{
    partnerName: string;
    partnershipType: string;
    description?: string;
    active: boolean;
  }>>(),

  awards: jsonb('awards').$type<Array<{
    name: string;
    issuer: string;
    year: number;
    description?: string;
  }>>(),

  // Flexible custom attributes
  customAttributes: jsonb('custom_attributes'),

  // Social media and online presence
  socialMedia: jsonb('social_media').$type<Record<string, string>>(),
  onlinePresence: jsonb('online_presence'),

  // Operational notes
  operationalNotes: jsonb('operational_notes').$type<string[]>(),

  // Provenance tracking
  sourceType: varchar('source_type', { length: 50 }).notNull(),
  sourceUrl: text('source_url').notNull(),
  extractedAt: timestamp('extracted_at', { withTimezone: true }).notNull().defaultNow(),
  confidence: real('confidence').notNull(),
  extractorVersion: varchar('extractor_version', { length: 20 }).notNull(),
  snapshotId: varchar('snapshot_id', { length: 50 }).notNull(),

  // Metadata
  lastUpdated: timestamp('last_updated', { withTimezone: true }).notNull().defaultNow(),
}, (table) => ({
  schoolIdIdx: index('attributes_school_id_idx').on(table.schoolId),
  snapshotIdx: index('attributes_snapshot_idx').on(table.snapshotId),
}));

// ============================================================================
// Relations
// ============================================================================

export const schoolsRelations = relations(schools, ({ many }) => ({
  programs: many(programs),
  pricing: many(pricing),
  metrics: many(metrics),
  attributes: many(attributes),
}));

export const programsRelations = relations(programs, ({ one }) => ({
  school: one(schools, {
    fields: [programs.schoolId],
    references: [schools.schoolId],
  }),
}));

export const pricingRelations = relations(pricing, ({ one }) => ({
  school: one(schools, {
    fields: [pricing.schoolId],
    references: [schools.schoolId],
  }),
}));

export const metricsRelations = relations(metrics, ({ one }) => ({
  school: one(schools, {
    fields: [metrics.schoolId],
    references: [schools.schoolId],
  }),
}));

export const attributesRelations = relations(attributes, ({ one }) => ({
  school: one(schools, {
    fields: [attributes.schoolId],
    references: [schools.schoolId],
  }),
}));

// ============================================================================
// Type Exports
// ============================================================================

export type School = typeof schools.$inferSelect;
export type NewSchool = typeof schools.$inferInsert;

export type Program = typeof programs.$inferSelect;
export type NewProgram = typeof programs.$inferInsert;

export type Pricing = typeof pricing.$inferSelect;
export type NewPricing = typeof pricing.$inferInsert;

export type Metric = typeof metrics.$inferSelect;
export type NewMetric = typeof metrics.$inferInsert;

export type Attribute = typeof attributes.$inferSelect;
export type NewAttribute = typeof attributes.$inferInsert;
