import { pruneArmors } from '../lib/solver/prune';
import { runSolver } from '../lib/solver/search';
import { SolverRequest } from '../lib/solver/types';

self.addEventListener('message', (e: MessageEvent<SolverRequest>) => {
  try {
    const request = e.data;
    
    // Phase 1: Prune
    const pruned = pruneArmors(request);

    // Phase 2 & 3 & 4: Search, Decorate, Score
    const results = runSolver(request, pruned, (progress) => {
      self.postMessage({ type: 'progress', progress });
    });

    self.postMessage({ type: 'done', results });
  } catch (error: any) {
    self.postMessage({ type: 'error', error: error.message });
  }
});
