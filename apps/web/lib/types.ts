/**
 * Type definitions for WheelsUp database layer
 *
 * This file contains additional type definitions and interfaces
 * that complement the Drizzle-generated types for API usage.
 */

import type { School, Program, Pricing, Metric, Attribute } from '../drizzle/schema';

// ============================================================================
// API Response Types
// ============================================================================

/**
 * School with related data for detailed view
 */
export interface SchoolWithRelations extends School {
  programs: Program[];
  pricing?: Pricing;
  metrics?: Metric;
  attributes?: Attribute;
}

/**
 * Search filters for schools
 */
export interface SchoolFilters {
  state?: string;
  city?: string;
  vaApproved?: boolean;
  minRating?: number;
  maxDistance?: number;
  latitude?: number;
  longitude?: number;
  programTypes?: string[];
  maxCost?: number;
  minCost?: number;
}

/**
 * Pagination parameters
 */
export interface PaginationParams {
  limit?: number;
  offset?: number;
  page?: number;
}

/**
 * Search result with metadata
 */
export interface SearchResult<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

/**
 * API error response
 */
export interface ApiError {
  error: string;
  code?: string;
  details?: any;
}

// ============================================================================
// Query Result Types
// ============================================================================

/**
 * School list item for search results
 */
export interface SchoolListItem {
  id: number;
  schoolId: string;
  name: string;
  location: {
    city?: string;
    state?: string;
    country: string;
  };
  googleRating?: number;
  googleReviewCount?: number;
  accreditation: {
    vaApproved?: boolean;
  };
  operations: {
    fleetSize?: number;
  };
  sourceType?: string;
  sourceUrl?: string;
  extractorVersion?: string;
  extractedAt: Date;
  confidence: number;
}

/**
 * School detail view
 */
export interface SchoolDetail extends SchoolListItem {
  description?: string;
  specialties?: string[];
  contact?: {
    phone?: string;
    email?: string;
    website?: string;
  };
  // Additional properties beyond SchoolListItem
  programs: Program[];
  pricing?: Pricing;
  metrics?: Metric;
  attributes?: Attribute;
  sourceType: string;
  sourceUrl: string;
  extractorVersion: string;
  snapshotId: string;
}

// ============================================================================
// Filter and Sort Types
// ============================================================================

/**
 * Sort options for school listings
 */
export type SchoolSortField =
  | 'name'
  | 'googleRating'
  | 'distance'
  | 'cost'
  | 'confidence'
  | 'extractedAt';

export type SortDirection = 'asc' | 'desc';

export interface SortOptions {
  field: SchoolSortField;
  direction: SortDirection;
}

// ============================================================================
// Geospatial Types
// ============================================================================

/**
 * Geographic bounds for area search
 */
export interface GeoBounds {
  northEast: {
    latitude: number;
    longitude: number;
  };
  southWest: {
    latitude: number;
    longitude: number;
  };
}

/**
 * Distance calculation result
 */
export interface DistanceResult {
  distance: number;
  unit: 'miles' | 'kilometers';
}

// ============================================================================
// Validation Types
// ============================================================================

/**
 * Validation result for database operations
 */
export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

// ============================================================================
// Cache Types
// ============================================================================

/**
 * Cache entry with metadata
 */
export interface CacheEntry<T> {
  data: T;
  timestamp: Date;
  expiresAt: Date;
  version: string;
}

// ============================================================================
// Utility Types
// ============================================================================

/**
 * Make specific properties optional in a type
 */
export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

/**
 * Make specific properties required in a type
 */
export type RequiredBy<T, K extends keyof T> = T & Required<Pick<T, K>>;

/**
 * Extract non-nullable properties from a type
 */
export type NonNullableFields<T> = {
  [P in keyof T]: NonNullable<T[P]>;
};

// ============================================================================
// Environment Types
// ============================================================================

/**
 * Database environment configuration
 */
export interface DatabaseConfig {
  url: string;
  maxConnections: number;
  idleTimeout: number;
  connectTimeout: number;
}

/**
 * Application environment
 */
export type AppEnvironment = 'development' | 'staging' | 'production';

/**
 * Feature flags
 */
export interface FeatureFlags {
  enableCaching: boolean;
  enableMetrics: boolean;
  enableDetailedLogging: boolean;
}

// ============================================================================
// Component Types
// ============================================================================

/**
 * Props for the SchoolCard component
 */
export interface SchoolCardProps {
  school: SchoolListItem;
  onSelect?: (school: SchoolListItem) => void;
  onCompare?: (school: SchoolListItem, selected: boolean) => void;
  isSelected?: boolean;
  isComparing?: boolean;
  showCompareButton?: boolean;
  className?: string;
}

/**
 * Props for the TrustBadge component
 */
export interface TrustBadgeProps {
  sourceType: string;
  confidence: number;
  extractedAt: Date;
  sourceUrl: string;
  extractorVersion: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

/**
 * Cost band display information
 */
export interface CostDisplay {
  band: string;
  color: string;
  textColor: string;
  estimatedRange?: string;
}

/**
 * Accreditation display information
 */
export interface AccreditationDisplay {
  type: string;
  color: string;
  icon: string;
  label: string;
}

/**
 * Rating display information
 */
export interface RatingDisplay {
  value: number;
  count?: number;
  color: string;
  icon: string;
}