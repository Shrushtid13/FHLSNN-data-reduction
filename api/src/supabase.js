import { createClient } from '@supabase/supabase-js';
import { config } from './config.js';

/**
 * Creates a scoped Supabase client using the anon key and the user's Authorization header.
 * Postgres evaluates RLS policies based on the JWT in this header.
 * @param {string} authHeader - e.g. "Bearer <token>"
 */
export function getAnonDbClient(authHeader) {
  return createClient(config.SUPABASE_URL, config.SUPABASE_ANON_KEY, {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
    },
    global: {
      headers: {
        Authorization: authHeader,
      },
    },
  });
}

/**
 * Service-role Supabase client used strictly for storage bucket uploads
 * and backend administrative tasks. Never exposed to browser or client.
 */
let serviceRoleClientInstance = null;

export function getServiceRoleClient() {
  if (!serviceRoleClientInstance) {
    serviceRoleClientInstance = createClient(
      config.SUPABASE_URL,
      config.SUPABASE_SERVICE_ROLE_KEY,
      {
        auth: {
          persistSession: false,
          autoRefreshToken: false,
        },
      }
    );
  }
  return serviceRoleClientInstance;
}
