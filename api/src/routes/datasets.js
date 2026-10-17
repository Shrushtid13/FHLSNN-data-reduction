import express from 'express';
import multer from 'multer';
import { parse } from 'csv-parse';
import crypto from 'crypto';
import { getServiceRoleClient } from '../supabase.js';

export const datasetsRouter = express.Router();

const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 10 * 1024 * 1024, // 10 MB limit
    files: 1,
  },
});

/**
 * Custom wrapper for multer upload to capture payload too large error as 413
 */
function uploadCsv(req, res, next) {
  upload.single('file')(req, res, (err) => {
    if (err) {
      if (err.code === 'LIMIT_FILE_SIZE') {
        return res.status(413).json({
          error: 'payload_too_large',
          detail: 'File size exceeds 10 MB limit',
        });
      }
      return res.status(400).json({
        error: 'bad_request',
        detail: 'File upload error',
      });
    }
    next();
  });
}

/**
 * Async helper to parse CSV buffer without blocking the event loop
 */
function parseCsvAsync(buffer) {
  return new Promise((resolve, reject) => {
    const csvContent = buffer.toString('utf-8');
    parse(
      csvContent,
      {
        columns: true,
        skip_empty_lines: true,
        trim: true,
        bom: true,
      },
      (err, records) => {
        if (err) return reject(err);
        resolve(records);
      }
    );
  });
}

/**
 * Security: Sanitize strings against CSV Formula Injection and limit length
 */
function sanitizeInputString(str, maxLength = 100) {
  if (!str || typeof str !== 'string') return '';
  let cleaned = str.trim().slice(0, maxLength);
  // Neutralize CSV formula injection characters (=, +, -, @, tab) if present at start
  if (/^[=+\-@\t\r]/.test(cleaned)) {
    cleaned = "'" + cleaned;
  }
  return cleaned;
}

// POST /datasets
datasetsRouter.post('/', uploadCsv, async (req, res) => {
  // 1. Extension .csv (else 415)
  if (!req.file || !req.file.originalname || !req.file.originalname.toLowerCase().endsWith('.csv')) {
    return res.status(415).json({
      error: 'unsupported_media_type',
      detail: 'File must have .csv extension',
    });
  }

  // 2. Size <= 10 MB (else 413)
  if (req.file.size > 10 * 1024 * 1024) {
    return res.status(413).json({
      error: 'payload_too_large',
      detail: 'File size exceeds 10 MB limit',
    });
  }

  // 3. Parseable with a header (else 422) - Async parsing prevents Event Loop Starvation
  let records = [];
  try {
    records = await parseCsvAsync(req.file.buffer);
  } catch (err) {
    return res.status(422).json({
      error: 'unprocessable_entity',
      detail: 'CSV cannot be parsed',
    });
  }

  if (!records || records.length === 0) {
    return res.status(422).json({
      error: 'unprocessable_entity',
      detail: 'CSV cannot be parsed or has no data rows',
    });
  }

  const headers = Object.keys(records[0]);
  if (headers.length === 0) {
    return res.status(422).json({
      error: 'unprocessable_entity',
      detail: 'CSV has no header row',
    });
  }

  // 4. Rows between 20 and 50000 (else 422)
  if (records.length < 20 || records.length > 50000) {
    return res.status(422).json({
      error: 'unprocessable_entity',
      detail: `Row count must be between 20 and 50000, got ${records.length}`,
    });
  }

  // Security: Sanitize target_column and name
  const target_column = sanitizeInputString(req.body.target_column);

  // 5. Features <= 200 (else 422)
  const numFeatures = headers.includes(target_column) ? headers.length - 1 : headers.length;
  if (numFeatures > 200) {
    return res.status(422).json({
      error: 'unprocessable_entity',
      detail: `Number of features (${numFeatures}) exceeds maximum limit of 200`,
    });
  }

  // 6. Target_column exists (else 422)
  if (!target_column || !headers.includes(target_column)) {
    return res.status(422).json({
      error: 'unprocessable_entity',
      detail: `Target column '${target_column}' does not exist in CSV`,
    });
  }

  const featureCols = headers.filter((h) => h !== target_column);

  // 7. Every feature column numeric (mixed attributes are out of scope; reject with the column name)
  for (const col of featureCols) {
    for (let i = 0; i < records.length; i++) {
      const val = records[i][col];
      if (val === '' || val === null || val === undefined || isNaN(Number(val))) {
        return res.status(422).json({
          error: 'unprocessable_entity',
          detail: `Feature column '${col}' contains non-numeric values at row ${i + 1}`,
        });
      }
    }
  }

  // 8. No missing values (else 422)
  for (let i = 0; i < records.length; i++) {
    const targetVal = records[i][target_column];
    if (targetVal === '' || targetVal === null || targetVal === undefined) {
      return res.status(422).json({
        error: 'unprocessable_entity',
        detail: `Missing value found in target column at row ${i + 1}`,
      });
    }
  }

  // 9. At least 2 classes (else 422)
  const class_counts = {};
  for (const row of records) {
    const cls = String(row[target_column]).trim();
    class_counts[cls] = (class_counts[cls] || 0) + 1;
  }

  const n_classes = Object.keys(class_counts).length;
  if (n_classes < 2) {
    return res.status(422).json({
      error: 'unprocessable_entity',
      detail: `Target column must have at least 2 distinct classes, found ${n_classes}`,
    });
  }

  const n_rows = records.length;
  const n_features = featureCols.length;
  const dataset_id = crypto.randomUUID();
  const storage_path = `${req.user.id}/${dataset_id}.csv`;
  const name = sanitizeInputString(req.body.name || req.file.originalname);

  try {
    // Upload to Supabase Storage (datasets bucket) via service role
    const serviceClient = getServiceRoleClient();
    const { error: storageError } = await serviceClient.storage
      .from('datasets')
      .upload(storage_path, req.file.buffer, {
        contentType: 'text/csv',
        upsert: true,
      });

    if (storageError) {
      console.error('Storage upload error:', storageError);
      return res.status(500).json({
        error: 'storage_error',
        detail: 'Failed to upload dataset to storage',
      });
    }

    // Insert row into datasets table via scoped user client (RLS applies)
    const { data, error: dbError } = await req.db
      .from('datasets')
      .insert({
        id: dataset_id,
        owner: req.user.id,
        name,
        storage_path,
        target_column,
        n_rows,
        n_features,
        n_classes,
        class_counts,
      })
      .select()
      .single();

    if (dbError) {
      console.error('Database insert error:', dbError);
      return res.status(500).json({
        error: 'database_error',
        detail: 'Failed to save dataset record',
      });
    }

    return res.status(201).json(data);
  } catch (err) {
    console.error('Unhandled upload error:', err);
    return res.status(500).json({
      error: 'internal_error',
      detail: 'An error occurred during dataset processing',
    });
  }
});

// GET /datasets (own only via RLS)
datasetsRouter.get('/', async (req, res) => {
  try {
    const { data, error } = await req.db
      .from('datasets')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) {
      console.error('Datasets fetch error:', error);
      return res.status(500).json({ error: 'database_error', detail: 'Failed to retrieve datasets' });
    }
    return res.json(data);
  } catch (err) {
    console.error('Unhandled datasets GET error:', err);
    return res.status(500).json({ error: 'internal_error', detail: 'An unexpected error occurred' });
  }
});

// GET /datasets/:id (own only via RLS)
datasetsRouter.get('/:id', async (req, res) => {
  // Validate UUID format
  const id = req.params.id;
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (!uuidRegex.test(id)) {
    return res.status(404).json({ error: 'not_found', detail: 'Dataset not found' });
  }

  try {
    const { data, error } = await req.db
      .from('datasets')
      .select('*')
      .eq('id', id)
      .single();

    if (error || !data) {
      return res.status(404).json({ error: 'not_found', detail: 'Dataset not found' });
    }
    return res.json(data);
  } catch (err) {
    console.error('Unhandled dataset GET by ID error:', err);
    return res.status(500).json({ error: 'internal_error', detail: 'An unexpected error occurred' });
  }
});
