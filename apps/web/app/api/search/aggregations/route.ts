/**
 * Search Aggregations API Route
 *
 * GET /api/search/aggregations - Get search filter aggregations/facets
 */

import { NextRequest, NextResponse } from 'next/server';
import { getSearchAggregations } from '../../../../lib/Newsearch';

export async function GET(request: NextRequest) {
  try {
    // Get aggregations from OpenSearch
    const aggregations = await getSearchAggregations();

    // Return response with caching headers
    const response = NextResponse.json(aggregations);
    response.headers.set('Cache-Control', 'public, s-maxage=900, stale-while-revalidate=1800'); // 15 min cache
    response.headers.set('X-API-Version', '1.0.0');

    return response;

  } catch (error) {
    console.error('Aggregations API error:', error);

    return NextResponse.json(
      {
        error: 'Search aggregations temporarily unavailable',
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
