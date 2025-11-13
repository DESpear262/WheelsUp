/**
 * Homepage Component
 *
 * Landing page for WheelsUp with a hero section and supporting feature summary.
 * Icons in the feature area are presented as compact sidebar tabs to avoid
 * overwhelming the layout while still guiding users to core value pillars.
 */

import type { ReactElement } from 'react';
import Link from 'next/link';

interface FeatureTab {
  id: string;
  title: string;
  summary: string;
  description: string;
  icon: ReactElement;
}

interface TrustMetric {
  label: string;
  value: string;
}

const FEATURE_TABS: FeatureTab[] = [
  {
    id: 'verified-data',
    title: 'Verified Data',
    summary: 'Confidence, freshness, and provenance at a glance.',
    description:
      'Every data point in WheelsUp is paired with provenance details, freshness indicators, and extraction confidence so students trust what they see.',
    icon: (
      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    ),
  },
  {
    id: 'location-search',
    title: 'Location-Based Search',
    summary: 'Precise filtering by airport, city, or region.',
    description:
      'Search tools are built around driving distance, hub airports, and map-first exploration so prospective students can compare nearby schools without guesswork.',
    icon: (
      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
        />
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
        />
      </svg>
    ),
  },
  {
    id: 'transparent-pricing',
    title: 'Transparent Pricing',
    summary: 'Side-by-side cost comparison for each program.',
    description:
      'Tuition, aircraft rental, instructor rates, and bundled packages are normalized across programs so students can project total spend before they call a school.',
    icon: (
      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"
        />
      </svg>
    ),
  },
];

const TRUST_METRICS: TrustMetric[] = [
  { label: 'Flight Schools', value: '1000+' },
  { label: 'Complete Data', value: '70%+' },
  { label: 'Confidence Score', value: '0.8+' },
];

export default function Home() {
  return (
    <div className="min-h-screen">
      <HeroSection />
      <FeaturesSection />
    </div>
  );
}

/**
 * HeroSection
 *
 * Renders the hero area with headline, supporting copy, call-to-action, and
 * trust metrics. Keeps markup under the function line limit by delegating the
 * metric grid and decorative background to helpers.
 */
function HeroSection() {
  return (
    <section className="relative bg-gradient-to-br from-blue-50 via-white to-blue-50">
      <div className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="mb-6 text-4xl font-bold text-gray-900 sm:text-5xl lg:text-6xl">
            Find Your
            <span className="block text-blue-600">Flight School</span>
          </h1>
          <p className="mx-auto mb-8 max-w-3xl text-xl leading-relaxed text-gray-600">
            Compare flight schools nationwide with transparent pricing, verified reviews, and
            complete training program information. Your aviation journey starts here.
          </p>

          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/search"
              className="btn-primary inline-flex items-center justify-center px-8 py-4 text-lg"
            >
              Start Searching Schools
              <svg className="ml-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </Link>
          </div>

          <TrustMetrics />
        </div>
      </div>
      <BackgroundPattern />
    </section>
  );
}

/**
 * TrustMetrics
 *
 * Displays key marketplace indicators below the hero call-to-action.
 */
function TrustMetrics() {
  return (
    <div className="mx-auto mt-12 grid max-w-2xl grid-cols-1 gap-6 sm:grid-cols-3">
      {TRUST_METRICS.map((metric) => (
        <div key={metric.label} className="text-center">
          <div className="text-2xl font-bold text-blue-600">{metric.value}</div>
          <div className="text-sm text-gray-600">{metric.label}</div>
        </div>
      ))}
    </div>
  );
}

/**
 * BackgroundPattern
 *
 * Renders the decorative SVG pattern behind the hero content.
 */
function BackgroundPattern() {
  return (
    <div className="absolute inset-0 -z-10 overflow-hidden">
      <svg
        className="absolute left-[max(50%,25rem)] top-0 h-[64rem] w-[128rem] -translate-x-1/2 stroke-gray-200 [mask-image:radial-gradient(64rem_64rem_at_top,white,transparent)]"
        aria-hidden="true"
      >
        <defs>
          <pattern
            id="hero-grid-pattern"
            width={200}
            height={200}
            x="50%"
            y={-1}
            patternUnits="userSpaceOnUse"
          >
            <path d="M100 200V.5M.5 .5H200" fill="none" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" strokeWidth={0} fill="url(#hero-grid-pattern)" />
      </svg>
    </div>
  );
}

/**
 * FeaturesSection
 *
 * Highlights the three core value pillars using a sidebar tab layout with
 * compact icons. The tablist uses static roles to communicate structure to
 * assistive tech without introducing client-side state.
 */
function FeaturesSection() {
  return (
    <section className="bg-white py-16">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-12 md:flex-row">
          <aside className="md:w-1/3">
            <div className="mb-6">
              <h2 className="text-3xl font-bold text-gray-900">Why Choose WheelsUp?</h2>
              <p className="mt-3 text-lg text-gray-600">
                We make flight training decisions transparent and data-driven.
              </p>
            </div>
            <nav
              aria-label="Key WheelsUp features"
              role="tablist"
              className="flex gap-3 overflow-x-auto pb-2 md:flex-col md:overflow-visible md:pb-0"
            >
              {FEATURE_TABS.map((tab, index) => (
                <div
                  key={tab.id}
                  role="tab"
                  aria-selected={index === 0}
                  tabIndex={index === 0 ? 0 : -1}
                  className="group flex min-w-[220px] items-center gap-3 rounded-lg border border-blue-100 bg-blue-50/40 px-3 py-2 text-left transition hover:border-blue-200 hover:bg-blue-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                >
                  <span className="flex h-8 w-8 items-center justify-center rounded-md bg-blue-100 text-blue-600">
                    {tab.icon}
                  </span>
                  <div>
                    <p className="text-sm font-semibold text-gray-900">{tab.title}</p>
                    <p className="text-xs text-gray-500">{tab.summary}</p>
                  </div>
                </div>
              ))}
            </nav>
          </aside>

          <div className="grid flex-1 gap-6">
            {FEATURE_TABS.map((tab) => (
              <article
                key={`${tab.id}-details`}
                className="rounded-xl border border-gray-100 bg-white p-6 shadow-sm ring-1 ring-black/5"
              >
                <h3 className="text-lg font-semibold text-gray-900">{tab.title}</h3>
                <p className="mt-2 text-gray-600">{tab.description}</p>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
