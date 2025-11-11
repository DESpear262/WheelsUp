/**
 * School Detail API Route
 *
 * GET /api/schools/[id] - Retrieve detailed information for a specific school
 *
 * Query Parameters:
 * - includePrograms: Include program offerings (default: true)
 * - includePricing: Include pricing information (default: true)
 * - includeMetrics: Include performance metrics (default: false)
 * - includeAttributes: Include additional attributes (default: false)
 */

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { findSchoolById, findProgramsBySchool, findPricingBySchool, handleDatabaseError } from '../../../../lib/db';
import { SchoolDetailQuerySchema } from '../../../../lib/schemas';

// ============================================================================
// Request Validation
// ============================================================================

/**
 * Validate and parse query parameters
 */
function validateQueryParams(request: NextRequest) {
  const { searchParams } = new URL(request.url);

  const queryData = {
    includePrograms: searchParams.get('includePrograms') !== 'false', // Default true
    includePricing: searchParams.get('includePricing') !== 'false', // Default true
    includeMetrics: searchParams.get('includeMetrics') === 'true', // Default false
    includeAttributes: searchParams.get('includeAttributes') === 'true', // Default false
  };

  return SchoolDetailQuerySchema.parse(queryData);
}

/**
 * Validate school ID parameter
 */
function validateSchoolId(id: string): string {
  if (!id || typeof id !== 'string' || id.length < 8 || id.length > 50) {
    throw new Error('Invalid school ID format');
  }

  // Check format (alphanumeric with dashes/underscores)
  if (!/^[a-zA-Z0-9_-]+$/.test(id)) {
    throw new Error('Invalid school ID characters');
  }

  return id;
}

// ============================================================================
// Response Formatting
// ============================================================================

/**
 * Format complete school data for API response
 */
function formatSchoolDetail(school: any, options: {
  includePrograms?: boolean;
  includePricing?: boolean;
  includeMetrics?: boolean;
  includeAttributes?: boolean;
} = {}) {
  const baseSchool = {
    id: school.id,
    schoolId: school.schoolId,
    name: school.name,
    description: school.description,
    specialties: school.specialties,

    // Contact information
    contact: school.contact,

    // Location information
    location: school.location,

    // Accreditation and operations
    accreditation: school.accreditation,
    operations: school.operations,

    // External references
    googleRating: school.googleRating,
    googleReviewCount: school.googleReviewCount,
    yelpRating: school.yelpRating,

    // Provenance metadata
    sourceType: school.sourceType,
    sourceUrl: school.sourceUrl,
    extractedAt: school.extractedAt,
    confidence: school.confidence,
    extractorVersion: school.extractorVersion,
    snapshotId: school.snapshotId,
    lastUpdated: school.lastUpdated,
    isActive: school.isActive,
  };

  const response: any = { school: baseSchool };

  // Add optional related data
  if (options.includePrograms) {
    response.programs = []; // Would be populated from database
  }

  if (options.includePricing) {
    response.pricing = null; // Would be populated from database
  }

  if (options.includeMetrics) {
    response.metrics = null; // Would be populated from database
  }

  if (options.includeAttributes) {
    response.attributes = null; // Would be populated from database
  }

  return response;
}

/**
 * Format program data for inclusion in school detail
 */
function formatProgramsForSchool(programs: any[]) {
  return programs.map(program => ({
    id: program.id,
    programId: program.programId,
    name: program.details?.name,
    programType: program.details?.programType,
    description: program.details?.description,
    duration: program.details?.duration,
    requirements: program.details?.requirements,
    aircraftTypes: program.details?.aircraftTypes,
    part61Available: program.details?.part61Available,
    part141Available: program.details?.part141Available,
    isActive: program.isActive,
    confidence: program.confidence,
  }));
}

/**
 * Format pricing data for inclusion in school detail
 */
function formatPricingForSchool(pricing: any) {
  if (!pricing) return null;

  return {
    id: pricing.id,
    hourlyRates: pricing.hourlyRates,
    packagePricing: pricing.packagePricing,
    programCosts: pricing.programCosts,
    additionalFees: pricing.additionalFees,
    currency: pricing.currency,
    priceLastUpdated: pricing.priceLastUpdated,
    valueInclusions: pricing.valueInclusions,
    scholarshipsAvailable: pricing.scholarshipsAvailable,
    confidence: pricing.confidence,
  };
}

/**
 * Fetch related data for a school based on query options
 */
async function fetchRelatedData(schoolId: string, queryOptions: any) {
  const relatedData: any = {};

  // Fetch programs if requested
  if (queryOptions.includePrograms) {
    try {
      const programs = await findProgramsBySchool(schoolId);
      relatedData.programs = formatProgramsForSchool(programs);
    } catch (error) {
      console.warn('Failed to fetch programs for school:', schoolId, error);
      relatedData.programs = [];
    }
  }

  // Fetch pricing if requested
  if (queryOptions.includePricing) {
    try {
      const pricing = await findPricingBySchool(schoolId);
      relatedData.pricing = formatPricingForSchool(pricing);
    } catch (error) {
      console.warn('Failed to fetch pricing for school:', schoolId, error);
      relatedData.pricing = null;
    }
  }

  // Metrics and attributes are placeholders for now
  if (queryOptions.includeMetrics) {
    relatedData.metrics = null; // Placeholder
  }

  if (queryOptions.includeAttributes) {
    relatedData.attributes = null; // Placeholder
  }

  return relatedData;
}

/**
 * Build metadata for the school response
 */
function buildSchoolMetadata(school: any, queryOptions: any, relatedData: any) {
  return {
    snapshotId: school.snapshotId,
    asOf: school.extractedAt,
    dataCompleteness: {
      hasPrograms: queryOptions.includePrograms ? (relatedData.programs?.length > 0) : null,
      hasPricing: queryOptions.includePricing ? (relatedData.pricing !== null) : null,
      hasMetrics: queryOptions.includeMetrics ? (relatedData.metrics !== null) : null,
      hasAttributes: queryOptions.includeAttributes ? (relatedData.attributes !== null) : null,
    },
  };
}

// ============================================================================
// Main Route Handler
// ============================================================================

/**
 * Process school detail request
 * Handles validation, data fetching, and response building
 */
async function processSchoolDetailRequest(
  request: NextRequest,
  params: { id: string }
) {
  // Validate inputs
  const schoolId = validateSchoolId(params.id);
  const queryOptions = validateQueryParams(request);

  // Fetch school data
  const school = await findSchoolById(schoolId);
  if (!school) {
    throw new Error('SCHOOL_NOT_FOUND');
  }

  // Fetch related data and build response
  const relatedData = await fetchRelatedData(schoolId, queryOptions);
  const metadata = buildSchoolMetadata(school, queryOptions, relatedData);

  const responseData = {
    school,
    ...relatedData,
    metadata,
  };

  return { responseData, schoolId, queryOptions };
}

/**
 * Handle API errors for school detail endpoint
 */
function handleSchoolDetailError(error: any): NextResponse {
  console.error('Error in school detail API:', error);

  // Handle validation errors
  if (error instanceof z.ZodError) {
    return NextResponse.json(
      {
        error: 'Invalid query parameters',
        details: error.errors.map(err => ({
          field: err.path.join('.'),
          message: err.message,
        })),
      },
      { status: 400 }
    );
  }

  // Handle custom validation errors
  if (error instanceof Error && error.message.includes('Invalid school ID')) {
    return NextResponse.json(
      { error: error.message },
      { status: 400 }
    );
  }

  // Handle school not found
  if (error instanceof Error && error.message === 'SCHOOL_NOT_FOUND') {
    return NextResponse.json(
      { error: 'School not found' },
      { status: 404 }
    );
  }

  // Handle database errors
  const errorMessage = handleDatabaseError(error);
  return NextResponse.json(
    { error: errorMessage },
    { status: 500 }
  );
}

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { responseData } = await processSchoolDetailRequest(request, params);

    // Create response with caching headers
    const response = NextResponse.json(responseData);
    response.headers.set('Cache-Control', 'public, s-maxage=180, stale-while-revalidate=300');
    response.headers.set('X-API-Version', '1.0.0');

    return response;
  } catch (error) {
    return handleSchoolDetailError(error);
  }
}

// ============================================================================
// Method Not Allowed Handler
// ============================================================================

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  return NextResponse.json(
    { error: 'Method not allowed' },
    { status: 405 }
  );
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  return NextResponse.json(
    { error: 'Method not allowed' },
    { status: 405 }
  );
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  return NextResponse.json(
    { error: 'Method not allowed' },
    { status: 405 }
  );
}
