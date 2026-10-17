import express from 'express';

export const stubsRouter = express.Router();

const notImplementedHandler = (req, res) => {
  return res.status(501).json({ error: 'not_implemented' });
};

stubsRouter.post('/profile', notImplementedHandler);
stubsRouter.post('/recommend', notImplementedHandler);
stubsRouter.post('/explain', notImplementedHandler);
stubsRouter.post('/agent/run', notImplementedHandler);
