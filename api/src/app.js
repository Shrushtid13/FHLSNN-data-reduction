import express from 'express';
import cors from 'cors';
import { config } from './config.js';
import { authMiddleware } from './middleware/auth.js';
import { datasetsRouter } from './routes/datasets.js';
import { experimentsRouter } from './routes/experiments.js';
import { stubsRouter } from './routes/stubs.js';

export const app = express();

// ── Security: Disable X-Powered-By header (prevents server fingerprinting) ──
app.disable('x-powered-by');

// ── Security: HTTP security headers middleware ──
app.use((req, res, next) => {
  // Prevent MIME type sniffing
  res.setHeader('X-Content-Type-Options', 'nosniff');
  // Prevent clickjacking by disallowing iframe embedding
  res.setHeader('X-Frame-Options', 'DENY');
  // Enable browser XSS filter
  res.setHeader('X-XSS-Protection', '1; mode=block');
  // Strict referrer policy to prevent URL leakage
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  // Content Security Policy to prevent XSS and data injection
  res.setHeader(
    'Content-Security-Policy',
    "default-src 'none'; frame-ancestors 'none'"
  );
  // Prevent browsers from caching sensitive API responses
  res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate');
  res.setHeader('Pragma', 'no-cache');
  // Strict Transport Security (for when served over HTTPS)
  res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
  next();
});

// ── Security: CORS restricted to WEB_ORIGIN only ──
app.use(
  cors({
    origin: config.WEB_ORIGIN,
    credentials: true,
    methods: ['GET', 'POST', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
    maxAge: 600, // Preflight cache: 10 minutes
  })
);

// ── Security: Limit JSON body size to prevent payload abuse ──
app.use(express.json({ limit: '1mb' }));

// ── Security: Simple in-memory rate limiter ──
const rateLimitStore = new Map();
const RATE_LIMIT_WINDOW_MS = 60 * 1000; // 1 minute
const RATE_LIMIT_MAX_REQUESTS = 60;      // 60 requests per minute per IP

function rateLimiter(req, res, next) {
  const ip = req.ip || req.connection.remoteAddress || 'unknown';
  const now = Date.now();

  if (!rateLimitStore.has(ip)) {
    rateLimitStore.set(ip, { count: 1, windowStart: now });
    return next();
  }

  const entry = rateLimitStore.get(ip);
  if (now - entry.windowStart > RATE_LIMIT_WINDOW_MS) {
    // Reset window
    entry.count = 1;
    entry.windowStart = now;
    return next();
  }

  entry.count++;
  if (entry.count > RATE_LIMIT_MAX_REQUESTS) {
    return res.status(429).json({
      error: 'too_many_requests',
      detail: 'Rate limit exceeded. Please try again later.',
    });
  }
  next();
}

app.use(rateLimiter);

// Periodically clean up expired rate limit entries (every 5 minutes)
setInterval(() => {
  const now = Date.now();
  for (const [ip, entry] of rateLimitStore.entries()) {
    if (now - entry.windowStart > RATE_LIMIT_WINDOW_MS * 2) {
      rateLimitStore.delete(ip);
    }
  }
}, 5 * 60 * 1000);

// Health check endpoint (unauthenticated, but rate-limited)
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// AI / ML stubs returning HTTP 501 (authenticated to prevent reconnaissance)
app.use('/', authMiddleware, stubsRouter);

// Authenticated routes
app.use('/datasets', authMiddleware, datasetsRouter);
app.use('/experiments', authMiddleware, experimentsRouter);

// 404 handler (do NOT echo back the URL to prevent reflected XSS in logs)
app.use((req, res) => {
  res.status(404).json({
    error: 'not_found',
    detail: 'The requested resource was not found',
  });
});

// Centralized error handler (never leak stack traces or internal details)
app.use((err, req, res, next) => {
  // Log internally for debugging but never send stack traces to clients
  if (process.env.NODE_ENV !== 'test') {
    console.error('Unhandled error:', err.message);
  }
  const status = err.status || 500;
  res.status(status).json({
    error: status === 500 ? 'server_error' : (err.error || 'error'),
    detail: status === 500 ? 'An unexpected error occurred' : (err.message || 'An error occurred'),
  });
});
