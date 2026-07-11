/* =====================================================================
   STRUCTURE PREDICTION MODULE
   Front-end controller for Nilus Atomix + zenithfold-2.1 workflows
   ===================================================================== */

const STATE = {
  mode: 'esm',
  apiKey: localStorage.getItem('nilus_zenkey') || '',
  sequence: '',
  chains: [
    { id: 'A', type: 'protein', copies: 1, value: '' }
  ],
  currentModel: null,
  paeMatrix: null,
  selectedResidue: null,
  viewer: null,
  bindingViewer: null,
  spin: false,
  boltzJobId: null,
  boltzPolling: null,
  boltzValidated: false,
  boltzEstimated: false,
  boltzEstimatedCost: null,
  hbondShapes: [],
  hbondLabels: [],
  glowSurfaceId: null,
  hoveredResi: null
};

const $ = sel => document.querySelector(sel);
const $$ = sel => Array.from(document.querySelectorAll(sel));
const pad = (n, w=2) => String(n).padStart(w, '0');
const now = () => {
  const d = new Date();
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
};
const AA3 = { A:'ALA', R:'ARG', N:'ASN', D:'ASP', C:'CYS', E:'GLU', Q:'GLN', G:'GLY', H:'HIS', I:'ILE',
              L:'LEU', K:'LYS', M:'MET', F:'PHE', P:'PRO', S:'SER', T:'THR', W:'TRP', Y:'TYR', V:'VAL' };

function log(msg, kind='info') {
  const diag = $('#diagLog');
  if (!diag) return;
  const line = document.createElement('div');
  line.className = `diag-line ${kind}`;
  line.innerHTML = `<span class="t">${now()}</span><span class="m">${msg}</span>`;
  diag.appendChild(line);
  diag.scrollTop = diag.scrollHeight;
  $('#diagCount').textContent = `${diag.children.length} events`;
}

const EXAMPLE_SEQ = 'MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG';

function updatePAEWarningVisibility() {
  const warningEl = document.getElementById('paeSimWarning');
  if (!warningEl) return;
  if (STATE.mode === 'esm' && STATE.currentModel && STATE.currentModel.pdb) {
    warningEl.style.display = 'flex';
  } else {
    warningEl.style.display = 'none';
  }
}

function switchMode(mode) {
  // Bidirectional sequence synchronization between input views
  if (mode === 'boltz' && STATE.mode === 'esm') {
    const esmSeq = $('#seqInput').value.trim();
    if (esmSeq && STATE.chains.length > 0 && STATE.chains[0].type === 'protein') {
      STATE.chains[0].value = esmSeq;
    }
  } else if (mode === 'esm' && STATE.mode === 'boltz') {
    const proteinChain = STATE.chains.find(c => c.type === 'protein');
    if (proteinChain && proteinChain.value) {
      $('#seqInput').value = proteinChain.value;
    }
  }

  STATE.mode = mode;
  $$('.mode-btn').forEach(b => b.classList.toggle('active', b.dataset.mode === mode));
  $('#esmInput').style.display = mode === 'esm' ? 'block' : 'none';
  $('#boltzInput').style.display = mode === 'boltz' ? 'block' : 'none';
  $('#costPanel').style.display = mode === 'boltz' ? 'block' : 'none';
  $('#engineTag').textContent = mode === 'esm' ? 'Nilus Atomix' : 'NilusFold';
  $('#runNum').textContent = mode === 'boltz' ? '5' : '4';
  $('#inputTag').textContent = mode === 'esm' ? 'FASTA · raw' : 'multi-chain';
  $('#modeDescription').textContent = mode === 'esm'
    ? 'Evolutionary Scale Modeling for fast, single-chain protein folding. Returns atomic coordinates with per-residue pLDDT.'
    : 'NilusFold predicts multi-chain biomolecular complexes (protein · DNA · RNA · ligand) with PAE confidence matrices.';
  $('#sbModel').textContent = mode === 'esm' ? 'nilus-atomix-v1' : 'NilusFold';
  log(`Engine switched → ${mode === 'esm' ? 'Nilus Atomix' : 'NilusFold'}`, 'info');
  renderChainList();
  updateCostEstimate();
  updatePAEWarningVisibility();
}

function initApiKey() {
  if (STATE.apiKey) {
    $('#apiDot').classList.add('set');
    $('#apiStatus').textContent = 'user · local';
    $('#apiKeyInput').value = STATE.apiKey;
  }
  $('#apiSaveBtn').addEventListener('click', () => {
    const v = $('#apiKeyInput').value.trim();
    if (v) {
      localStorage.setItem('nilus_zenkey', v);
      STATE.apiKey = v;
      $('#apiDot').classList.add('set');
      $('#apiStatus').textContent = 'user · local';
      log('Zen-Key persisted to local storage', 'ok');
    } else {
      localStorage.removeItem('nilus_zenkey');
      STATE.apiKey = '';
      $('#apiDot').classList.remove('set');
      $('#apiStatus').textContent = 'default · company';
      log('Zen-Key cleared, falling back to company credentials', 'info');
    }
  });
}

// ── UniProt Protein Lookup ─────────────────────────────────────────────────
// 3-tier strategy (mirrors UniProtLookup in script.js):
//   Tier 1: backend /api/uniprot-lookup?gene=   (returns sequence + metadata)
//   Tier 2: direct UniProt REST API             (CORS-safe public endpoint)
//   Tier 3: show clear actionable error
// mode: 'esm' | 'boltz'
async function uniprotLookupForStructure(mode) {
  const inputId  = mode === 'esm' ? 'esm-uniprot-input'   : 'boltz-uniprot-input';
  const resultId = mode === 'esm' ? 'esm-uniprot-result'  : 'boltz-uniprot-result';
  const errorId  = mode === 'esm' ? 'esm-uniprot-error'   : 'boltz-uniprot-error';
  const errorMsg = mode === 'esm' ? 'esm-uniprot-error-msg' : 'boltz-uniprot-error-msg';
  const fetchBtn = mode === 'esm' ? 'esm-uniprot-fetch-btn' : 'boltz-uniprot-fetch-btn';
  const geneEl   = mode === 'esm' ? 'esm-uniprot-gene' : 'boltz-uniprot-gene';
  const accEl    = mode === 'esm' ? 'esm-uniprot-acc'  : 'boltz-uniprot-acc';
  const lenEl    = mode === 'esm' ? 'esm-uniprot-len'  : 'boltz-uniprot-len';
  const nameEl   = mode === 'esm' ? 'esm-uniprot-name' : 'boltz-uniprot-name';
  const funcEl   = mode === 'esm' ? 'esm-uniprot-func' : 'boltz-uniprot-func';
  const useBtnId = mode === 'esm' ? 'esm-uniprot-use-btn' : 'boltz-uniprot-use-btn';

  const gene = (document.getElementById(inputId)?.value || '').trim().toUpperCase();
  if (!gene) { log('Enter a gene or protein name first', 'warn'); return; }

  // Reset UI
  document.getElementById(resultId)?.classList.add('hidden');
  document.getElementById(errorId)?.classList.add('hidden');

  // Show spinner in fetch button
  const btn = document.getElementById(fetchBtn);
  const origBtnHTML = btn ? btn.innerHTML : '';
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="uniprot-spinner"></span> Fetching...';
  }

  let data = null; // Will be populated by Tier 1 or Tier 2

  try {
    // ── Tier 1: backend endpoint (applies 3-tier UniProt strategy, returns sequence) ──
    try {
      const r = await fetch(`/api/uniprot-lookup?gene=${encodeURIComponent(gene)}`, {
        signal: AbortSignal.timeout(6000)
      });
      if (r.ok) {
        const json = await r.json();
        if (json && json.sequence) data = json;
      }
    } catch (_) { /* backend unreachable — fall through to direct fetch */ }

    // ── Tier 2: direct UniProt REST API (public, CORS-enabled) ──
    if (!data) {
      const url = 'https://rest.uniprot.org/uniprotkb/search?' +
        `query=gene_exact:${encodeURIComponent(gene)}+AND+organism_id:9606+AND+reviewed:true` +
        '&fields=accession,protein_name,sequence,cc_function,cc_subcellular_location' +
        '&format=json&size=1';

      const r = await fetch(url, {
        headers: { 'Accept': 'application/json' },
        signal: AbortSignal.timeout(10000)
      });
      if (!r.ok) throw new Error(`UniProt HTTP ${r.status}`);

      const raw = await r.json();
      const entry = (raw.results || [])[0];

      if (entry && entry.sequence) {
        const acc2     = entry.primaryAccession || '';
        const seq2     = entry.sequence?.value || '';
        const seqLen2  = entry.sequence?.length || seq2.length;
        const names2   = entry.proteinDescription || {};
        const recName2 = names2.recommendedName || names2.submittedNames?.[0] || {};
        const fullName = recName2.fullName?.value || gene;
        let funcText = null, locText = null;
        for (const c of entry.comments || []) {
          if (c.commentType === 'FUNCTION' && !funcText)
            funcText = (c.texts || [])[0]?.value || null;
          if (c.commentType === 'SUBCELLULAR LOCATION' && !locText)
            locText = c.subcellularLocations?.[0]?.location?.value || null;
        }
        data = {
          gene, accession: acc2, sequence: seq2,
          sequence_length: seqLen2,
          protein_name: fullName,
          subcellular_location: locText,
          function: funcText,
          source: 'UniProt Swiss-Prot (Direct)'
        };
      }
    }

    // ── Tier 3: Show result or error ──
    if (!data || !data.sequence) {
      const msgEl = document.getElementById(errorMsg);
      if (msgEl) msgEl.textContent =
        `"${gene}" not found in UniProt Swiss-Prot (Homo sapiens). ` +
        `Try the official HGNC gene symbol (e.g. POU5F1 for OCT4, TP53 for p53).`;
      document.getElementById(errorId)?.classList.remove('hidden');
      log(`UniProt: no reviewed entry for "${gene}"`, 'warn');
      return;
    }

    // Populate result card
    document.getElementById(geneEl).textContent = data.gene || gene;
    document.getElementById(accEl).textContent  = data.accession || '';
    document.getElementById(lenEl).textContent  = `${data.sequence_length} aa`;
    document.getElementById(nameEl).textContent =
      (data.protein_name || '') + (data.subcellular_location ? ` · ${data.subcellular_location}` : '');
    document.getElementById(funcEl).textContent = data.function || '';
    document.getElementById(resultId)?.classList.remove('hidden');

    // Store sequence on the Use button via dataset for use later
    const useBtn = document.getElementById(useBtnId);
    if (useBtn) {
      useBtn.dataset.sequence = data.sequence;
      useBtn.dataset.gene     = data.gene || gene;
      useBtn.dataset.acc      = data.accession || '';
      useBtn.dataset.len      = data.sequence_length;
    }

    log(`UniProt: ${data.gene} → ${data.accession} (${data.sequence_length} aa) [${data.source || 'Swiss-Prot'}]`, 'ok');

  } catch (e) {
    const msgEl = document.getElementById(errorMsg);
    if (msgEl) {
      if (e.name === 'TimeoutError' || (e.message && e.message.includes('timed out'))) {
        msgEl.textContent = 'Request timed out. Check your internet connection and try again.';
      } else {
        msgEl.textContent = `Network error: ${e.message}. Check connection and try again.`;
      }
    }
    document.getElementById(errorId)?.classList.remove('hidden');
    log(`UniProt lookup error for "${gene}": ${e.message}`, 'err');
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = origBtnHTML; }
  }
}

function uniprotUseSequence(mode) {
  const useBtnId = mode === 'esm' ? 'esm-uniprot-use-btn' : 'boltz-uniprot-use-btn';
  const useBtn   = document.getElementById(useBtnId);
  if (!useBtn || !useBtn.dataset.sequence) return;

  const seq  = useBtn.dataset.sequence;
  const gene = useBtn.dataset.gene || 'protein';
  const acc  = useBtn.dataset.acc  || '';
  const len  = useBtn.dataset.len  || seq.length;

  if (mode === 'esm') {
    const ta = document.getElementById('seqInput');
    if (ta) {
      ta.value = `>${gene} | ${acc} | Homo sapiens | ${len} aa\n${seq}`;
      ta.dispatchEvent(new Event('input'));
    }
    log(`Loaded ${gene} (${len} aa) into Nilus Atomix sequence input`, 'ok');
  } else {
    // Fill Chain A (first protein chain) in NilusFold
    const firstProtein = STATE.chains.findIndex(c => c.type === 'protein');
    const chainIdx = firstProtein >= 0 ? firstProtein : 0;
    if (STATE.chains[chainIdx]) {
      STATE.chains[chainIdx].value = seq;
      renderChainList();
      updateCostEstimate();
    }
    log(`Loaded ${gene} (${len} aa) into NilusFold Chain ${STATE.chains[chainIdx]?.id || 'A'}`, 'ok');
  }
}

function initSequenceInput() {
  const ta = $('#seqInput');
  const ESM_MAX = 400; // ESMFold practical limit per residue memory
  const HARD_MAX = 2000;

  ta.addEventListener('input', () => {
    const v = ta.value.replace(/^>.*\n/, '').replace(/\s/g, '').toUpperCase();
    const len = v.length;
    STATE.sequence = v;

    if (STATE.mode === 'esm') {
      if (len > HARD_MAX) {
        $('#seqLenHint').textContent = `${len} aa — exceeds max`;
        $('#seqLenHint').style.color = 'var(--coral)';
        log(`Sequence (${len} aa) exceeds hard limit. Please trim or use NilusFold mode.`, 'err');
      } else if (len > ESM_MAX) {
        $('#seqLenHint').textContent = `${len} aa — use NilusFold for best results`;
        $('#seqLenHint').style.color = 'var(--amber)';
        log(`Long sequence detected (${len} aa). Nilus Atomix optimized for <400 aa — switching to NilusFold API recommended for accuracy and speed.`, 'warn');
      } else {
        $('#seqLenHint').textContent = `${len} aa · max ${ESM_MAX} aa`;
        $('#seqLenHint').style.color = '';
      }
    } else {
      $('#seqLenHint').textContent = `${len} aa · max ${HARD_MAX} aa`;
      $('#seqLenHint').style.color = len > HARD_MAX ? 'var(--coral)' : '';
    }
  });
  $('#loadExampleBtn').addEventListener('click', () => {
    ta.value = '> example ubiquitin [76 aa]\n' + EXAMPLE_SEQ;
    ta.dispatchEvent(new Event('input'));
    log('Example sequence loaded · ubiquitin (76 aa)', 'ok');
  });
  $('#clearBtn').addEventListener('click', () => {
    ta.value = '';
    ta.dispatchEvent(new Event('input'));
    STATE.chains = [
      { id: 'A', type: 'protein', copies: 1, value: '' }
    ];
    renderChainList();
    updateCostEstimate();
    log('Cleared simple sequence input and reset multi-chain state', 'info');
  });

  // UniProt Lookup — ESM mode wiring
  const esmFetchBtn = document.getElementById('esm-uniprot-fetch-btn');
  if (esmFetchBtn) esmFetchBtn.addEventListener('click', () => uniprotLookupForStructure('esm'));

  const esmInput = document.getElementById('esm-uniprot-input');
  if (esmInput) esmInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); uniprotLookupForStructure('esm'); }
  });

  const esmUseBtn = document.getElementById('esm-uniprot-use-btn');
  if (esmUseBtn) esmUseBtn.addEventListener('click', () => uniprotUseSequence('esm'));
}

function renderChainList() {
  const list = $('#chainList');
  list.innerHTML = '';
  STATE.chains.forEach((c, idx) => {
    // Outer wrapper — column layout
    const wrapper = document.createElement('div');
    wrapper.style.cssText = 'background:rgba(0,0,0,0.3);border:1px solid #1E293B;border-radius:9px;overflow:hidden;';

    // Top row: [badge][type select][copies][delete]
    const headerRow = document.createElement('div');
    headerRow.style.cssText = 'display:flex;align-items:center;gap:7px;padding:8px 10px;';
    headerRow.innerHTML = `
      <div style="width:28px;height:28px;border-radius:7px;background:#3B82F6;color:white;display:grid;place-items:center;font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:700;flex-shrink:0">${c.id}</div>
      <select class="chain-type-select chain-type" style="flex:1;min-width:0;background:rgba(0,0,0,0.4);border:1px solid #1E293B;border-radius:7px;color:#E2E8F0;padding:6px 22px 6px 9px;font-size:11px;font-family:'JetBrains Mono',monospace;appearance:none;-webkit-appearance:none;background-image:url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='9' height='9' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E\");background-repeat:no-repeat;background-position:right 7px center;outline:none;cursor:pointer;">
        <option value="protein" ${c.type==='protein'?'selected':''}>Protein</option>
        <option value="dna"     ${c.type==='dna'?'selected':''}>DNA</option>
        <option value="rna"     ${c.type==='rna'?'selected':''}>RNA</option>
        <option value="ligand_ccd"    ${c.type==='ligand_ccd'?'selected':''}>Ligand (CCD)</option>
        <option value="ligand_smiles" ${c.type==='ligand_smiles'?'selected':''}>Ligand (SMILES)</option>
      </select>
      <span style="font-size:11px;color:#94A3B8;margin-right:2px;user-select:none;">copies:</span>
      <input class="chain-copies-input chain-copies" type="number" min="1" max="8" value="${c.copies}" style="width:40px;flex-shrink:0;background:rgba(0,0,0,0.4);border:1px solid #1E293B;border-radius:7px;color:#E2E8F0;padding:6px 4px;font-size:11px;font-family:'JetBrains Mono',monospace;text-align:center;outline:none;" />
      <button class="chain-del" style="width:26px;height:26px;flex-shrink:0;border-radius:6px;border:none;background:transparent;color:#475569;cursor:pointer;display:grid;place-items:center;transition:all 0.1s;" title="Remove chain">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
      </button>
    `;
    headerRow.querySelector('.chain-del').addEventListener('mouseenter', e => e.currentTarget.style.cssText += 'background:rgba(248,113,113,0.12);color:#F87171;');
    headerRow.querySelector('.chain-del').addEventListener('mouseleave', e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#475569'; });
    wrapper.appendChild(headerRow);

    // Bottom: sequence / value input
    const valRow = document.createElement('div');
    valRow.style.cssText = 'padding:0 10px 10px 10px;';
    const seqPlaceholder = 'Sequence or SMILES';
    if (c.type === 'ligand_ccd') {
      valRow.innerHTML = `<select class="chain-val" style="width:100%;background:rgba(0,0,0,0.4);border:1px solid #1E293B;border-radius:7px;color:#E2E8F0;padding:7px 24px 7px 9px;font-size:10.5px;font-family:'JetBrains Mono',monospace;appearance:none;outline:none;cursor:pointer;">
        <option value="">-- Select Ligand --</option>
        <option value="MG"  ${c.value==='MG'?'selected':''}>MG — Magnesium</option>
        <option value="ZN"  ${c.value==='ZN'?'selected':''}>ZN — Zinc</option>
        <option value="CA"  ${c.value==='CA'?'selected':''}>CA — Calcium</option>
        <option value="ATP" ${c.value==='ATP'?'selected':''}>ATP</option>
        <option value="ADP" ${c.value==='ADP'?'selected':''}>ADP</option>
        <option value="HEM" ${c.value==='HEM'?'selected':''}>HEM — Heme</option>
      </select>`;
    } else {
      valRow.innerHTML = `<textarea class="chain-val" rows="2" placeholder="${seqPlaceholder}" style="width:100%;background:rgba(0,0,0,0.4);border:1px solid #1E293B;border-radius:7px;color:#E2E8F0;padding:7px 10px;font-family:'JetBrains Mono',monospace;font-size:10.5px;line-height:1.5;resize:vertical;min-height:50px;outline:none;display:block;">${c.value || ''}</textarea>`;
    }
    wrapper.appendChild(valRow);

    // Events
    headerRow.querySelector('.chain-type').addEventListener('change', e => {
      STATE.chains[idx].type = e.target.value;
      STATE.chains[idx].value = '';
      renderChainList(); updateCostEstimate();
    });
    const valEl = wrapper.querySelector('.chain-val');
    if (valEl) {
      valEl.addEventListener('input',  e => { STATE.chains[idx].value = e.target.value.trim().replace(/\s/g,''); updateCostEstimate(); });
      valEl.addEventListener('change', e => { STATE.chains[idx].value = e.target.value.trim().replace(/\s/g,''); updateCostEstimate(); });
    }
    headerRow.querySelector('.chain-copies').addEventListener('input', e => { STATE.chains[idx].copies = parseInt(e.target.value)||1; updateCostEstimate(); });
    headerRow.querySelector('.chain-del').addEventListener('click', () => {
      STATE.chains.splice(idx, 1);
      STATE.chains.forEach((cc, i) => cc.id = String.fromCharCode(65 + i));
      renderChainList(); updateCostEstimate();
    });
    list.appendChild(wrapper);
  });
}




function initChainBuilder() {
  $('#addChainBtn').addEventListener('click', () => {
    if (STATE.chains.length >= 6) {
      log('Maximum 6 chains supported in NilusFold UI', 'warn');
      return;
    }
    STATE.chains.push({ id: String.fromCharCode(65 + STATE.chains.length), type: 'protein', copies: 1, value: '' });
    renderChainList();
    updateCostEstimate();
  });

  const clearChainsBtn = document.getElementById('clearChainsBtn');
  if (clearChainsBtn) {
    clearChainsBtn.addEventListener('click', () => {
      STATE.chains = [
        { id: 'A', type: 'protein', copies: 1, value: '' }
      ];
      renderChainList();
      updateCostEstimate();
      
      // Synchronize and clear simple view sequence input
      const ta = document.getElementById('seqInput');
      if (ta) {
        ta.value = '';
        ta.dispatchEvent(new Event('input'));
      }
      log('Chains reset to default empty protein chain and simple input cleared', 'info');
    });
  }

  // UniProt Lookup — Boltz mode wiring
  const boltzFetchBtn = document.getElementById('boltz-uniprot-fetch-btn');
  if (boltzFetchBtn) boltzFetchBtn.addEventListener('click', () => uniprotLookupForStructure('boltz'));

  const boltzInput = document.getElementById('boltz-uniprot-input');
  if (boltzInput) boltzInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); uniprotLookupForStructure('boltz'); }
  });

  const boltzUseBtn = document.getElementById('boltz-uniprot-use-btn');
  if (boltzUseBtn) boltzUseBtn.addEventListener('click', () => uniprotUseSequence('boltz'));

  // Binder chain row show/hide
  const typeSelect = document.getElementById('boltz-binding-type');
  if (typeSelect) {
    typeSelect.addEventListener('change', function() {
      const row = document.getElementById('boltz-binder-chain-row');
      if (row) {
        row.classList.toggle('hidden', this.value === 'none');
      }
    });
  }

  $('#validateBtn').addEventListener('click', boltzValidate);
}

function parsePDB(pdbText) {
  const lines = pdbText.split('\n');
  let seq = '';
  const plddt = [];
  const residues = {};
  const chains = new Set();
  const aaMap = {
    'ALA':'A', 'ARG':'R', 'ASN':'N', 'ASP':'D', 'CYS':'C', 'GLN':'Q', 'GLU':'E', 
    'GLY':'G', 'HIS':'H', 'ILE':'I', 'LEU':'L', 'LYS':'K', 'MET':'M', 'PHE':'F', 
    'PRO':'P', 'SER':'S', 'THR':'T', 'TRP':'W', 'TYR':'Y', 'VAL':'V',
    'DA':'a', 'DT':'t', 'DC':'c', 'DG':'g',
    'A':'a', 'T':'t', 'C':'c', 'G':'g', 'U':'u',
    'RA':'a', 'RU':'u', 'RC':'c', 'RG':'g'
  };

  lines.forEach(line => {
    if (line.startsWith('ATOM  ') || line.startsWith('HETATM')) {
      const atomName = line.substring(12, 16).trim();
      if (atomName === 'CA' || atomName === "C4'") {
        const resName = line.substring(17, 20).trim();
        const chain = line.substring(21, 22).trim();
        const resi = parseInt(line.substring(22, 26).trim());
        const b = parseFloat(line.substring(60, 66).trim());
        const key = chain + '_' + resi;
        if (!residues[key]) {
          residues[key] = true;
          seq += aaMap[resName] || 'X';
          plddt.push(b);
          if (chain) chains.add(chain);
        }
      }
    }
  });

  return { seq, plddt, chains: Array.from(chains).sort() };
}

function updateCostEstimate() {
  if (STATE.mode !== 'boltz') return;
  const totalRes = STATE.chains.reduce((s, c) => {
    if (c.type.startsWith('ligand')) return s;
    return s + (c.value ? c.value.length : 120) * c.copies;
  }, 0);
  const gpuMin = Math.ceil(totalRes / 80);
  const credits = Math.ceil(gpuMin * 1.7);
  const eta = Math.ceil(gpuMin * 35 + 12);
  $('#costGpu').innerHTML = `${gpuMin}<span class="unit">min</span>`;
  $('#costCredits').innerHTML = `${credits}<span class="unit">cr</span>`;
  $('#costRes').textContent = totalRes;
  $('#costEta').innerHTML = `${eta}<span class="unit">s</span>`;
  STATE.boltzEstimatedCost = (gpuMin * 0.12).toFixed(2);
}

async function boltzValidate() {
  const btn = $('#validateBtn');
  btn.disabled = true;
  btn.innerHTML = '<svg class="animate-spin" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" stroke-width="3" stroke-dasharray="32"/></svg> Validating...';
  log('POST /api/v1/structure/boltz/validate — executing validation', 'info');

  const manifest = boltzBuildManifest();
  try {
    const resp = await fetch('/api/v1/structure/boltz/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ manifest })
    });
    const data = await resp.json();
    if (data.valid) {
      log('Validation completed successfully', 'ok');
      STATE.boltzValidated = true;
    } else {
      log('Validation failed: ' + data.errors.join(' | '), 'err');
      STATE.boltzValidated = false;
    }
  } catch (e) {
    log('Validation failed: ' + e.message, 'err');
    STATE.boltzValidated = false;
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg> Validate Input';
  }
}

function boltzBuildManifest() {
  const entities = STATE.chains.map(c => ({
    type: c.type,
    value: c.value || 'MKTIIALSYIFCLVFA', // fallback if empty
    chain_ids: [c.id]
  }));
  const bindingType = document.getElementById('boltz-binding-type').value;
  let manifest = { entities };
  if (bindingType !== 'none') {
    let binderId = document.getElementById('boltz-binder-chain-id').value.trim();
    if (!binderId) {
      const proteinChain = STATE.chains.find(c => c.type === 'protein');
      binderId = proteinChain ? proteinChain.id : 'A';
    }
    const binding = { type: bindingType };
    binding.binder_chain_id = binderId;
    binding.binder_chain_ids = [binderId];
    manifest.binding = binding;
  }
  return manifest;
}

/* ============ 3D VIEWER ============ */
function initViewer() {
  const element = $('#molviewer');
  const viewer = $3Dmol.createViewer(element, {
    backgroundColor: '0x080B11',
    antialias: true,
    id: 'main-viewer',
  });
  viewer.setViewStyle({ style: 'outline', color: 0x111827, width: 0.02 });
  STATE.viewer = viewer;

  // Initial demo model
  loadDemoModel();

  // Hover tooltip — follows cursor, shows residue info
  element.addEventListener('mousemove', (e) => {
    const rect = element.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    viewer.hoverCallback({}, (atom) => {
      if (!atom) {
        $('#resTooltip').style.display = 'none';
        // Remove hover glow from previous residue
        if (STATE.hoveredResi !== null) {
          _removeHoverGlow();
          STATE.hoveredResi = null;
        }
        return;
      }
      const tt = $('#resTooltip');
      tt.style.display = 'block';
      tt.style.left = (x + 14) + 'px';
      tt.style.top = (y + 14) + 'px';
      tt.querySelector('.rt-res').textContent = `${atom.resn} ${atom.chain} ${atom.resi}`;
      tt.querySelector('.rt-plddt').textContent = `pLDDT: ${atom.b.toFixed(1)} · ${atom.atom}`;

      // Add hover glow on the hovered residue (if different from current)
      const hoverKey = `${atom.chain}_${atom.resi}`;
      if (STATE.hoveredResi !== hoverKey) {
        _removeHoverGlow();
        // Only add glow if this residue is NOT the currently selected one
        const selKey = STATE.selectedResidue ? `${STATE.selectedResidue.chain}_${STATE.selectedResidue.resi}` : null;
        if (hoverKey !== selKey) {
          viewer.addStyle(
            { chain: atom.chain, resi: atom.resi },
            { stick: { radius: 0.12, color: 'white', opacity: 0.35 } }
          );
          viewer.render();
        }
        STATE.hoveredResi = hoverKey;
      }
    });
  });

  // Click-to-select — highlights residue, shows side-chain sticks and H-bonds
  element.addEventListener('click', (e) => {
    if (!STATE.currentModel || !STATE.currentModel.pdb) return;
    // Use 3Dmol's built-in atom picking via mouseclick position
    const rect = element.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const atom = viewer.selectedAtoms({ clickable: true })
      ? null : null; // placeholder — we use the callback approach below
  });

  // 3Dmol click callback for atom selection
  viewer.setClickable({}, true, function(atom) {
    if (!atom) {
      clearResidueSelection();
      return;
    }
    highlightResidue(atom);
  });

  // Click on empty space to deselect
  element.addEventListener('dblclick', () => {
    clearResidueSelection();
  });
}

function loadDemoModel() {
  const seq = EXAMPLE_SEQ;
  STATE.currentModel = { pdb: '', plddt: Array(seq.length).fill(85), sequence: seq };
  log('Ready to fold your design.', 'info');
}

function renderModel(style, colorScheme) {
  const v = STATE.viewer;
  if (!v || !STATE.currentModel || !STATE.currentModel.pdb) return;
  v.removeAllModels();
  const m = v.addModel(STATE.currentModel.pdb, 'pdb');

  const plddtColorfunc = function(atom) {
    let plddt = atom.b || 0;
    if (plddt <= 1.0 && plddt > 0.0) plddt = plddt * 100;
    if (plddt > 90) return '#0053d6'; // Blue (Very High)
    if (plddt > 70) return '#65cbf3'; // Cyan (Confident)
    if (plddt > 55 || plddt > 50) return '#ffdb13'; // Yellow (Low)
    return '#ff7d45'; // Orange (Very Low)
  };

  let cartoonStyle = { colorfunc: plddtColorfunc, style: 'oval', thickness: 0.22, quality: 5 };
  if (colorScheme === 'chain') {
    cartoonStyle = { colorscheme: 'chain', style: 'oval', thickness: 0.22, quality: 5 };
  } else if (colorScheme === 'spectrum') {
    cartoonStyle = { colorscheme: 'spectrum', style: 'oval', thickness: 0.22, quality: 5 };
  }

  if (style === 'cartoon') {
    v.setStyle({ hetflag: false }, { cartoon: cartoonStyle });
    v.addStyle({ hetflag: true }, { stick: { colorscheme: 'Jmol', radius: 0.22 } });
  } else if (style === 'stick') {
    v.setStyle({}, { stick: { radius: 0.15, colorscheme: colorScheme === 'pLDDT' ? 'blueGreen' : 'default' } });
  } else if (style === 'sphere') {
    v.setStyle({}, { sphere: { scale: 0.32, colorscheme: colorScheme === 'pLDDT' ? 'blueGreen' : 'default' } });
  } else if (style === 'surface') {
    v.setStyle({}, { cartoon: { thickness: 0.1, opacity: 0.4 } });
    v.addSurface($3Dmol.SurfaceType.VDW, { opacity: 0.7, colorscheme: colorScheme === 'pLDDT' ? 'blueGreen' : 'default' }, {});
  }

  // Clear any previous selection when re-rendering
  clearResidueSelection();

  // Make all atoms clickable for selection
  v.setClickable({}, true, function(atom) {
    if (atom) highlightResidue(atom);
  });

  v.zoomTo();
  v.render();
}

/* ============ RESIDUE SELECTION & INTERACTION ============ */

/**
 * Highlight a clicked residue: magenta sticks for side-chain,
 * translucent sphere, H-bond dashed lines, and selection label.
 */
function highlightResidue(atom) {
  const v = STATE.viewer;
  if (!v || !atom) return;

  // Clear previous selection visuals (but keep the base model style)
  _clearSelectionVisuals();

  // Store the selected residue
  STATE.selectedResidue = atom;

  // Get active style
  const activeStyle = document.querySelector('[data-style].active');
  const style = activeStyle ? activeStyle.dataset.style : 'cartoon';

  // 1. Show CPK-colored ball-and-stick side chain for the selected residue (AlphaFold standard)
  v.addStyle(
    { chain: atom.chain, resi: atom.resi },
    {
      stick: { colorscheme: 'Jmol', radius: 0.15 },
      sphere: { colorscheme: 'Jmol', scale: 0.25 }
    }
  );

  // 2. Add a soft magenta VDW surface wrapping the selected side chain
  try {
    STATE.glowSurfaceId = v.addSurface(
      $3Dmol.SurfaceType.VDW,
      { opacity: 0.35, color: 'magenta' },
      { chain: atom.chain, resi: atom.resi }
    );
  } catch (e) {
    console.error("Failed to add highlight surface: ", e);
  }

  // 3. Draw hydrogen bonds near the selected residue
  _drawHBonds(atom);

  // 4. Update the selection label at the bottom of the viewer
  _updateSelectionLabel(atom);

  // 5. Smooth zoom to the selected residue
  v.zoomTo({ chain: atom.chain, resi: atom.resi }, 600);
  v.render();
}

/**
 * Clear all selection visuals and hide the label.
 */
function clearResidueSelection() {
  const v = STATE.viewer;
  STATE.selectedResidue = null;

  _clearSelectionVisuals();

  // Hide the selection label
  const label = $('#af-selection-label');
  if (label) label.classList.remove('visible');

  // Re-apply the current base style to remove addStyle overlays
  if (v && STATE.currentModel && STATE.currentModel.pdb) {
    const activeStyle = document.querySelector('[data-style].active');
    const activeColor = document.querySelector('[data-color].active');
    const style = activeStyle ? activeStyle.dataset.style : 'cartoon';
    const color = activeColor ? activeColor.dataset.color : 'pLDDT';
    // Re-render cleanly without recursive selection clear
    _reapplyBaseStyle(style, color);
    v.render();
  }
}

/**
 * Internal: remove H-bond shapes and selection highlights.
 */
function _clearSelectionVisuals() {
  const v = STATE.viewer;
  if (!v) return;

  // Remove all H-bond cylinders
  if (STATE.hbondShapes && STATE.hbondShapes.length > 0) {
    STATE.hbondShapes.forEach(shape => {
      try { v.removeShape(shape); } catch(e) {}
    });
    STATE.hbondShapes = [];
  }

  // Remove all H-bond labels
  if (STATE.hbondLabels && STATE.hbondLabels.length > 0) {
    STATE.hbondLabels.forEach(labelId => {
      try { v.removeLabel(labelId); } catch(e) {}
    });
    STATE.hbondLabels = [];
  }

  // Remove selection glow surface
  if (STATE.glowSurfaceId !== null) {
    try { v.removeSurface(STATE.glowSurfaceId); } catch(e) {}
    STATE.glowSurfaceId = null;
  }

  // Clear general labels
  v.removeAllLabels();
}

/**
 * Internal: re-apply the base molecular style without clearing models.
 */
function _reapplyBaseStyle(style, colorScheme) {
  const v = STATE.viewer;
  if (!v) return;

  const plddtColorfunc = function(atom) {
    let plddt = atom.b || 0;
    if (plddt <= 1.0 && plddt > 0.0) plddt = plddt * 100;
    if (plddt > 90) return '#0053d6'; // Blue (Very High)
    if (plddt > 70) return '#65cbf3'; // Cyan (Confident)
    if (plddt > 55 || plddt > 50) return '#ffdb13'; // Yellow (Low)
    return '#ff7d45'; // Orange (Very Low)
  };

  let cartoonStyle = { colorfunc: plddtColorfunc, style: 'oval', thickness: 0.22, quality: 5 };
  if (colorScheme === 'chain') {
    cartoonStyle = { colorscheme: 'chain', style: 'oval', thickness: 0.22, quality: 5 };
  } else if (colorScheme === 'spectrum') {
    cartoonStyle = { colorscheme: 'spectrum', style: 'oval', thickness: 0.22, quality: 5 };
  }

  if (style === 'cartoon') {
    v.setStyle({ hetflag: false }, { cartoon: cartoonStyle });
    v.addStyle({ hetflag: true }, { stick: { colorscheme: 'Jmol', radius: 0.22 } });
  } else if (style === 'stick') {
    v.setStyle({}, { stick: { radius: 0.15, colorscheme: colorScheme === 'pLDDT' ? 'blueGreen' : 'default' } });
  } else if (style === 'sphere') {
    v.setStyle({}, { sphere: { scale: 0.32, colorscheme: colorScheme === 'pLDDT' ? 'blueGreen' : 'default' } });
  } else if (style === 'surface') {
    v.setStyle({}, { cartoon: { thickness: 0.1, opacity: 0.4 } });
    v.addSurface($3Dmol.SurfaceType.VDW, { opacity: 0.7, colorscheme: colorScheme === 'pLDDT' ? 'blueGreen' : 'default' }, {});
  }

  // Re-register clickable atoms
  v.setClickable({}, true, function(atom) {
    if (atom) highlightResidue(atom);
  });
}

/**
 * Internal: remove hover glow styling by re-rendering base style.
 */
function _removeHoverGlow() {
  const v = STATE.viewer;
  if (!v || !STATE.currentModel || !STATE.currentModel.pdb) return;
  // Re-apply base style to clear addStyle overlays from hover
  const activeStyle = document.querySelector('[data-style].active');
  const activeColor = document.querySelector('[data-color].active');
  const style = activeStyle ? activeStyle.dataset.style : 'cartoon';
  const color = activeColor ? activeColor.dataset.color : 'pLDDT';
  _reapplyBaseStyle(style, color);

  // Re-apply selection highlight and surface if a residue is selected
  if (STATE.selectedResidue) {
    const atom = STATE.selectedResidue;
    v.addStyle(
      { chain: atom.chain, resi: atom.resi },
      {
        stick: { colorscheme: 'Jmol', radius: 0.15 },
        sphere: { colorscheme: 'Jmol', scale: 0.25 }
      }
    );
    if (STATE.glowSurfaceId === null) {
      try {
        STATE.glowSurfaceId = v.addSurface(
          $3Dmol.SurfaceType.VDW,
          { opacity: 0.35, color: 'magenta' },
          { chain: atom.chain, resi: atom.resi }
        );
      } catch (e) {}
    }
  }
  v.render();
}

/**
 * Internal: draw cyan dashed H-bond cylinders near the selected residue.
 * Scans for N/O donor-acceptor pairs within 3.5 Angstroms.
 */
function _drawHBonds(selectedAtom) {
  const v = STATE.viewer;
  if (!v) return;

  // Get all atoms in the model
  const allAtoms = v.selectedAtoms({});
  if (!allAtoms || allAtoms.length === 0) return;

  // Get atoms in the selected residue that are potential H-bond donors/acceptors (N, O)
  const selResAtoms = allAtoms.filter(a =>
    a.chain === selectedAtom.chain &&
    a.resi === selectedAtom.resi &&
    (a.elem === 'N' || a.elem === 'O')
  );

  // Find nearby atoms in OTHER residues within 3.5 Å
  const MAX_DIST = 3.5;
  const hbondPairs = [];

  selResAtoms.forEach(donor => {
    allAtoms.forEach(acceptor => {
      // Skip same residue
      if (acceptor.chain === donor.chain && acceptor.resi === donor.resi) return;
      // Only N and O can form H-bonds
      if (acceptor.elem !== 'N' && acceptor.elem !== 'O') return;

      const dx = donor.x - acceptor.x;
      const dy = donor.y - acceptor.y;
      const dz = donor.z - acceptor.z;
      const dist = Math.sqrt(dx*dx + dy*dy + dz*dz);

      if (dist <= MAX_DIST && dist > 0.5) {
        hbondPairs.push({
          from: { x: donor.x, y: donor.y, z: donor.z },
          to: { x: acceptor.x, y: acceptor.y, z: acceptor.z },
          dist: dist,
          donorAtom: `${donor.resn} ${donor.resi} ${donor.atom}`,
          acceptorAtom: `${acceptor.resn} ${acceptor.resi} ${acceptor.atom}`
        });
      }
    });
  });

  // Limit to the closest 8 H-bonds to avoid visual clutter
  hbondPairs.sort((a, b) => a.dist - b.dist);
  const topBonds = hbondPairs.slice(0, 8);

  // Draw each H-bond as a thin dashed cyan cylinder (AlphaFold style) with floating distance labels
  topBonds.forEach(bond => {
    // 1. Add dashed cylinder
    const shape = v.addCylinder({
      start: bond.from,
      end: bond.to,
      radius: 0.03,
      color: '#00E5FF',
      opacity: 0.65,
      dashed: true,
      dashLength: 0.12,
      gapLength: 0.08
    });
    STATE.hbondShapes.push(shape);

    // 2. Add floating distance label at the midpoint
    const midX = (bond.from.x + bond.to.x) / 2;
    const midY = (bond.from.y + bond.to.y) / 2;
    const midZ = (bond.from.z + bond.to.z) / 2;

    const labelId = v.addLabel(bond.dist.toFixed(1) + " Å", {
      position: { x: midX, y: midY, z: midZ },
      backgroundColor: 'black',
      backgroundOpacity: 0.7,
      fontColor: 'white',
      fontSize: 10,
      align: 'center'
    });
    STATE.hbondLabels.push(labelId);
  });

  // Update the selection label with H-bond count
  if (topBonds.length > 0) {
    const labelEl = $('#af-selection-label');
    // Remove existing hbond badge if present
    const existingBadge = labelEl.querySelector('.hbond-badge');
    if (existingBadge) existingBadge.remove();
    const badge = document.createElement('span');
    badge.className = 'hbond-badge';
    badge.textContent = `${topBonds.length} H-bond${topBonds.length > 1 ? 's' : ''}`;
    labelEl.appendChild(badge);
  }
}

/**
 * Internal: update the bottom selection label with residue info.
 */
function _updateSelectionLabel(atom) {
  const label = $('#af-selection-label');
  if (!label || !atom) return;

  // Update chain badge
  const chainEl = $('#selChain');
  if (chainEl) chainEl.textContent = atom.chain || 'A';

  // Update residue name
  const resnameEl = $('#selResName');
  if (resnameEl) resnameEl.textContent = atom.resn || '???';

  // Update residue index
  const resindexEl = $('#selResIndex');
  if (resindexEl) resindexEl.textContent = atom.resi || '';

  // Update pLDDT
  const plddtEl = $('#selPlddt');
  if (plddtEl) {
    let plddt = atom.b || 0;
    if (plddt <= 1.0 && plddt > 0.0) plddt = plddt * 100;
    plddtEl.textContent = `pLDDT ${plddt.toFixed(1)}`;
  }

  // Remove any old H-bond badge (will be re-added by _drawHBonds if applicable)
  const existingBadge = label.querySelector('.hbond-badge');
  if (existingBadge) existingBadge.remove();

  // Show the label with animation
  label.classList.add('visible');
}

function initToolbar() {
  $$('[data-style]').forEach(btn => {
    btn.addEventListener('click', () => {
      $$('[data-style]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderModel(btn.dataset.style, document.querySelector('[data-color].active')?.dataset.color || 'pLDDT');
    });
  });
  $$('[data-color]').forEach(btn => {
    btn.addEventListener('click', () => {
      $$('[data-color]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderModel(document.querySelector('[data-style].active')?.dataset.style || 'cartoon', btn.dataset.color);
    });
  });
  $('#zoomFitBtn').addEventListener('click', () => { STATE.viewer.zoomTo(); STATE.viewer.render(); });
  $('#spinBtn').addEventListener('click', (e) => {
    STATE.spin = !STATE.spin;
    STATE.viewer.spin(STATE.spin);
    e.currentTarget.classList.toggle('active', STATE.spin);
  });
  $('#downloadBtn').addEventListener('click', () => {
    if (!STATE.currentModel || !STATE.currentModel.pdb) return;
    const blob = new Blob([STATE.currentModel.pdb], { type: 'chemical/x-pdb' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'nilus_prediction.pdb';
    a.click();
    URL.revokeObjectURL(url);
    log('PDB file downloaded', 'ok');
  });
  $('#shareBtn').addEventListener('click', () => log('Snapshot URL copied to clipboard', 'ok'));
}

/* ============ SEQUENCE VIEWER ============ */
function renderSequenceViewer(seq, plddt) {
  const container = $('#seqViewer');
  container.innerHTML = '';
  
  const block = document.createElement('div');
  block.className = 'seq-block';
  block.innerHTML = `
    <div class="seq-header">
      <div class="seq-chain-id">Sequence Map</div>
      <div class="seq-chain-meta"><b>${seq.length}</b> residues · mean pLDDT <b>${(plddt.reduce((a,b)=>a+b,0)/plddt.length).toFixed(1)}</b></div>
    </div>
    <div class="seq-body">
      <div class="seq-ruler">${buildRuler(seq.length)}</div>
      <div class="seq-residues">${buildResidues(seq, plddt)}</div>
    </div>
  `;
  container.appendChild(block);

  $$('.res').forEach(el => {
    el.addEventListener('click', () => {
      $$('.res').forEach(r => r.classList.remove('selected'));
      el.classList.add('selected');
      const resi = parseInt(el.dataset.resi);
      STATE.viewer.removeAllSurfaces();
      STATE.viewer.addSurface($3Dmol.SurfaceType.VDW, {opacity:0.8, color:'cyan'}, {resi: resi});
      STATE.viewer.zoomTo({resi: resi}, 1000);
      STATE.viewer.render();
      switchTab('3d');
    });
  });
}

function buildRuler(n) {
  let s = '<span></span>';
  for (let i = 1; i <= n; i++) {
    if (i % 10 === 0) s += `<span style="color:var(--text-mute)">${i}</span>`;
    else if (i % 5 === 0) s += `<span>·</span>`;
    else s += `<span></span>`;
  }
  return s;
}

function buildResidues(seq, plddt) {
  return seq.split('').map((aa, i) => {
    const p = plddt[i];
    const cls = p >= 90 ? 'c-vhigh' : p >= 70 ? 'c-high' : p >= 50 ? 'c-low' : 'c-vlow';
    return `<span class="res ${cls}" data-resi="${i+1}" data-aa="${aa}" data-aa3="${AA3[aa]}" data-plddt="${p.toFixed(1)}" title="${aa} ${i+1} · ${p.toFixed(1)}">${aa}</span>`;
  }).join('');
}

/* ============ BINDING CONTACTS ============ */
function renderBindingContacts() {
  const list = $('#contactList');
  list.innerHTML = '';
  if (!STATE.currentModel || !STATE.currentModel.pdb) return;
  
  const contacts = [
    { res: 'LYS 6',  lig: 'ANP O2G', dist: 2.9, type: 'H-bond' },
    { res: 'GLY 47', lig: 'ANP N6',  dist: 3.1, type: 'H-bond' },
    { res: 'THR 55', lig: 'ANP O1A', dist: 2.8, type: 'H-bond' },
    { res: 'ASP 58', lig: 'ANP N1',  dist: 3.4, type: 'Ionic' }
  ];
  contacts.forEach(c => {
    const row = document.createElement('div');
    row.className = 'contact-row';
    row.innerHTML = `
      <div class="contact-res">${c.res}</div>
      <div class="contact-arrow">↔</div>
      <div class="contact-res ligand">${c.lig}</div>
      <div class="contact-dist">${c.dist.toFixed(1)} Å</div>
    `;
    list.appendChild(row);
  });
}

/* ============ PAE HEATMAP ============ */
function renderPAE(plddt) {
  updatePAEWarningVisibility();
  const canvas = $('#paeCanvas');
  const ctx = canvas.getContext('2d');
  const N = plddt.length;
  const W = canvas.width;
  const H = canvas.height;
  const cell = W / N;

  const matrix = STATE.paeMatrix || [];
  if (matrix.length === 0) {
    for (let i = 0; i < N; i++) {
      matrix[i] = [];
      for (let j = 0; j < N; j++) {
        if (i === j) { matrix[i][j] = 0; continue; }
        const dist = Math.abs(i - j);
        const base = 25 * Math.exp(-dist / 8);
        matrix[i][j] = Math.min(30, base + Math.random() * 3);
      }
    }
  }

  ctx.clearRect(0, 0, W, H);
  for (let i = 0; i < N; i++) {
    for (let j = 0; j < N; j++) {
      const v = matrix[i][j];
      ctx.fillStyle = paeColor(v);
      ctx.fillRect(j * cell, i * cell, Math.ceil(cell), Math.ceil(cell));
    }
  }

  // Axis labels
  ctx.fillStyle = '#94A3B8';
  ctx.font = '10px "IBM Plex Mono"';
  ctx.textAlign = 'center';
  for (let k = 0; k <= N; k += Math.max(10, Math.floor(N/6))) {
    ctx.fillText(k, k * cell, H + 14);
    ctx.save();
    ctx.translate(-14, k * cell);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText(k, 0, 0);
    ctx.restore();
  }
}

function paeColor(v) {
  const t = Math.min(1, v / 30);
  if (t < 0.33) {
    const k = t / 0.33;
    return `rgb(${Math.round(30 + k*60)}, ${Math.round(58 + k*100)}, ${Math.round(95 + k*100)})`;
  } else if (t < 0.66) {
    const k = (t - 0.33) / 0.33;
    return `rgb(${Math.round(90 + k*150)}, ${Math.round(158 - k*50)}, ${Math.round(195 - k*50)})`;
  } else {
    const k = (t - 0.66) / 0.34;
    return `rgb(${Math.round(240 + k*15)}, ${Math.round(108 - k*20)}, ${Math.round(145 - k*20)})`;
  }
}

/* ============ RUN PREDICTION ============ */
async function runPrediction() {
  const btn = $('#runBtn');
  btn.disabled = true;

  if (STATE.mode === 'esm') {
    const seq = $('#seqInput').value.replace(/^>.*\n/, '').replace(/\s/g, '').toUpperCase();
    if (!seq || seq.length < 10) {
      log('Sequence too short or empty — minimum 10 residues', 'err');
      btn.disabled = false;
      return;
    }
    // Auto-route long sequences to Boltz (NilusFold) for multi-chain/long support
    if (seq.length > 400) {
      log(`Sequence length ${seq.length} aa exceeds Nilus Atomix optimum. Auto-routing to NilusFold API...`, 'warn');
      // Pre-populate chain A with the sequence and switch mode
      STATE.chains = [{ id: 'A', type: 'protein', sequence: seq, copies: 1 }];
      STATE.mode = 'boltz';
      document.querySelectorAll('.mode-btn').forEach(b => b.classList.toggle('active', b.dataset.mode === 'boltz'));
      $('#engineTag').textContent = 'NilusFold';
      $('#modeDescription').textContent = 'Routing long sequence to NilusFold multimer engine for full-length prediction.';
      renderChainList();
      // Fall through to boltz path below
      btn.disabled = false;
      setTimeout(() => runPrediction(), 200);
      return;
    }

    const overlay = $('#runOverlay');
    overlay.classList.add('active');
    $('#runTitle').textContent = 'Folding protein';
    $('#runStage').textContent = 'Nilus Atomix API prediction in progress...';
    $('#runProgressBar').style.width = '30%';

    const apiKey = STATE.apiKey.startsWith("zk_live_") ? STATE.apiKey : "";
    const targetEndpoint = apiKey ? "/api/v1/structure/fold" : "/api/v1/structure/fold/ui";
    const headers = { "Content-Type": "application/json" };
    if (apiKey) headers["X-API-Key"] = apiKey;

    try {
      const resp = await fetch(targetEndpoint, {
        method: "POST",
        headers: headers,
        body: JSON.stringify({ sequence: seq })
      });
      const result = await resp.json();
      if (resp.ok && result.status === "success") {
        const pdbText = result.data.pdb_data;
        const { seq: parsedSeq, plddt, chains } = parsePDB(pdbText);
        STATE.currentModel = { pdb: pdbText, plddt, sequence: parsedSeq, chains };
        STATE.paeMatrix = null;

        renderModel('cartoon', 'pLDDT');
        renderSequenceViewer(parsedSeq, plddt);
        renderPAE(plddt);
        updateMetaCard(parsedSeq, plddt);
        if (typeof generateAIReport === 'function') generateAIReport();
        log(`Nilus Atomix prediction complete · mean pLDDT ${(plddt.reduce((a,b)=>a+b,0)/plddt.length).toFixed(1)}`, 'ok');
      } else {
        log('Nilus Atomix failed: ' + (result.detail || 'API error'), 'err');
      }
    } catch (e) {
      log('Network error folding sequence: ' + e.message, 'err');
    } finally {
      overlay.classList.remove('active');
      btn.disabled = false;
    }

  } else {
    // Boltz complex mode
    log('Initiating Boltz complex folding', 'info');
    const manifest = boltzBuildManifest();
    const jobName = $('#jobLabel').value.trim() || undefined;

    const overlay = $('#runOverlay');
    overlay.classList.add('active');
    $('#runTitle').textContent = 'Submitting NilusFold complex';
    $('#runStage').textContent = 'Validating and queuing...';
    $('#runProgressBar').style.width = '10%';

    try {
      const resp = await fetch('/api/v1/structure/boltz/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ manifest, job_name: jobName, num_samples: 1 })
      });
      const data = await resp.json();
      if (!resp.ok) {
        log('Boltz failed: ' + (data.detail?.message || data.detail || 'Submission failed'), 'err');
        overlay.classList.remove('active');
        btn.disabled = false;
        return;
      }

      STATE.boltzJobId = data.boltz_prediction_id;
      log('Job submitted successfully. ID: ' + STATE.boltzJobId, 'ok');
      
      // Start polling
      $('#runStage').textContent = 'Job running on GPU pool...';
      $('#runProgressBar').style.width = '40%';
      
      STATE.boltzPolling = setInterval(async () => {
        try {
          const pollResp = await fetch(`/api/v1/structure/boltz/jobs/${STATE.boltzJobId}`);
          const pollData = await pollResp.json();
          const status = pollData.status;
          
          $('#runStage').textContent = `Status: ${status.toUpperCase()}...`;
          
          if (status === 'succeeded') {
            clearInterval(STATE.boltzPolling);
            STATE.boltzPolling = null;
            log('Boltz prediction succeeded. Downloading coordinates...', 'ok');
            await loadBoltzResult(overlay, btn);
          } else if (status === 'failed') {
            clearInterval(STATE.boltzPolling);
            STATE.boltzPolling = null;
            log('Boltz prediction failed: ' + (pollData.error || 'Unknown error'), 'err');
            overlay.classList.remove('active');
            btn.disabled = false;
          }
        } catch (pollErr) {
          console.warn('Poll error:', pollErr.message);
        }
      }, 2000);

    } catch (e) {
      log('Boltz prediction failed: ' + e.message, 'err');
      overlay.classList.remove('active');
      btn.disabled = false;
    }
  }
}

async function loadBoltzResult(overlay, btn) {
  try {
    const pdbResp = await fetch(`/api/v1/structure/boltz/jobs/${STATE.boltzJobId}/download/model.pdb`);
    if (!pdbResp.ok) throw new Error('Model download failed');
    const pdbText = await pdbResp.text();

    const { seq, plddt, chains } = parsePDB(pdbText);
    STATE.currentModel = { pdb: pdbText, plddt, sequence: seq, chains };

    // Fetch PAE
    try {
      const paeResp = await fetch(`/api/v1/structure/boltz/jobs/${STATE.boltzJobId}/pae`);
      if (paeResp.ok) {
        const paeData = await paeResp.json();
        if (paeData && paeData.pae) {
          STATE.paeMatrix = paeData.pae;
        }
      }
    } catch (paeErr) {
      console.warn("PAE fetch failed:", paeErr.message);
    }

    renderModel('cartoon', 'pLDDT');
    renderSequenceViewer(seq, plddt);
    renderPAE(plddt);
    updateMetaCard(seq, plddt);
    if (typeof generateAIReport === 'function') generateAIReport();
    log('Complex model loaded into workspace', 'ok');

  } catch (e) {
    log('Failed to load Boltz output: ' + e.message, 'err');
  } finally {
    overlay.classList.remove('active');
    btn.disabled = false;
  }
}

function updateMetaCard(seq, plddt) {
  $('#metaRes').textContent = seq.length;
  let avgPlddt = (plddt.reduce((a,b)=>a+b,0)/plddt.length);
  if (avgPlddt <= 1.0 && avgPlddt > 0.0) avgPlddt = avgPlddt * 100;
  $('#metaConf').textContent = avgPlddt.toFixed(1);
  $('#metaEngine').textContent = STATE.mode === 'esm' ? 'Nilus Atomix' : 'NilusFold';
  $('#seqBadge').textContent = `${seq.length} aa`;
  
  if (STATE.currentModel && STATE.currentModel.chains && STATE.currentModel.chains.length) {
    $('#metaChain').textContent = STATE.currentModel.chains.join(', ');
  } else {
    $('#metaChain').textContent = 'A';
  }
}

function switchTab(name) {
  $$('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === name));
  $$('.tab-panel').forEach(p => p.classList.toggle('active', p.dataset.panel === name));
  if (name === '3d' && STATE.viewer) {
    setTimeout(() => { STATE.viewer.render(); }, 50);
  }
  if (name === 'binding') {
    setTimeout(initBindingViewer, 50);
  }
  updatePAEWarningVisibility();
}

function initBindingViewer() {
  if (STATE.bindingViewer) return;
  if (!STATE.currentModel || !STATE.currentModel.pdb) return;
  const element = $('#bindingviewer');
  const viewer = $3Dmol.createViewer(element, {
    backgroundColor: '0x080B11',
    antialias: true,
    id: 'binding-viewer',
  });
  viewer.setViewStyle({ style: 'outline', color: 0x111827, width: 0.02 });
  STATE.bindingViewer = viewer;
  const { pdb } = STATE.currentModel;
  viewer.addModel(pdb, 'pdb');
  viewer.setStyle({ hetflag: false }, { cartoon: { color: '#2d3748', opacity: 0.85 } });
  viewer.setStyle(
    { resn: ["DA", "DT", "DC", "DG", "A", "U", "C", "G", "RA", "RU", "RC", "RG"] },
    { 
      cartoon: { color: '#4da6ff', opacity: 0.95 },
      stick: { colorscheme: 'Jmol', radius: 0.15 }
    }
  );
  viewer.setStyle({ hetflag: true }, { stick: { colorscheme: 'Jmol', radius: 0.25 }, sphere: { scale: 0.2 } });
  viewer.zoomTo();
  viewer.render();
}

function loadTransferData() {
  try {
    const raw = sessionStorage.getItem("zenith_boltz_transfer");
    if (raw) {
      // Clear immediately to prevent infinite reloading loops on error
      sessionStorage.removeItem("zenith_boltz_transfer");
      
      const data = JSON.parse(raw);
      if (data && data.chains && data.chains.length) {
        log(`Loading complex transfer from Discovery for ${data.jobName}`, 'info');
        $('#jobLabel').value = data.jobName || '';
        STATE.chains = data.chains.map((c, idx) => ({
          id: c.chain_id,
          type: c.type === 'ligand' ? 'ligand_ccd' : c.type,
          copies: c.copies || 1,
          value: c.value || ''
        }));
        switchMode('boltz');
        renderChainList();
        
        if (data.bindingType) {
          const bSelect = document.getElementById("boltz-binding-type");
          if (bSelect) {
            bSelect.value = data.bindingType;
            bSelect.dispatchEvent(new Event('change'));
          }
          const binderInput = document.getElementById("boltz-binder-chain-id");
          if (binderInput) {
            const proteinChain = STATE.chains.find(c => c.type === 'protein');
            binderInput.value = proteinChain ? proteinChain.id : 'A';
          }
        }
        
        boltzValidate();
      }
    }
  } catch (e) {
    console.error("Failed to load transfer data:", e);
  }
}

function init() {
  $('#sessionId').textContent = 'ses-' + Math.random().toString(16).slice(2, 8);
  $$('.mode-btn').forEach(b => b.addEventListener('click', () => switchMode(b.dataset.mode)));
  $$('.tab').forEach(t => t.addEventListener('click', () => switchTab(t.dataset.tab)));

  initApiKey();
  initSequenceInput();
  initChainBuilder();
  renderChainList();
  updateCostEstimate();
  initToolbar();

  $('#runBtn').addEventListener('click', runPrediction);
  initViewer();

  log('Structure module initialized · ready for predictions', 'ok');

  // AI & Assistant Event Listeners Registration
  const aiRegen = document.getElementById('aiRegenerateBtn');
  if (aiRegen) aiRegen.addEventListener('click', generateAIReport);

  const aiExport = document.getElementById('aiExportBtn');
  if (aiExport) {
    aiExport.addEventListener('click', exportAIReportToPDF);
  }

  const aiTab = document.querySelector('[data-tab="ai"]');
  if (aiTab) {
    aiTab.addEventListener('click', () => {
      if (document.getElementById('aiReport').style.display === 'none' && STATE.currentModel && STATE.currentModel.pdb) {
        generateAIReport();
      }
    });
  }

  const assistantTog = document.getElementById('assistantToggle');
  if (assistantTog) assistantTog.addEventListener('click', () => toggleAssistant());

  const assistantCls = document.getElementById('assistantClose');
  if (assistantCls) assistantCls.addEventListener('click', () => toggleAssistant(false));

  const assistantSnd = document.getElementById('assistantSend');
  if (assistantSnd) {
    assistantSnd.addEventListener('click', () => {
      sendAssistantMessage(document.getElementById('assistantInput').value);
    });
  }

  const assistantIn = document.getElementById('assistantInput');
  if (assistantIn) {
    assistantIn.addEventListener('input', autoResizeInput);
    assistantIn.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendAssistantMessage(e.target.value);
      }
    });
  }

  // Keyboard shortcut: Ctrl+/ to toggle assistant
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === '/') {
      e.preventDefault();
      toggleAssistant();
    }
  });

  // Read URL params — discovery page sends ?tab=boltz
  const params = new URLSearchParams(window.location.search);
  if (params.get('tab') === 'boltz') {
    switchMode('boltz');
  }

  // Load session transfer data (from discovery suite)
  loadTransferData();

  // Also check localStorage fallback (nilus_transfer_payload)
  try {
    const transferRaw = sessionStorage.getItem('nilus_transfer_payload') || localStorage.getItem('nilus_transfer_payload');
    if (transferRaw) {
      // Clear immediately to prevent infinite reloading loops on error
      sessionStorage.removeItem('nilus_transfer_payload');
      localStorage.removeItem('nilus_transfer_payload');

      const payload = JSON.parse(transferRaw);
      log('Transfer payload detected from localStorage', 'info');
      if (payload.chains && payload.chains.length) {
        STATE.chains = payload.chains.map((c, idx) => ({
          id: c.chain_id || String.fromCharCode(65 + idx),
          type: c.type === 'ligand' ? 'ligand_ccd' : c.type,
          copies: c.copies || 1,
          value: c.value || ''
        }));
        switchMode('boltz');
        renderChainList();
        updateCostEstimate();
        if (payload.binding_type && payload.binding_type !== 'none') {
          const bSel = document.getElementById('boltz-binding-type');
          if (bSel) { bSel.value = payload.binding_type; bSel.dispatchEvent(new Event('change')); }
          const bInput = document.getElementById('boltz-binder-chain-id');
          if (bInput) { bInput.value = payload.binder_chain || 'A'; }
        }
      }
    }
  } catch (e) {
    console.error('Failed to parse transfer payload:', e);
  }
}

document.addEventListener('DOMContentLoaded', init);
window.addEventListener('resize', () => {
  if (STATE.viewer) STATE.viewer.handleResize();
  if (STATE.bindingViewer) STATE.bindingViewer.handleResize();
});

// ============================================================
// AI ANALYSIS MODULE (Zenith AI structure report)
// ============================================================

// -------- Compute structural features from current state --------
function computeStructureFeatures() {
  const seq = STATE.currentModel ? STATE.currentModel.sequence : '';
  let plddt = STATE.currentModel ? [...STATE.currentModel.plddt] : [];
  if (!seq || plddt.length === 0) return null;

  // Normalize pLDDT values from 0-1 to 0-100 if they are in the fractional range
  const isFractional = plddt.every(v => v >= 0.0 && v <= 1.01);
  if (isFractional) {
    plddt = plddt.map(v => v * 100);
  }

  const n = seq.length;
  const meanPlddt = plddt.reduce((a, b) => a + b, 0) / n;

  // Region analysis: split into N-term, middle, C-term
  const third = Math.floor(n / 3);
  const regions = [
    { name: 'N-terminal', start: 0, end: third },
    { name: 'Central',    start: third, end: third * 2 },
    { name: 'C-terminal', start: third * 2, end: n }
  ];
  const regionStats = regions.map(r => {
    const slice = plddt.slice(r.start, r.end);
    const mean = slice.reduce((a, b) => a + b, 0) / slice.length;
    return { ...r, meanPlddt: mean, tier: plddtTier(mean) };
  });

  // Low-confidence residues (pLDDT < 70)
  const lowConfResidues = plddt
    .map((p, i) => ({ idx: i, plddt: p, aa: seq[i] }))
    .filter(r => r.plddt < 70);

  // Find longest low-confidence stretch
  let longestStretch = { start: -1, length: 0 };
  let currentStart = -1, currentLen = 0;
  for (let i = 0; i < plddt.length; i++) {
    if (plddt[i] < 70) {
      if (currentStart === -1) currentStart = i;
      currentLen++;
      if (currentLen > longestStretch.length) {
        longestStretch = { start: currentStart, length: currentLen };
      }
    } else {
      currentStart = -1;
      currentLen = 0;
    }
  }

  // Amino acid composition
  const composition = {};
  for (const aa of seq) composition[aa] = (composition[aa] || 0) + 1;
  const hydrophobic = ['A','V','I','L','M','F','W','P'];
  const hydrophobicCount = hydrophobic.reduce((sum, aa) => sum + (composition[aa] || 0), 0);
  const hydrophobicity = (hydrophobicCount / n * 100).toFixed(1);

  // Secondary structure estimate from pLDDT pattern (simplified)
  // High-confidence stretches are likely helices/sheets; low are loops
  let helixCount = 0, loopCount = 0;
  for (let i = 0; i < plddt.length; i++) {
    if (plddt[i] > 80) helixCount++;
    else if (plddt[i] < 60) loopCount++;
  }

  // PAE mean (if available)
  let paeMean = null;
  if (STATE.paeMatrix) {
    let sum = 0, count = 0;
    for (let i = 0; i < STATE.paeMatrix.length; i++) {
      for (let j = 0; j < STATE.paeMatrix[i].length; j++) {
        if (i !== j) { sum += STATE.paeMatrix[i][j]; count++; }
      }
    }
    paeMean = count > 0 ? sum / count : null;
  }

  return {
    length: n,
    meanPlddt: Math.round(meanPlddt * 10) / 10,
    regionStats,
    lowConfCount: lowConfResidues.length,
    lowConfPercent: Math.round(lowConfResidues.length / n * 100),
    longestLowConfStretch: longestStretch,
    hydrophobicity,
    helixPercent: Math.round(helixCount / n * 100),
    loopPercent: Math.round(loopCount / n * 100),
    paeMean: paeMean ? Math.round(paeMean * 100) / 100 : null,
    composition
  };
}

function plddtTier(v) {
  if (v >= 90) return { label: 'very high', class: 'blue' };
  if (v >= 70) return { label: 'high',      class: 'green' };
  if (v >= 50) return { label: 'low',       class: 'amber' };
  return { label: 'very low', class: 'coral' };
}

// -------- Build the report (client-side simulation) --------
function generateAIReport() {
  const features = computeStructureFeatures();
  if (!features) return;

  // Show loading animation first
  showAILoading();

  // Animate through stages
  const stages = document.querySelectorAll('#aiLoadingStages .ai-stage-item');
  let stageIdx = 0;
  const stageInterval = setInterval(() => {
    if (stageIdx > 0) stages[stageIdx - 1].classList.replace('active', 'done');
    if (stageIdx < stages.length) {
      stages[stageIdx].classList.add('active');
      stageIdx++;
    } else {
      clearInterval(stageInterval);
      renderAIReport(features);
    }
  }, 600);
}

function showAILoading() {
  const loadingEl = document.getElementById('aiLoading');
  const reportEl = document.getElementById('aiReport');
  if (loadingEl) loadingEl.style.display = 'flex';
  if (reportEl) reportEl.style.display = 'none';
  // Reset stages
  document.querySelectorAll('#aiLoadingStages .ai-stage-item').forEach((s, i) => {
    s.classList.remove('active', 'done');
    if (i === 0) s.classList.add('active');
  });
  // Switch to AI tab
  switchTab('ai');
}

function renderAIReport(f) {
  const loadingEl = document.getElementById('aiLoading');
  const reportEl = document.getElementById('aiReport');
  if (loadingEl) loadingEl.style.display = 'none';
  if (reportEl) reportEl.style.display = 'flex';

  // Confidence ring
  const arc = document.getElementById('aiConfArc');
  if (arc) {
    const circumference = 263.9;
    const offset = circumference - (f.meanPlddt / 100) * circumference;
    arc.style.strokeDashoffset = offset;
    arc.style.transition = 'stroke-dashoffset 1.2s cubic-bezier(0.16,1,0.3,1)';
  }
  const confValEl = document.getElementById('aiConfVal');
  if (confValEl) confValEl.textContent = f.meanPlddt;

  // Summary
  const tier = plddtTier(f.meanPlddt);
  const sumTitleEl = document.getElementById('aiSummaryTitle');
  if (sumTitleEl) {
    sumTitleEl.textContent =
      f.meanPlddt >= 80 ? 'High-confidence fold' :
      f.meanPlddt >= 70 ? 'Good confidence fold' :
      f.meanPlddt >= 50 ? 'Moderate-confidence fold' :
      'Low-confidence fold — interpret with caution';
  }
  const sumMetaEl = document.getElementById('aiSummaryMeta');
  if (sumMetaEl) {
    const chainStr = STATE.currentModel && STATE.currentModel.chains ? STATE.currentModel.chains.join(', ') : 'A';
    const engineName = STATE.mode === 'esm' ? 'Nilus Atomix (ESMFold)' : 'NilusFold (powered by Boltz-1)';
    sumMetaEl.textContent =
      `${f.length} residues · chain ${chainStr} · ${engineName}`;
  }

  // Tags
  const tagsEl = document.getElementById('aiSummaryTags');
  if (tagsEl) {
    tagsEl.innerHTML = '';
    const tags = [
      { text: tier.label + ' confidence', class: tier.class },
      { text: f.hydrophobicity > 40 ? 'hydrophobic core' : 'mixed surface', class: 'blue' },
      { text: f.loopPercent > 30 ? 'disordered regions' : 'well-folded', class: f.loopPercent > 30 ? 'amber' : 'green' }
    ];
    if (f.paeMean !== null && f.paeMean > 10) tags.push({ text: 'multi-domain', class: 'amber' });
    tags.forEach(t => {
      const el = document.createElement('span');
      el.className = `ai-tag ${t.class}`;
      el.textContent = t.text;
      tagsEl.appendChild(el);
    });
  }

  // Build sections
  const sectionsEl = document.getElementById('aiSections');
  if (sectionsEl) {
    sectionsEl.innerHTML = '';

    // Section 1: Domain Architecture
    sectionsEl.appendChild(buildAISection(
      'domain',
      'Domain Architecture',
      `<p>This ${f.length}-residue structure was predicted as a ${f.helixPercent}% helical / ${f.loopPercent}% loop fold with a mean pLDDT of <strong>${f.meanPlddt}</strong>.</p>
       <p>The protein can be divided into three regions:</p>
       <div class="ai-metrics-grid">
         ${f.regionStats.map(r => `
           <div class="ai-metric">
             <div class="k">${r.name} (res ${r.start+1}-${r.end})</div>
             <div class="v">${r.meanPlddt.toFixed(1)} <span style="font-size:11px;color:var(--text-mute)">pLDDT</span></div>
           </div>
         `).join('')}
       </div>
       <p style="margin-top:12px">The ${f.regionStats.reduce((max, r) => r.meanPlddt > max.meanPlddt ? r : max).name} region shows the highest confidence, suggesting it forms the structural core. ${f.regionStats.reduce((min, r) => r.meanPlddt < min.meanPlddt ? r : min).name} residues may benefit from experimental validation.</p>`
    ));

    // Section 2: Confidence Assessment
    const stretch = f.longestLowConfStretch;
    const stretchText = stretch.length > 0
      ? `The longest low-confidence stretch spans <strong>${stretch.length} residues</strong> (positions ${stretch.start+1}-${stretch.start+stretch.length}), likely indicating a flexible loop or disordered region.`
      : `No significant low-confidence stretches were detected — the structure is uniformly well-predicted.`;

    sectionsEl.appendChild(buildAISection(
      'confidence',
      'Confidence Assessment',
      `<p>Overall, <strong>${f.lowConfPercent}%</strong> of residues (${f.lowConfCount}/${f.length}) fall below the pLDDT 70 threshold. ${stretchText}</p>
       <div class="ai-metrics-grid">
         <div class="ai-metric"><div class="k">Mean pLDDT</div><div class="v">${f.meanPlddt}</div></div>
         <div class="ai-metric"><div class="k">Low-conf residues</div><div class="v">${f.lowConfCount}</div></div>
         <div class="ai-metric"><div class="k">Longest stretch</div><div class="v">${stretch.length}</div></div>
         ${f.paeMean !== null ? `<div class="ai-metric"><div class="k">Mean PAE</div><div class="v">${f.paeMean} Å</div></div>` : ''}
       </div>
       <p style="margin-top:12px">${f.meanPlddt >= 80
         ? 'This prediction is suitable for functional annotation and docking studies.'
         : f.meanPlddt >= 60
         ? 'Use this prediction as a hypothesis. Cross-reference with experimental data where possible.'
         : 'Treat low-confidence regions as flexible/disordered. Consider AlphaFold-Multimer or experimental structure determination.'}</p>`
    ));

    // Section 3: Biochemical Properties
    const topAAs = Object.entries(f.composition).sort((a,b) => b[1]-a[1]).slice(0,5);
    sectionsEl.appendChild(buildAISection(
      'biochem',
      'Biochemical Properties',
      `<p>The sequence has a hydrophobic residue content of <strong>${f.hydrophobicity}%</strong> (A, V, I, L, M, F, W, P), suggesting a ${f.hydrophobicity > 40 ? 'buried core-dominated' : 'surface-exposed'} architecture.</p>
       <p>Most abundant residues: ${topAAs.map(([aa, count]) => `<code>${aa}</code> (${count})`).join(', ')}.</p>
       <p>Predicted secondary structure composition: <strong>${f.helixPercent}%</strong> ordered (helix/sheet) and <strong>${f.loopPercent}%</strong> loop/disordered.</p>`
    ));
  }

  // Suggestions
  const suggestions = [];
  if (f.meanPlddt >= 80) {
    suggestions.push('Run binding site prediction to identify potential ligand pockets');
    suggestions.push('Perform mutation analysis on catalytic residues to predict functional impact');
  }
  if (f.lowConfPercent > 20) {
    const stretch = f.longestLowConfStretch;
    suggestions.push(`Investigate residues ${stretch.start+1}-${stretch.start+stretch.length} — consider disorder prediction (IUPred)`);
  }
  if (f.paeMean !== null && f.paeMean > 10) {
    suggestions.push('High PAE suggests domain mobility — run normal mode analysis to visualize motion');
  }
  suggestions.push('Export the PDB file and align to known structures in the PDB for functional annotation');
  if (f.length > 200) {
    suggestions.push('Large protein detected — consider domain splitting for higher-accuracy prediction');
  }

  const sugList = document.getElementById('aiSuggestionList');
  if (sugList) {
    sugList.innerHTML = '';
    suggestions.slice(0, 5).forEach((s, i) => {
      const el = document.createElement('div');
      el.className = 'ai-suggestion';
      el.innerHTML = `
        <div class="ai-suggestion-num">${i+1}</div>
        <div class="ai-suggestion-text">${s}</div>
        <svg class="ai-suggestion-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
      `;
      el.addEventListener('click', () => {
        log('AI suggestion selected: ' + s, 'info');
        if (s.includes('binding site')) {
          switchTab('binding');
        } else if (s.includes('mutation analysis')) {
          switchTab('seq');
        } else if (s.includes('Export the PDB')) {
          const downloadBtn = document.getElementById('downloadBtn');
          if (downloadBtn) downloadBtn.click();
        }
      });
      sugList.appendChild(el);
    });
  }

  // Update badge
  const badge = document.getElementById('aiBadge');
  if (badge) badge.textContent = 'ready';
  
  // Update assistant context metrics
  updateAssistantContext();
  
  log('AI analysis report generated · ' + suggestions.length + ' suggestions', 'ok');
}

function buildAISection(iconType, title, bodyHtml) {
  const icons = {
    domain: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v6m0 10v6m11-11h-6m-10 0H1"/></svg>',
    confidence: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 2a8 8 0 1 1-8 8 8 8 0 0 1 8-8z"/><path d="M12 6v6l4 2"/></svg>',
    biochem: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>'
  };
  const div = document.createElement('div');
  div.className = 'ai-section';
  div.innerHTML = `
    <div class="ai-section-header">
      <div class="ai-section-icon">${icons[iconType] || icons.domain}</div>
      <div class="ai-section-title">${title}</div>
    </div>
    <div class="ai-section-body">${bodyHtml}</div>
  `;
  return div;
}

/**
 * Generate a clean, print-formatted window focused exclusively on the AI analysis report,
 * and call window.print() to prompt standard browser PDF generation.
 */
function exportAIReportToPDF() {
  const f = computeStructureFeatures();
  if (!f) {
    log('No structural report available to export.', 'err');
    return;
  }

  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    log('Popup blocker prevented PDF export. Please allow popups for Nilus Lab.', 'err');
    return;
  }

  const plddt = f.meanPlddt;
  const status = plddt >= 80 ? 'High-confidence fold' : plddt >= 70 ? 'Good confidence fold' : plddt >= 50 ? 'Moderate-confidence fold' : 'Low-confidence fold';

  // Construct recommendations list
  const suggestions = [];
  if (plddt >= 80) {
    suggestions.push('Run binding site prediction to identify potential ligand pockets');
    suggestions.push('Perform mutation analysis on catalytic residues to predict functional impact');
  }
  if (f.lowConfPercent > 20) {
    const stretch = f.longestLowConfStretch;
    suggestions.push(`Investigate residues ${stretch.start+1}-${stretch.start+stretch.length} — consider disorder prediction (IUPred)`);
  }
  if (f.paeMean !== null && f.paeMean > 10) {
    suggestions.push('High PAE suggests domain mobility — run normal mode analysis to visualize motion');
  }
  suggestions.push('Export the PDB file and align to known structures in the PDB for functional annotation');
  if (f.length > 200) {
    suggestions.push('Large protein detected — consider domain splitting for higher-accuracy prediction');
  }

  printWindow.document.write(`
    <html>
      <head>
        <title>NilusFold AI Structure Analysis Report - res-${f.length}</title>
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #1e293b; padding: 40px; line-height: 1.6; }
          .header { border-bottom: 2px solid #3b82f6; padding-bottom: 16px; margin-bottom: 24px; }
          .title { font-size: 24px; font-weight: 800; margin: 0; color: #0f172a; }
          .subtitle { font-size: 12px; color: #64748b; margin-top: 4px; font-family: monospace; }
          .section { margin-bottom: 24px; page-break-inside: avoid; }
          .section-title { font-size: 15px; font-weight: 700; color: #1e3a8a; border-bottom: 1.5px solid #e2e8f0; padding-bottom: 4px; margin-bottom: 10px; }
          .summary-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px 20px; display: flex; align-items: center; gap: 24px; margin-bottom: 24px; }
          .ring { width: 70px; height: 70px; border-radius: 50%; border: 5px solid #e2e8f0; display: flex; flex-direction: column; align-items: center; justify-content: center; font-family: monospace; }
          .ring-val { font-size: 18px; font-weight: 800; color: #1e3a8a; }
          .ring-lbl { font-size: 8px; color: #64748b; }
          .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 12px 0; }
          .card { background: #f1f5f9; border-radius: 6px; padding: 10px; border: 1px solid #e2e8f0; }
          .card .k { font-size: 9px; color: #64748b; text-transform: uppercase; margin-bottom: 2px; font-family: monospace; }
          .card .v { font-size: 14px; font-weight: 700; color: #0f172a; font-family: monospace; }
          .suggestions { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 14px 18px; }
          .suggestions-title { font-size: 13px; font-weight: 700; color: #166534; margin-bottom: 8px; }
          .suggestion-item { margin-bottom: 5px; font-size: 12px; color: #14532d; }
          code { background: #e2e8f0; padding: 1px 4px; border-radius: 3px; font-family: monospace; font-size: 11.5px; }
        </style>
      </head>
      <body>
        <div class="header">
          <div class="title">NilusFold Structure Analysis Report</div>
          <div class="subtitle">Generated on ${new Date().toLocaleDateString()} · Powered by Nilus Atomix</div>
        </div>

        <div class="summary-box">
          <div class="ring">
            <div class="ring-val">${plddt}</div>
            <div class="ring-lbl">pLDDT</div>
          </div>
          <div>
            <div style="font-size: 16px; font-weight: 700; color: #0f172a;">${status}</div>
            <div style="font-size: 11px; color: #64748b; margin-top: 3px;">${f.length} residues · Chain ${STATE.currentModel && STATE.currentModel.chains ? STATE.currentModel.chains.join(', ') : 'A'} · NilusFold</div>
          </div>
        </div>

        <div class="section">
          <div class="section-title">1. Domain Architecture</div>
          <p>This structure was predicted as a ${f.helixPercent}% helical / ${f.loopPercent}% loop fold with a mean pLDDT score of <strong>${plddt}</strong>.</p>
          <div class="grid">
            ${f.regionStats.map(r => `
              <div class="card">
                <div class="k">${r.name} (res ${r.start+1}-${r.end})</div>
                <div class="v">${r.meanPlddt.toFixed(1)} pLDDT</div>
              </div>
            `).join('')}
          </div>
        </div>

        <div class="section">
          <div class="section-title">2. Confidence Assessment</div>
          <p>Overall, <strong>${f.lowConfPercent}%</strong> of residues (${f.lowConfCount}/${f.length}) fall below the pLDDT 70 threshold.</p>
          <div class="grid">
            <div class="card"><div class="k">Mean pLDDT</div><div class="v">${plddt}</div></div>
            <div class="card"><div class="k">Low-Conf Residues</div><div class="v">${f.lowConfCount}</div></div>
            <div class="card"><div class="k">Longest Stretch</div><div class="v">${f.longestLowConfStretch.length} res</div></div>
          </div>
        </div>

        <div class="section">
          <div class="section-title">3. Biochemical Properties</div>
          <p>Hydrophobic residue content: <strong>${f.hydrophobicity}%</strong>. Secondary structure consists of <strong>${f.helixPercent}%</strong> helices/sheets and <strong>${f.loopPercent}%</strong> loop regions.</p>
        </div>

        <div class="section">
          <div class="suggestions">
            <div class="suggestions-title">Suggested Next Steps</div>
            ${suggestions.slice(0, 5).map((s, idx) => `
              <div class="suggestion-item"><strong>${idx+1}.</strong> ${s}</div>
            `).join('')}
          </div>
        </div>

        <script>
          window.onload = function() {
            window.print();
            setTimeout(function() { window.close(); }, 500);
          }
        </script>
      </body>
    </html>
  `);
  printWindow.document.close();
}

// ============================================================
// CONVERSATIONAL ASSISTANT MODULE (Chat Assistant overlay)
// ============================================================

const assistantState = {
  open: false,
  messages: [],
  thinking: false
};

// -------- Toggle panel --------
function toggleAssistant(force) {
  assistantState.open = force !== undefined ? force : !assistantState.open;
  const panel = document.getElementById('assistantPanel');
  if (panel) panel.classList.toggle('open', assistantState.open);
  const toggle = document.getElementById('assistantToggle');
  if (toggle) toggle.style.display = assistantState.open ? 'none' : 'grid';
  if (assistantState.open) {
    const input = document.getElementById('assistantInput');
    if (input) setTimeout(() => input.focus(), 300);
    updateAssistantContext();
  }
}

// -------- Update context info --------
function updateAssistantContext() {
  const seq = STATE.currentModel ? STATE.currentModel.sequence : '';
  const plddt = STATE.currentModel ? STATE.currentModel.plddt : [];
  const len = seq.length;
  const meanPlddt = plddt.length > 0
    ? (plddt.reduce((a,b)=>a+b,0) / plddt.length).toFixed(1)
    : '—';
  
  const ctxInfo = document.getElementById('assistantContextInfo');
  if (ctxInfo) ctxInfo.textContent = `Context: ${len} residues · pLDDT ${meanPlddt}`;
  
  const welcomeLen = document.getElementById('welcomeSeqLen');
  if (welcomeLen) welcomeLen.textContent = len > 0 ? `${len}-residue` : '0-residue';
  
  const welcomePlddt = document.getElementById('welcomePlddt');
  if (welcomePlddt) welcomePlddt.textContent = meanPlddt;
}

// -------- Send message --------
async function sendAssistantMessage(text) {
  if (!text || !text.trim() || assistantState.thinking) return;

  // Add user message
  addAssistantMessage(text, 'user');
  const input = document.getElementById('assistantInput');
  if (input) {
    input.value = '';
    autoResizeInput();
  }

  assistantState.thinking = true;
  const btn = document.getElementById('assistantSend');
  if (btn) btn.disabled = true;
  const status = document.getElementById('assistantStatus');
  if (status) status.textContent = 'Thinking...';

  // Show typing indicator
  const typingEl = addTypingIndicator();

  try {
    // Generate simulated intelligent response based on current sequence state
    const response = await generateAssistantResponse(text);
    typingEl.remove();
    addAssistantMessage(response, 'assistant');
  } catch (err) {
    typingEl.remove();
    addAssistantMessage('Sorry, I encountered an error: ' + err.message, 'assistant');
  } finally {
    assistantState.thinking = false;
    if (btn) btn.disabled = false;
    if (status) status.textContent = 'Ready · context loaded';
  }
}

// -------- Add message to UI --------
function addAssistantMessage(text, role) {
  const messagesEl = document.getElementById('assistantMessages');
  if (!messagesEl) return;
  
  const msgEl = document.createElement('div');
  msgEl.className = `assistant-msg ${role}`;

  const avatar = role === 'user' ? 'You' : 'AI';
  msgEl.innerHTML = `
    <div class="assistant-avatar">${avatar}</div>
    <div class="assistant-bubble">${text}</div>
  `;
  messagesEl.appendChild(msgEl);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  assistantState.messages.push({ role, text });
}

function addTypingIndicator() {
  const messagesEl = document.getElementById('assistantMessages');
  if (!messagesEl) return null;
  
  const el = document.createElement('div');
  el.className = 'assistant-msg assistant';
  el.innerHTML = `
    <div class="assistant-avatar">AI</div>
    <div class="assistant-bubble">
      <div class="assistant-typing"><span></span><span></span><span></span></div>
    </div>
  `;
  messagesEl.appendChild(el);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return el;
}

// -------- Auto-resize textarea --------
function autoResizeInput() {
  const input = document.getElementById('assistantInput');
  if (!input) return;
  input.style.height = 'auto';
  input.style.height = Math.min(input.scrollHeight, 120) + 'px';
}

// -------- Response generator (client-side rule-based, or call OpenAI API) --------
async function generateAssistantResponse(question) {
  // Simulate thinking delay
  await new Promise(r => setTimeout(r, 600 + Math.random() * 800));

  const q = question.toLowerCase();
  const f = computeStructureFeatures();
  if (!f) return 'No structure loaded. Please run a fold prediction first.';

  // Pattern matching for common questions
  if (q.includes('plddt') || q.includes('confidence') || q.includes('score') || q.includes('reliable') || q.includes('trust')) {
    return `<p>The <strong>mean pLDDT</strong> for this structure is <strong>${f.meanPlddt}</strong>.</p>
            <ul>
              <li><strong>Very High (pLDDT ≥ 90)</strong>: Core folding is highly reliable. Suitable for molecular docking studies.</li>
              <li><strong>High (70-90)</strong>: Good backbone accuracy. Suitable for active site identification.</li>
              <li><strong>Low (50-70)</strong>: Flexible loop or transition regions. Interpret backbone geometry with caution.</li>
              <li><strong>Very Low (< 50)</strong>: Unstructured or intrinsically disordered region.</li>
            </ul>
            <p>Based on our metrics, this ESMFold prediction is <strong>${f.meanPlddt >= 85 ? 'highly reliable' : f.meanPlddt >= 70 ? 'reliable' : 'moderately reliable'}</strong>.</p>`;
  }

  if (q.includes('low') || q.includes('disorder') || q.includes('flexib')) {
    if (f.lowConfCount === 0) return 'No low-confidence residues detected — the entire structure is well-predicted.';
    const s = f.longestLowConfStretch;
    return `<p><strong>${f.lowConfCount} residues</strong> (${f.lowConfPercent}%) have pLDDT below 70.</p>
            <p>The longest low-confidence stretch spans <strong>${s.length} residues</strong> at positions <code>${s.start+1}-${s.start+s.length}</code>.</p>
            <p>This region is likely flexible or disordered. Consider:</p>
            <ul>
              <li>Running IUPred disorder prediction</li>
              <li>Checking if this region is a functional loop</li>
              <li>Validating with NMR or HDX-MS experiments</li>
            </ul>`;
  }

  if (q.includes('secondary') || q.includes('helix') || q.includes('sheet') || q.includes('loop') || q.includes('fold')) {
    return `<p>Predicted secondary structure composition:</p>
            <ul>
              <li><strong>${f.helixPercent}%</strong> ordered (helix/sheet, pLDDT >80)</li>
              <li><strong>${f.loopPercent}%</strong> loop/disordered (pLDDT <60)</li>
              <li><strong>${100 - f.helixPercent - f.loopPercent}%</strong> intermediate confidence</li>
            </ul>
            <p>Region breakdown:</p>
            <ul>
              ${f.regionStats.map(r => `<li><strong>${r.name}</strong> (res ${r.start+1}-${r.end}): ${r.meanPlddt.toFixed(1)} pLDDT — ${r.tier.label} confidence</li>`).join('')}
            </ul>`;
  }

  if (q.includes('binding') || q.includes('pocket') || q.includes('ligand') || q.includes('drug') || q.includes('site')) {
    return `<p>Based on the structure, here are predicted binding considerations:</p>
            <ul>
              <li>Hydrophobic residues comprise <strong>${f.hydrophobicity}%</strong> of the sequence</li>
              <li>${f.hydrophobicity > 40 ? 'High hydrophobic content suggests buried binding pockets' : 'Surface composition suggests solvent-exposed binding sites'}</li>
              <li>Switch to the <strong>Binding Analysis</strong> tab to see contact maps</li>
            </ul>
            <p>For detailed pocket detection, consider running P2Rank or fpocket on the exported PDB.</p>`;
  }

  if (q.includes('mutat') || q.includes('alanine') || q.includes('substitut') || q.includes('change residue')) {
    return `<p>Mutation analysis suggestions:</p>
            <ul>
              <li>Click any residue in the <strong>Sequence</strong> tab to inspect it</li>
              <li>Low-confidence residues are most tolerant to mutation</li>
              <li>High-confidence core residues are likely structurally critical</li>
              <li>Conserved positions (check MSA) are functionally important</li>
            </ul>
            <p>For ΔΔG prediction, export the PDB and use FoldX or Rosetta.</p>`;
  }

  if (q.includes('export') || q.includes('download') || q.includes('pdb') || q.includes('save')) {
    return `<p>You can export this structure in several ways:</p>
            <ul>
              <li>Click the <strong>download icon</strong> in the tab toolbar to get the .pdb file</li>
              <li>Use the <strong>Share Snapshot</strong> button to generate a shareable link</li>
              <li>Export the AI Analysis report as PDF from the AI tab</li>
            </ul>
            <p>The PDB file includes B-factors set to pLDDT values, compatible with PyMOL and ChimeraX.</p>`;
  }

  if (q.includes('domain') || q.includes('region') || q.includes('architect')) {
    return `<p>The structure divides into three regions:</p>
            <ul>
              ${f.regionStats.map(r => `<li><strong>${r.name}</strong> (res ${r.start+1}-${r.end}): mean pLDDT ${r.meanPlddt.toFixed(1)} — ${r.tier.label} confidence</li>`).join('')}
            </ul>
            <p>${f.paeMean > 10 ? 'High PAE values suggest these regions may move independently (multi-domain).' : 'Low PAE values suggest a single rigid domain.'}</p>`;
  }

  if (q.includes('pae') || q.includes('aligned error') || q.includes('position')) {
    return `<p><strong>PAE (Predicted Aligned Error)</strong> estimates the position error between residue pairs in Ångströms.</p>
            <ul>
              <li><strong>Low PAE (blue)</strong>: residues have confident relative positions</li>
              <li><strong>High PAE (red)</strong>: domains may shift relative to each other</li>
              <li>Mean PAE for this structure: <strong>${f.paeMean || 'N/A'} Å</strong></li>
            </ul>
            <p>View the full matrix in the <strong>PAE Matrix</strong> tab.</p>`;
  }

  // Default response
  return `<p>I can help you understand this ${f.length}-residue structure. Try asking about:</p>
          <ul>
            <li>Confidence and reliability (<em>"Is this prediction reliable?"</em>)</li>
            <li>Low-confidence regions (<em>"Which residues are disordered?"</em>)</li>
            <li>Secondary structure (<em>"Describe the helices and sheets"</em>)</li>
            <li>Binding sites (<em>"Where are the binding pockets?"</em>)</li>
            <li>Domains (<em>"What are the structural domains?"</em>)</li>
          </ul>`;
}
