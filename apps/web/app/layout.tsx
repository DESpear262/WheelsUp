/**
 * Root Layout Component
 *
 * Main layout wrapper for the WheelsUp application.
 * Includes navigation, footer, React Query provider, and global metadata configuration.
 */

import React from 'react';
import type { Metadata } from 'next';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import NavBar from '@/components/NavBar';
import Footer from '@/components/Footer';
import './globals.css';

export const metadata: Metadata = {
  title: 'WheelsUp - Find Your Flight School',
  description: 'Compare flight schools nationwide. Transparent pricing, verified reviews, and complete training program information.',
  keywords: ['flight school', 'pilot training', 'aviation', 'flight instruction', 'compare schools'],
  authors: [{ name: 'WheelsUp Team' }],
  viewport: 'width=device-width, initial-scale=1',
  robots: 'index, follow',
  icons: {
    icon: '/favicon.svg',
  },
};

// Create a client component for React Query setup
function QueryProvider({ children }: { children: React.ReactNode }) {
  // Create QueryClient instance
  const [queryClient] = React.useState(
    () => new QueryClient({
      defaultOptions: {
        queries: {
          staleTime: 5 * 60 * 1000, // 5 minutes
          gcTime: 10 * 60 * 1000, // 10 minutes
          retry: (failureCount, error) => {
            // Don't retry on 4xx errors
            if (error instanceof Error && error.message.includes('Invalid')) {
              return false;
            }
            return failureCount < 3;
          },
        },
      },
    })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-white">
        <QueryProvider>
          <div className="flex flex-col min-h-screen">
            <NavBar />
            <main className="flex-1">
              {children}
            </main>
            <Footer />
          </div>
        </QueryProvider>
      </body>
    </html>
  );
}
