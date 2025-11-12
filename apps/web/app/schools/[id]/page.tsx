/**
 * School Profile Page
 *
 * Displays comprehensive information for a specific flight school.
 * Includes programs, pricing, location map, and data provenance.
 */

import { notFound } from 'next/navigation';
import { Metadata } from 'next';
import Link from 'next/link';
import { ArrowLeft, ExternalLink, MapPin, Star, Award, Users, Plane } from 'lucide-react';
import SchoolDetails from '../../../components/SchoolDetails';
import ProvenancePanel from '../../../components/ProvenancePanel';
import MapView from '../../../components/MapView';

// ============================================================================
// Types
// ============================================================================

interface SchoolProfilePageProps {
  params: Promise<{
    id: string;
  }>;
  searchParams: Promise<{
    includePrograms?: string;
    includePricing?: string;
    includeMetrics?: string;
    includeAttributes?: string;
  }>;
}

// ============================================================================
// Data Fetching
// ============================================================================

/**
 * Fetch school profile data from API
 */
async function fetchSchoolProfile(schoolId: string, options: {
  includePrograms?: boolean;
  includePricing?: boolean;
  includeMetrics?: boolean;
  includeAttributes?: boolean;
}) {
  try {
    const params = new URLSearchParams();

    if (options.includePrograms !== undefined) params.set('includePrograms', options.includePrograms.toString());
    if (options.includePricing !== undefined) params.set('includePricing', options.includePricing.toString());
    if (options.includeMetrics !== undefined) params.set('includeMetrics', options.includeMetrics.toString());
    if (options.includeAttributes !== undefined) params.set('includeAttributes', options.includeAttributes.toString());

    const queryString = params.toString();
    const url = `${process.env.NEXT_PUBLIC_API_URL || ''}/api/schools/${schoolId}${queryString ? `?${queryString}` : ''}`;

    const response = await fetch(url, {
      next: { revalidate: 300 }, // Cache for 5 minutes
    });

    if (!response.ok) {
      if (response.status === 404) {
        return null; // School not found
      }
      throw new Error(`Failed to fetch school data: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching school profile:', error);
    throw error;
  }
}

// ============================================================================
// Metadata Generation
// ============================================================================

export async function generateMetadata({ params }: SchoolProfilePageProps): Promise<Metadata> {
  try {
    const resolvedParams = await params;
    const data = await fetchSchoolProfile(resolvedParams.id, {
      includePrograms: false,
      includePricing: false,
      includeMetrics: false,
      includeAttributes: false
    });

    if (!data?.school) {
      return {
        title: 'School Not Found - WheelsUp',
        description: 'The requested flight school could not be found.',
      };
    }

    const school = data.school;
    const title = `${school.name} - Flight School Profile | WheelsUp`;
    const description = school.description ||
      `${school.name} is a ${school.accreditation?.type || 'flight'} accredited flight school located in ${school.location?.city || 'the area'}. View programs, pricing, and reviews.`;

    return {
      title,
      description,
      keywords: [
        'flight school',
        school.name,
        school.location?.city,
        school.location?.state,
        school.accreditation?.type,
        'pilot training',
        'aviation education'
      ].filter(Boolean),
      openGraph: {
        title,
        description,
        type: 'website',
        images: [
          {
            url: '/og-school-profile.png',
            width: 1200,
            height: 630,
            alt: `${school.name} - Flight School`,
          },
        ],
      },
      twitter: {
        card: 'summary_large_image',
        title,
        description,
        images: ['/og-school-profile.png'],
      },
    };
  } catch (error) {
    return {
      title: 'Flight School Profile - WheelsUp',
      description: 'View detailed information about flight schools and pilot training programs.',
    };
  }
}

// ============================================================================
// Main Page Component
// ============================================================================

export default async function SchoolProfilePage({ params, searchParams }: SchoolProfilePageProps) {
  const [resolvedParams, resolvedSearchParams] = await Promise.all([params, searchParams]);

  // Parse query parameters
  const includePrograms = resolvedSearchParams.includePrograms !== 'false'; // Default true
  const includePricing = resolvedSearchParams.includePricing !== 'false'; // Default true
  const includeMetrics = resolvedSearchParams.includeMetrics === 'true'; // Default false
  const includeAttributes = resolvedSearchParams.includeAttributes === 'true'; // Default false

  try {
    const data = await fetchSchoolProfile(resolvedParams.id, {
      includePrograms,
      includePricing,
      includeMetrics,
      includeAttributes,
    });

    if (!data?.school) {
      notFound();
    }

    const { school, programs, pricing, metrics, attributes, metadata } = data;

    return (
      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <Link
                href="/"
                className="inline-flex items-center text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Search
              </Link>

              <div className="text-sm text-gray-500">
                School ID: {school.schoolId}
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Content Column */}
            <div className="lg:col-span-2 space-y-8">
              {/* School Details */}
              <SchoolDetails
                school={school}
                programs={programs}
                pricing={pricing}
                metrics={metrics}
                attributes={attributes}
              />

              {/* Map View */}
              {school.location?.latitude && school.location?.longitude && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                  <div className="p-6 border-b border-gray-200">
                    <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                      <MapPin className="w-5 h-5 mr-2 text-blue-600" />
                      Location & Campus
                    </h2>
                  </div>
                  <div className="p-6">
                    <MapView
                      latitude={school.location.latitude}
                      longitude={school.location.longitude}
                      schoolName={school.name}
                      address={school.location.address}
                      city={school.location.city}
                      state={school.location.state}
                      zoom={12}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Quick Stats */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Stats</h3>
                <div className="space-y-3">
                  {school.googleRating && (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center text-sm text-gray-600">
                        <Star className="w-4 h-4 mr-1 text-yellow-500" />
                        Google Rating
                      </div>
                      <div className="font-semibold">{school.googleRating.toFixed(1)}</div>
                    </div>
                  )}

                  {school.accreditation?.type && (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center text-sm text-gray-600">
                        <Award className="w-4 h-4 mr-1 text-blue-600" />
                        Accreditation
                      </div>
                      <div className="font-semibold text-xs">{school.accreditation.type}</div>
                    </div>
                  )}

                  {school.operations?.fleetSize && (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center text-sm text-gray-600">
                        <Plane className="w-4 h-4 mr-1 text-green-600" />
                        Fleet Size
                      </div>
                      <div className="font-semibold">{school.operations.fleetSize}</div>
                    </div>
                  )}

                  {school.operations?.studentCapacity && (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center text-sm text-gray-600">
                        <Users className="w-4 h-4 mr-1 text-purple-600" />
                        Capacity
                      </div>
                      <div className="font-semibold">{school.operations.studentCapacity}</div>
                    </div>
                  )}
                </div>
              </div>

              {/* Contact Information */}
              {(school.contact?.phone || school.contact?.email || school.contact?.website) && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Contact Information</h3>
                  <div className="space-y-3">
                    {school.contact?.phone && (
                      <div>
                        <div className="text-sm font-medium text-gray-700">Phone</div>
                        <a
                          href={`tel:${school.contact.phone}`}
                          className="text-blue-600 hover:text-blue-800"
                        >
                          {school.contact.phone}
                        </a>
                      </div>
                    )}

                    {school.contact?.email && (
                      <div>
                        <div className="text-sm font-medium text-gray-700">Email</div>
                        <a
                          href={`mailto:${school.contact.email}`}
                          className="text-blue-600 hover:text-blue-800 break-all"
                        >
                          {school.contact.email}
                        </a>
                      </div>
                    )}

                    {school.contact?.website && (
                      <div>
                        <div className="text-sm font-medium text-gray-700">Website</div>
                        <a
                          href={school.contact.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 inline-flex items-center"
                        >
                          Visit Website
                          <ExternalLink className="w-3 h-3 ml-1" />
                        </a>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Data Provenance */}
              <ProvenancePanel
                sourceType={school.sourceType}
                sourceUrl={school.sourceUrl}
                confidence={school.confidence}
                extractedAt={school.extractedAt}
                extractorVersion={school.extractorVersion}
                snapshotId={school.snapshotId}
              />
            </div>
          </div>
        </div>
      </div>
    );
  } catch (error) {
    console.error('Error loading school profile:', error);

    // Error state
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
          <div className="text-red-500 mb-4">
            <Award className="w-12 h-12 mx-auto" />
          </div>
          <h1 className="text-xl font-semibold text-gray-900 mb-2">
            Unable to Load School Profile
          </h1>
          <p className="text-gray-600 mb-6">
            We encountered an error while loading this school&apos;s information. Please try again later.
          </p>
          <Link
            href="/"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Search
          </Link>
        </div>
      </div>
    );
  }
}

