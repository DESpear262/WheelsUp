# WheelsUp Web Application Dockerfile
# Multi-stage build for optimized production image

# =============================================================================
# Build Stage
# =============================================================================
FROM node:22-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    libc6-compat \
    python3 \
    make \
    g++

# Set working directory
WORKDIR /app

# Copy package files for dependency installation
COPY package*.json ./

# Install all dependencies (including dev dependencies for build)
RUN npm ci --only=production=false && npm cache clean --force

# Copy source code
COPY . .

# Build the application
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# =============================================================================
# Runtime Stage
# =============================================================================
FROM node:22-alpine AS runtime

# Install only runtime dependencies
RUN apk add --no-cache \
    libc6-compat \
    curl

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Set working directory
WORKDIR /app

# Copy built application from builder stage
COPY --from=builder --chown=nextjs:nodejs /app/package*.json ./
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules

# Install only production dependencies
RUN npm ci --only=production && npm cache clean --force

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Set environment variables
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

# Start the application
CMD ["npm", "start"]
