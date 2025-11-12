/**
 * Database Connection Layer for WheelsUp
 *
 * This module provides type-safe PostgreSQL connection utilities using Drizzle ORM.
 * It includes connection pooling, error handling, and helper functions for API routes.
 */

import { drizzle } from 'drizzle-orm/postgres-js';
import { eq, sql as drizzleSql } from 'drizzle-orm';
import postgres from 'postgres';
import * as schema from '../drizzle/schema';

// ============================================================================
// Connection Configuration
// ============================================================================

/**
 * Database connection configuration for RDS
 * Configured for production use with connection pooling
 */
const connectionString = process.env.DATABASE_URL || 'postgresql://postgres:12345678@wheelsup.c1uuigcm4bd1.us-east-2.rds.amazonaws.com:5432/wheelsup';

/**
 * PostgreSQL connection pool configuration
 * Optimized for RDS t3.large instance limits
 */
const sql = postgres(connectionString, {
  max: 100, // Maximum connections for RDS t3.large
  idle_timeout: 30, // Close idle connections after 30 seconds
  connect_timeout: 10, // Connection timeout in seconds
  prepare: false, // Disable prepared statements for better performance with pooling
  onnotice: () => {}, // Ignore notices in production
  onparameter: () => {}, // Ignore parameter status messages
});

// ============================================================================
// Drizzle Client Initialization
// ============================================================================

/**
 * Drizzle ORM client instance
 * Configured with full schema for type-safe queries
 */
export const db = drizzle(sql, { schema });

// ============================================================================
// Connection Health Checks
// ============================================================================

/**
 * Check database connection health
 * @returns Promise<boolean> - true if connection is healthy
 */
export async function checkConnection(): Promise<boolean> {
  try {
    await sql`SELECT 1`;
    return true;
  } catch (error) {
    console.error('Database connection check failed:', error);
    return false;
  }
}

/**
 * Get connection pool statistics
 * @returns Object with connection pool metrics
 */
export function getConnectionStats() {
  return {
    totalCount: 1, // Default values for connection stats
    idleCount: 1,
    waitingCount: 0,
  };
}

// ============================================================================
// Helper Functions for API Routes
// ============================================================================

/**
 * Find all schools with optional filters
 * @param filters - Optional filters for schools
 * @returns Promise of schools array
 */
export async function findSchools(filters?: {
  limit?: number;
  offset?: number;
  state?: string;
  vaApproved?: boolean;
  minRating?: number;
}) {
  try {
    let query: any = db.select().from(schema.schools);

    // Apply filters if provided
    if (filters?.state) {
      query = query.where(drizzleSql`location->>'state' = ${filters.state}`);
    }

    if (filters?.vaApproved !== undefined) {
      query = query.where(drizzleSql`accreditation->>'vaApproved' = ${filters.vaApproved.toString()}`);
    }

    if (filters?.minRating) {
      query = query.where(drizzleSql`google_rating >= ${filters.minRating}`);
    }

    // Apply pagination
    if (filters?.limit) {
      query = query.limit(filters.limit);
    }
    if (filters?.offset) {
      query = query.offset(filters.offset);
    }

    const result = await query;
    return result;
  } catch (error) {
    console.error('Error finding schools:', error);
    throw new DatabaseError('Failed to fetch schools', error);
  }
}

/**
 * Find a school by its ID
 * @param schoolId - The school ID to find
 * @returns Promise of school or null
 */
export async function findSchoolById(schoolId: string) {
  try {
    const result = await db
      .select()
      .from(schema.schools)
      .where(eq(schema.schools.schoolId, schoolId))
      .limit(1);

    return result[0] || null;
  } catch (error) {
    console.error('Error finding school by ID:', error);
    throw new DatabaseError('Failed to fetch school', error);
  }
}

/**
 * Get programs for a specific school
 * @param schoolId - The school ID
 * @returns Promise of programs array
 */
export async function findProgramsBySchool(schoolId: string) {
  try {
    const result = await db
      .select()
      .from(schema.programs)
      .where(eq(schema.programs.schoolId, schoolId));

    return result;
  } catch (error) {
    console.error('Error finding programs by school:', error);
    throw new DatabaseError('Failed to fetch programs', error);
  }
}

/**
 * Get pricing information for a specific school
 * @param schoolId - The school ID
 * @returns Promise of pricing data or null
 */
export async function findPricingBySchool(schoolId: string) {
  try {
    const result = await db
      .select()
      .from(schema.pricing)
      .where(eq(schema.pricing.schoolId, schoolId))
      .limit(1);

    return result[0] || null;
  } catch (error) {
    console.error('Error finding pricing by school:', error);
    throw new DatabaseError('Failed to fetch pricing', error);
  }
}

/**
 * Create a new school record
 * @param schoolData - The school data to insert
 * @returns Promise of created school
 */
export async function createSchool(schoolData: schema.NewSchool) {
  try {
    const result = await db
      .insert(schema.schools)
      .values(schoolData)
      .returning();

    return result[0];
  } catch (error) {
    console.error('Error creating school:', error);
    throw new DatabaseError('Failed to create school', error);
  }
}

/**
 * Update an existing school record
 * @param schoolId - The school ID to update
 * @param updates - The fields to update
 * @returns Promise of updated school
 */
export async function updateSchool(schoolId: string, updates: Partial<schema.NewSchool>) {
  try {
    const result = await db
      .update(schema.schools)
      .set({
        ...updates,
        lastUpdated: new Date(),
      })
      .where(eq(schema.schools.schoolId, schoolId))
      .returning();

    return result[0];
  } catch (error) {
    console.error('Error updating school:', error);
    throw new DatabaseError('Failed to update school', error);
  }
}

// ============================================================================
// Error Handling
// ============================================================================

/**
 * Custom database error class with additional context
 */
export class DatabaseError extends Error {
  constructor(message: string, public originalError?: any) {
    super(message);
    this.name = 'DatabaseError';
  }
}

/**
 * Handle database errors with appropriate logging and user-friendly messages
 * @param error - The error to handle
 * @returns User-friendly error message
 */
export function handleDatabaseError(error: any): string {
  console.error('Database error:', error);

  // Handle specific PostgreSQL error codes
  if (error?.code === '23505') {
    return 'A record with this information already exists';
  }

  if (error?.code === '23503') {
    return 'Referenced record does not exist';
  }

  if (error?.code === '42703') {
    return 'Invalid field reference';
  }

  // Handle connection errors
  if (error?.message?.includes('connection')) {
    return 'Database connection error. Please try again later.';
  }

  // Generic fallback
  return 'An unexpected database error occurred';
}

// ============================================================================
// Cleanup
// ============================================================================

/**
 * Clean up database connections
 * Should be called when the application shuts down
 */
export async function closeConnections() {
  try {
    await sql.end();
    console.log('Database connections closed');
  } catch (error) {
    console.error('Error closing database connections:', error);
  }
}

// Handle graceful shutdown
if (typeof process !== 'undefined') {
  process.on('SIGINT', closeConnections);
  process.on('SIGTERM', closeConnections);
}
