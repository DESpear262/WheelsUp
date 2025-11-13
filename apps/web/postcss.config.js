/**
 * PostCSS configuration
 *
 * Ensures Tailwind CSS directives (@tailwind, @apply) are processed during
 * build so utility classes are available at runtime.
 */
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};

