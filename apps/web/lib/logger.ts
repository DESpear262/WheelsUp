/**
 * Logger Configuration for WheelsUp Web Application
 *
 * Structured logging with Sentry integration and console output.
 * Supports environment-based configuration and performance monitoring.
 */

import { init, captureException, captureMessage, withScope } from '@sentry/nextjs';

// Define Severity enum locally since it's not exported in newer Sentry versions
enum Severity {
  Warning = 'warning',
  Error = 'error',
}

// ============================================================================
// Configuration
// ============================================================================

/**
 * Logger configuration interface
 */
interface LoggerConfig {
  level: 'debug' | 'info' | 'warn' | 'error';
  enableSentry: boolean;
  sentryDSN?: string;
  environment: string;
}

/**
 * Get logger configuration from environment variables
 */
function getLoggerConfig(): LoggerConfig {
  return {
    level: (process.env.LOG_LEVEL as LoggerConfig['level']) || 'info',
    enableSentry: process.env.SENTRY_DSN ? true : false,
    sentryDSN: process.env.SENTRY_DSN,
    environment: process.env.NODE_ENV || 'development',
  };
}

// ============================================================================
// Sentry Integration
// ============================================================================

/**
 * Initialize Sentry for error tracking and performance monitoring
 */
export function initSentry(): void {
  const config = getLoggerConfig();

  if (config.enableSentry && config.sentryDSN) {
    init({
      dsn: config.sentryDSN,
      environment: config.environment,
      tracesSampleRate: 0.1, // Capture 10% of transactions for performance monitoring
      debug: config.environment === 'development',
      integrations: [],
      beforeSend: (event) => {
        // Filter out development noise
        if (config.environment === 'development' && event.level === 'warning') {
          return null;
        }
        return event;
      },
    });

    console.log(`[Logger] Sentry initialized for ${config.environment} environment`);
  } else {
    console.log('[Logger] Sentry not configured - skipping initialization');
  }
}

// ============================================================================
// Log Level Management
// ============================================================================

/**
 * Log levels enum for type safety
 */
export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
}

/**
 * Convert string level to LogLevel enum
 */
function parseLogLevel(level: string): LogLevel {
  switch (level.toLowerCase()) {
    case 'debug': return LogLevel.DEBUG;
    case 'info': return LogLevel.INFO;
    case 'warn': return LogLevel.WARN;
    case 'error': return LogLevel.ERROR;
    default: return LogLevel.INFO;
  }
}

// ============================================================================
// Logger Class
// ============================================================================

/**
 * Structured logger with Sentry integration
 */
class Logger {
  private config: LoggerConfig;
  private minLevel: LogLevel;

  constructor() {
    this.config = getLoggerConfig();
    this.minLevel = parseLogLevel(this.config.level);
  }

  /**
   * Check if a log level should be processed
   */
  private shouldLog(level: LogLevel): boolean {
    return level >= this.minLevel;
  }

  /**
   * Format log message with timestamp and level
   */
  private formatMessage(level: string, message: string, meta?: any): string {
    const timestamp = new Date().toISOString();
    const levelStr = level.toUpperCase().padEnd(5);
    const metaStr = meta ? ` ${JSON.stringify(meta)}` : '';
    return `[${timestamp}] ${levelStr} ${message}${metaStr}`;
  }

  /**
   * Log debug message
   */
  debug(message: string, meta?: any): void {
    if (this.shouldLog(LogLevel.DEBUG)) {
      console.debug(this.formatMessage('debug', message, meta));
    }
  }

  /**
   * Log info message
   */
  info(message: string, meta?: any): void {
    if (this.shouldLog(LogLevel.INFO)) {
      console.info(this.formatMessage('info', message, meta));
    }
  }

  /**
   * Log warning message
   */
  warn(message: string, meta?: any): void {
    if (this.shouldLog(LogLevel.WARN)) {
      console.warn(this.formatMessage('warn', message, meta));

      // Send warnings to Sentry in production
      if (this.config.enableSentry && this.config.environment === 'production') {
        withScope((scope) => {
          if (meta) {
            scope.setContext('metadata', meta);
          }
          captureMessage(message, Severity.Warning);
        });
      }
    }
  }

  /**
   * Log error message and capture exception
   */
  error(message: string, error?: Error, meta?: any): void {
    if (this.shouldLog(LogLevel.ERROR)) {
      console.error(this.formatMessage('error', message, meta));
      if (error) {
        console.error(error);
      }

      // Send errors to Sentry
      if (this.config.enableSentry) {
        withScope((scope) => {
          if (meta) {
            scope.setContext('metadata', meta);
          }
          if (error) {
            scope.setContext('error_details', {
              name: error.name,
              message: error.message,
              stack: error.stack,
            });
            captureException(error);
          } else {
            captureMessage(message, Severity.Error);
          }
        });
      }
    }
  }

  /**
   * Log API request (for performance monitoring)
   */
  apiRequest(method: string, url: string, statusCode: number, duration: number, meta?: any): void {
    const message = `API ${method} ${url} - ${statusCode} (${duration}ms)`;
    const logMeta = { method, url, statusCode, duration, ...meta };

    if (statusCode >= 400) {
      this.warn(message, logMeta);
    } else {
      this.info(message, logMeta);
    }

    // Send performance data to Sentry
    if (this.config.enableSentry && duration > 5000) { // Log slow requests (>5s)
      withScope((scope) => {
        scope.setTag('type', 'performance');
        scope.setContext('api_request', logMeta);
        captureMessage(`Slow API request: ${message}`, Severity.Warning);
      });
    }
  }

  /**
   * Log database operation
   */
  database(operation: string, table: string, duration: number, success: boolean, meta?: any): void {
    const status = success ? 'SUCCESS' : 'FAILED';
    const message = `DB ${operation} on ${table} - ${status} (${duration}ms)`;
    const logMeta = { operation, table, duration, success, ...meta };

    if (success) {
      this.debug(message, logMeta);
    } else {
      this.error(message, undefined, logMeta);
    }
  }
}

// ============================================================================
// Exports
// ============================================================================

/**
 * Global logger instance
 */
export const logger = new Logger();

// Export utility functions
export type { LoggerConfig };
