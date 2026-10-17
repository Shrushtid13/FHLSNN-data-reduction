import { describe, it, expect, vi, beforeEach } from 'vitest';
import request from 'supertest';

// In-memory mock DB and storage for testing
const mockDatasets = new Map();
const mockExperiments = new Map();

// Mock supabase module before importing app
vi.mock('../src/supabase.js', () => {
  return {
    getServiceRoleClient: () => ({
      auth: {
        getUser: async (token) => {
          if (token === 'user-a-token') {
            return { data: { user: { id: 'user-a-1111', email: 'user_a@test.com' } }, error: null };
          }
          if (token === 'user-b-token') {
            return { data: { user: { id: 'user-b-2222', email: 'user_b@test.com' } }, error: null };
          }
          return { data: { user: null }, error: { message: 'Invalid token' } };
        },
      },
      storage: {
        from: () => ({
          upload: async () => ({ data: { path: 'uploaded' }, error: null }),
        }),
      },
    }),
    getAnonDbClient: (authHeader) => {
      // Determine user from authHeader
      const token = authHeader?.replace('Bearer ', '');
      const userId = token === 'user-a-token' ? 'user-a-1111' : token === 'user-b-token' ? 'user-b-2222' : null;

      return {
        from: (table) => {
          if (table === 'datasets') {
            return {
              insert: (row) => ({
                select: () => ({
                  single: async () => {
                    const saved = { ...row, created_at: new Date().toISOString() };
                    mockDatasets.set(row.id, saved);
                    return { data: saved, error: null };
                  },
                }),
              }),
              select: () => ({
                order: () => {
                  const rows = Array.from(mockDatasets.values()).filter((d) => d.owner === userId);
                  return Promise.resolve({ data: rows, error: null });
                },
                eq: (col, val) => ({
                  single: async () => {
                    const row = mockDatasets.get(val);
                    // RLS: User can only select their own dataset
                    if (!row || row.owner !== userId) {
                      return { data: null, error: { message: 'Row not found' } };
                    }
                    return { data: row, error: null };
                  },
                }),
              }),
            };
          }

          if (table === 'experiments') {
            return {
              insert: (row) => ({
                select: () => ({
                  single: async () => {
                    const saved = { ...row, id: 'exp-' + Math.random().toString(36).substring(7), created_at: new Date().toISOString() };
                    mockExperiments.set(saved.id, saved);
                    return { data: saved, error: null };
                  },
                }),
              }),
              select: () => ({
                order: () => {
                  const rows = Array.from(mockExperiments.values()).filter(
                    (e) => e.owner === userId || e.source === 'benchmark'
                  );
                  return Promise.resolve({ data: rows, error: null });
                },
                eq: (col, val) => ({
                  single: async () => {
                    const row = mockExperiments.get(val);
                    if (!row || (row.owner !== userId && row.source !== 'benchmark')) {
                      return { data: null, error: { message: 'Row not found' } };
                    }
                    return { data: row, error: null };
                  },
                }),
              }),
            };
          }
        },
      };
    },
  };
});

// Import app after mocking
const { app } = await import('../src/app.js');

// Helper to create a valid CSV string with N rows and 2 classes
function makeValidCsv(rowCount = 25, featureCount = 3) {
  const header = ['target', ...Array.from({ length: featureCount }, (_, i) => `f${i + 1}`)].join(',');
  const lines = [header];
  for (let i = 0; i < rowCount; i++) {
    const cls = i % 2 === 0 ? 'classA' : 'classB';
    const features = Array.from({ length: featureCount }, () => (Math.random() * 10).toFixed(2));
    lines.push([cls, ...features].join(','));
  }
  return lines.join('\n');
}

describe('Express Platform API Test Suite', () => {
  beforeEach(() => {
    mockDatasets.clear();
    mockExperiments.clear();
  });

  // 1. No token -> 401
  it('rejects requests with no token with 401', async () => {
    const res = await request(app).get('/datasets');
    expect(res.status).toBe(401);
    expect(res.body.error).toBe('unauthorized');
  });

  // 1b. Invalid token -> 401
  it('rejects requests with invalid token with 401', async () => {
    const res = await request(app)
      .get('/datasets')
      .set('Authorization', 'Bearer invalid-token');
    expect(res.status).toBe(401);
    expect(res.body.error).toBe('unauthorized');
  });

  // 2. Wrong extension -> 415
  it('rejects uploads with wrong extension with 415', async () => {
    const res = await request(app)
      .post('/datasets')
      .set('Authorization', 'Bearer user-a-token')
      .field('name', 'Invalid File')
      .field('target_column', 'target')
      .attach('file', Buffer.from('a,b\n1,2'), 'data.txt');

    expect(res.status).toBe(415);
    expect(res.body.error).toBe('unsupported_media_type');
  });

  // 3. Oversize -> 413
  it('rejects uploads exceeding 10 MB with 413', async () => {
    // 10 MB + 1 KB buffer
    const largeBuffer = Buffer.alloc(10 * 1024 * 1024 + 1024, 65);
    const res = await request(app)
      .post('/datasets')
      .set('Authorization', 'Bearer user-a-token')
      .field('name', 'Big File')
      .field('target_column', 'target')
      .attach('file', largeBuffer, 'large.csv');

    expect(res.status).toBe(413);
    expect(res.body.error).toBe('payload_too_large');
  });

  // 4a. Too few rows (< 20) -> 422
  it('rejects CSV with fewer than 20 rows with 422', async () => {
    const csv = makeValidCsv(10); // only 10 rows
    const res = await request(app)
      .post('/datasets')
      .set('Authorization', 'Bearer user-a-token')
      .field('name', 'Too Few Rows')
      .field('target_column', 'target')
      .attach('file', Buffer.from(csv), 'too_few.csv');

    expect(res.status).toBe(422);
    expect(res.body.error).toBe('unprocessable_entity');
    expect(res.body.detail).toContain('between 20 and 50000');
  });

  // 4b. Too many rows (> 50000) -> 422
  it('rejects CSV with more than 50000 rows with 422', async () => {
    // Generate a CSV header + 50001 lines quickly
    const lines = ['target,f1,f2'];
    for (let i = 0; i < 50001; i++) {
      lines.push(`${i % 2 === 0 ? 'A' : 'B'},1.0,2.0`);
    }
    const csv = lines.join('\n');

    const res = await request(app)
      .post('/datasets')
      .set('Authorization', 'Bearer user-a-token')
      .field('name', 'Too Many Rows')
      .field('target_column', 'target')
      .attach('file', Buffer.from(csv), 'too_many.csv');

    expect(res.status).toBe(422);
    expect(res.body.error).toBe('unprocessable_entity');
    expect(res.body.detail).toContain('between 20 and 50000');
  });

  // 5. Missing target column -> 422
  it('rejects CSV when target column does not exist with 422', async () => {
    const csv = makeValidCsv(25);
    const res = await request(app)
      .post('/datasets')
      .set('Authorization', 'Bearer user-a-token')
      .field('name', 'Missing Target')
      .field('target_column', 'non_existent_column')
      .attach('file', Buffer.from(csv), 'data.csv');

    expect(res.status).toBe(422);
    expect(res.body.error).toBe('unprocessable_entity');
    expect(res.body.detail).toContain("Target column 'non_existent_column' does not exist");
  });

  // 6. Non-numeric feature column -> 422
  it('rejects non-numeric feature column with 422 and names the column', async () => {
    let csv = 'target,feature_one,feature_bad\n';
    for (let i = 0; i < 25; i++) {
      const badVal = i === 5 ? 'not_a_number' : '1.5';
      csv += `${i % 2 === 0 ? 'A' : 'B'},1.0,${badVal}\n`;
    }

    const res = await request(app)
      .post('/datasets')
      .set('Authorization', 'Bearer user-a-token')
      .field('name', 'Non-numeric column test')
      .field('target_column', 'target')
      .attach('file', Buffer.from(csv), 'bad_feature.csv');

    expect(res.status).toBe(422);
    expect(res.body.error).toBe('unprocessable_entity');
    expect(res.body.detail).toContain('feature_bad');
    expect(res.body.detail).toContain('non-numeric');
  });

  // 7. Valid upload -> 201 with correct metrics
  it('accepts valid CSV upload with 201 and computes correct metadata', async () => {
    const csv = makeValidCsv(30, 4);
    const res = await request(app)
      .post('/datasets')
      .set('Authorization', 'Bearer user-a-token')
      .field('name', 'Valid Dataset')
      .field('target_column', 'target')
      .attach('file', Buffer.from(csv), 'valid.csv');

    expect(res.status).toBe(201);
    expect(res.body.name).toBe('Valid Dataset');
    expect(res.body.n_rows).toBe(30);
    expect(res.body.n_features).toBe(4);
    expect(res.body.n_classes).toBe(2);
    expect(res.body.class_counts).toEqual({ classA: 15, classB: 15 });
  });

  // 8. RLS isolation: second user cannot read first user's dataset
  it('proves a second user cannot read the first user dataset', async () => {
    // User A uploads dataset
    const csv = makeValidCsv(25, 2);
    const uploadRes = await request(app)
      .post('/datasets')
      .set('Authorization', 'Bearer user-a-token')
      .field('name', 'User A Secret Dataset')
      .field('target_column', 'target')
      .attach('file', Buffer.from(csv), 'user_a.csv');

    expect(uploadRes.status).toBe(201);
    const datasetId = uploadRes.body.id;

    // User A can read it
    const readUserA = await request(app)
      .get(`/datasets/${datasetId}`)
      .set('Authorization', 'Bearer user-a-token');
    expect(readUserA.status).toBe(200);
    expect(readUserA.body.name).toBe('User A Secret Dataset');

    // User B attempts to read it -> 404 (Row Level Security blocked)
    const readUserB = await request(app)
      .get(`/datasets/${datasetId}`)
      .set('Authorization', 'Bearer user-b-token');
    expect(readUserB.status).toBe(404);
    expect(readUserB.body.error).toBe('not_found');
  });

  // 9. Stubs return 501 when authenticated, 401 when unauthenticated
  it('returns 501 not_implemented for authenticated AI/ML/profiler endpoints and 401 without auth', async () => {
    const unauth = await request(app).post('/profile');
    expect(unauth.status).toBe(401);

    const p1 = await request(app).post('/profile').set('Authorization', 'Bearer user-a-token');
    expect(p1.status).toBe(501);
    expect(p1.body).toEqual({ error: 'not_implemented' });

    const p2 = await request(app).post('/recommend').set('Authorization', 'Bearer user-a-token');
    expect(p2.status).toBe(501);
    expect(p2.body).toEqual({ error: 'not_implemented' });

    const p3 = await request(app).post('/explain').set('Authorization', 'Bearer user-a-token');
    expect(p3.status).toBe(501);
    expect(p3.body).toEqual({ error: 'not_implemented' });

    const p4 = await request(app).post('/agent/run').set('Authorization', 'Bearer user-a-token');
    expect(p4.status).toBe(501);
    expect(p4.body).toEqual({ error: 'not_implemented' });
  });

  // 10. POST /experiments validation
  it('validates experiment creation schema and rejects invalid methods', async () => {
    const res = await request(app)
      .post('/experiments')
      .set('Authorization', 'Bearer user-a-token')
      .send({
        dataset_id: '11111111-1111-1111-1111-111111111111',
        method: 'invalid_method',
      });

    expect(res.status).toBe(422);
    expect(res.body.error).toBe('validation_error');
  });
});
