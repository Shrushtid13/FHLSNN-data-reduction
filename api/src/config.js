import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

// Load .env from api or workspace root
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config({ path: path.resolve(__dirname, '../../.env') });
dotenv.config();

const isProduction = process.env.NODE_ENV === 'production';

// In production, enforce that critical secrets are explicitly provided and not default placeholders
if (isProduction) {
  if (!process.env.INTERNAL_API_TOKEN || process.env.INTERNAL_API_TOKEN === 'placeholder-internal-token') {
    throw new Error('FATAL SECURITY ERROR: INTERNAL_API_TOKEN must be securely set in production.');
  }
  if (!process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY === 'placeholder-service-role-key') {
    throw new Error('FATAL SECURITY ERROR: SUPABASE_SERVICE_ROLE_KEY must be securely set in production.');
  }
}

export const config = {
  PORT: process.env.PORT ? parseInt(process.env.PORT, 10) : 4000,
  WEB_ORIGIN: process.env.WEB_ORIGIN || 'http://localhost:5173',
  SUPABASE_URL: process.env.SUPABASE_URL || 'https://placeholder.supabase.co',
  SUPABASE_ANON_KEY: process.env.SUPABASE_ANON_KEY || 'placeholder-anon-key',
  SUPABASE_SERVICE_ROLE_KEY: process.env.SUPABASE_SERVICE_ROLE_KEY || 'placeholder-service-role-key',
  FASTAPI_URL: process.env.FASTAPI_URL || 'http://localhost:8000',
  INTERNAL_API_TOKEN: process.env.INTERNAL_API_TOKEN || 'placeholder-internal-token',
};
