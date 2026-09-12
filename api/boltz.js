'use strict';

const {
  authenticate,
  downloadArtifact,
  estimatePrediction,
  getApiKey,
  getPrediction,
  keyMode,
  startPrediction,
} = require('../lib/boltz-client');

const ALLOWED_ENTITY_TYPES = new Set(['protein', 'dna', 'rna', 'ligand_ccd', 'ligand_smiles']);
const MAX_BODY_BYTES = 250_000;

function json(res, status, payload) {
  res.statusCode = status;
  res.setHeader('content-type', 'application/json; charset=utf-8');
  res.setHeader('cache-control', 'no-store, max-age=0');
  res.end(JSON.stringify(payload));
}

async function readBody(req) {
  if (req.body && typeof req.body === 'object' && !Buffer.isBuffer(req.body)) return req.body;
  if (typeof req.body === 'string') {
    if (Buffer.byteLength(req.body) > MAX_BODY_BYTES) throw Object.assign(new Error('Request body is too large.'), { statusCode: 413 });
    return req.body ? JSON.parse(req.body) : {};
  }

  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > MAX_BODY_BYTES) throw Object.assign(new Error('Request body is too large.'), { statusCode: 413 });
    chunks.push(chunk);
  }
  const text = Buffer.concat(chunks).toString('utf8');
  return text ? JSON.parse(text) : {};
}

function requestError(message) {
  return Object.assign(new Error(message), { statusCode: 400 });
}

function validateProteinMsa(entity, index) {
  if (entity.type !== 'protein' || entity.msa == null) return { custom: false };
  const msa = entity.msa;
  if (!msa || typeof msa !== 'object') throw requestError(`Entity ${index + 1} has an invalid MSA configuration.`);
  if (msa.type === 'empty') return { custom: false };
  if (msa.type !== 'custom') throw requestError(`Entity ${index + 1} MSA type must be custom or empty.`);
  if (!['a3m', 'csv'].includes(msa.format)) throw requestError(`Entity ${index + 1} custom MSA format must be a3m or csv.`);
  const url = msa.source?.url;
  if (typeof url !== 'string' || !/^https:\/\//i.test(url)) throw requestError(`Entity ${index + 1} custom MSA must use an HTTPS source URL.`);
  return { custom: true };
}

function validateModelOptions(options) {
  if (options == null) return;
  if (!options || typeof options !== 'object' || Array.isArray(options)) throw requestError('model_options must be an object.');
  const recycling = Number(options.recycling_steps ?? 3);
  const sampling = Number(options.sampling_steps ?? 200);
  const scale = Number(options.step_scale ?? 1.638);
  if (!Number.isInteger(recycling) || recycling < 1) throw requestError('recycling_steps must be an integer of at least 1.');
  if (!Number.isInteger(sampling) || sampling < 50) throw requestError('sampling_steps must be an integer of at least 50.');
  if (!Number.isFinite(scale) || scale < 1.3 || scale > 2) throw requestError('step_scale must be between 1.3 and 2.0.');
}

function validateRequest(request) {
  if (!request || typeof request !== 'object') throw requestError('Prediction request is missing.');
  if (request.model !== 'boltz-2.1') throw requestError('Only model boltz-2.1 is allowed by this UI.');
  const input = request.input;
  if (!input || typeof input !== 'object') throw requestError('Prediction input is missing.');
  if (!Array.isArray(input.entities) || input.entities.length < 1 || input.entities.length > 12) {
    throw requestError('Prediction must contain between 1 and 12 entities.');
  }

  const chainIds = new Set();
  const chainTypes = new Map();
  let hasCustomMsa = false;
  let hasAutomaticMsa = false;

  for (const [i, entity] of input.entities.entries()) {
    if (!entity || !ALLOWED_ENTITY_TYPES.has(entity.type)) throw requestError(`Entity ${i + 1} has an unsupported type.`);
    if (typeof entity.value !== 'string' || entity.value.length < 1 || entity.value.length > 50_000) throw requestError(`Entity ${i + 1} has an invalid value.`);
    if (!Array.isArray(entity.chain_ids) || entity.chain_ids.length < 1 || entity.chain_ids.length > 12) throw requestError(`Entity ${i + 1} has invalid chain IDs.`);
    for (const rawId of entity.chain_ids) {
      const id = String(rawId);
      if (!/^[A-Za-z0-9]{1,4}$/.test(id)) throw requestError(`Invalid chain ID: ${id}`);
      if (chainIds.has(id)) throw requestError(`Duplicate chain ID: ${id}`);
      chainIds.add(id);
      chainTypes.set(id, entity.type);
    }
    if (entity.type === 'protein') {
      const { custom } = validateProteinMsa(entity, i);
      if (custom) hasCustomMsa = true;
      else if (entity.msa == null) hasAutomaticMsa = true;
    }
  }

  if (hasCustomMsa && hasAutomaticMsa) throw requestError('Custom MSA and automatic MSA cannot be mixed in the same Boltz request.');

  const samples = Number(input.num_samples ?? 1);
  if (!Number.isInteger(samples) || samples < 1 || samples > 10) throw requestError('num_samples must be an integer from 1 to 10.');
  validateModelOptions(input.model_options);
  validateTemplates(input.templates, chainIds);
  validateConstraints(input.constraints, chainIds);

  if (input.binding) {
    const type = input.binding.type;
    if (!['ligand_protein_binding', 'protein_protein_binding'].includes(type)) throw requestError('Unsupported binding metric type.');
    if (type === 'ligand_protein_binding') {
      const id = String(input.binding.binder_chain_id || '');
      if (!id || !chainIds.has(id)) throw requestError('Ligand–protein binding requires an explicit valid binder_chain_id.');
      if (!String(chainTypes.get(id) || '').startsWith('ligand')) throw requestError('Ligand–protein binder_chain_id must refer to a ligand chain.');
      if (input.entities.some(e => !['protein', 'ligand_ccd', 'ligand_smiles'].includes(e.type))) throw requestError('Boltz ligand–protein binding metrics support protein + ligand entities only.');
    }
    if (type === 'protein_protein_binding') {
      const ids = input.binding.binder_chain_ids;
      if (!Array.isArray(ids) || !ids.length) throw requestError('Protein–protein binding requires at least one explicit binder_chain_id.');
      for (const rawId of ids) {
        const id = String(rawId);
        if (!chainIds.has(id) || chainTypes.get(id) !== 'protein') throw requestError(`Protein–protein binder chain ${id} is not a valid protein chain.`);
      }
    }
  }
  return request;
}


function validateTemplates(templates, chainIds) {
  if (templates == null) return;
  if (!Array.isArray(templates) || templates.length > 4) throw requestError('templates must be an array with at most 4 items.');
  templates.forEach((template, index) => {
    if (!template || typeof template !== 'object') throw requestError(`Template ${index + 1} is invalid.`);
    const url = template.template_structure?.url;
    if (typeof url !== 'string' || !/^https:\/\//i.test(url)) throw requestError(`Template ${index + 1} must use an HTTPS PDB/mmCIF source URL.`);
    if (!Array.isArray(template.template_chains) || !template.template_chains.length) throw requestError(`Template ${index + 1} requires explicit chain mappings.`);
    const seenInput = new Set(), seenTemplate = new Set();
    for (const mapping of template.template_chains) {
      const inputId = String(mapping?.input_chain_id || ''), templateId = String(mapping?.template_chain_id || '');
      if (!chainIds.has(inputId)) throw requestError(`Template ${index + 1} input chain ${inputId} is not present in the prediction.`);
      if (!/^[A-Za-z0-9]{1,4}$/.test(templateId)) throw requestError(`Template ${index + 1} has an invalid template chain ID.`);
      if (seenInput.has(inputId) || seenTemplate.has(templateId)) throw requestError(`Template ${index + 1} chain mappings must be unique.`);
      seenInput.add(inputId); seenTemplate.add(templateId);
    }
    if (template.force_threshold_angstroms != null) {
      const v = Number(template.force_threshold_angstroms);
      if (!Number.isFinite(v) || v <= 0 || v > 100) throw requestError(`Template ${index + 1} force_threshold_angstroms must be >0 and <=100.`);
    }
  });
}

function validateConstraintToken(token, chainIds, label) {
  if (!token || typeof token !== 'object') throw requestError(`${label} is missing.`);
  const chain = String(token.chain_id || '');
  if (!chainIds.has(chain)) throw requestError(`${label} chain ${chain || '(blank)'} is not present in the prediction.`);
  if (token.type === 'polymer_contact') {
    if (!Number.isInteger(Number(token.residue_index)) || Number(token.residue_index) < 0) throw requestError(`${label} residue_index must be a 0-based non-negative integer.`);
    return;
  }
  if (token.type === 'ligand_contact') {
    const atom = String(token.atom_name || '');
    if (!/^[A-Za-z0-9]{1,4}$/.test(atom)) throw requestError(`${label} ligand atom_name must be 1-4 alphanumeric characters.`);
    return;
  }
  throw requestError(`${label} type must be polymer_contact or ligand_contact.`);
}

function validateConstraints(constraints, chainIds) {
  if (constraints == null) return;
  if (!Array.isArray(constraints) || constraints.length > 16) throw requestError('constraints must be an array with at most 16 items.');
  constraints.forEach((constraint, index) => {
    if (!constraint || typeof constraint !== 'object') throw requestError(`Constraint ${index + 1} is invalid.`);
    const maxDistance = Number(constraint.max_distance_angstrom);
    if (!Number.isFinite(maxDistance) || maxDistance <= 0 || maxDistance > 50) throw requestError(`Constraint ${index + 1} max_distance_angstrom must be >0 and <=50.`);
    if (constraint.type === 'contact') {
      validateConstraintToken(constraint.token1, chainIds, `Constraint ${index + 1} token1`);
      validateConstraintToken(constraint.token2, chainIds, `Constraint ${index + 1} token2`);
      return;
    }
    if (constraint.type === 'pocket') {
      const binder = String(constraint.binder_chain_id || '');
      if (!chainIds.has(binder)) throw requestError(`Constraint ${index + 1} binder_chain_id is invalid.`);
      const residues = constraint.contact_residues;
      if (!residues || typeof residues !== 'object' || Array.isArray(residues) || !Object.keys(residues).length) throw requestError(`Constraint ${index + 1} pocket requires contact_residues.`);
      for (const [chain, values] of Object.entries(residues)) {
        if (!chainIds.has(chain)) throw requestError(`Constraint ${index + 1} pocket chain ${chain} is not present in the prediction.`);
        if (!Array.isArray(values) || !values.length || values.some(v => !Number.isInteger(Number(v)) || Number(v) < 0)) throw requestError(`Constraint ${index + 1} pocket residue indices must be a non-empty 0-based integer array.`);
      }
      return;
    }
    throw requestError(`Constraint ${index + 1} type must be contact or pocket.`);
  });
}

function costLimit() {
  const raw = process.env.NILUS_MAX_COST_USD;
  if (raw == null || raw === '') return 0.50;
  const value = Number(raw);
  return Number.isFinite(value) && value >= 0 ? value : 0.50;
}

async function enforceLiveCostLimit(request) {
  if (keyMode(getApiKey()) !== 'live') return null;
  const limit = costLimit();
  if (limit <= 0) return null;
  const estimate = await estimatePrediction(request);
  const estimated = Number(estimate?.estimated_cost_usd);
  if (Number.isFinite(estimated) && estimated > limit) {
    const err = new Error(`Estimated cost $${estimated.toFixed(4)} exceeds server limit $${limit.toFixed(2)}. Increase NILUS_MAX_COST_USD only if you intend to allow this run.`);
    err.statusCode = 402;
    throw err;
  }
  return estimate;
}

function detectStructureFormat(text, url = '') {
  const lower = String(url).toLowerCase();
  if (lower.includes('.pdb')) return 'pdb';
  if (lower.includes('.cif') || lower.includes('.mmcif')) return 'cif';
  const head = text.slice(0, 5000);
  if (/^(ATOM  |HETATM|HEADER|MODEL )/m.test(head)) return 'pdb';
  return 'cif';
}

function structureUrl(sample) {
  return sample?.structure?.url || '';
}

function sampleMetricSignature(sample) {
  const m = sample?.metrics || {};
  const keys = ['structure_confidence', 'complex_plddt', 'ptm', 'iptm', 'complex_iplddt', 'complex_ipde', 'complex_pde', 'ligand_iptm', 'protein_iptm'];
  return keys.map(key => {
    const value = Number(m[key]);
    return Number.isFinite(value) ? value.toPrecision(12) : '';
  }).join('|');
}

function resolveSample(prediction, requestedIndex) {
  const all = Array.isArray(prediction?.output?.all_sample_results) ? prediction.output.all_sample_results : [];
  const best = prediction?.output?.best_sample || null;
  const bestUrl = structureUrl(best);
  let bestIndex = bestUrl ? all.findIndex(s => structureUrl(s) === bestUrl) : -1;
  // Presigned artifact URLs are normally identical between best_sample and the
  // corresponding item in all_sample_results. If an upstream response rewrites
  // the URL, fall back to the complete metric tuple instead of guessing by rank.
  if (bestIndex < 0 && best) {
    const signature = sampleMetricSignature(best);
    if (signature.replace(/\|/g, '')) bestIndex = all.findIndex(s => sampleMetricSignature(s) === signature);
  }

  if (requestedIndex !== undefined && requestedIndex !== null && requestedIndex !== '') {
    const index = Number(requestedIndex);
    if (!Number.isInteger(index) || index < 0 || index >= all.length) throw requestError(`sampleIndex must be between 0 and ${Math.max(0, all.length - 1)}.`);
    return { sample: all[index], sampleIndex: index, bestIndex, isBest: index === bestIndex };
  }
  return { sample: best, sampleIndex: bestIndex >= 0 ? bestIndex : null, bestIndex, isBest: true };
}

module.exports = async function handler(req, res) {
  if (req.method !== 'POST') return json(res, 405, { error: 'Use POST /api/boltz.' });

  try {
    const body = await readBody(req);
    const action = String(body?.action || '');

    if (action === 'health') {
      const key = getApiKey();
      await authenticate();
      return json(res, 200, { configured: true, authenticated: true, mode: keyMode(key) });
    }

    if (action === 'estimate') {
      const request = validateRequest(body.request);
      return json(res, 200, await estimatePrediction(request));
    }

    if (action === 'submit') {
      const request = validateRequest(body.request);
      await enforceLiveCostLimit(request);
      return json(res, 200, await startPrediction(request));
    }

    if (action === 'status') return json(res, 200, await getPrediction(body.id));

    if (action === 'structure') {
      const prediction = await getPrediction(body.id);
      if (prediction.status !== 'succeeded') return json(res, 409, { error: `Prediction status is ${prediction.status || 'unknown'}.` });
      const resolved = resolveSample(prediction, body.sampleIndex);
      const artifact = resolved.sample?.structure;
      if (!artifact?.url) return json(res, 404, { error: 'Boltz result does not expose a structure URL for the requested sample.' });
      const downloaded = await downloadArtifact(artifact.url, { maxBytes: 35 * 1024 * 1024 });
      const structure = downloaded.buffer.toString('utf8');
      return json(res, 200, {
        result: prediction,
        structure,
        format: detectStructureFormat(structure, artifact.url),
        metrics: resolved.sample?.metrics || null,
        sample_index: resolved.sampleIndex,
        best_sample_index: resolved.bestIndex >= 0 ? resolved.bestIndex : null,
        is_best_sample: resolved.isBest,
      });
    }

    return json(res, 400, { error: 'Unknown Boltz action.' });
  } catch (error) {
    const status = Number(error?.statusCode) || 500;
    const payload = { error: error?.message || 'Unexpected server error.' };
    if (error?.details && status < 500) payload.details = error.details;
    return json(res, status, payload);
  }
};
