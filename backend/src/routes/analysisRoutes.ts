import { Router } from 'express';
import { 
  startAnalysis, 
  approveAction, 
  getSessionById, 
  listSessions,
  deleteSession,
  deleteAllSessions
} from '../controllers/analysisController';

const router = Router();

router.post('/start', startAnalysis);
router.post('/approve', approveAction);
router.get('/sessions', listSessions);
router.get('/session/:id', getSessionById);
router.delete('/session/:id', deleteSession);
router.delete('/sessions', deleteAllSessions);

export default router;
