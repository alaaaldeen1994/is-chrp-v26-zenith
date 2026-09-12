'use strict';

const { downloadArtifact, getPrediction } = require('./boltz-client');

function requestError(message,statusCode=400){return Object.assign(new Error(message),{statusCode});}
function detectStructureFormat(text,url=''){
  const lower=String(url).toLowerCase();
  if(lower.includes('.pdb'))return'pdb';
  if(lower.includes('.cif')||lower.includes('.mmcif'))return'cif';
  return /^(ATOM  |HETATM|HEADER|MODEL )/m.test(String(text||'').slice(0,5000))?'pdb':'cif';
}
function structureUrl(sample){return sample?.structure?.url||'';}
function sampleMetricSignature(sample){
  const m=sample?.metrics||{};
  return ['structure_confidence','complex_plddt','ptm','iptm','complex_iplddt','complex_ipde','complex_pde','ligand_iptm','protein_iptm']
    .map(k=>{const v=Number(m[k]);return Number.isFinite(v)?v.toPrecision(12):'';}).join('|');
}
function resolveSample(prediction,requestedIndex){
  const all=Array.isArray(prediction?.output?.all_sample_results)?prediction.output.all_sample_results:[];
  const best=prediction?.output?.best_sample||null; const bestUrl=structureUrl(best);
  let bestIndex=bestUrl?all.findIndex(s=>structureUrl(s)===bestUrl):-1;
  if(bestIndex<0&&best){const sig=sampleMetricSignature(best);if(sig.replace(/\|/g,''))bestIndex=all.findIndex(s=>sampleMetricSignature(s)===sig);}
  if(requestedIndex!==undefined&&requestedIndex!==null&&requestedIndex!==''){
    const index=Number(requestedIndex); if(!Number.isInteger(index)||index<0||index>=all.length)throw requestError(`sampleIndex must be between 0 and ${Math.max(0,all.length-1)}.`);
    return {sample:all[index],sampleIndex:index,bestIndex,isBest:index===bestIndex};
  }
  return {sample:best,sampleIndex:bestIndex>=0?bestIndex:null,bestIndex,isBest:true};
}
async function loadPredictionStructure(id,sampleIndex){
  if(!id)throw requestError('Prediction ID is required.');
  const prediction=await getPrediction(id);
  if(prediction.status!=='succeeded')throw requestError(`Prediction status is ${prediction.status||'unknown'}.`,409);
  const resolved=resolveSample(prediction,sampleIndex); const artifact=resolved.sample?.structure;
  if(!artifact?.url)throw requestError('Boltz result does not expose a structure URL for the requested sample.',404);
  const downloaded=await downloadArtifact(artifact.url,{maxBytes:35*1024*1024,timeoutMs:60_000});
  const structure=downloaded.buffer.toString('utf8');
  return {prediction,structure,format:detectStructureFormat(structure,artifact.url),metrics:resolved.sample?.metrics||null,sampleIndex:resolved.sampleIndex,bestIndex:resolved.bestIndex,isBest:resolved.isBest};
}
module.exports={resolveSample,loadPredictionStructure,detectStructureFormat};
