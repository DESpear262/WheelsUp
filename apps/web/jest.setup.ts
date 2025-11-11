// Jest setup file for database tests
import { jest } from '@jest/globals';

// Mock postgres module to prevent actual database connections during testing
const mockPostgres = jest.fn(() => ({
  end: jest.fn().mockResolvedValue(undefined),
  totalCount: 0,
  idleCount: 0,
  waitingCount: 0,
}));

jest.mock('postgres', () => mockPostgres);

// Mock drizzle-orm to prevent actual database queries during testing
const mockDrizzle = jest.fn(() => ({
  select: jest.fn(() => ({
    from: jest.fn(() => ({
      where: jest.fn(() => ({
        limit: jest.fn(() => ({
          offset: jest.fn(() => []),
        })),
      })),
    })),
  })),
  insert: jest.fn(() => ({
    values: jest.fn(() => ({
      returning: jest.fn(() => []),
    })),
  })),
  update: jest.fn(() => ({
    set: jest.fn(() => ({
      where: jest.fn(() => ({
        returning: jest.fn(() => []),
      })),
    })),
  })),
}));

jest.mock('drizzle-orm/postgres-js', () => ({
  drizzle: mockDrizzle,
}));

// Set test environment variables
process.env.DATABASE_URL = 'postgresql://test:test@localhost:5432/testdb';

// Clean up mocks after all tests
afterAll(async () => {
  jest.clearAllMocks();
});
