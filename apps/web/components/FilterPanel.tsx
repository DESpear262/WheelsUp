/**
 * FilterPanel Component
 *
 * Collapsible filter panel with cost ranges, training types, and VA eligibility.
 * Mobile-responsive with smooth animations.
 */

'use client';

import { useState } from 'react';
import { ChevronDown, Filter, X } from 'lucide-react';

export interface FilterState {
  costRange?: string;
  trainingTypes?: string[];
  vaApproved?: boolean;
}

interface FilterPanelProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  isOpen: boolean;
  onToggle: () => void;
  className?: string;
}

const COST_RANGES = [
  { value: '0-25000', label: '$0 - $25K', display: '$0–$25K' },
  { value: '25000-50000', label: '$25K - $50K', display: '$25K–$50K' },
  { value: '50000-100000', label: '$50K - $100K', display: '$50K–$100K' },
  { value: '100000+', label: '$100K+', display: '$100K+' },
];

const TRAINING_TYPES = [
  { value: 'PPL', label: 'Private Pilot License (PPL)' },
  { value: 'IR', label: 'Instrument Rating (IR)' },
  { value: 'CPL', label: 'Commercial Pilot License (CPL)' },
  { value: 'CFI', label: 'Certified Flight Instructor (CFI)' },
];

export default function FilterPanel({
  filters,
  onFiltersChange,
  isOpen,
  onToggle,
  className = ""
}: FilterPanelProps) {
  const [tempFilters, setTempFilters] = useState<FilterState>(filters);

  // Update temporary filters
  const updateTempFilters = (newFilters: Partial<FilterState>) => {
    setTempFilters(prev => ({ ...prev, ...newFilters }));
  };

  // Apply filters
  const applyFilters = () => {
    onFiltersChange(tempFilters);
  };

  // Clear all filters
  const clearFilters = () => {
    const clearedFilters = {};
    setTempFilters(clearedFilters);
    onFiltersChange(clearedFilters);
  };

  // Check if any filters are active
  const hasActiveFilters = Object.keys(filters).some(key => {
    const value = filters[key as keyof FilterState];
    if (Array.isArray(value)) return value.length > 0;
    return value !== undefined && value !== null && value !== false;
  });

  // Handle training type toggle
  const toggleTrainingType = (type: string) => {
    const currentTypes = tempFilters.trainingTypes || [];
    const newTypes = currentTypes.includes(type)
      ? currentTypes.filter(t => t !== type)
      : [...currentTypes, type];
    updateTempFilters({ trainingTypes: newTypes });
  };

  return (
    <>
      {/* Mobile filter toggle button */}
      <div className="md:hidden">
        <button
          onClick={onToggle}
          className={`flex items-center px-4 py-2 rounded-lg border transition-colors ${
            hasActiveFilters
              ? 'border-blue-300 bg-blue-50 text-blue-700'
              : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
          }`}
        >
          <Filter className="h-4 w-4 mr-2" />
          Filters
          {hasActiveFilters && (
            <span className="ml-2 bg-blue-600 text-white text-xs px-2 py-0.5 rounded-full">
              Active
            </span>
          )}
          <ChevronDown className={`h-4 w-4 ml-2 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>
      </div>

      {/* Filter panel */}
      <div className={`${
        isOpen ? 'block' : 'hidden md:block'
      } bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
            <div className="flex items-center space-x-2">
              {hasActiveFilters && (
                <button
                  onClick={clearFilters}
                  className="text-sm text-gray-600 hover:text-gray-900 underline"
                >
                  Clear all
                </button>
              )}
              <button
                onClick={onToggle}
                className="md:hidden p-1 rounded-md hover:bg-gray-100"
              >
                <X className="h-5 w-5 text-gray-500" />
              </button>
            </div>
          </div>

          {/* Cost Range Filter */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Training Cost Range
            </label>
            <div className="grid grid-cols-2 gap-3">
              {COST_RANGES.map((range) => (
                <button
                  key={range.value}
                  onClick={() => updateTempFilters({
                    costRange: tempFilters.costRange === range.value ? undefined : range.value
                  })}
                  className={`px-3 py-2 text-sm border rounded-md transition-colors ${
                    tempFilters.costRange === range.value
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {range.display}
                </button>
              ))}
            </div>
          </div>

          {/* Training Types Filter */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Training Programs
            </label>
            <div className="space-y-2">
              {TRAINING_TYPES.map((type) => (
                <label key={type.value} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={tempFilters.trainingTypes?.includes(type.value) || false}
                    onChange={() => toggleTrainingType(type.value)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="ml-3 text-sm text-gray-700">{type.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* VA Approved Filter */}
          <div className="mb-6">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={tempFilters.vaApproved || false}
                onChange={(e) => updateTempFilters({ vaApproved: e.target.checked || undefined })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="ml-3 text-sm text-gray-700">
                VA Approved Schools Only
              </span>
            </label>
            <p className="text-xs text-gray-500 mt-1 ml-7">
              Show only schools approved for VA education benefits
            </p>
          </div>

          {/* Apply Filters Button */}
          <div className="pt-4 border-t border-gray-200">
            <button
              onClick={applyFilters}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Apply Filters
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
