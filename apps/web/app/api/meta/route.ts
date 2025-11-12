/**
 * Metadata API Route
 *
 * GET /api/meta - Retrieve system metadata and data coverage statistics
 *
 * Returns comprehensive information about the flight school dataset including:
 * - Current snapshot information
 * - Data coverage statistics
 * - Last ETL run timestamp
 * - System health indicators
 */

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { db, handleDatabaseError } from '../../../lib/db';
import { sql } from 'drizzle-orm';

// ============================================================================
// Response Schema Validation
// ============================================================================

/**
 * Coverage statistics schema
 */
const CoverageStatsSchema = z.object({
  totalSchools: z.number(),
  totalPrograms: z.number(),
  totalPricingRecords: z.number(),
  schoolsWithPricing: z.number(),
  schoolsWithPrograms: z.number(),
  geographicCoverage: z.object({
    statesCovered: z.number(),
    countriesCovered: z.number(),
  }),
  dataCompleteness: z.object({
    pricingCompletenessPercent: z.number(),
    programCompletenessPercent: z.number(),
  }),
});

/**
 * Metadata response schema
 */
const MetadataResponseSchema = z.object({
  snapshotId: z.string(),
  lastEtlRun: z.string(),
  asOf: z.string(),
  coverage: CoverageStatsSchema,
  version: z.string(),
  generatedAt: z.string(),
});

/**
 * Error response schema
 */
const ErrorResponseSchema = z.object({
  error: z.string(),
  message: z.string(),
  timestamp: z.string(),
});

// ============================================================================
// Database Queries
// ============================================================================

/**
 * Get the most recent snapshot ID from the database
 */
async function getLatestSnapshotId(): Promise<string | null> {
  try {
    const result = await db.execute(sql`
      SELECT DISTINCT snapshot_id
      FROM schools
      ORDER BY snapshot_id DESC
      LIMIT 1
    `);

    return (result[0]?.snapshot_id as string) || null;
  } catch (error) {
    console.error('Error fetching latest snapshot ID:', error);
    return null;
  }
}

/**
 * Get the most recent ETL run timestamp
 */
async function getLastEtlRun(): Promise<Date | null> {
  try {
    const result = await db.execute(sql`
      SELECT MAX(extracted_at) as last_run
      FROM schools
    `);

    return (result[0]?.last_run as Date) || null;
  } catch (error) {
    console.error('Error fetching last ETL run:', error);
    return null;
  }
}

/**
 * Get comprehensive coverage statistics
 */
async function getCoverageStatistics(): Promise<z.infer<typeof CoverageStatsSchema>> {
  try {
    // Get total counts
    const [schoolsResult, programsResult, pricingResult] = await Promise.all([
      db.execute(sql`SELECT COUNT(*) as count FROM schools`),
      db.execute(sql`SELECT COUNT(*) as count FROM programs`),
      db.execute(sql`SELECT COUNT(*) as count FROM pricing`),
    ]);

    const totalSchools = parseInt((schoolsResult[0]?.count as string) || '0');
    const totalPrograms = parseInt((programsResult[0]?.count as string) || '0');
    const totalPricingRecords = parseInt((pricingResult[0]?.count as string) || '0');

    // Get schools with pricing data
    const schoolsWithPricingResult = await db.execute(sql`
      SELECT COUNT(DISTINCT school_id) as count
      FROM pricing
    `);
    const schoolsWithPricing = parseInt((schoolsWithPricingResult[0]?.count as string) || '0');

    // Get schools with programs data
    const schoolsWithProgramsResult = await db.execute(sql`
      SELECT COUNT(DISTINCT school_id) as count
      FROM programs
    `);
    const schoolsWithPrograms = parseInt((schoolsWithProgramsResult[0]?.count as string) || '0');

    // Get geographic coverage
    const [statesResult, countriesResult] = await Promise.all([
      db.execute(sql`
        SELECT COUNT(DISTINCT location->>'state') as count
        FROM schools
        WHERE location->>'state' IS NOT NULL
      `),
      db.execute(sql`
        SELECT COUNT(DISTINCT location->>'country') as count
        FROM schools
        WHERE location->>'country' IS NOT NULL
      `),
    ]);

    const statesCovered = parseInt((statesResult[0]?.count as string) || '0');
    const countriesCovered = parseInt((countriesResult[0]?.count as string) || '0');

    // Calculate completeness percentages
    const pricingCompletenessPercent = totalSchools > 0 ? (schoolsWithPricing / totalSchools) * 100 : 0;
    const programCompletenessPercent = totalSchools > 0 ? (schoolsWithPrograms / totalSchools) * 100 : 0;

    return {
      totalSchools,
      totalPrograms,
      totalPricingRecords,
      schoolsWithPricing,
      schoolsWithPrograms,
      geographicCoverage: {
        statesCovered,
        countriesCovered,
      },
      dataCompleteness: {
        pricingCompletenessPercent: Math.round(pricingCompletenessPercent * 100) / 100,
        programCompletenessPercent: Math.round(programCompletenessPercent * 100) / 100,
      },
    };
  } catch (error) {
    console.error('Error fetching coverage statistics:', error);
    throw error;
  }
}

// ============================================================================
// API Route Handler
// ============================================================================

/**
 * GET /api/meta - Retrieve system metadata and coverage statistics
 */
export async function GET(request: NextRequest) {
  const startTime = Date.now();

  try {
    // Fetch all metadata in parallel
    const [snapshotId, lastEtlRun, coverage] = await Promise.allSettled([
      getLatestSnapshotId(),
      getLastEtlRun(),
      getCoverageStatistics(),
    ]);

    // Extract values, handling rejections
    const snapshotIdValue = snapshotId.status === 'fulfilled' ? snapshotId.value : null;
    const lastEtlRunValue = lastEtlRun.status === 'fulfilled' ? lastEtlRun.value : null;
    const coverageValue = coverage.status === 'fulfilled' ? coverage.value : null;

    // Check if any critical queries failed
    const hasDatabaseError = [snapshotId, lastEtlRun, coverage].some(result => result.status === 'rejected');

    // Validate that we have required data
    if (!snapshotIdValue) {
      return NextResponse.json(
        {
          error: 'NO_DATA',
          message: 'No flight school data found in the system',
          timestamp: new Date().toISOString(),
        } satisfies z.infer<typeof ErrorResponseSchema>,
        { status: 404 }
      );
    }

    if (!lastEtlRunValue) {
      return NextResponse.json(
        {
          error: 'NO_ETL_RUN',
          message: 'No ETL run timestamp found',
          timestamp: new Date().toISOString(),
        } satisfies z.infer<typeof ErrorResponseSchema>,
        { status: 404 }
      );
    }

    if (!coverageValue) {
      return NextResponse.json(
        {
          error: 'NO_COVERAGE_DATA',
          message: 'Unable to calculate coverage statistics',
          timestamp: new Date().toISOString(),
        } satisfies z.infer<typeof ErrorResponseSchema>,
        { status: 500 }
      );
    }

    // Build response
    const response = {
      snapshotId: snapshotIdValue,
      lastEtlRun: lastEtlRunValue.toISOString(),
      asOf: new Date().toISOString(), // Current timestamp when API is called
      coverage: coverageValue,
      version: '1.0.0',
      generatedAt: new Date().toISOString(),
    };

    // Validate response against schema
    const validatedResponse = MetadataResponseSchema.parse(response);

    const duration = Date.now() - startTime;
    console.log(`Metadata API request completed in ${duration}ms`);

    // Return response with caching headers
    return NextResponse.json(validatedResponse, {
      headers: {
        'Cache-Control': 'public, s-maxage=300, stale-while-revalidate=600', // Cache for 5 minutes, serve stale for 10 minutes
        'CDN-Cache-Control': 'max-age=300',
        'Vercel-CDN-Cache-Control': 'max-age=300',
      },
    });

  } catch (error) {
    console.error('Metadata API error:', error);

    // Handle database errors
    if (error && typeof error === 'object' && 'code' in error) {
      const dbError = handleDatabaseError(error);
      return NextResponse.json(
        {
          error: 'DATABASE_ERROR',
          message: dbError,
          timestamp: new Date().toISOString(),
        } satisfies z.infer<typeof ErrorResponseSchema>,
        { status: 500 }
      );
    }

    // Handle validation errors
    if (error && typeof error === 'object' && 'name' in error && error.name === 'ZodError') {
      return NextResponse.json(
        {
          error: 'VALIDATION_ERROR',
          message: 'Response validation failed',
          timestamp: new Date().toISOString(),
        } satisfies z.infer<typeof ErrorResponseSchema>,
        { status: 500 }
      );
    }

    // Generic error
    return NextResponse.json(
      {
        error: 'INTERNAL_ERROR',
        message: 'An unexpected error occurred',
        timestamp: new Date().toISOString(),
      } satisfies z.infer<typeof ErrorResponseSchema>,
      { status: 500 }
    );
  }
}

// ============================================================================
// Development Helpers
// ============================================================================

/**
 * Force refresh cache (for development)
 * GET /api/meta?refresh=true
 */
export async function POST(request: NextRequest) {
  // This endpoint can be used to force refresh any cached data
  // For now, just return the same as GET
  return GET(request);
}
