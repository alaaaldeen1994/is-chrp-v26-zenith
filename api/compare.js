'use strict';

const { loadPredictionStructure } = require('../lib/prediction-source');
const { parseStructure, compareProteinStructures } = require('../lib/structure-analysis');

function json(res,status,payload){res.statusCode=status;res.setHeader('content-type','application/json; charset=utf-8');res.setHeader('cache-control','no-store, max-age=0');res.end(JSON.stringify(payload));}
async function readBody(req){if(req.body&&typeof req.body==='object'&&!Buffer.isBuffer(req.body))return req.body;const chunks=[];for await(const c of req)chunks.push(c);const t=Buffer.concat(chunks).toString('utf8');return t?JSON.parse(t):{};}
function bad(msg,statusCode=400){return Object.assign(new Error(msg),{statusCode});}
async function fetchText(url,timeout=20000){const r=await fetch(url,{headers:{accept:'text/plain,chemical/x-cif,application/json;q=0.9,*/*;q=0.8'},signal:AbortSignal.timeout(timeout)});if(!r.ok)throw bad(`Reference source returned HTTP ${r.status}.`,502);return r.text();}
async function alphaFoldReference(accession){
  const acc=String(accession||'').trim().toUpperCase(); if(!/^[A-Z0-9][A-Z0-9-]{4,19}$/.test(acc))throw bad('A valid UniProt accession is required for AlphaFold DB comparison.');
  const metaR=await fetch(`https://alphafold.ebi.ac.uk/api/prediction/${encodeURIComponent(acc)}`,{headers:{accept:'application/json'},signal:AbortSignal.timeout(15000)});
  if(metaR.status===404)throw bad('No AlphaFold DB prediction was found for this accession.',404); if(!metaR.ok)throw bad(`AlphaFold DB returned HTTP ${metaR.status}.`,502);
  const arr=await metaR.json(); const e=Array.isArray(arr)?(arr.find(x=>String(x?.uniprotAccession||'').toUpperCase()===acc)||arr[0]):null; if(!e)throw bad('AlphaFold DB returned no usable prediction record.',404);
  const url=e.cifUrl||e.pdbUrl; if(!url)throw bad('AlphaFold DB did not expose coordinates for this entry.',502);
  const structure=await fetchText(url); return {structure,format:String(url).toLowerCase().includes('.pdb')?'pdb':'cif',chain:null,metadata:{source:'AlphaFold DB',accession:acc,entry_id:e.entryId||e.modelEntityId||null,version:e.latestVersion??null,model_created_at:e.modelCreatedDate||null,source_url:e.entryId?`https://alphafold.ebi.ac.uk/entry/${encodeURIComponent(e.entryId)}`:null}};
}
async function pdbReference(pdbId,chain){
  const id=String(pdbId||'').trim().toUpperCase(); if(!/^[0-9][A-Z0-9]{3}$/.test(id))throw bad('A valid four-character PDB ID is required.');
  const structure=await fetchText(`https://files.rcsb.org/download/${encodeURIComponent(id)}.cif`);
  let metadata={source:'RCSB PDB',pdb_id:id,chain:chain||null,source_url:`https://www.rcsb.org/structure/${encodeURIComponent(id)}`};
  try{const r=await fetch(`https://data.rcsb.org/rest/v1/core/entry/${encodeURIComponent(id)}`,{headers:{accept:'application/json'},signal:AbortSignal.timeout(10000)});if(r.ok){const e=await r.json();metadata={...metadata,title:e?.struct?.title||null,experimental_method:e?.exptl?.map(x=>x.method).filter(Boolean).join('; ')||null,resolution_angstrom:Array.isArray(e?.rcsb_entry_info?.resolution_combined)?e.rcsb_entry_info.resolution_combined[0]??null:null,release_date:e?.rcsb_accession_info?.initial_release_date||null};}}catch{}
  return {structure,format:'cif',chain:chain?String(chain):null,metadata};
}

module.exports=async function handler(req,res){
  if(req.method!=='POST')return json(res,405,{error:'Use POST /api/compare.'});
  try{
    const body=await readBody(req); const id=body.prediction_id; const sample=body.sample_index; const ref=body.reference||{};
    if(!id)throw bad('prediction_id is required.');
    const mobileRaw=await loadPredictionStructure(id,sample); const mobile=parseStructure(mobileRaw.structure,mobileRaw.format);
    let referenceRaw; if(ref.type==='alphafold')referenceRaw=await alphaFoldReference(ref.accession); else if(ref.type==='pdb')referenceRaw=await pdbReference(ref.pdb_id,ref.chain); else throw bad('reference.type must be alphafold or pdb.');
    const reference=parseStructure(referenceRaw.structure,referenceRaw.format);
    const comparison=compareProteinStructures(mobile,reference,{mobileChain:body.mobile_chain||null,referenceChain:ref.chain||null});
    const payload={available:true,prediction_id:id,sample_index:mobileRaw.sampleIndex,reference:referenceRaw.metadata,comparison,scientific_note:'Structural agreement quantifies coordinate similarity. AlphaFold DB is a computational reference, not experimental validation. PDB concordance is structural agreement with a deposited experimental model and does not by itself prove biological function.'}; if(body.include_coordinates===true){payload.coordinates={mobile:{structure:mobileRaw.structure,format:mobileRaw.format},reference:{structure:referenceRaw.structure,format:referenceRaw.format}};} return json(res,200,payload);
  }catch(error){return json(res,Number(error?.statusCode)||500,{error:error?.message||'Unable to compare structures.'});}
};
