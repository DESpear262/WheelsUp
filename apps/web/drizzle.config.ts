import { defineConfig } from 'drizzle-kit';

export default defineConfig({
  schema: './drizzle/schema.ts',
  out: './drizzle/migrations',
  dialect: 'postgresql',
  dbCredentials: {
    url: process.env.DATABASE_URL || 'postgresql://postgres:12345678@wheelsup.c1uuigcm4bd1.us-east-2.rds.amazonaws.com:5432/wheelsup',
  },
  verbose: true,
  strict: true,
});
