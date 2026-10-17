import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  // Read root .env safely
  const env = loadEnv(mode, '../', ['VITE_', 'SUPABASE_']);
  const supabaseUrl = env.VITE_SUPABASE_URL || env.SUPABASE_URL || 'https://placeholder.supabase.co';
  const supabaseAnonKey = env.VITE_SUPABASE_ANON_KEY || env.SUPABASE_ANON_KEY || 'placeholder-anon-key';

  return {
    plugins: [react()],
    // SECURITY: Strictly restrict envPrefix to VITE_ so SUPABASE_SERVICE_ROLE_KEY is never bundled into client
    envPrefix: ['VITE_'],
    define: {
      'import.meta.env.VITE_SUPABASE_URL': JSON.stringify(supabaseUrl),
      'import.meta.env.VITE_SUPABASE_ANON_KEY': JSON.stringify(supabaseAnonKey),
    },
    server: {
      port: 5173,
      host: true,
    },
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: './src/setupTests.js',
    },
  };
});
