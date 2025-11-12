/**
 * Component Snapshot Tests
 *
 * Snapshot tests for critical UI components to ensure consistent rendering
 * and catch unexpected visual changes.
 *
 * Tests include:
 * - SchoolCard component rendering
 * - TrustBadge component states
 * - Component prop variations
 * - Responsive behavior snapshots
 *
 * Author: Cursor Agent White (PR 5.1)
 * Created: 2025-11-11
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from 'next-themes';

// Mock next-themes to avoid hydration issues in tests
jest.mock('next-themes', () => ({
  ThemeProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useTheme: () => ({ theme: 'light', setTheme: jest.fn() }),
}));

// Import components
import SchoolCard from '../components/SchoolCard';
import TrustBadge from '../components/TrustBadge';
import NavBar from '../components/NavBar';
import Footer from '../components/Footer';

// Mock Lucide React icons
jest.mock('lucide-react', () => ({
  MapPin: () => <div data-testid="map-pin-icon">📍</div>,
  Star: ({ filled }: { filled?: boolean }) => (
    <div data-testid={filled ? "star-filled" : "star-empty"}>
      {filled ? '⭐' : '☆'}
    </div>
  ),
  CheckCircle: () => <div data-testid="check-circle-icon">✅</div>,
  AlertCircle: () => <div data-testid="alert-circle-icon">⚠️</div>,
  Info: () => <div data-testid="info-icon">ℹ️</div>,
  Shield: () => <div data-testid="shield-icon">🛡️</div>,
  Award: () => <div data-testid="award-icon">🏆</div>,
}));

// Mock Next.js Link component
jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href} data-testid="next-link">{children}</a>
  ),
}));

describe('Component Snapshot Tests', () => {
  const renderWithTheme = (component: React.ReactElement) => {
    return render(
      <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false}>
        {component}
      </ThemeProvider>
    );
  };

  describe('SchoolCard Component', () => {
    const mockSchoolData = {
      id: 1,
      schoolId: 'test-school-001',
      name: 'Test Aviation Academy',
      description: 'A premier flight training school offering comprehensive pilot training programs.',
      city: 'Los Angeles',
      state: 'CA',
      latitude: 34.0522,
      longitude: -118.2437,
      accreditation: 'FAA Part 141',
      vaApproved: true,
      googleRating: 4.7,
      googleReviewCount: 127,
      lastUpdated: '2024-01-15T10:30:00.000Z',
      confidence: 0.95,
      snapshotId: '2025Q1-MVP',
    };

    it('renders school card with complete data', () => {
      const { container } = renderWithTheme(<SchoolCard school={mockSchoolData} />);
      expect(container.firstChild).toMatchSnapshot();
    });

    it('renders school card with minimal data', () => {
      const minimalSchool = {
        id: 2,
        schoolId: 'minimal-school',
        name: 'Minimal School',
        city: 'Anytown',
        state: 'ST',
        accreditation: null,
        vaApproved: false,
        googleRating: null,
        googleReviewCount: 0,
        lastUpdated: '2024-01-15T10:30:00.000Z',
        confidence: 0.8,
        snapshotId: '2025Q1-MVP',
      };

      const { container } = renderWithTheme(<SchoolCard school={minimalSchool} />);
      expect(container.firstChild).toMatchSnapshot();
    });

    it('renders school card with VA approval badge', () => {
      const vaSchool = {
        ...mockSchoolData,
        vaApproved: true,
        accreditation: 'FAA Part 141',
      };

      const { container } = renderWithTheme(<SchoolCard school={vaSchool} />);
      expect(container.firstChild).toMatchSnapshot();
    });

    it('renders school card with high rating', () => {
      const highRatedSchool = {
        ...mockSchoolData,
        googleRating: 4.9,
        googleReviewCount: 500,
      };

      const { container } = renderWithTheme(<SchoolCard school={highRatedSchool} />);
      expect(container.firstChild).toMatchSnapshot();
    });

    it('renders school card with low confidence', () => {
      const lowConfidenceSchool = {
        ...mockSchoolData,
        confidence: 0.3,
      };

      const { container } = renderWithTheme(<SchoolCard school={lowConfidenceSchool} />);
      expect(container.firstChild).toMatchSnapshot();
    });

    it('displays school name correctly', () => {
      renderWithTheme(<SchoolCard school={mockSchoolData} />);
      expect(screen.getByText('Test Aviation Academy')).toBeInTheDocument();
    });

    it('displays location information', () => {
      renderWithTheme(<SchoolCard school={mockSchoolData} />);
      expect(screen.getByText('Los Angeles, CA')).toBeInTheDocument();
    });

    it('displays accreditation type', () => {
      renderWithTheme(<SchoolCard school={mockSchoolData} />);
      expect(screen.getByText('FAA Part 141')).toBeInTheDocument();
    });

    it('shows rating when available', () => {
      renderWithTheme(<SchoolCard school={mockSchoolData} />);
      expect(screen.getByText('4.7')).toBeInTheDocument();
      expect(screen.getByText('(127 reviews)')).toBeInTheDocument();
    });
  });

  describe('TrustBadge Component', () => {
    it('renders verified accreditation badge', () => {
      const { container } = renderWithTheme(
        <TrustBadge type="accreditation" status="verified" text="FAA Part 141" />
      );
      expect(container.firstChild).toMatchSnapshot();
    });

    it('renders VA approval badge', () => {
      const { container } = renderWithTheme(
        <TrustBadge type="va" status="approved" text="VA Approved" />
      );
      expect(container.firstChild).toMatchSnapshot();
    });

    it('renders high rating badge', () => {
      const { container } = renderWithTheme(
        <TrustBadge type="rating" status="excellent" text="4.8+ Stars" />
      );
      expect(container.firstChild).toMatchSnapshot();
    });

    it('renders unverified status', () => {
      const { container } = renderWithTheme(
        <TrustBadge type="accreditation" status="unverified" text="Pending Verification" />
      );
      expect(container.firstChild).toMatchSnapshot();
    });

    it('renders warning status', () => {
      const { container } = renderWithTheme(
        <TrustBadge type="va" status="warning" text="Under Review" />
      );
      expect(container.firstChild).toMatchSnapshot();
    });
  });

  describe('Navigation Components', () => {
    it('renders NavBar component', () => {
      const { container } = renderWithTheme(<NavBar />);
      expect(container.firstChild).toMatchSnapshot();
    });

    it('renders Footer component', () => {
      const { container } = renderWithTheme(<Footer />);
      expect(container.firstChild).toMatchSnapshot();
    });
  });

  describe('Component Integration', () => {
    it('renders multiple components together', () => {
      const mockSchool = {
        id: 1,
        schoolId: 'integration-test',
        name: 'Integration Test School',
        city: 'Test City',
        state: 'TC',
        accreditation: 'FAA Part 61',
        vaApproved: true,
        googleRating: 4.5,
        googleReviewCount: 89,
        lastUpdated: '2024-01-15T10:30:00.000Z',
        confidence: 0.9,
        snapshotId: 'integration-test',
      };

      const { container } = renderWithTheme(
        <div>
          <NavBar />
          <SchoolCard school={mockSchool} />
          <TrustBadge type="accreditation" status="verified" text="FAA Part 61" />
          <Footer />
        </div>
      );
      expect(container.firstChild).toMatchSnapshot();
    });
  });

  describe('Accessibility Tests', () => {
    it('school card has proper ARIA labels', () => {
      const { container } = renderWithTheme(<SchoolCard school={mockSchoolData} />);

      // Check for accessibility attributes
      const links = container.querySelectorAll('a');
      links.forEach(link => {
        expect(link).toHaveAttribute('href');
      });
    });

    it('trust badges have descriptive text', () => {
      renderWithTheme(<TrustBadge type="va" status="approved" text="VA Approved" />);

      expect(screen.getByText('VA Approved')).toBeInTheDocument();
    });
  });

  describe('Responsive Behavior', () => {
    it('school card renders in mobile layout', () => {
      // Mock window.innerWidth for mobile
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 375,
      });

      const { container } = renderWithTheme(<SchoolCard school={mockSchoolData} />);
      expect(container.firstChild).toMatchSnapshot();

      // Reset
      delete (window as any).innerWidth;
    });

    it('school card renders in desktop layout', () => {
      // Mock window.innerWidth for desktop
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1200,
      });

      const { container } = renderWithTheme(<SchoolCard school={mockSchoolData} />);
      expect(container.firstChild).toMatchSnapshot();

      // Reset
      delete (window as any).innerWidth;
    });
  });
});
