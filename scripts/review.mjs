import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { setTimeout } from 'node:timers/promises';
import { prepareReview, readReview, acknowledgeReview } from './review-store.mjs';

export async function waitForSubmission(root, kind, id, seconds = 45) {
  if (!Number.isFinite(seconds) || seconds < 0 || seconds > 45) throw Error('Wait must be between 0 and 45 seconds.');
  const deadline = Date.now() + seconds * 1000;
  do {
    const state = readReview(root, kind, id);
    const event = state.submissions.find(s => s.status === 'pending' && (s.action==='feedback'||s.requestId === state.request.id));
    if (event) return { status: 'submitted', stale: state.stale, request: state.request, submission: event };
    if (state.stale) return { status: 'review_changed', request: state.request, message: 'The plan, scene composition or actual frames changed. Publish a fresh review.' };
    if (Date.now() >= deadline) break;
    await setTimeout(Math.min(500, deadline - Date.now()));
  } while (Date.now() <= deadline);
  return { status: 'no_submission', kind, project: id };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const { values, positionals } = parseArgs({ allowPositionals: true, options: {
      kind: { type: 'string' }, id: { type: 'string' }, stage: { type: 'string', default: 'plan' },
      document: { type: 'string' }, event: { type: 'string' }, message: { type: 'string' },
      seconds: { type: 'string', default: '45' }, port: { type: 'string', default: process.env.DASHBOARD_PORT || '4173' },
    } });
    const root = fileURLToPath(new URL('../', import.meta.url)), { kind, id } = values;
    let result;
    if (positionals[0] === 'prepare') {
      const state = prepareReview(root, { kind, id, stage: values.stage, document: values.document || null });
      result = { ...state.request, url: `http://127.0.0.1:${values.port}/review/${kind}/${id}` };
    } else if (positionals[0] === 'status') result = readReview(root, kind, id);
    else if (positionals[0] === 'wait') result = await waitForSubmission(root, kind, id, Number(values.seconds));
    else if (positionals[0] === 'ack') result = acknowledgeReview(root, kind, id, values.event, values.message);
    else throw Error('Use prepare, status, wait, or ack with --kind and --id.');
    console.log(JSON.stringify(result, null, 2));
  } catch (error) { console.error(JSON.stringify({ error: error.message })); process.exitCode = 1; }
}
