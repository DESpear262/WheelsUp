/**
 * Footer Component
 *
 * Footer for the WheelsUp flight school marketplace.
 * Contains copyright information and basic links.
 */

import Link from 'next/link';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gray-50 border-t border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand Section */}
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <div className="w-6 h-6 bg-blue-600 rounded-md flex items-center justify-center">
                <svg
                  className="w-4 h-4 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
              </div>
              <span className="text-lg font-bold text-gray-900">WheelsUp</span>
            </div>
            <p className="text-sm text-gray-600 max-w-xs">
              The flight school marketplace that puts students first. Compare schools, find training, and start your aviation journey.
            </p>
          </div>

          {/* Links Section */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
              Explore
            </h3>
            <div className="flex flex-col space-y-2">
              <Link
                href="/search"
                className="text-sm text-gray-600 hover:text-blue-600 transition-colors"
              >
                Search Schools
              </Link>
              <Link
                href="/about"
                className="text-sm text-gray-600 hover:text-blue-600 transition-colors"
              >
                About WheelsUp
              </Link>
            </div>
          </div>

          {/* Contact Section */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
              Contact
            </h3>
            <div className="flex flex-col space-y-2">
              <a
                href="mailto:hello@wheelsup.com"
                className="text-sm text-gray-600 hover:text-blue-600 transition-colors"
              >
                hello@wheelsup.com
              </a>
              <p className="text-sm text-gray-600">
                Questions about flight training?
              </p>
            </div>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="mt-8 pt-8 border-t border-gray-200">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
            <p className="text-sm text-gray-500">
              © {currentYear} WheelsUp. All rights reserved.
            </p>
            <div className="flex space-x-6">
              <a
                href="#"
                className="text-sm text-gray-500 hover:text-blue-600 transition-colors"
              >
                Privacy Policy
              </a>
              <a
                href="#"
                className="text-sm text-gray-500 hover:text-blue-600 transition-colors"
              >
                Terms of Service
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
