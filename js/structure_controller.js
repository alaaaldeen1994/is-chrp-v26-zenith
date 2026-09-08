const CANONICAL_SEQS = {
  sirt1: `>SIRT1_HUMAN (Sirtuin 1, 747 aa)\nMADEAALALQPGGSPSAAGADREAASSPAGEPLRKRPRRDGPGLERSPGEPGGAAPEREVPAAARGCPGAAAAALWREAEAEAAAAGGEQEAQATAAAGEGDNGPGLQGPSREPPLADNLYDEDDDDEGEEEEEAAAAAIGYRDNLLFGDEIITNGFHSCESDEEDRASHASSSDWTPRPRIGPYTFVQQHLMIGTDPRTILKDLLPETIPPPELDDMTLWQIVINILSEPPKRKKRKDINTIEDAVKLLQECKKIIVLTGAGVSVSCGIPDFRSRDGIYARLAVDFPDLPDPQAMFDIEYFRKDPRPFFKFAKEIYPGQFQPSLCHKFIALSDKEGKLLRNYTQNIDTLEQVAGIQRIIQCHGSFATASCLICKYKVDCEAVRGDIFNQVVPRCPRCPADEPLAIMKPEIVFFGENLPEQFHRAMKYDKDEVDLLIVIGSSLKVRPVALIPSSIPHEVPQILINREPLPHLHFDVELLGDCDVIINELCHRLGGEYAKLCCNPVKLSEITEKPPRTQKELAYLSELPPTPLHVSEDSSSPERTSPPDSSVIVTLLDQAAKSNDDLDVSESKGCMEEKPQEVQTSRNVESIAEQMENPDLKNVGSSTGEKNERTSVAGTVRKCWPNRVAKEQISRRLDGNQYLFLPPNRYIFHGAEVYSDSEDDVLSSSSCGSNSDSGTCQSPSLEEPMEDESEIEEFYNGLEDEPDVPERAGGAGFGTDGDDQEAINEAISVKQEVTDMNYPSNKS`,
  tp53: `>TP53_HUMAN (Cellular tumor antigen p53, 393 aa)\nMEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQWFTEDPGPDEAPRMPEAAPPVAPAPAAPTPAAPAPAPSWPLSSSVPSQKTYQGSYGFRLGFLHSGTAKSVTCTYSPALNKMFCQLAKTCPVQLWVDSTPPPGTRVRAMAIYKQSQHMTEVVRRCPHHERCSDSDGLAPPQHLIRVEGNLRVEYLDDRNTFRHSVVVPYEPPEVGSDCTTIHYNYMCNSSCMGGMNRRPILTIITLEDSSGNLLGRNSFEVRVCACPGRDRRTEEENLRKKGEPHHELPPGSTKRALPNNTSSSPQPKKKPLDGEYFTLQIRGRERFEMFRELNEALELKDAQAGKEPGGSRAHSSHLKSKKGQSTSRHKKLMFKTEGPDSD`,
  brca1: `>BRCA1_HUMAN (Breast cancer type 1 susceptibility protein, 1863 aa)\nMDLSALRVEEVQNVINAMQKILECPICLELIKEPVSTKCDHIFCKFCMLKLLNQKKGPSQCPLCKNDITKRSLQESTRFSQLVEELLKIICAFQLDTGLEYANSYNFAKKENNSPEHLKDEVSIIQSMGYRNRAKRLLQSEPENPSLQETSLSVQLSNLGTVRTLRTKQRIQPQKTSVYIELGSDSSEDTVNKATYCSVGDQELLQITPQGTRDEISLDSKKAACEFSETDVTNTEHHQPSNNDVDNTCPNLPEEKNVLVNQCKKNENILKADADISLEKVSPRNKKVKELKNKEKNLKEVTKDLGKNKDTLKKNLKDVKDVTKDGKNKDTLKKNLKDVKEVTKDGKNKDTLKKNLKDVKEVTKDGKNKDTLKKNLKDVKEVTKDGKNKDTLKKNLKDVKEVTKDGKNKDTLKKNLKDVK`,
  ace2: `>ACE2_HUMAN (Angiotensin-converting enzyme 2, 805 aa)\nMSSSSWLLLSLVAVTAAQSTIEEQAKTFLDKFNHEAEDLFYQSSLASWNYNTNITEENVQNMNNAGDKWSAFLKEQSTLAQMYPLQEIQNLTVKLQLQALQQNGSSVLSEDKSKRLNTILNTMSTIYSTGKVCNPDNPQECLLLEPGLNEIMANSLDYNERLWAWESWRSEVGKQLRPLYEEYVVLKNEMARANHYEDYGDYWRGDYEVNGVDGYDYSRGQLIEDVEHTFEEIKPLYEHLHAYVRAKLMNAYPSYISPIGCLPAHLLGDMWGRFWTNLYSLTVPFGQKPNIDVTDAMVDQAWDAQRIFKEAEKFFVSVGLPNMTQGFWENSMLTDPGNVQKAVCHPTAWDLGKGDFRILMCTKVTMDDFLTAHHEMGHIQYDMAYAAQPFLLRNGANEGFHEAVGEIMSLSAATPKHLKSIGLLSPDFQEDNETEINFLLKQALTIVGTLPFTYMLEKWRWMVFRGEIPKEQWMKKWWEMKREIVGVVEPVPHDETYCDPASLFHVSNDYSFIRYYTRTLYQFQFQEALCQAAKHEGPLHKCDISNSTEAGQKLFNMLRLGKSEPWTLALENVVGAKNMNVRPLLNYFEPLFTWLKDQNKNSFVGWSTDWSPYADQSIKVRISLKSALGDKAYEWNDNEMYLFRSSVAYAMRQYFLKVKNQMILFGEEDVRVANLKPRISFNFFVTAPKNVSDIIPRTEVEKAIRMSRSRINDAFRLNDNSLEFLGIQPTLGPPNQPPVSIWLIVFGVVMGVIVVGIVILIFTGIRDRKKKNKARSGENPYASIDISKGENNPGFQNTDDVQTSF`
};

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

  // Hide credentials panel — not required in either mode currently (future use)
  // Panel numbering: ESM = 1 Engine, 2 Input, 3 Execute
  //                  Boltz = 1 Engine, 2 Input, 3 Pre-flight, 4 Execute
  const inputPanelNum = document.getElementById('inputPanelNum');
  if (inputPanelNum) inputPanelNum.textContent = '2';

  $('#runNum').textContent = mode === 'boltz' ? '4' : '3';
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
  const saveBtn = $('#apiSaveBtn');
  if (saveBtn) saveBtn.addEventListener('click', () => {
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

  document.getElementById(resultId)?.classList.add('hidden');
  document.getElementById(errorId)?.classList.add('hidden');

  const btn = document.getElementById(fetchBtn);
  const origBtnHTML = btn ? btn.innerHTML : '';
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<span class="uniprot-spinner"></span> Fetching...';
  }

  let data = null;

  try {
    try {
      const r = await fetch(`/api/uniprot-lookup?gene=${encodeURIComponent(gene)}`, {
        signal: AbortSignal.timeout(6000)
      });
      if (r.ok) {
        const json = await r.json();
        if (json && json.sequence) data = json;
      }
    } catch (_) {}

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

    if (!data || !data.sequence) {
      const msgEl = document.getElementById(errorMsg);
      if (msgEl) msgEl.textContent =
        `"${gene}" not found in UniProt Swiss-Prot (Homo sapiens). ` +
        `Try the official HGNC gene symbol (e.g. POU5F1 for OCT4, TP53 for p53).`;
      document.getElementById(errorId)?.classList.remove('hidden');
      log(`UniProt: no reviewed entry for "${gene}"`, 'warn');
      return;
    }

    document.getElementById(geneEl).textContent = data.gene || gene;
    document.getElementById(accEl).textContent  = data.accession || '';
    document.getElementById(lenEl).textContent  = `${data.sequence_length} aa`;
    document.getElementById(nameEl).textContent =
      (data.protein_name || '') + (data.subcellular_location ? ` · ${data.subcellular_location}` : '');
    document.getElementById(funcEl).textContent = data.function || '';
    document.getElementById(resultId)?.classList.remove('hidden');

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
  if (!ta) return;
  ta.addEventListener('input', () => {
    const raw = ta.value;
    const cleanSeq = raw.replace(/^>.*\n/, '').replace(/[^A-Za-z]/g, '').toUpperCase();
    const len = cleanSeq.length;
    STATE.sequence = cleanSeq;
    const lenText = $('#seqLenText');
    if (lenText) lenText.textContent = `${len} amino acids`;
    const badge = $('#seqValidationBadge');
    if (badge) {
      if (len === 0) badge.innerHTML = '<span style="color:#64748B;">Empty</span>';
      else {
        const invalidChars = cleanSeq.replace(/[ACDEFGHIKLMNPQRSTVWY]/g, '');
        badge.innerHTML = invalidChars.length === 0
          ? '<span style="color:#10B981;font-weight:600;">&#x25CF; Valid AA</span>'
          : `<span style="color:#EF4444;font-weight:600;">&#x25CF; ${invalidChars.length} non-standard AA</span>`;
      }
    }
  });

  const loadExBtn = $('#loadExampleBtn');
  if (loadExBtn) {
    loadExBtn.addEventListener('click', () => {
      const emptyOverlay = document.getElementById('viewerEmptyPlaceholder');
      if (emptyOverlay) emptyOverlay.style.display = 'none';
      const stageTL = document.getElementById('stageTopLeft');
      if (stageTL) stageTL.style.display = 'flex';
      const stageTR = document.getElementById('stageTopRight');
      if (stageTR) stageTR.style.display = 'flex';
      const stageFB = document.getElementById('stageFloatingBar');
      if (stageFB) stageFB.style.display = 'flex';
      const dlBtn = document.getElementById('downloadBtn');
      if (dlBtn) { dlBtn.style.opacity = '1'; dlBtn.style.pointerEvents = 'auto'; }
      const shareBtn = document.getElementById('shareBtn');
      if (shareBtn) { shareBtn.style.opacity = '1'; shareBtn.style.pointerEvents = 'auto'; }
      const badge = document.getElementById('instTargetBadge');
      if (badge) {
        badge.textContent = 'Completed'; badge.className = 'inst-badge-status completed';
        badge.style.background = 'rgba(16, 185, 129, 0.15)';
        badge.style.borderColor = 'rgba(16, 185, 129, 0.35)';
        badge.style.color = '#10B981';
      }
      window.loadPreset('SIRT1_HUMAN');
    });
  }

  const clrBtn = $('#clearBtn');
  if (clrBtn) clrBtn.addEventListener('click', () => { ta.value = ''; ta.dispatchEvent(new Event('input')); });

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
  if (!list) return;
  list.innerHTML = '';
  STATE.chains.forEach((c, idx) => {
    const wrapper = document.createElement('div');
    wrapper.style.cssText = 'background:rgba(0,0,0,0.3);border:1px solid #1E293B;border-radius:9px;overflow:hidden;';
    const headerRow = document.createElement('div');
    headerRow.style.cssText = 'display:flex;align-items:center;gap:7px;padding:8px 10px;';
    headerRow.innerHTML = `
      <div style="width:28px;height:28px;border-radius:7px;background:#3B82F6;color:white;display:grid;place-items:center;font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:700;flex-shrink:0">${c.id}</div>
      <select class="chain-type-select chain-type" style="flex:1;min-width:0;background:rgba(0,0,0,0.4);border:1px solid #1E293B;border-radius:7px;color:#E2E8F0;padding:6px 22px 6px 9px;font-size:11px;font-family:'JetBrains Mono',monospace;appearance:none;-webkit-appearance:none;background-image:url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='9' height='9' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2.5'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E\");background-repeat:no-repeat;background-position:right 7px center;outline:none;cursor:pointer;">
        <option value="protein" ${c.type==='protein'?'selected':''}>Protein</option>
        <option value="dna" ${c.type==='dna'?'selected':''}>DNA</option>
        <option value="rna" ${c.type==='rna'?'selected':''}>RNA</option>
        <option value="ligand_ccd" ${c.type==='ligand_ccd'?'selected':''}>Ligand (CCD)</option>
        <option value="ligand_smiles" ${c.type==='ligand_smiles'?'selected':''}>Ligand (SMILES)</option>
      </select>
      <span style="font-size:11px;color:#94A3B8;margin-right:2px;user-select:none;">copies:</span>
      <input class="chain-copies-input chain-copies" type="number" min="1" max="8" value="${c.copies}" style="width:40px;flex-shrink:0;background:rgba(0,0,0,0.4);border:1px solid #1E293B;border-radius:7px;color:#E2E8F0;padding:6px 4px;font-size:11px;font-family:'JetBrains Mono',monospace;text-align:center;outline:none;" />
      <button class="chain-del" style="width:26px;height:26px;flex-shrink:0;border-radius:6px;border:none;background:transparent;color:#475569;cursor:pointer;display:grid;place-items:center;transition:all 0.1s;" title="Remove chain"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg></button>`;
    wrapper.appendChild(headerRow);
    const valRow = document.createElement('div');
    valRow.style.cssText = 'padding:0 10px 10px 10px;';
    if (c.type === 'ligand_ccd') {
      valRow.innerHTML = `<select class="chain-val" style="width:100%;background:rgba(0,0,0,0.4);border:1px solid #1E293B;border-radius:7px;color:#E2E8F0;padding:7px 24px 7px 9px;font-size:10.5px;font-family:'JetBrains Mono',monospace;appearance:none;outline:none;cursor:pointer;">
        <option value="">-- Select Ligand --</option><option value="MG" ${c.value==='MG'?'selected':''}>MG — Magnesium</option><option value="ZN" ${c.value==='ZN'?'selected':''}>ZN — Zinc</option><option value="CA" ${c.value==='CA'?'selected':''}>CA — Calcium</option><option value="ATP" ${c.value==='ATP'?'selected':''}>ATP</option><option value="ADP" ${c.value==='ADP'?'selected':''}>ADP</option><option value="HEM" ${c.value==='HEM'?'selected':''}>HEM — Heme</option></select>`;
    } else {
      valRow.innerHTML = `<textarea class="chain-val" rows="2" placeholder="Sequence or SMILES" style="width:100%;background:rgba(0,0,0,0.4);border:1px solid #1E293B;border-radius:7px;color:#E2E8F0;padding:7px 10px;font-family:'JetBrains Mono',monospace;font-size:10.5px;line-height:1.5;resize:vertical;min-height:50px;outline:none;display:block;">${c.value || ''}</textarea>`;
    }
    wrapper.appendChild(valRow);
    headerRow.querySelector('.chain-type').addEventListener('change', e => { STATE.chains[idx].type = e.target.value; STATE.chains[idx].value = ''; renderChainList(); updateCostEstimate(); });
    const valEl = wrapper.querySelector('.chain-val');
    if (valEl) {
      valEl.addEventListener('input', e => { STATE.chains[idx].value = e.target.value.trim().replace(/\s/g,''); updateCostEstimate(); });
      valEl.addEventListener('change', e => { STATE.chains[idx].value = e.target.value.trim().replace(/\s/g,''); updateCostEstimate(); });
    }
    headerRow.querySelector('.chain-copies').addEventListener('input', e => { STATE.chains[idx].copies = parseInt(e.target.value)||1; updateCostEstimate(); });
    headerRow.querySelector('.chain-del').addEventListener('click', () => { STATE.chains.splice(idx,1); STATE.chains.forEach((cc,i)=>cc.id=String.fromCharCode(65+i)); renderChainList(); updateCostEstimate(); });
    list.appendChild(wrapper);
  });
}

function initChainBuilder() {
  const addBtn = $('#addChainBtn');
  if (addBtn) addBtn.addEventListener('click', () => {
    if (STATE.chains.length >= 6) { log('Maximum 6 chains supported in NilusFold UI', 'warn'); return; }
    STATE.chains.push({ id: String.fromCharCode(65 + STATE.chains.length), type: 'protein', copies: 1, value: '' });
    renderChainList(); updateCostEstimate();
  });
  const clearChainsBtn = document.getElementById('clearChainsBtn');
  if (clearChainsBtn) clearChainsBtn.addEventListener('click', () => {
    STATE.chains = [{ id:'A', type:'protein', copies:1, value:'' }];
    renderChainList(); updateCostEstimate();
    const ta = document.getElementById('seqInput');
    if (ta) { ta.value=''; ta.dispatchEvent(new Event('input')); }
    log('Chains reset to default empty protein chain and simple input cleared','info');
  });
  const boltzFetchBtn = document.getElementById('boltz-uniprot-fetch-btn');
  if (boltzFetchBtn) boltzFetchBtn.addEventListener('click', () => uniprotLookupForStructure('boltz'));
  const boltzInput = document.getElementById('boltz-uniprot-input');
  if (boltzInput) boltzInput.addEventListener('keydown', e => { if (e.key==='Enter') { e.preventDefault(); uniprotLookupForStructure('boltz'); } });
  const boltzUseBtn = document.getElementById('boltz-uniprot-use-btn');
  if (boltzUseBtn) boltzUseBtn.addEventListener('click', () => uniprotUseSequence('boltz'));
  const typeSelect = document.getElementById('boltz-binding-type');
  if (typeSelect) typeSelect.addEventListener('change', function() { const row=document.getElementById('boltz-binder-chain-row'); if(row) row.classList.toggle('hidden',this.value==='none'); });
  const valBtn = $('#validateBtn');
  if (valBtn) valBtn.addEventListener('click', boltzValidate);
}

function parsePDB(pdbText) {
  const lines = pdbText.split('\n');
  let seq = '';
  const plddt = [];
  const residues = {};
  const chains = new Set();
  const aaMap = {'ALA':'A','ARG':'R','ASN':'N','ASP':'D','CYS':'C','GLN':'Q','GLU':'E','GLY':'G','HIS':'H','ILE':'I','LEU':'L','LYS':'K','MET':'M','PHE':'F','PRO':'P','SER':'S','THR':'T','TRP':'W','TYR':'Y','VAL':'V','DA':'a','DT':'t','DC':'c','DG':'g','A':'a','T':'t','C':'c','G':'g','U':'u','RA':'a','RU':'u','RC':'c','RG':'g'};
  lines.forEach(line => {
    if (line.startsWith('ATOM  ') || line.startsWith('HETATM')) {
      const atomName = line.substring(12,16).trim();
      if (atomName==='CA' || atomName==="C4'" || atomName==='P') {
        const resName=line.substring(17,20).trim(); const chain=line.substring(21,22).trim(); const resi=parseInt(line.substring(22,26).trim()); let b=parseFloat(line.substring(60,66).trim()); if(isNaN(b)) b=80.0;
        const key=chain+'_'+resi;
        if(!residues[key]) { residues[key]=true; seq += aaMap[resName] || 'X'; plddt.push(b); if(chain) chains.add(chain); }
      }
    }
  });
  const maxP=Math.max(...plddt,0); const finalPlddt=(maxP>0&&maxP<=1.0)?plddt.map(v=>Math.round(v*1000)/10):plddt;
  return {seq,plddt:finalPlddt,chains:Array.from(chains).sort()};
}

function updateCostEstimate() {
  if (STATE.mode !== 'boltz') return;
  const totalRes=STATE.chains.reduce((s,c)=>{ if(c.type.startsWith('ligand')) return s; return s+(c.value?c.value.length:120)*c.copies; },0);
  const gpuMin=Math.ceil(totalRes/80), credits=Math.ceil(gpuMin*1.7), eta=Math.ceil(gpuMin*35+12);
  $('#costGpu').innerHTML=`${gpuMin}<span class="unit">min</span>`; $('#costCredits').innerHTML=`${credits}<span class="unit">cr</span>`; $('#costRes').textContent=totalRes; $('#costEta').innerHTML=`${eta}<span class="unit">s</span>`; STATE.boltzEstimatedCost=(gpuMin*0.12).toFixed(2);
}

async function boltzValidate() {
  const btn=$('#validateBtn'); btn.disabled=true; btn.innerHTML='Validating...';
  const manifest=boltzBuildManifest();
  try { const resp=await fetch('/api/v1/structure/boltz/validate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({manifest})}); const data=await resp.json(); STATE.boltzValidated=!!data.valid; if(data.valid) log('Validation completed successfully','ok'); else log('Validation failed: '+data.errors.join(' | '),'err'); }
  catch(e){ log('Validation failed: '+e.message,'err'); STATE.boltzValidated=false; }
  finally { btn.disabled=false; btn.innerHTML='Validate Input'; }
}

function boltzBuildManifest() {
  const manifestChains = (STATE.chains || []).filter(c => c.value && c.value.trim().length > 0);
  const entities = manifestChains.map(c => ({
    type: c.type,
    value: c.value,
    chain_ids: [c.id]
  }));
  const bindingType = document.getElementById('boltz-binding-type').value;
  let manifest = { entities };
  if (bindingType !== 'none') {
    let binderId = document.getElementById('boltz-binder-chain-id').value.trim();
    if (!binderId) {
      const proteinChain = manifestChains.find(c => c.type === 'protein');
      binderId = proteinChain ? proteinChain.id : 'A';
    }
    const binding = { type: bindingType };
    binding.binder_chain_id = binderId;
    binding.binder_chain_ids = [binderId];
    manifest.binding = binding;
  }
  return manifest;
}

/* NOTE: remainder of controller preserved from main in repository update */
