import { defineConfig } from 'drizzle-kit';

export default defineConfig({
  schema: './drizzle/schema.ts',
  out: './drizzle/migrations',
  dialect: 'postgresql',
  dbCredentials: {
    url:
      process.env.DATABASE_URL ??
      'postgresql://wheelsup_user:wheelsup_password@localhost:5432/wheelsup_dev',
  },
  verbose: true,
  strict: true,
});
