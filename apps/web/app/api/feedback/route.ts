/**
 * Feedback API Route - Handle user feedback submissions
 *
 * POST /api/feedback - Accept and store user feedback/corrections
 *
 * Request Body:
 * {
 *   "schoolId": "school_123",
 *   "schoolName": "Example Aviation Academy",
 *   "submittedAt": "2025-11-11T17:00:00.000Z",
 *   "submitter": {
 *     "name": "John Doe",
 *     "email": "john@example.com",
 *     "phone": "+1-555-123-4567"
 *   },
 *   "corrections": {
 *     "contactInfo": "Updated phone number...",
 *     "pricing": "Hourly rate should be $185",
 *     "description": "School description corrections...",
 *     "programs": "Additional program information...",
 *     "otherCorrections": "Any other corrections..."
 *   },
 *   "userAgent": "Mozilla/5.0...",
 *   "url": "https://wheelsup.com/schools/school_123"
 * }
 */

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import crypto from 'crypto';

// Feedback submission schema validation
const FeedbackSubmissionSchema = z.object({
  schoolId: z.string().min(1),
  schoolName: z.string().min(1),
  submittedAt: z.string().datetime(),
  submitter: z.object({
    name: z.string().optional(),
    email: z.string().email(),
    phone: z.string().optional(),
  }),
  corrections: z.object({
    contactInfo: z.string().optional(),
    pricing: z.string().optional(),
    description: z.string().optional(),
    programs: z.string().optional(),
    otherCorrections: z.string().optional(),
  }),
  userAgent: z.string().optional(),
  url: z.string().url().optional(),
});

// Mock S3 client for development
// In production, this would use actual AWS S3 client
class MockS3Client {
  public bucketName: string;

  constructor(bucketName: string = 'wheelsup-feedback') {
    this.bucketName = bucketName;
  }

  async putObject(params: { Bucket: string; Key: string; Body: string; ContentType: string; Metadata: Record<string, string> }) {
    // In production, this would upload to actual S3
    console.log(`[MOCK S3] Would upload to s3://${params.Bucket}/${params.Key}`);
    console.log(`[MOCK S3] Content length: ${params.Body.length} characters`);
    console.log(`[MOCK S3] Metadata:`, params.Metadata);

    // Simulate successful upload
    return {
      ETag: `"${crypto.randomBytes(16).toString('hex')}"`,
      VersionId: crypto.randomBytes(8).toString('hex'),
    };
  }
}

// Initialize mock S3 client
const s3Client = new MockS3Client();

/**
 * Generate a unique feedback ID
 */
function generateFeedbackId(): string {
  return crypto.randomBytes(8).toString('hex');
}

/**
 * Generate S3 key for feedback storage
 */
function generateS3Key(schoolId: string, timestamp: Date): string {
  const dateStr = timestamp.toISOString().split('T')[0].replace(/-/g, ''); // YYYYMMDD
  const timeStr = timestamp.toISOString().split('T')[1].split('.')[0].replace(/:/g, ''); // HHMMSS
  const feedbackId = generateFeedbackId();

  return `feedback/${dateStr}/${schoolId}_${timeStr}_${feedbackId}.json`;
}

/**
 * Validate feedback submission data
 */
function validateFeedbackSubmission(data: any) {
  try {
    const validated = FeedbackSubmissionSchema.parse(data);

    // Additional business logic validation
    const hasCorrections = Object.values(validated.corrections).some(
      value => value && typeof value === 'string' && value.trim().length > 0
    );

    if (!hasCorrections) {
      throw new Error('Please provide at least one correction or suggestion');
    }

    return validated;
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errorMessages = error.issues.map(e => `${e.path.join('.')}: ${e.message}`);
      throw new Error(`Validation failed: ${errorMessages.join(', ')}`);
    }
    throw error;
  }
}

/**
 * Check for spam/rate limiting (basic implementation)
 */
async function checkRateLimit(email: string): Promise<boolean> {
  // In production, this would check Redis or database for recent submissions
  // For now, allow all submissions in development
  return true;
}

/**
 * Store feedback in S3
 */
async function storeFeedback(feedback: any): Promise<{ success: boolean; s3Key?: string; error?: string }> {
  try {
    const timestamp = new Date(feedback.submittedAt);
    const s3Key = generateS3Key(feedback.schoolId, timestamp);

    // Prepare metadata for S3
    const metadata = {
      'school-id': feedback.schoolId,
      'school-name': feedback.schoolName,
      'submitter-email': feedback.submitter.email,
      'submitted-at': feedback.submittedAt,
      'feedback-type': 'correction',
      'source-url': feedback.url || '',
    };

    // Convert to JSON string
    const feedbackJson = JSON.stringify(feedback, null, 2);

    // Upload to S3 (mock implementation)
    await s3Client.putObject({
      Bucket: s3Client.bucketName,
      Key: s3Key,
      Body: feedbackJson,
      ContentType: 'application/json',
      Metadata: metadata,
    });

    return { success: true, s3Key };
  } catch (error) {
    console.error('Error storing feedback in S3:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown storage error'
    };
  }
}

/**
 * Log feedback submission for monitoring
 */
function logFeedbackSubmission(feedback: any, s3Key?: string) {
  const logEntry = {
    timestamp: new Date().toISOString(),
    schoolId: feedback.schoolId,
    schoolName: feedback.schoolName,
    submitterEmail: feedback.submitter.email,
    s3Key: s3Key,
    correctionsCount: Object.values(feedback.corrections).filter((v): v is string => typeof v === 'string' && v.trim().length > 0).length,
  };

  console.log('[FEEDBACK]', JSON.stringify(logEntry));
}

/**
 * Handle feedback submission
 */
async function processFeedbackSubmission(feedback: any) {
  // Validate submission
  const validatedFeedback = validateFeedbackSubmission(feedback);

  // Check rate limiting
  const rateLimitAllowed = await checkRateLimit(validatedFeedback.submitter.email);
  if (!rateLimitAllowed) {
    throw new Error('Rate limit exceeded. Please try again later.');
  }

  // Store in S3
  const storageResult = await storeFeedback(validatedFeedback);

  if (!storageResult.success) {
    throw new Error(`Storage failed: ${storageResult.error}`);
  }

  // Log submission
  logFeedbackSubmission(validatedFeedback, storageResult.s3Key);

  return {
    feedbackId: generateFeedbackId(),
    s3Key: storageResult.s3Key,
    stored: true,
  };
}

/**
 * POST handler for feedback submissions
 */
export async function POST(request: NextRequest) {
  try {
    // Parse request body
    const requestBody = await request.json();

    // Process feedback submission
    const result = await processFeedbackSubmission(requestBody);

    // Return success response
    return NextResponse.json({
      success: true,
      message: 'Feedback submitted successfully',
      feedbackId: result.feedbackId,
      storedAt: result.s3Key,
    }, {
      status: 200,
      headers: {
        'X-API-Version': '1.0.0',
      },
    });

  } catch (error) {
    console.error('Feedback submission error:', error);

    // Handle different error types
    if (error instanceof Error) {
      const errorMessage = error.message;

      if (errorMessage.includes('Validation failed')) {
        return NextResponse.json({
          success: false,
          error: 'Invalid feedback data',
          details: errorMessage,
        }, { status: 400 });
      }

      if (errorMessage.includes('provide at least one correction')) {
        return NextResponse.json({
          success: false,
          error: errorMessage,
        }, { status: 400 });
      }

      if (errorMessage.includes('Rate limit')) {
        return NextResponse.json({
          success: false,
          error: errorMessage,
        }, { status: 429 });
      }

      if (errorMessage.includes('Storage failed')) {
        return NextResponse.json({
          success: false,
          error: 'Failed to store feedback',
          details: errorMessage,
        }, { status: 500 });
      }
    }

    // Generic error response
    return NextResponse.json({
      success: false,
      error: 'Internal server error',
    }, { status: 500 });
  }
}

/**
 * GET handler - not implemented for feedback
 */
export async function GET(request: NextRequest) {
  return NextResponse.json(
    { error: 'Method not allowed' },
    { status: 405 }
  );
}

/**
 * PUT/PATCH/DELETE handlers - not implemented for feedback
 */
export async function PUT(request: NextRequest) {
  return NextResponse.json(
    { error: 'Method not allowed' },
    { status: 405 }
  );
}

export async function PATCH(request: NextRequest) {
  return NextResponse.json(
    { error: 'Method not allowed' },
    { status: 405 }
  );
}

export async function DELETE(request: NextRequest) {
  return NextResponse.json(
    { error: 'Method not allowed' },
    { status: 405 }
  );
}
