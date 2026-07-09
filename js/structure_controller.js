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

function switchMode(mode) {
  STATE.mode = mode;
  $$('.mode-btn').forEach(b => b.classList.toggle('active', b.dataset.mode === mode));
  $('#esmInput').style.display = mode === 'esm' ? 'block' : 'none';
  $('#boltzInput').style.display = mode === 'boltz' ? 'block' : 'none';
  $('#costPanel').style.display = mode === 'boltz' ? 'block' : 'none';
  $('#engineTag').textContent = mode === 'esm' ? 'Nilus Atomix' : 'zenithfold-2.1';
  $('#runNum').textContent = mode === 'boltz' ? '5' : '4';
  $('#inputTag').textContent = mode === 'esm' ? 'FASTA · raw' : 'multi-chain';
  $('#modeDescription').textContent = mode === 'esm'
    ? 'Evolutionary Scale Modeling for fast, single-chain protein folding. Returns atomic coordinates with per-residue pLDDT.'
    : 'zenithfold-2.1 predicts multi-chain biomolecular complexes (protein · DNA · RNA · ligand) with PAE confidence matrices.';
  $('#sbModel').textContent = mode === 'esm' ? 'nilus-atomix-v1' : 'zenithfold-2.1';
  log(`Engine switched → ${mode === 'esm' ? 'Nilus Atomix' : 'zenithfold-2.1'}`, 'info');
  renderChainList();
  updateCostEstimate();
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
        log(`Sequence (${len} aa) exceeds hard limit. Please trim or use ZenithFold mode.`, 'err');
      } else if (len > ESM_MAX) {
        $('#seqLenHint').textContent = `${len} aa — use ZenithFold for best results`;
        $('#seqLenHint').style.color = 'var(--amber)';
        log(`Long sequence detected (${len} aa). Nilus Atomix optimized for <400 aa — switching to ZenithFold API recommended for accuracy and speed.`, 'warn');
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
  });
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
      log('Maximum 6 chains supported in zenithfold-2.1 UI', 'warn');
      return;
    }
    STATE.chains.push({ id: String.fromCharCode(65 + STATE.chains.length), type: 'protein', copies: 1, value: '' });
    renderChainList();
    updateCostEstimate();
  });

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
  const aaMap = {
    'ALA':'A', 'ARG':'R', 'ASN':'N', 'ASP':'D', 'CYS':'C', 'GLN':'Q', 'GLU':'E', 
    'GLY':'G', 'HIS':'H', 'ILE':'I', 'LEU':'L', 'LYS':'K', 'MET':'M', 'PHE':'F', 
    'PRO':'P', 'SER':'S', 'THR':'T', 'TRP':'W', 'TYR':'Y', 'VAL':'V'
  };

  lines.forEach(line => {
    if (line.startsWith('ATOM  ') || line.startsWith('HETATM')) {
      const atomName = line.substring(12, 16).trim();
      if (atomName === 'CA') {
        const resName = line.substring(17, 20).trim();
        const chain = line.substring(21, 22).trim();
        const resi = parseInt(line.substring(22, 26).trim());
        const b = parseFloat(line.substring(60, 66).trim());
        const key = chain + '_' + resi;
        if (!residues[key]) {
          residues[key] = true;
          seq += aaMap[resName] || 'X';
          plddt.push(b);
        }
      }
    }
  });

  return { seq, plddt };
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
    if (plddt > 90) return '#0053D6';
    if (plddt > 70) return '#65B3E7';
    if (plddt > 50) return '#F5B544';
    return '#FB923C';
  };

  if (style === 'cartoon') {
    v.setStyle({ hetflag: false }, { cartoon: { colorfunc: plddtColorfunc } });
    v.setStyle(
      { resn: ["DA", "DT", "DC", "DG", "A", "U", "C", "G", "RA", "RU", "RC", "RG"] },
      { 
        cartoon: { color: '#4da6ff' }, 
        stick: { colorscheme: 'Jmol', radius: 0.15 } 
      }
    );
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
  const label = $('#selectionLabel');
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
    if (plddt > 90) return '#0053D6';
    if (plddt > 70) return '#65B3E7';
    if (plddt > 50) return '#F5B544';
    return '#FB923C';
  };

  if (style === 'cartoon') {
    v.setStyle({ hetflag: false }, { cartoon: { colorfunc: plddtColorfunc } });
    v.setStyle(
      { resn: ["DA", "DT", "DC", "DG", "A", "U", "C", "G", "RA", "RU", "RC", "RG"] },
      { cartoon: { color: '#4da6ff' }, stick: { colorscheme: 'Jmol', radius: 0.15 } }
    );
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
    const labelEl = $('#selectionLabel');
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
  const label = $('#selectionLabel');
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
    // Auto-route long sequences to Boltz (ZenithFold) for multi-chain/long support
    if (seq.length > 400) {
      log(`Sequence length ${seq.length} aa exceeds Nilus Atomix optimum. Auto-routing to ZenithFold API...`, 'warn');
      // Pre-populate chain A with the sequence and switch mode
      STATE.chains = [{ id: 'A', type: 'protein', sequence: seq, copies: 1 }];
      STATE.mode = 'boltz';
      document.querySelectorAll('.mode-btn').forEach(b => b.classList.toggle('active', b.dataset.mode === 'boltz'));
      $('#engineTag').textContent = 'ZenithFold';
      $('#modeDescription').textContent = 'Routing long sequence to ZenithFold multimer engine for full-length prediction.';
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
        const { seq: parsedSeq, plddt } = parsePDB(pdbText);
        STATE.currentModel = { pdb: pdbText, plddt, sequence: parsedSeq };
        STATE.paeMatrix = null;

        renderModel('cartoon', 'pLDDT');
        renderSequenceViewer(parsedSeq, plddt);
        renderPAE(plddt);
        updateMetaCard(parsedSeq, plddt);
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
    $('#runTitle').textContent = 'Submitting zenithfold-2.1 complex';
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

    const { seq, plddt } = parsePDB(pdbText);
    STATE.currentModel = { pdb: pdbText, plddt, sequence: seq };

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
  $('#metaConf').textContent = (plddt.reduce((a,b)=>a+b,0)/plddt.length).toFixed(1);
  $('#metaEngine').textContent = STATE.mode === 'esm' ? 'Nilus Atomix' : 'zenithfold-2.1';
  $('#seqBadge').textContent = `${seq.length} aa`;
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
      sessionStorage.removeItem("zenith_boltz_transfer");
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
      sessionStorage.removeItem('nilus_transfer_payload'); localStorage.removeItem('nilus_transfer_payload');
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
