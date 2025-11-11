/**
 * Schools API Route - List Endpoint
 *
 * GET /api/schools - Retrieve a paginated list of schools with optional filtering
 *
 * Query Parameters:
 * - city: Filter by city
 * - state: Filter by state
 * - lat, lng, radius: Geographic filtering (miles)
 * - accreditation: Filter by accreditation type (Part 61, Part 141)
 * - vaApproved: Filter by VA approval status
 * - maxCost: Filter by maximum cost
 * - costBand: Filter by cost band
 * - minRating: Filter by minimum rating
 * - page: Page number (default: 1)
 * - limit: Results per page (default: 20, max: 100)
 * - sortBy: Sort field (name, rating, cost, distance)
 * - sortOrder: Sort order (asc, desc)
 */

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { findSchools, handleDatabaseError } from '../../../lib/db';
import { SchoolsQuerySchema } from '../../../lib/schemas';

// ============================================================================
// Request Validation
// ============================================================================

/**
 * Validate and parse query parameters
 */
function validateQueryParams(request: NextRequest) {
  const { searchParams } = new URL(request.url);

  // Parse query parameters
  const queryData = {
    city: searchParams.get('city'),
    state: searchParams.get('state'),
    lat: searchParams.get('lat') ? parseFloat(searchParams.get('lat')!) : undefined,
    lng: searchParams.get('lng') ? parseFloat(searchParams.get('lng')!) : undefined,
    radius: searchParams.get('radius') ? parseFloat(searchParams.get('radius')!) : undefined,
    accreditation: searchParams.get('accreditation'),
    vaApproved: searchParams.get('vaApproved') === 'true' ? true :
               searchParams.get('vaApproved') === 'false' ? false : undefined,
    maxCost: searchParams.get('maxCost') ? parseFloat(searchParams.get('maxCost')!) : undefined,
    costBand: searchParams.get('costBand'),
    minRating: searchParams.get('minRating') ? parseFloat(searchParams.get('minRating')!) : undefined,
    page: searchParams.get('page') ? parseInt(searchParams.get('page')!) : 1,
    limit: searchParams.get('limit') ? parseInt(searchParams.get('limit')!) : 20,
    sortBy: searchParams.get('sortBy') || 'name',
    sortOrder: searchParams.get('sortOrder') || 'asc',
  };

  // Validate with Zod schema
  return SchoolsQuerySchema.parse(queryData);
}

/**
 * Build database filters from validated query parameters
 */
function buildDatabaseFilters(queryParams: any) {
  const dbFilters: any = {};

  // Basic filters that can be handled by database
  if (queryParams.state) dbFilters.state = queryParams.state;
  if (queryParams.vaApproved !== undefined) dbFilters.vaApproved = queryParams.vaApproved;
  if (queryParams.minRating) dbFilters.minRating = queryParams.minRating;

  // Pagination
  dbFilters.limit = Math.min(queryParams.limit, 100); // Max 100 per page
  dbFilters.offset = (queryParams.page - 1) * dbFilters.limit;

  return dbFilters;
}

/**
 * Apply application-level filtering that requires business logic
 */
function applyApplicationFilters(schools: any[], queryParams: any) {
  let filteredSchools = schools;

  // Geographic filtering (placeholder)
  filteredSchools = applyGeoFiltering(
    filteredSchools,
    queryParams.lat,
    queryParams.lng,
    queryParams.radius
  );

  // Cost band filtering (would require joining with pricing table)
  if (queryParams.costBand) {
    // Placeholder: In production, this would join with pricing table
    // For now, skip this filter
  }

  // Accreditation filtering
  if (queryParams.accreditation) {
    filteredSchools = filteredSchools.filter(
      school => school.accreditation?.type === queryParams.accreditation
    );
  }

  // City filtering
  if (queryParams.city) {
    filteredSchools = filteredSchools.filter(
      school => school.location?.city?.toLowerCase() === queryParams.city?.toLowerCase()
    );
  }

  return filteredSchools;
}

/**
 * Calculate pagination metadata
 */
function calculatePagination(schools: any[], queryParams: any) {
  const totalCount = schools.length; // In production, this would be a separate COUNT query
  const totalPages = Math.ceil(totalCount / queryParams.limit);

  return {
    page: queryParams.page,
    limit: queryParams.limit,
    totalCount,
    totalPages,
    hasNext: queryParams.page < totalPages,
    hasPrev: queryParams.page > 1,
  };
}

/**
 * Build complete API response
 */
function buildSchoolsResponse(filteredSchools: any[], queryParams: any, pagination: any) {
  // Format response
  const formattedSchools = filteredSchools.map(formatSchoolResponse);

  return {
    schools: formattedSchools,
    pagination,
    filters: {
      applied: {
        city: queryParams.city,
        state: queryParams.state,
        accreditation: queryParams.accreditation,
        vaApproved: queryParams.vaApproved,
        costBand: queryParams.costBand,
        minRating: queryParams.minRating,
        lat: queryParams.lat,
        lng: queryParams.lng,
        radius: queryParams.radius,
      },
    },
    metadata: {
      snapshotId: '2025Q1-MVP', // Would come from current snapshot
      asOf: new Date().toISOString(),
      totalSchoolsIndexed: pagination.totalCount,
    },
  };
}

// ============================================================================
// Response Formatting
// ============================================================================

/**
 * Format school data for API response
 * Strips internal fields and formats for frontend consumption
 */
function formatSchoolResponse(school: any) {
  return {
    id: school.id,
    schoolId: school.schoolId,
    name: school.name,
    description: school.description,
    city: school.location?.city,
    state: school.location?.state,
    latitude: school.location?.latitude,
    longitude: school.location?.longitude,
    accreditation: school.accreditation?.type,
    vaApproved: school.accreditation?.vaApproved,
    googleRating: school.googleRating,
    googleReviewCount: school.googleReviewCount,
    // Include provenance metadata
    lastUpdated: school.lastUpdated,
    confidence: school.confidence,
    snapshotId: school.snapshotId,
  };
}

// ============================================================================
// Sorting Logic
// ============================================================================

/**
 * Apply sorting to school results
 */
function sortSchools(schools: any[], sortBy: string, sortOrder: 'asc' | 'desc') {
  return schools.sort((a, b) => {
    let aValue, bValue;

    switch (sortBy) {
      case 'name':
        aValue = a.name?.toLowerCase() || '';
        bValue = b.name?.toLowerCase() || '';
        break;
      case 'rating':
        aValue = a.googleRating || 0;
        bValue = b.googleRating || 0;
        break;
      case 'cost':
        // For now, sort by school ID as proxy for cost data
        // In production, this would use pricing data
        aValue = a.schoolId;
        bValue = b.schoolId;
        break;
      case 'distance':
        // Distance sorting would require geo queries
        // For now, sort by name
        aValue = a.name?.toLowerCase() || '';
        bValue = b.name?.toLowerCase() || '';
        break;
      default:
        aValue = a.name?.toLowerCase() || '';
        bValue = b.name?.toLowerCase() || '';
    }

    if (sortOrder === 'desc') {
      return aValue < bValue ? 1 : aValue > bValue ? -1 : 0;
    } else {
      return aValue > bValue ? 1 : aValue < bValue ? -1 : 0;
    }
  });
}

// ============================================================================
// Geographic Filtering
// ============================================================================

/**
 * Apply geographic filtering using PostGIS (when available)
 * For now, this is a placeholder that would use ST_DWithin or similar
 */
function applyGeoFiltering(schools: any[], lat?: number, lng?: number, radius?: number) {
  if (!lat || !lng || !radius) return schools;

  // Placeholder: In production, this would use PostGIS spatial queries
  // For now, return all schools (spatial filtering would be done in the database)
  return schools;
}

// ============================================================================
// Main Route Handler
// ============================================================================

/**
 * Process schools list request
 * Handles parameter validation, data fetching, filtering, and response formatting
 */
async function processSchoolsRequest(request: NextRequest) {
  // Validate and parse query parameters
  const queryParams = validateQueryParams(request);

  // Build database filters and fetch schools
  const dbFilters = buildDatabaseFilters(queryParams);
  const schools = await findSchools(dbFilters);

  // Apply application-level filtering
  let filteredSchools = applyApplicationFilters(schools, queryParams);

  // Apply sorting
  filteredSchools = sortSchools(
    filteredSchools,
    queryParams.sortBy,
    queryParams.sortOrder as 'asc' | 'desc'
  );

  // Calculate pagination and build response
  const pagination = calculatePagination(schools, queryParams);
  const responseData = buildSchoolsResponse(filteredSchools, queryParams, pagination);

  return { responseData, queryParams };
}

/**
 * Handle API errors and return appropriate responses
 */
function handleApiError(error: any): NextResponse {
  console.error('Error in schools API:', error);

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

  // Handle database errors
  const errorMessage = handleDatabaseError(error);
  return NextResponse.json(
    { error: errorMessage },
    { status: 500 }
  );
}

export async function GET(request: NextRequest) {
  try {
    const { responseData } = await processSchoolsRequest(request);

    // Create response with caching headers
    const response = NextResponse.json(responseData);
    response.headers.set('Cache-Control', 'public, s-maxage=300, stale-while-revalidate=600');
    response.headers.set('X-API-Version', '1.0.0');

    return response;
  } catch (error) {
    return handleApiError(error);
  }
}

// ============================================================================
// Method Not Allowed Handler
// ============================================================================

export async function POST(request: NextRequest) {
  return NextResponse.json(
    { error: 'Method not allowed' },
    { status: 405 }
  );
}

export async function PUT(request: NextRequest) {
  return NextResponse.json(
    { error: 'Method not allowed' },
    { status: 405 }
  );
}

export async function DELETE(request: NextRequest) {
  return NextResponse.json(
    { error: 'Method not allowed' },
    { status: 405 }
  );
}
