/**
 * Search API Route
 *
 * GET /api/search - Search flight schools using OpenSearch
 *
 * Query Parameters:
 * - q: Search query string
 * - state: Filter by state
 * - city: Filter by city
 * - lat, lng: Geographic coordinates for location-based search
 * - radius: Search radius in miles (default: 100)
 * - vaApproved: Filter by VA approval (true/false)
 * - minRating: Minimum rating filter
 * - accreditation: Accreditation type filter
 * - specialties: Comma-separated list of specialties
 * - sort: Sort field (relevance, rating, name, distance)
 * - order: Sort order (asc, desc)
 * - page: Page number (default: 1)
 * - limit: Results per page (default: 20, max: 100)
 */

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { searchSchools, getSearchAggregations } from '../../../lib/Newsearch';

// ============================================================================
// Request Validation
// ============================================================================

const SearchQuerySchema = z.object({
  q: z.string().optional(),
  state: z.string().optional(),
  city: z.string().optional(),
  lat: z.string().transform(val => val ? parseFloat(val) : undefined).optional(),
  lng: z.string().transform(val => val ? parseFloat(val) : undefined).optional(),
  radius: z.string().transform(val => val ? parseFloat(val) : 100).optional(),
  vaApproved: z.enum(['true', 'false']).transform(val => val === 'true').optional(),
  minRating: z.string().transform(val => val ? parseFloat(val) : undefined).optional(),
  accreditation: z.string().optional(),
  specialties: z.string().optional(),
  sort: z.enum(['relevance', 'rating', 'name', 'distance']).optional(),
  order: z.enum(['asc', 'desc']).optional(),
  page: z.string().transform(val => val ? parseInt(val) : 1).optional(),
  limit: z.string().transform(val => val ? Math.min(parseInt(val), 100) : 20).optional(),
});

function validateSearchParams(request: NextRequest) {
  const { searchParams } = new URL(request.url);

  const queryData = {
    q: searchParams.get('q'),
    state: searchParams.get('state'),
    city: searchParams.get('city'),
    lat: searchParams.get('lat'),
    lng: searchParams.get('lng'),
    radius: searchParams.get('radius'),
    vaApproved: searchParams.get('vaApproved'),
    minRating: searchParams.get('minRating'),
    accreditation: searchParams.get('accreditation'),
    specialties: searchParams.get('specialties'),
    sort: searchParams.get('sort'),
    order: searchParams.get('order'),
    page: searchParams.get('page'),
    limit: searchParams.get('limit'),
  };

  return SearchQuerySchema.parse(queryData);
}

// ============================================================================
// Search Logic
// ============================================================================

export async function GET(request: NextRequest) {
  try {
    const params = validateSearchParams(request);

    // Build search parameters
    const searchParams = {
      query: params.q,
      location: params.lat && params.lng ? {
        lat: params.lat,
        lon: params.lng,
        distance: `${params.radius}mi`
      } : undefined,
      filters: {
        state: params.state,
        vaApproved: params.vaApproved,
        minRating: params.minRating,
        accreditationTypes: params.accreditation ? [params.accreditation] : undefined,
        specialties: params.specialties ? params.specialties.split(',').map(s => s.trim()) : undefined,
      },
      sort: params.sort ? {
        field: params.sort,
        order: params.order || 'desc'
      } : undefined,
      pagination: {
        page: params.page || 1,
        limit: params.limit || 20
      }
    };

    // Execute search
    const result = await searchSchools(searchParams);

    // Get aggregations for filters
    const aggregations = await getSearchAggregations();

    // Build response
    const response = {
      schools: result.schools,
      pagination: {
        page: result.page,
        limit: result.limit,
        total: result.total,
        hasNext: (result.page * result.limit) < result.total,
        hasPrev: result.page > 1
      },
      aggregations: {
        states: aggregations.states,
        accreditationTypes: aggregations.accreditationTypes,
        specialties: aggregations.specialties,
        vaApproved: aggregations.vaApproved,
        ratingRanges: aggregations.ratingRanges
      },
      metadata: {
        query: params.q,
        took: result.took,
        totalFound: result.total
      }
    };

    // Return response with caching headers
    const nextResponse = NextResponse.json(response);
    nextResponse.headers.set('Cache-Control', 'public, s-maxage=60, stale-while-revalidate=120');
    nextResponse.headers.set('X-API-Version', '1.0.0');

    return nextResponse;

  } catch (error) {
    console.error('Search API error:', error);

    // Handle validation errors
    if (error && typeof error === 'object' && 'name' in error && error.name === 'ZodError') {
      const zodError = error as any;
      return NextResponse.json(
        {
          error: 'Invalid search parameters',
          details: zodError.errors.map((err: any) => ({
            field: err.path.join('.'),
            message: err.message,
          })),
        },
        { status: 400 }
      );
    }

    // Handle search errors
    return NextResponse.json(
      {
        error: 'Search service temporarily unavailable',
        message: 'Please try again in a few moments'
      },
      { status: 503 }
    );
  }
}

// ============================================================================
// Method Handlers
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
