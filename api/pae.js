'use strict';

const { downloadArtifact, getPrediction } = require('../lib/boltz-client');
const { downsample, extractPaeFromArchive } = require('../lib/pae-parser');

function json(res, status, payload) {
  res.statusCode = status;
  res.setHeader('content-type', 'application/json; charset=utf-8');
  res.setHeader('cache-control', 'no-store, max-age=0');
  res.end(JSON.stringify(payload));
}

module.exports = async function handler(req, res) {
  if (req.method !== 'GET') return json(res, 405, { error: 'Use GET /api/pae?id=<prediction-id>&sample=<index>.' });
  try {
    const id = Array.isArray(req.query?.id) ? req.query.id[0] : req.query?.id;
    if (!id) return json(res, 400, { error: 'Prediction ID is required.' });
    const sampleRaw = Array.isArray(req.query?.sample) ? req.query.sample[0] : req.query?.sample;
    const sampleIndex = sampleRaw === undefined || sampleRaw === null || sampleRaw === '' ? null : Number(sampleRaw);
    if (sampleIndex !== null && (!Number.isInteger(sampleIndex) || sampleIndex < 0 || sampleIndex > 9)) return json(res, 400, { error: 'sample must be an integer from 0 to 9.' });

    const prediction = await getPrediction(id);
    if (prediction.status !== 'succeeded') return json(res, 200, { available: false, reason: `Prediction status is ${prediction.status || 'unknown'}.` });
    const archive = prediction?.output?.archive;
    if (!archive?.url) return json(res, 200, { available: false, reason: 'Boltz did not expose a result archive for this prediction.' });

    const { buffer } = await downloadArtifact(archive.url, { maxBytes: 120 * 1024 * 1024, timeoutMs: 60_000 });
    const pae = await extractPaeFromArchive(buffer, { sampleIndex });
    if (!pae) return json(res, 200, { available: false, reason: sampleIndex == null ? 'No explicitly labelled PAE array was found in the Boltz archive.' : `No explicitly labelled PAE array was found for sample ${sampleIndex}.` });

    let actualMax = 0;
    for (const value of pae.values) if (Number.isFinite(Number(value))) actualMax = Math.max(actualMax, Number(value));
    const display = downsample(pae.values, pae.rows, pae.cols, 220);
    return json(res, 200, {
      available: true,
      sample_index: sampleIndex,
      original_shape: [pae.rows, pae.cols],
      display_shape: [display.rows, display.cols],
      values: display.values,
      max: 32,
      actual_max: Number(actualMax.toFixed(4)),
      source: pae.archive_member || pae.source || 'Boltz archive',
    });
  } catch (error) {
    const status = Number(error?.statusCode) || 500;
    return json(res, status, { error: error?.message || 'Unable to load PAE.' });
  }
};
