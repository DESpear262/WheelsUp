/**
 * Search Page
 *
 * Main search interface with filters, sorting, and results display.
 * Handles search queries, location-based search, and faceted filtering.
 */

'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ArrowUpDown, SlidersHorizontal, Loader2 } from 'lucide-react';
import SearchBar from '@/components/SearchBar';
import FilterPanel, { FilterState } from '@/components/FilterPanel';
import { useSearch, useSearchAggregations } from '@/hooks/useSearch';
import { SearchParams } from '@/lib/search_utils';

const SORT_OPTIONS = [
  { value: 'relevance', label: 'Relevance' },
  { value: 'rating', label: 'Rating (High to Low)' },
  { value: 'name', label: 'Name (A-Z)' },
  { value: 'distance', label: 'Distance' },
] as const;

type SortOption = typeof SORT_OPTIONS[number]['value'];

// Placeholder school card component (will be implemented in PR 3.3)
function SchoolCard({ school }: { school: any }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{school.name || 'School Name'}</h3>
          <p className="text-sm text-gray-600">{school.location?.city}, {school.location?.state}</p>
        </div>
        <div className="text-right">
          <div className="text-sm text-gray-500">Rating</div>
          <div className="text-lg font-semibold text-blue-600">
            {school.googleRating ? `${school.googleRating}★` : 'N/A'}
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between text-sm text-gray-600 mb-4">
        <span>VA Approved: {school.accreditation?.vaApproved ? 'Yes' : 'No'}</span>
        <span>Fleet: {school.operations?.fleetSize || 'N/A'} aircraft</span>
      </div>

      <div className="flex justify-between items-center">
        <div className="text-sm text-gray-500">
          Founded: {school.operations?.foundedYear || 'N/A'}
        </div>
        <button className="btn-primary text-sm px-4 py-2">
          View Details
        </button>
      </div>
    </div>
  );
}

export default function SearchPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Parse URL parameters into search state
  const [searchQuery, setSearchQuery] = useState(searchParams.get('q') || '');
  const [location, setLocation] = useState<{
    latitude: number;
    longitude: number;
    placeName: string;
  } | undefined>(
    searchParams.get('lat') && searchParams.get('lng') && searchParams.get('place')
      ? {
          latitude: parseFloat(searchParams.get('lat')!),
          longitude: parseFloat(searchParams.get('lng')!),
          placeName: searchParams.get('place')!
        }
      : undefined
  );

  const [filters, setFilters] = useState<FilterState>({
    costRange: searchParams.get('costRange') || undefined,
    trainingTypes: searchParams.getAll('trainingType'),
    vaApproved: searchParams.get('vaApproved') === 'true' || undefined,
  });

  const [sortBy, setSortBy] = useState<SortOption>('relevance');
  const [isFiltersOpen, setIsFiltersOpen] = useState(false);

  // Build search parameters
  const searchParameters: SearchParams = {
    query: searchQuery,
    location: location ? {
      latitude: location.latitude,
      longitude: location.longitude,
      radiusMiles: 100, // Default radius
    } : undefined,
    filters: {
      state: filters.costRange === 'state' ? filters.costRange : undefined, // This logic needs refinement
      vaApproved: filters.vaApproved,
      accreditationTypes: filters.trainingTypes,
      // Add cost range logic when pricing data is available
    },
    sort: {
      field: sortBy,
      order: 'desc' as const,
    },
    pagination: {
      page: 1,
      limit: 20,
    },
  };

  // Use search hook
  const { data: searchResults, isLoading, error, isFetching } = useSearch(searchParameters, !!searchQuery);

  // Use aggregations for filter options
  const { data: aggregations } = useSearchAggregations();

  // Update URL when search parameters change
  useEffect(() => {
    if (searchQuery || location) {
      const params = new URLSearchParams();

      if (searchQuery) params.set('q', searchQuery);
      if (location) {
        params.set('lat', location.latitude.toString());
        params.set('lng', location.longitude.toString());
        params.set('place', location.placeName);
      }

      // Add filters to URL
      if (filters.costRange) params.set('costRange', filters.costRange);
      if (filters.trainingTypes) {
        filters.trainingTypes.forEach(type => params.append('trainingType', type));
      }
      if (filters.vaApproved) params.set('vaApproved', 'true');

      router.replace(`/search?${params.toString()}`, { scroll: false });
    }
  }, [searchQuery, location, filters, router]);

  // Handle search submission
  const handleSearch = (query: string, newLocation?: typeof location) => {
    setSearchQuery(query);
    setLocation(newLocation);
  };

  // Handle filter changes
  const handleFiltersChange = (newFilters: FilterState) => {
    setFilters(newFilters);
  };

  // Handle sort changes
  const handleSortChange = (newSort: SortOption) => {
    setSortBy(newSort);
  };

  const hasActiveSearch = !!(searchQuery || location);
  const resultsCount = searchResults?.total || 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Find Your Flight School
          </h1>
          <p className="text-lg text-gray-600">
            Search and compare flight schools nationwide
          </p>
        </div>

        {/* Search Bar */}
        <div className="mb-8">
          <SearchBar
            onSearch={handleSearch}
            initialQuery={searchQuery}
            initialLocation={location}
            placeholder="Search by school name, location, or specialty..."
          />
        </div>

        {/* Filters and Results */}
        <div className="flex gap-8">
          {/* Filters Sidebar */}
          <div className="w-full md:w-80 flex-shrink-0">
            <FilterPanel
              filters={filters}
              onFiltersChange={handleFiltersChange}
              isOpen={isFiltersOpen}
              onToggle={() => setIsFiltersOpen(!isFiltersOpen)}
            />
          </div>

          {/* Results Area */}
          <div className="flex-1">
            {/* Results Header */}
            {hasActiveSearch && (
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-4">
                  <h2 className="text-xl font-semibold text-gray-900">
                    Search Results
                  </h2>
                  {isLoading || isFetching ? (
                    <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
                  ) : (
                    <span className="text-sm text-gray-600">
                      {resultsCount.toLocaleString()} schools found
                    </span>
                  )}
                </div>

                {/* Sort Options */}
                <div className="flex items-center space-x-2">
                  <ArrowUpDown className="h-4 w-4 text-gray-400" />
                  <select
                    value={sortBy}
                    onChange={(e) => handleSortChange(e.target.value as SortOption)}
                    className="text-sm border border-gray-300 rounded-md px-3 py-1 bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                  >
                    {SORT_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            {/* Results Grid */}
            {hasActiveSearch ? (
              <div className="space-y-6">
                {isLoading ? (
                  <div className="flex justify-center items-center py-12">
                    <div className="text-center">
                      <Loader2 className="h-8 w-8 text-blue-500 animate-spin mx-auto mb-4" />
                      <p className="text-gray-600">Searching flight schools...</p>
                    </div>
                  </div>
                ) : error ? (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                    <h3 className="text-lg font-medium text-red-800 mb-2">
                      Search Error
                    </h3>
                    <p className="text-red-600">
                      {error instanceof Error ? error.message : 'An unexpected error occurred'}
                    </p>
                  </div>
                ) : searchResults && searchResults.schools.length > 0 ? (
                  <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-1">
                    {searchResults.schools.map((school, index) => (
                      <SchoolCard key={school._id || index} school={school} />
                    ))}
                  </div>
                ) : (
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-12 text-center">
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      No schools found
                    </h3>
                    <p className="text-gray-600 mb-4">
                      Try adjusting your search criteria or location
                    </p>
                    <button
                      onClick={() => {
                        setSearchQuery('');
                        setLocation(undefined);
                        setFilters({});
                      }}
                      className="btn-secondary"
                    >
                      Clear Search
                    </button>
                  </div>
                )}
              </div>
            ) : (
              /* Initial State */
              <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
                <div className="max-w-md mx-auto">
                  <SlidersHorizontal className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Start Your Search
                  </h3>
                  <p className="text-gray-600">
                    Enter a school name, location, or training type above to find flight schools that match your needs.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
