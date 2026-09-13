'use strict';

function json(res, status, payload) {
  res.statusCode = status;
  res.setHeader('content-type', 'application/json; charset=utf-8');
  res.setHeader('cache-control', 'public, max-age=300, s-maxage=3600');
  res.end(JSON.stringify(payload));
}

module.exports = async function handler(req, res) {
  if (req.method !== 'GET') return json(res, 405, { error: 'Use GET /api/alphafold?accession=<UniProt-accession>.' });
  const accession = String(Array.isArray(req.query?.accession) ? req.query.accession[0] : req.query?.accession || '').trim().toUpperCase();
  if (!/^[A-Z0-9][A-Z0-9-]{4,19}$/.test(accession)) return json(res, 400, { error: 'A valid UniProt accession is required.' });

  try {
    const url = `https://alphafold.ebi.ac.uk/api/prediction/${encodeURIComponent(accession)}`;
    const response = await fetch(url, { headers: { accept: 'application/json', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 NilusLab/3.2' }, signal: AbortSignal.timeout(15_000) });
    if (response.status === 404) return json(res, 404, { error: 'No AlphaFold DB prediction was found for this accession.' });
    if (!response.ok) return json(res, 502, { error: `AlphaFold DB API returned ${response.status}.` });
    const entries = await response.json();
    if (!Array.isArray(entries) || !entries.length) return json(res, 404, { error: 'AlphaFold DB returned no prediction records.' });
    const entry = entries.find(x => String(x?.uniprotAccession || '').toUpperCase() === accession) || entries[0];
    return json(res, 200, {
      accession: entry.uniprotAccession || accession,
      entry_id: entry.entryId || entry.modelEntityId || null,
      tool: entry.toolUsed || null,
      version: entry.latestVersion ?? null,
      model_created_at: entry.modelCreatedDate || null,
      sequence: entry.sequence || entry.uniprotSequence || null,
      mean_plddt: Number.isFinite(Number(entry.globalMetricValue)) ? Number(entry.globalMetricValue) : null,
      fractions: {
        very_low: Number.isFinite(Number(entry.fractionPlddtVeryLow)) ? Number(entry.fractionPlddtVeryLow) : null,
        low: Number.isFinite(Number(entry.fractionPlddtLow)) ? Number(entry.fractionPlddtLow) : null,
        confident: Number.isFinite(Number(entry.fractionPlddtConfident)) ? Number(entry.fractionPlddtConfident) : null,
        very_high: Number.isFinite(Number(entry.fractionPlddtVeryHigh)) ? Number(entry.fractionPlddtVeryHigh) : null,
      },
      pdb_url: entry.pdbUrl || null,
      cif_url: entry.cifUrl || null,
      pae_url: entry.paeDocUrl || null,
      msa_url: entry.msaUrl || null,
      source_url: entry.entryId ? `https://alphafold.ebi.ac.uk/entry/${encodeURIComponent(entry.entryId)}` : null,
      license_note: 'AlphaFold DB data are provided by EMBL-EBI/Google DeepMind; retain source attribution when reusing data.',
    });
  } catch (error) {
    return json(res, 502, { error: `Unable to reach AlphaFold DB: ${error?.message || error}` });
  }
};
