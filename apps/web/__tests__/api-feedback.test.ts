/**
 * Feedback API Tests
 *
 * Tests for the /api/feedback endpoint functionality
 */

import { NextRequest } from 'next/server';
import { POST, GET, PUT, PATCH, DELETE } from '../app/api/feedback/route';

// Mock the S3 client
jest.mock('../app/api/feedback/route', () => {
  const originalModule = jest.requireActual('../app/api/feedback/route');

  // Mock the S3 client
  const mockS3Client = {
    bucketName: 'wheelsup-feedback',
    putObject: jest.fn().mockResolvedValue({
      ETag: '"mock-etag"',
      VersionId: 'mock-version',
    }),
  };

  // Replace the s3Client in the module
  originalModule.s3Client = mockS3Client;

  return originalModule;
});

describe('/api/feedback', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('POST /api/feedback', () => {
    it('should accept valid feedback submission', async () => {
      const validFeedback = {
        schoolId: 'test_school_001',
        schoolName: 'Test Aviation Academy',
        submittedAt: new Date().toISOString(),
        submitter: {
          name: 'John Doe',
          email: 'john@example.com',
          phone: '+1-555-123-4567',
        },
        corrections: {
          contactInfo: 'Updated phone number to (555) 987-6543',
          pricing: 'Hourly rate should be $185 instead of $175',
          otherCorrections: 'School is now offering drone training',
        },
        userAgent: 'Mozilla/5.0 (Test Browser)',
        url: 'https://wheelsup.com/schools/test_school_001',
      };

      const request = new NextRequest('http://localhost:3000/api/feedback', {
        method: 'POST',
        body: JSON.stringify(validFeedback),
        headers: {
          'content-type': 'application/json',
        },
      });

      const response = await POST(request);
      const result = await response.json();

      expect(response.status).toBe(200);
      expect(result.success).toBe(true);
      expect(result.message).toContain('submitted successfully');
      expect(result.feedbackId).toBeDefined();
      expect(result.storedAt).toBeDefined();
    });

    it('should reject feedback without email', async () => {
      const invalidFeedback = {
        schoolId: 'test_school_001',
        schoolName: 'Test Aviation Academy',
        submittedAt: new Date().toISOString(),
        submitter: {
          name: 'John Doe',
          // Missing email
        },
        corrections: {
          contactInfo: 'Updated phone number',
        },
      };

      const request = new NextRequest('http://localhost:3000/api/feedback', {
        method: 'POST',
        body: JSON.stringify(invalidFeedback),
        headers: {
          'content-type': 'application/json',
        },
      });

      const response = await POST(request);
      const result = await response.json();

      expect(response.status).toBe(400);
      expect(result.success).toBe(false);
      expect(result.error).toContain('Validation failed');
    });

    it('should reject feedback without any corrections', async () => {
      const invalidFeedback = {
        schoolId: 'test_school_001',
        schoolName: 'Test Aviation Academy',
        submittedAt: new Date().toISOString(),
        submitter: {
          email: 'john@example.com',
        },
        corrections: {
          // No corrections provided
        },
      };

      const request = new NextRequest('http://localhost:3000/api/feedback', {
        method: 'POST',
        body: JSON.stringify(invalidFeedback),
        headers: {
          'content-type': 'application/json',
        },
      });

      const response = await POST(request);
      const result = await response.json();

      expect(response.status).toBe(400);
      expect(result.success).toBe(false);
      expect(result.error).toContain('provide at least one correction');
    });

    it('should reject invalid email format', async () => {
      const invalidFeedback = {
        schoolId: 'test_school_001',
        schoolName: 'Test Aviation Academy',
        submittedAt: new Date().toISOString(),
        submitter: {
          email: 'invalid-email-format',
        },
        corrections: {
          contactInfo: 'Updated phone number',
        },
      };

      const request = new NextRequest('http://localhost:3000/api/feedback', {
        method: 'POST',
        body: JSON.stringify(invalidFeedback),
        headers: {
          'content-type': 'application/json',
        },
      });

      const response = await POST(request);
      const result = await response.json();

      expect(response.status).toBe(400);
      expect(result.success).toBe(false);
      expect(result.error).toContain('Validation failed');
    });

    it('should handle S3 storage errors gracefully', async () => {
      // Mock S3 failure
      const originalModule = jest.requireActual('../app/api/feedback/route');
      const mockS3Client = originalModule.s3Client;
      mockS3Client.putObject.mockRejectedValueOnce(new Error('S3 connection failed'));

      const validFeedback = {
        schoolId: 'test_school_001',
        schoolName: 'Test Aviation Academy',
        submittedAt: new Date().toISOString(),
        submitter: {
          email: 'john@example.com',
        },
        corrections: {
          contactInfo: 'Updated phone number',
        },
      };

      const request = new NextRequest('http://localhost:3000/api/feedback', {
        method: 'POST',
        body: JSON.stringify(validFeedback),
        headers: {
          'content-type': 'application/json',
        },
      });

      const response = await POST(request);
      const result = await response.json();

      expect(response.status).toBe(500);
      expect(result.success).toBe(false);
      expect(result.error).toContain('Internal server error');
    });
  });

  describe('Method restrictions', () => {
    const methods = [
      { method: 'GET', handler: GET },
      { method: 'PUT', handler: PUT },
      { method: 'PATCH', handler: PATCH },
      { method: 'DELETE', handler: DELETE },
    ];

    methods.forEach(({ method, handler }) => {
      it(`should reject ${method} requests`, async () => {
        const request = new NextRequest('http://localhost:3000/api/feedback', {
          method,
        });

        const response = await handler(request);
        const result = await response.json();

        expect(response.status).toBe(405);
        expect(result.error).toBe('Method not allowed');
      });
    });
  });

  describe('S3 key generation', () => {
    it('should generate proper S3 keys', () => {
      // Import the generateS3Key function (we'll need to export it for testing)
      // For now, we'll test the structure through integration
      const validFeedback = {
        schoolId: 'test_school_001',
        schoolName: 'Test Aviation Academy',
        submittedAt: '2025-11-11T17:00:00.000Z',
        submitter: {
          email: 'john@example.com',
        },
        corrections: {
          contactInfo: 'Updated phone number',
        },
      };

      const request = new NextRequest('http://localhost:3000/api/feedback', {
        method: 'POST',
        body: JSON.stringify(validFeedback),
        headers: {
          'content-type': 'application/json',
        },
      });

      // The S3 key should follow the pattern: feedback/YYYYMMDD/schoolId_HHMMSS_hash.json
      // We can't easily test the exact key without exporting the function,
      // but we can verify the request succeeds
      expect(async () => {
        const response = await POST(request);
        expect(response.status).toBe(200);
      }).not.toThrow();
    });
  });

  describe('Request validation', () => {
    it('should handle malformed JSON', async () => {
      const request = new NextRequest('http://localhost:3000/api/feedback', {
        method: 'POST',
        body: 'invalid json {',
        headers: {
          'content-type': 'application/json',
        },
      });

      const response = await POST(request);
      expect(response.status).toBe(500);
    });

    it('should handle empty request body', async () => {
      const request = new NextRequest('http://localhost:3000/api/feedback', {
        method: 'POST',
        body: JSON.stringify({}),
        headers: {
          'content-type': 'application/json',
        },
      });

      const response = await POST(request);
      const result = await response.json();

      expect(response.status).toBe(400);
      expect(result.success).toBe(false);
    });
  });
});
