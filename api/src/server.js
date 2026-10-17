import { app } from './app.js';
import { config } from './config.js';

app.listen(config.PORT, () => {
  console.log(`Express API server running on port ${config.PORT}`);
});
