/**
 * Logger Tests
 *
 * Tests for the structured logging functionality
 */

import { logger, initSentry } from '../lib/logger';

// Mock Sentry
jest.mock('@sentry/nextjs', () => ({
  init: jest.fn(),
  captureException: jest.fn(),
  captureMessage: jest.fn(),
  withScope: jest.fn((callback) => callback({ setContext: jest.fn(), setTag: jest.fn() })),
  Severity: {
    Warning: 'warning',
    Error: 'error',
  },
}));

// Mock console methods
const originalConsole = { ...console };
beforeAll(() => {
  console.log = jest.fn();
  console.info = jest.fn();
  console.warn = jest.fn();
  console.error = jest.fn();
  console.debug = jest.fn();
});

afterAll(() => {
  Object.assign(console, originalConsole);
});

describe('Logger', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset environment
    process.env.LOG_LEVEL = 'info';
    process.env.SENTRY_DSN = undefined;
    process.env.NODE_ENV = 'development';
  });

  describe('initSentry', () => {
    test('initializes Sentry when DSN is provided', () => {
      process.env.SENTRY_DSN = 'https://test@test.ingest.sentry.io/test';
      process.env.NODE_ENV = 'production';

      initSentry();

      const { init } = require('@sentry/nextjs');
      expect(init).toHaveBeenCalledWith(
        expect.objectContaining({
          dsn: 'https://test@test.ingest.sentry.io/test',
          environment: 'production',
        })
      );
    });

    test('skips Sentry initialization when no DSN', () => {
      delete process.env.SENTRY_DSN;
      initSentry();
      const { init } = require('@sentry/nextjs');
      expect(init).not.toHaveBeenCalled();
    });
  });

  describe('Basic Logging', () => {
    test('info logs are displayed', () => {
      logger.info('Test message');
      expect(console.info).toHaveBeenCalledWith(
        expect.stringContaining('INFO  Test message')
      );
    });

    test('warn logs are displayed', () => {
      logger.warn('Warning message');
      expect(console.warn).toHaveBeenCalledWith(
        expect.stringContaining('WARN  Warning message')
      );
    });

    test('error logs are displayed', () => {
      logger.error('Error message');
      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining('ERROR Error message')
      );
    });

    test('debug logs are filtered at info level', () => {
      logger.debug('Debug message');
      expect(console.debug).not.toHaveBeenCalled();
    });
  });

  describe('API Request Logging', () => {
    test('logs successful API requests', () => {
      logger.apiRequest('GET', '/api/schools', 200, 150);
      expect(console.info).toHaveBeenCalledWith(
        expect.stringContaining('INFO  API GET /api/schools - 200 (150ms)')
      );
    });

    test('logs failed API requests as warnings', () => {
      logger.apiRequest('GET', '/api/schools', 500, 200);
      expect(console.warn).toHaveBeenCalledWith(
        expect.stringContaining('WARN  API GET /api/schools - 500 (200ms)')
      );
    });
  });

  describe('Database Logging', () => {
    test('logs failed database operations as errors', () => {
      logger.database('INSERT', 'schools', 100, false);
      expect(console.error).toHaveBeenCalledWith(
        expect.stringContaining('ERROR DB INSERT on schools - FAILED (100ms)')
      );
    });
  });

  describe('Message Formatting', () => {
    test('includes timestamp in log messages', () => {
      logger.info('Test message');
      const loggedMessage = (console.info as jest.Mock).mock.calls[0][0];
      expect(loggedMessage).toMatch(/^\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
    });

    test('includes metadata in JSON format', () => {
      logger.info('Test with metadata', { userId: 123 });
      const loggedMessage = (console.info as jest.Mock).mock.calls[0][0];
      expect(loggedMessage).toContain('"userId":123');
    });
  });
});
