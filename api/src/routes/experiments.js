import express from 'express';
import { z } from 'zod';
import { config } from '../config.js';

export const experimentsRouter = express.Router();

const createExperimentSchema = z.object({
  dataset_id: z.string().uuid({ message: 'dataset_id must be a valid UUID' }),
  method: z.enum(['unreduced', 'm1', 'm3', 'hybrid'], {
    errorMap: () => ({ message: "method must be one of 'unreduced', 'm1', 'm3', 'hybrid'" }),
  }),
  params: z
    .record(z.any())
    .refine((obj) => Object.keys(obj).length <= 50, {
      message: 'params object cannot exceed 50 keys',
    })
    .optional()
    .default({}),
  seed: z
    .number()
    .int()
    .min(0, { message: 'seed must be >= 0' })
    .max(2147483647, { message: 'seed must be <= 2147483647' })
    .optional()
    .default(42),
});

// POST /experiments
experimentsRouter.post('/', async (req, res) => {
  const parseResult = createExperimentSchema.safeParse(req.body);
  if (!parseResult.success) {
    return res.status(422).json({
      error: 'validation_error',
      detail: parseResult.error.errors.map((e) => `${e.path.join('.')}: ${e.message}`).join('; '),
    });
  }

  const { dataset_id, method, params, seed } = parseResult.data;

  try {
    // Insert into experiments table with status 'queued' (RLS enforces owner = auth.uid() and source = 'user')
    const { data: experiment, error: dbError } = await req.db
      .from('experiments')
      .insert({
        dataset_id,
        method,
        params,
        seed,
        status: 'queued',
        progress: 0,
        owner: req.user.id,
        source: 'user',
      })
      .select()
      .single();

    if (dbError) {
      console.error('Experiment insert error:', dbError);
      return res.status(422).json({
        error: 'database_error',
        detail: 'Failed to record experiment',
      });
    }

    // Call FastAPI POST /jobs with header X-Internal-Token
    try {
      const fastApiResponse = await fetch(`${config.FASTAPI_URL}/jobs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Internal-Token': config.INTERNAL_API_TOKEN,
        },
        body: JSON.stringify({ experiment_id: experiment.id }),
      });

      if (!fastApiResponse.ok) {
        console.warn(
          `FastAPI /jobs returned status ${fastApiResponse.status} for experiment ${experiment.id}`
        );
      }
    } catch (err) {
      console.warn(`Could not reach FastAPI at ${config.FASTAPI_URL}/jobs: ${err.message}`);
    }

    return res.status(201).json(experiment);
  } catch (err) {
    console.error('Unhandled experiment creation error:', err);
    return res.status(500).json({
      error: 'internal_error',
      detail: 'An unexpected error occurred while creating the experiment',
    });
  }
});

// GET /experiments (own rows + benchmark rows via RLS)
experimentsRouter.get('/', async (req, res) => {
  try {
    const { data, error } = await req.db
      .from('experiments')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) {
      console.error('Experiments fetch error:', error);
      return res.status(500).json({ error: 'database_error', detail: 'Failed to retrieve experiments' });
    }
    return res.json(data);
  } catch (err) {
    console.error('Unhandled experiments GET error:', err);
    return res.status(500).json({ error: 'internal_error', detail: 'An unexpected error occurred' });
  }
});

// GET /experiments/:id
experimentsRouter.get('/:id', async (req, res) => {
  const id = req.params.id;
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (!uuidRegex.test(id)) {
    return res.status(404).json({ error: 'not_found', detail: 'Experiment not found' });
  }

  try {
    const { data, error } = await req.db
      .from('experiments')
      .select('*')
      .eq('id', id)
      .single();

    if (error || !data) {
      return res.status(404).json({ error: 'not_found', detail: 'Experiment not found' });
    }
    return res.json(data);
  } catch (err) {
    console.error('Unhandled experiment GET by ID error:', err);
    return res.status(500).json({ error: 'internal_error', detail: 'An unexpected error occurred' });
  }
});
