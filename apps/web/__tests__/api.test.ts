/**
 * API Routes Tests
 *
 * Comprehensive tests for API endpoints to improve test coverage
 */

import { NextRequest, NextResponse } from 'next/server';

// Mock the database and other dependencies before importing
const mockFindSchools = jest.fn();
const mockFindSchoolById = jest.fn();
const mockFindProgramsBySchool = jest.fn();
const mockFindPricingBySchool = jest.fn();
const mockHandleDatabaseError = jest.fn();

jest.mock('../lib/db', () => ({
  findSchools: mockFindSchools,
  findSchoolById: mockFindSchoolById,
  findProgramsBySchool: mockFindProgramsBySchool,
  findPricingBySchool: mockFindPricingBySchool,
  handleDatabaseError: mockHandleDatabaseError,
}));

const mockSchoolsQueryParse = jest.fn();
const mockSchoolDetailQueryParse = jest.fn();

jest.mock('../lib/schemas', () => ({
  SchoolsQuerySchema: {
    parse: mockSchoolsQueryParse,
  },
  SchoolDetailQuerySchema: {
    parse: mockSchoolDetailQueryParse,
  },
}));

// Import the API functions after mocking
import { GET as getSchools } from '../app/api/schools/route';
import { GET as getSchoolById } from '../app/api/schools/[id]/route';

describe('Schools API Routes', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('GET /api/schools', () => {
    const mockSchools = [
      {
        id: '1',
        name: 'Test School 1',
        state: 'CA',
        vaApproved: true,
        minRating: 4.5,
        location: { city: 'Los Angeles' },
        accreditation: { type: 'Part 141' },
      },
      {
        id: '2',
        name: 'Test School 2',
        state: 'TX',
        vaApproved: false,
        minRating: 4.0,
      },
    ];

    it('should return schools with default pagination', async () => {
      // Mock the schema parsing and database call
      mockSchoolsQueryParse.mockReturnValue({
        page: 1,
        limit: 20,
        sortBy: 'name',
        sortOrder: 'asc',
      });
      mockFindSchools.mockResolvedValue(mockSchools);

      // Create mock request
      const url = new URL('http://localhost:3000/api/schools');
      const request = new NextRequest(url);

      const response = await getSchools(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(mockFindSchools).toHaveBeenCalledWith({
        limit: 20,
        offset: 0,
      });
      expect(data.schools).toHaveLength(2);
      expect(data.pagination).toEqual({
        page: 1,
        limit: 20,
        totalCount: 2,
        totalPages: 1,
        hasNext: false,
        hasPrev: false,
      });
    });

    it('should apply state filter correctly', async () => {
      mockFindSchools.mockResolvedValue([mockSchools[0]]);
      mockSchoolsQueryParse.mockReturnValue({
        state: 'CA',
        page: 1,
        limit: 20,
        sortBy: 'name',
        sortOrder: 'asc',
      });

      const url = new URL('http://localhost:3000/api/schools?state=CA');
      const request = new NextRequest(url);

      await getSchools(request);

      expect(mockFindSchools).toHaveBeenCalledWith({
        state: 'CA',
        limit: 20,
        offset: 0,
      });
    });

    it('should apply VA approval filter', async () => {
      mockFindSchools.mockResolvedValue([mockSchools[0]]);
      mockSchoolsQueryParse.mockReturnValue({
        vaApproved: true,
        page: 1,
        limit: 20,
        sortBy: 'name',
        sortOrder: 'asc',
      });

      const url = new URL('http://localhost:3000/api/schools?vaApproved=true');
      const request = new NextRequest(url);

      await getSchools(request);

      expect(mockFindSchools).toHaveBeenCalledWith({
        vaApproved: true,
        limit: 20,
        offset: 0,
      });
    });

    it('should apply city filter', async () => {
      mockFindSchools.mockResolvedValue([mockSchools[0]]);
      mockSchoolsQueryParse.mockReturnValue({
        city: 'Los Angeles',
        page: 1,
        limit: 20,
        sortBy: 'name',
        sortOrder: 'asc',
      });

      const url = new URL('http://localhost:3000/api/schools?city=Los Angeles');
      const request = new NextRequest(url);

      const response = await getSchools(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.schools).toHaveLength(1);
    });

    it('should handle pagination correctly', async () => {
      mockFindSchools.mockResolvedValue(mockSchools);
      mockSchoolsQueryParse.mockReturnValue({
        page: 2,
        limit: 1,
        sortBy: 'name',
        sortOrder: 'asc',
      });

      const url = new URL('http://localhost:3000/api/schools?page=2&limit=1');
      const request = new NextRequest(url);

      const response = await getSchools(request);
      const data = await response.json();

      expect(mockFindSchools).toHaveBeenCalledWith({
        limit: 1,
        offset: 1, // (page-1) * limit = 1
      });
      expect(data.pagination.page).toBe(2);
      expect(data.pagination.limit).toBe(1);
    });

    it('should handle invalid query parameters', async () => {
      mockSchoolsQueryParse.mockImplementation(() => {
        throw new Error('Invalid parameters');
      });

      const url = new URL('http://localhost:3000/api/schools?invalid=param');
      const request = new NextRequest(url);

      const response = await getSchools(request);
      expect(response.status).toBe(500);
    });

    it('should handle database errors', async () => {
      mockFindSchools.mockRejectedValue(new Error('Database error'));
      mockHandleDatabaseError.mockReturnValue('Database connection failed');

      const url = new URL('http://localhost:3000/api/schools');
      const request = new NextRequest(url);

      const response = await getSchools(request);
      const data = await response.json();

      expect(response.status).toBe(500);
      expect(data.error).toBe('Database connection failed');
    });
  });

  describe('GET /api/schools/[id]', () => {
    const mockSchool = {
      id: '123',
      schoolId: 'school-123',
      name: 'Test Aviation School',
      snapshotId: '2025Q1-MVP',
      extractedAt: '2025-01-15T10:00:00Z',
    };

    it('should return school details successfully', async () => {
      mockFindSchoolById.mockResolvedValue(mockSchool);
      mockSchoolDetailQueryParse.mockReturnValue({
        includePrograms: false,
        includePricing: false,
        includeMetrics: false,
        includeAttributes: false,
      });

      const url = new URL('http://localhost:3000/api/schools/123');
      const request = new NextRequest(url);

      const response = await getSchoolById(request, { params: { id: '123' } });
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(mockFindSchoolById).toHaveBeenCalledWith('123');
      expect(data.school).toEqual(mockSchool);
      expect(data.metadata.snapshotId).toBe('2025Q1-MVP');
    });

    it('should return 404 for non-existent school', async () => {
      mockFindSchoolById.mockResolvedValue(null);

      const url = new URL('http://localhost:3000/api/schools/999');
      const request = new NextRequest(url);

      const response = await getSchoolById(request, { params: { id: '999' } });
      const data = await response.json();

      expect(response.status).toBe(404);
      expect(data.error).toBe('School not found');
    });

    it('should include programs when requested', async () => {
      const mockPrograms = [{ id: '1', programId: 'ppl', name: 'Private Pilot License' }];

      mockFindSchoolById.mockResolvedValue(mockSchool);
      mockFindProgramsBySchool.mockResolvedValue(mockPrograms);
      mockSchoolDetailQueryParse.mockReturnValue({
        includePrograms: true,
        includePricing: false,
        includeMetrics: false,
        includeAttributes: false,
      });

      const url = new URL('http://localhost:3000/api/schools/123?includePrograms=true');
      const request = new NextRequest(url);

      const response = await getSchoolById(request, { params: { id: '123' } });
      const data = await response.json();

      expect(mockFindProgramsBySchool).toHaveBeenCalledWith('123');
      expect(data.programs).toHaveLength(1);
      expect(data.metadata.dataCompleteness.hasPrograms).toBe(true);
    });

    it('should include pricing when requested', async () => {
      const mockPricing = { id: '1', hourlyRates: { c172: 150 } };

      mockFindSchoolById.mockResolvedValue(mockSchool);
      mockFindPricingBySchool.mockResolvedValue(mockPricing);
      mockSchoolDetailQueryParse.mockReturnValue({
        includePrograms: false,
        includePricing: true,
        includeMetrics: false,
        includeAttributes: false,
      });

      const url = new URL('http://localhost:3000/api/schools/123?includePricing=true');
      const request = new NextRequest(url);

      const response = await getSchoolById(request, { params: { id: '123' } });
      const data = await response.json();

      expect(mockFindPricingBySchool).toHaveBeenCalledWith('123');
      expect(data.pricing).toEqual(mockPricing);
      expect(data.metadata.dataCompleteness.hasPricing).toBe(true);
    });

    it('should handle invalid school ID', async () => {
      const url = new URL('http://localhost:3000/api/schools/invalid-id');
      const request = new NextRequest(url);

      const response = await getSchoolById(request, { params: { id: 'invalid-id' } });
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toContain('Invalid school ID');
    });

    it('should handle database errors gracefully', async () => {
      mockFindSchoolById.mockRejectedValue(new Error('Database error'));
      mockHandleDatabaseError.mockReturnValue('Database connection failed');

      const url = new URL('http://localhost:3000/api/schools/123');
      const request = new NextRequest(url);

      const response = await getSchoolById(request, { params: { id: '123' } });
      const data = await response.json();

      expect(response.status).toBe(500);
      expect(data.error).toBe('Database connection failed');
    });
  });
});
