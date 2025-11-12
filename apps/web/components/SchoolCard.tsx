/**
 * SchoolCard Component
 *
 * Displays a flight school in card format with key information,
 * trust indicators, and comparison functionality.
 */

import { useState } from 'react';
import Link from 'next/link';
import {
  MapPin,
  Star,
  Users,
  Plane,
  CheckSquare,
  Square,
  ChevronRight,
  Award
} from 'lucide-react';
import { SchoolCardProps, CostDisplay, AccreditationDisplay, RatingDisplay } from '../lib/types';
import TrustBadge from './TrustBadge';

export default function SchoolCard({
  school,
  onSelect,
  onCompare,
  isSelected = false,
  isComparing = false,
  showCompareButton = true,
  className = ''
}: SchoolCardProps) {
  const [isHovered, setIsHovered] = useState(false);
  const [imageError, setImageError] = useState(false);

  // Error handling for missing school data
  if (!school) {
    return (
      <div className={`
        bg-white border border-red-200 rounded-lg p-6 text-center
        ${className}
      `}>
        <div className="text-red-500 mb-2">
          <Award className="w-8 h-8 mx-auto" />
        </div>
        <p className="text-sm text-red-600">School data unavailable</p>
      </div>
    );
  }

  // Handle loading state (if school data is incomplete)
  const isLoading = !school.name || !school.id;

  // Loading state component
  if (isLoading) {
    return (
      <div className={`
        bg-white border border-gray-200 rounded-lg p-6 animate-pulse
        ${className}
      `}>
        <div className="flex items-center space-x-4">
          <div className="flex-1 space-y-3">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-3 bg-gray-200 rounded w-1/2"></div>
          </div>
          <div className="w-12 h-12 bg-gray-200 rounded-full"></div>
        </div>
        <div className="grid grid-cols-2 gap-4 mt-4">
          <div className="h-16 bg-gray-200 rounded"></div>
          <div className="h-16 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  // Cost band display logic with error handling
  const getCostDisplay = (school: any): CostDisplay => {
    try {
      // This would typically come from pricing data, but for now we'll use placeholder logic
      // In a real implementation, this would be calculated from the school's pricing data
      const costBands: Record<string, CostDisplay> = {
        'budget': { band: 'Budget', color: 'bg-green-100', textColor: 'text-green-800', estimatedRange: '$5k-$10k' },
        '$5k-$10k': { band: '$5k-$10k', color: 'bg-green-100', textColor: 'text-green-800' },
        '$10k-$15k': { band: '$10k-$15k', color: 'bg-blue-100', textColor: 'text-blue-800' },
        '$15k-$25k': { band: '$15k-$25k', color: 'bg-yellow-100', textColor: 'text-yellow-800' },
        '$25k+': { band: '$25k+', color: 'bg-red-100', textColor: 'text-red-800' }
      };

      // Placeholder: determine cost band based on school data
      // In reality, this would come from pricing analysis
      return costBands['$10k-$15k'] || costBands['$10k-$15k'];
    } catch (error) {
      // Fallback for any errors in cost calculation
      return { band: 'Unknown', color: 'bg-gray-100', textColor: 'text-gray-800' };
    }
  };

  // Accreditation display logic with error handling
  const getAccreditationDisplay = (accreditation: any): AccreditationDisplay => {
    try {
      const vaApproved = accreditation?.vaApproved;

      if (accreditation?.type === 'Part 141') {
        return {
          type: 'Part 141',
          color: 'text-blue-600',
          icon: '🎓',
          label: 'FAA Part 141' + (vaApproved ? ' • VA Approved' : '')
        };
      } else if (accreditation?.type === 'Part 61') {
        return {
          type: 'Part 61',
          color: 'text-green-600',
          icon: '✈️',
          label: 'FAA Part 61' + (vaApproved ? ' • VA Approved' : '')
        };
      }

      return {
        type: 'Unknown',
        color: 'text-gray-500',
        icon: '❓',
        label: 'Accreditation Unknown'
      };
    } catch (error) {
      return {
        type: 'Error',
        color: 'text-red-500',
        icon: '⚠️',
        label: 'Accreditation Error'
      };
    }
  };

  // Rating display logic with error handling
  const getRatingDisplay = (rating?: number, count?: number): RatingDisplay | null => {
    try {
      if (!rating || rating < 0 || rating > 5) return null;

      return {
        value: rating,
        count: count && count > 0 ? count : undefined,
        color: rating >= 4.5 ? 'text-green-600' : rating >= 4.0 ? 'text-yellow-600' : 'text-red-600',
        icon: '⭐'
      };
    } catch (error) {
      return null;
    }
  };

  const costDisplay = getCostDisplay(school);
  const accreditationDisplay = getAccreditationDisplay(school.accreditation);
  const ratingDisplay = getRatingDisplay(school.googleRating, school.googleReviewCount);

  return (
    <div
      className={`
        relative bg-white border border-gray-200 rounded-lg shadow-sm
        hover:shadow-lg transition-all duration-200 cursor-pointer
        ${isSelected ? 'ring-2 ring-blue-500 border-blue-500' : ''}
        ${isHovered ? 'transform scale-[1.02]' : ''}
        ${className}
      `}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => onSelect?.(school)}
    >
      {/* Compare Checkbox */}
      {showCompareButton && (
        <div className="absolute top-3 right-3 z-10">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onCompare?.(school, !isComparing);
            }}
            className={`
              p-1.5 rounded-full transition-colors
              ${isComparing
                ? 'bg-blue-100 text-blue-600 hover:bg-blue-200'
                : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
              }
            `}
            aria-label={isComparing ? 'Remove from comparison' : 'Add to comparison'}
          >
            {isComparing ? (
              <CheckSquare className="w-4 h-4" />
            ) : (
              <Square className="w-4 h-4" />
            )}
          </button>
        </div>
      )}

      <div className="p-6">
        {/* Header Section */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-gray-900 truncate mb-1">
              {school.name}
            </h3>

            {/* Location */}
            <div className="flex items-center text-gray-600 text-sm">
              <MapPin className="w-4 h-4 mr-1 flex-shrink-0" />
              <span className="truncate">
                {(() => {
                  try {
                    const city = school.location?.city;
                    const state = school.location?.state;
                    if (city && state) {
                      return `${city}, ${state}`;
                    } else if (city) {
                      return city;
                    } else if (state) {
                      return state;
                    }
                    return 'Location not specified';
                  } catch (error) {
                    return 'Location not specified';
                  }
                })()}
              </span>
            </div>
          </div>

          {/* Trust Badge */}
          <div className="ml-3 flex-shrink-0">
            <TrustBadge
              sourceType={school.sourceType || 'website'}
              confidence={school.confidence || 0}
              extractedAt={(() => {
                try {
                  return new Date(school.extractedAt);
                } catch (error) {
                  return new Date(); // fallback to current date
                }
              })()}
              sourceUrl={school.sourceUrl || '#'}
              extractorVersion={school.extractorVersion || '1.0.0'}
              size="sm"
            />
          </div>
        </div>

        {/* Key Metrics Row */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          {/* Cost Band */}
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-xs font-medium text-gray-500 mb-1">Cost Range</div>
            <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${costDisplay.color} ${costDisplay.textColor}`}>
              {costDisplay.band}
            </div>
            {costDisplay.estimatedRange && (
              <div className="text-xs text-gray-600 mt-1">
                {costDisplay.estimatedRange}
              </div>
            )}
          </div>

          {/* Rating */}
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-xs font-medium text-gray-500 mb-1">Rating</div>
            {ratingDisplay ? (
              <div className="flex items-center">
                <div className={`flex items-center ${ratingDisplay.color}`}>
                  <Star className="w-4 h-4 fill-current" />
                  <span className="ml-1 font-semibold">{ratingDisplay.value.toFixed(1)}</span>
                </div>
                {ratingDisplay.count && (
                  <span className="text-xs text-gray-500 ml-1">
                    ({ratingDisplay.count})
                  </span>
                )}
              </div>
            ) : (
              <div className="text-xs text-gray-400">Not rated</div>
            )}
          </div>
        </div>

        {/* Accreditation and Fleet */}
        <div className="space-y-3 mb-4">
          {/* Accreditation */}
          <div className="flex items-center justify-between">
            <div className="flex items-center text-sm">
              <Award className={`w-4 h-4 mr-2 ${accreditationDisplay.color}`} />
              <span className={accreditationDisplay.color}>
                {accreditationDisplay.label}
              </span>
            </div>
          </div>

          {/* Fleet Size */}
          {(() => {
            try {
              const fleetSize = school.operations?.fleetSize;
              if (fleetSize && fleetSize > 0) {
                return (
                  <div className="flex items-center text-sm text-gray-600">
                    <Plane className="w-4 h-4 mr-2" />
                    <span>{fleetSize} aircraft in fleet</span>
                  </div>
                );
              }
              return null;
            } catch (error) {
              return null;
            }
          })()}
        </div>

        {/* Footer with CTA */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          <div className="text-xs text-gray-500">
            {isComparing && (
              <span className="inline-flex items-center px-2 py-1 rounded-full bg-blue-100 text-blue-800 text-xs">
                In Comparison
              </span>
            )}
          </div>

          <Link
            href={`/schools/${school.id}`}
            className="
              inline-flex items-center text-sm font-medium text-blue-600
              hover:text-blue-800 transition-colors group
            "
            onClick={(e) => e.stopPropagation()}
          >
            View Details
            <ChevronRight className="w-4 h-4 ml-1 group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </div>
      </div>
    </div>
  );
}
