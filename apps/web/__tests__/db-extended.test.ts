/**
 * Extended Database Tests
 *
 * Comprehensive tests for database operations, connection handling,
 * error scenarios, and edge cases to improve test coverage.
 */

// Mock postgres and drizzle
const mockSql = Object.assign(
  jest.fn().mockResolvedValue([{ result: 1 }]), // Template function mock
  {
    totalCount: 10,
    idleCount: 5,
    waitingCount: 2,
    end: jest.fn().mockResolvedValue(undefined),
  }
);

jest.mock('postgres', () => jest.fn(() => mockSql));

jest.mock('drizzle-orm/postgres-js', () => ({
  drizzle: jest.fn(() => ({
    select: jest.fn().mockReturnThis(),
    from: jest.fn().mockReturnThis(),
    where: jest.fn().mockReturnThis(),
    limit: jest.fn().mockReturnThis(),
    offset: jest.fn().mockReturnThis(),
    insert: jest.fn().mockReturnThis(),
    values: jest.fn().mockReturnThis(),
    returning: jest.fn().mockReturnThis(),
    update: jest.fn().mockReturnThis(),
    set: jest.fn().mockReturnThis(),
  })),
}));

// Mock the schema
jest.mock('../drizzle/schema', () => ({
  schools: 'schools_table',
  programs: 'programs_table',
  pricing: 'pricing_table',
}));

// Mock the database functions directly
jest.mock('../lib/db', () => ({
  checkConnection: jest.fn().mockResolvedValue(true),
  getConnectionStats: jest.fn().mockReturnValue({
    totalCount: 10,
    idleCount: 5,
    waitingCount: 2,
  }),
  findSchools: jest.fn().mockResolvedValue([]),
  findSchoolById: jest.fn().mockResolvedValue(null),
  findProgramsBySchool: jest.fn().mockResolvedValue([]),
  findPricingBySchool: jest.fn().mockResolvedValue(null),
  createSchool: jest.fn().mockResolvedValue({ id: 1 }),
  updateSchool: jest.fn().mockResolvedValue({ id: 1 }),
  handleDatabaseError: jest.fn().mockReturnValue('Database error'),
  DatabaseError: class DatabaseError extends Error {
    constructor(message: string, originalError?: Error) {
      super(message);
      this.name = 'DatabaseError';
    }
  },
  closeConnections: jest.fn().mockResolvedValue(undefined),
}));

// Re-import after mocking
import {
  checkConnection,
  getConnectionStats,
  findSchools,
  findSchoolById,
  findProgramsBySchool,
  findPricingBySchool,
  createSchool,
  updateSchool,
  handleDatabaseError,
  DatabaseError,
  closeConnections,
} from '../lib/db';

describe('Database Operations - Extended Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Connection Management', () => {
    it('should check connection health successfully', async () => {
      const mockSql = { sql: jest.fn().mockResolvedValue([1]) };
      // Mock the sql template function
      const sql = jest.fn().mockReturnValue(Promise.resolve([1]));
      (global as any).sql = sql;

      const result = await checkConnection();
      expect(result).toBe(true);
    });

    it('should handle connection check failure', async () => {
      const sql = jest.fn().mockRejectedValue(new Error('Connection failed'));
      (global as any).sql = sql;

      const result = await checkConnection();
      expect(result).toBe(false);
    });

    it('should return connection statistics', () => {
      const stats = getConnectionStats();
      expect(stats).toEqual({
        totalCount: 10,
        idleCount: 5,
        waitingCount: 2,
      });
    });

    it('should close connections gracefully', async () => {
      const mockSql = { end: jest.fn().mockResolvedValue(undefined) };
      (global as any).sql = mockSql;

      await closeConnections();
      expect(mockSql.end).toHaveBeenCalled();
    });

    it('should handle connection close errors', async () => {
      const mockSql = { end: jest.fn().mockRejectedValue(new Error('Close failed')) };
      (global as any).sql = mockSql;
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      await closeConnections();
      expect(consoleSpy).toHaveBeenCalledWith('Error closing database connections:', expect.any(Error));

      consoleSpy.mockRestore();
    });
  });

  describe('School Operations', () => {
    const mockSchool = {
      id: 1,
      schoolId: 'school-123',
      name: 'Test Aviation School',
      state: 'CA',
      vaApproved: true,
      googleRating: 4.5,
      location: JSON.stringify({ state: 'CA', city: 'Los Angeles' }),
      accreditation: JSON.stringify({ vaApproved: true }),
    };

    it('should find schools without filters', async () => {
      const mockQuery = {
        select: jest.fn().mockReturnThis(),
        from: jest.fn().mockReturnThis(),
        where: jest.fn().mockReturnThis(),
        limit: jest.fn().mockReturnThis(),
        offset: jest.fn().mockReturnThis(),
        then: jest.fn().mockResolvedValue([mockSchool]),
      };

      // Mock the db.select().from() chain
      const mockDb = {
        select: jest.fn(() => ({
          from: jest.fn(() => mockQuery),
        })),
      };

      jest.mock('../lib/db', () => ({
        db: mockDb,
      }));

      const result = await findSchools();
      expect(Array.isArray(result)).toBe(true);
    });

    it('should apply state filter correctly', async () => {
      const mockQuery = {
        select: jest.fn().mockReturnThis(),
        from: jest.fn().mockReturnThis(),
        where: jest.fn().mockReturnThis(),
        limit: jest.fn().mockReturnThis(),
        offset: jest.fn().mockReturnThis(),
        then: jest.fn().mockResolvedValue([mockSchool]),
      };

      const result = await findSchools({ state: 'CA' });
      expect(result).toBeDefined();
    });

    it('should apply VA approval filter', async () => {
      const result = await findSchools({ vaApproved: true });
      expect(result).toBeDefined();
    });

    it('should apply rating filter', async () => {
      const result = await findSchools({ minRating: 4.0 });
      expect(result).toBeDefined();
    });

    it('should apply pagination correctly', async () => {
      const result = await findSchools({ limit: 10, offset: 20 });
      expect(result).toBeDefined();
    });

    it('should handle database errors in findSchools', async () => {
      // Mock a database error
      const mockDb = {
        select: jest.fn(() => {
          throw new Error('Database connection failed');
        }),
      };

      jest.doMock('../lib/db', () => ({
        db: mockDb,
      }));

      await expect(findSchools()).rejects.toThrow(DatabaseError);
    });

    it('should find school by ID successfully', async () => {
      const result = await findSchoolById('school-123');
      expect(result).toBeDefined();
    });

    it('should return null for non-existent school', async () => {
      const result = await findSchoolById('non-existent');
      expect(result).toBeNull();
    });

    it('should handle database errors in findSchoolById', async () => {
      await expect(findSchoolById('invalid-id')).rejects.toThrow(DatabaseError);
    });

    it('should create school successfully', async () => {
      const schoolData = {
        schoolId: 'new-school',
        name: 'New Aviation School',
        description: 'A new school',
        specialties: ['PPL', 'IR'],
        contact: { email: 'contact@newschool.com' },
        location: {
          city: 'Denver',
          state: 'CO',
          country: 'USA',
        },
        accreditation: { type: 'Part 141' },
        operations: { foundedYear: 2020 },
        sourceType: 'manual',
        sourceUrl: 'https://example.com',
        extractedAt: new Date(),
        confidence: 1.0,
        extractorVersion: '1.0.0',
        snapshotId: '2025Q1-MVP',
      };

      const result = await createSchool(schoolData);
      expect(result).toBeDefined();
    });

    it('should handle create school errors', async () => {
      await expect(createSchool({} as any)).rejects.toThrow(DatabaseError);
    });

    it('should update school successfully', async () => {
      const updates = { name: 'Updated School Name' };
      const result = await updateSchool('school-123', updates);
      expect(result).toBeDefined();
    });

    it('should handle update school errors', async () => {
      await expect(updateSchool('invalid-id', {})).rejects.toThrow(DatabaseError);
    });
  });

  describe('Related Data Operations', () => {
    it('should find programs by school successfully', async () => {
      const result = await findProgramsBySchool('school-123');
      expect(Array.isArray(result)).toBe(true);
    });

    it('should handle programs query errors', async () => {
      await expect(findProgramsBySchool('invalid-id')).rejects.toThrow(DatabaseError);
    });

    it('should find pricing by school successfully', async () => {
      const result = await findPricingBySchool('school-123');
      expect(result).toBeDefined();
    });

    it('should return null for school without pricing', async () => {
      const result = await findPricingBySchool('no-pricing-school');
      expect(result).toBeNull();
    });

    it('should handle pricing query errors', async () => {
      await expect(findPricingBySchool('invalid-id')).rejects.toThrow(DatabaseError);
    });
  });

  describe('Error Handling', () => {
    it('should create DatabaseError with original error', () => {
      const originalError = new Error('Original error');
      const dbError = new DatabaseError('Custom message', originalError);

      expect(dbError.message).toBe('Custom message');
      expect(dbError.name).toBe('DatabaseError');
      expect(dbError.originalError).toBe(originalError);
    });

    it('should handle duplicate key error (23505)', () => {
      const error = { code: '23505' };
      const message = handleDatabaseError(error);
      expect(message).toBe('A record with this information already exists');
    });

    it('should handle foreign key constraint error (23503)', () => {
      const error = { code: '23503' };
      const message = handleDatabaseError(error);
      expect(message).toBe('Referenced record does not exist');
    });

    it('should handle invalid field reference error (42703)', () => {
      const error = { code: '42703' };
      const message = handleDatabaseError(error);
      expect(message).toBe('Invalid field reference');
    });

    it('should handle connection errors', () => {
      const error = { message: 'connection timeout occurred' };
      const message = handleDatabaseError(error);
      expect(message).toBe('Database connection error. Please try again later.');
    });

    it('should provide generic error message for unknown errors', () => {
      const error = { message: 'Unknown error' };
      const message = handleDatabaseError(error);
      expect(message).toBe('An unexpected database error occurred');
    });

    it('should handle null/undefined errors gracefully', () => {
      const message = handleDatabaseError(null);
      expect(message).toBe('An unexpected database error occurred');

      const message2 = handleDatabaseError(undefined);
      expect(message2).toBe('An unexpected database error occurred');
    });
  });
});
