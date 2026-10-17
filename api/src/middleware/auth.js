import { getAnonDbClient, getServiceRoleClient } from '../supabase.js';

// ── Security: Auth token length bounds to reject obviously malformed tokens early ──
const MIN_TOKEN_LENGTH = 8;
const MAX_TOKEN_LENGTH = 8192;

export async function authMiddleware(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({
      error: 'unauthorized',
      detail: 'Missing or malformed Authorization header',
    });
  }

  const token = authHeader.split(' ')[1];
  if (!token) {
    return res.status(401).json({
      error: 'unauthorized',
      detail: 'Missing bearer token',
    });
  }

  // Security: Reject tokens that are too short or too long before hitting Supabase
  if (token.length < MIN_TOKEN_LENGTH || token.length > MAX_TOKEN_LENGTH) {
    return res.status(401).json({
      error: 'unauthorized',
      detail: 'Invalid token format',
    });
  }

  try {
    const supabaseService = getServiceRoleClient();
    const { data, error } = await supabaseService.auth.getUser(token);

    if (error || !data || !data.user) {
      return res.status(401).json({
        error: 'unauthorized',
        // Security: Do NOT echo back the Supabase error message (could leak internal details)
        detail: 'Invalid or expired token',
      });
    }

    // Security: Verify the user object has the expected shape
    if (!data.user.id || typeof data.user.id !== 'string') {
      return res.status(401).json({
        error: 'unauthorized',
        detail: 'Invalid user identity',
      });
    }

    req.user = data.user;
    // Security: Do NOT store the raw token on req (minimize token exposure in memory)
    req.db = getAnonDbClient(authHeader);
    next();
  } catch (err) {
    // Security: Never leak internal error details to the client
    return res.status(401).json({
      error: 'unauthorized',
      detail: 'Authentication failed',
    });
  }
}
