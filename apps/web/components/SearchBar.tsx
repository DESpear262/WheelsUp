/**
 * SearchBar Component
 *
 * Interactive search bar with location autocomplete using Mapbox Geocoding.
 * Handles text search and location-based search functionality.
 */

'use client';

import { useState, useRef, useCallback, type FormEvent } from 'react';
import { MapPin, Search, Loader2 } from 'lucide-react';

interface LocationSuggestion {
  place_name: string;
  center: [number, number]; // [longitude, latitude]
  context?: Array<{
    id: string;
    text: string;
  }>;
}

interface SearchBarProps {
  onSearch: (query: string, location?: { latitude: number; longitude: number; placeName: string }) => void;
  initialQuery?: string;
  initialLocation?: { latitude: number; longitude: number; placeName: string };
  placeholder?: string;
  className?: string;
}

export default function SearchBar({
  onSearch,
  initialQuery = '',
  initialLocation,
  placeholder = "Search flight schools...",
  className = ""
}: SearchBarProps) {
  const [query, setQuery] = useState(initialQuery);
  const [location, setLocation] = useState(initialLocation);
  const [locationQuery, setLocationQuery] = useState(initialLocation?.placeName || '');
  const [locationSuggestions, setLocationSuggestions] = useState<LocationSuggestion[]>([]);
  const [showLocationSuggestions, setShowLocationSuggestions] = useState(false);
  const [isSearchingLocation, setIsSearchingLocation] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const locationInputRef = useRef<HTMLInputElement>(null);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout>>();

  // Debounced location search
  const searchLocations = useCallback(async (searchText: string) => {
    if (!searchText.trim() || searchText.length < 2) {
      setLocationSuggestions([]);
      setShowLocationSuggestions(false);
      return;
    }

    setIsSearchingLocation(true);

    try {
      const mapboxToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
      if (!mapboxToken) {
        console.warn('Mapbox token not configured');
        return;
      }

      const response = await fetch(
        `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(searchText)}.json?access_token=${mapboxToken}&types=place,postcode,locality,neighborhood&limit=5&country=us`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch location suggestions');
      }

      const data = await response.json();
      setLocationSuggestions(data.features || []);
      setShowLocationSuggestions(true);
    } catch (error) {
      console.error('Location search error:', error);
      setLocationSuggestions([]);
    } finally {
      setIsSearchingLocation(false);
    }
  }, []);

  // Handle location input changes with debouncing
  const handleLocationChange = useCallback((value: string) => {
    setLocationQuery(value);

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (!value.trim()) {
      setLocationSuggestions([]);
      setShowLocationSuggestions(false);
      setLocation(undefined);
      return;
    }

    searchTimeoutRef.current = setTimeout(() => {
      searchLocations(value);
    }, 300);
  }, [searchLocations]);

  // Handle location selection
  const handleLocationSelect = (suggestion: LocationSuggestion) => {
    const [longitude, latitude] = suggestion.center;
    const newLocation = {
      latitude,
      longitude,
      placeName: suggestion.place_name
    };

    setLocation(newLocation);
    setLocationQuery(suggestion.place_name);
    setLocationSuggestions([]);
    setShowLocationSuggestions(false);
  };

  // Clear location
  const clearLocation = () => {
    setLocation(undefined);
    setLocationQuery('');
    setLocationSuggestions([]);
    setShowLocationSuggestions(false);
  };

  // Handle search submission
  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      onSearch(query.trim(), location);
    } catch (error) {
      console.error('Search submission error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle input focus/blur for suggestions
  const handleLocationFocus = () => {
    if (locationSuggestions.length > 0) {
      setShowLocationSuggestions(true);
    }
  };

  const handleLocationBlur = () => {
    // Delay hiding suggestions to allow for clicks
    setTimeout(() => setShowLocationSuggestions(false), 200);
  };

  return (
    <form onSubmit={handleSubmit} className={`w-full max-w-4xl mx-auto ${className}`}>
      <div className="flex flex-col md:flex-row gap-4">
        {/* Main search input */}
        <div className="flex-1 relative">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={placeholder}
              className="w-full pl-12 pr-4 py-4 text-lg border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none shadow-sm"
              disabled={isSubmitting}
            />
          </div>
        </div>

        {/* Location input with autocomplete */}
        <div className="md:w-80 relative">
          <div className="relative">
            <MapPin className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
            <input
              ref={locationInputRef}
              type="text"
              value={locationQuery}
              onChange={(e) => handleLocationChange(e.target.value)}
              onFocus={handleLocationFocus}
              onBlur={handleLocationBlur}
              placeholder="Enter city or airport..."
              className="w-full pl-12 pr-10 py-4 text-lg border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none shadow-sm"
              disabled={isSubmitting}
            />
            {locationQuery && (
              <button
                type="button"
                onClick={clearLocation}
                className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
            {isSearchingLocation && (
              <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
                <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
              </div>
            )}
          </div>

          {/* Location suggestions dropdown */}
          {showLocationSuggestions && locationSuggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-60 overflow-y-auto">
              {locationSuggestions.map((suggestion, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => handleLocationSelect(suggestion)}
                  className="w-full px-4 py-3 text-left hover:bg-gray-50 focus:bg-gray-50 focus:outline-none border-b border-gray-100 last:border-b-0"
                >
                  <div className="flex items-start">
                    <MapPin className="h-4 w-4 text-gray-400 mt-0.5 mr-3 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900 truncate">
                        {suggestion.place_name}
                      </div>
                      {suggestion.context && (
                        <div className="text-xs text-gray-500 truncate">
                          {suggestion.context.map(ctx => ctx.text).join(', ')}
                        </div>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Search button */}
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-8 py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold rounded-lg transition-colors duration-200 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 outline-none shadow-sm flex items-center justify-center"
        >
          {isSubmitting ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <>
              <Search className="h-5 w-5 mr-2" />
              Search
            </>
          )}
        </button>
      </div>

      {/* Selected location display */}
      {location && (
        <div className="mt-3 flex items-center text-sm text-gray-600">
          <MapPin className="h-4 w-4 mr-1 text-blue-600" />
          <span>Searching near: <strong>{location.placeName}</strong></span>
        </div>
      )}
    </form>
  );
}
