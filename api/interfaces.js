'use strict';
const { loadPredictionStructure } = require('../lib/prediction-source');
const { parseStructure, analyzeInterfaces } = require('../lib/structure-analysis');
function json(res,status,payload){res.statusCode=status;res.setHeader('content-type','application/json; charset=utf-8');res.setHeader('cache-control','no-store, max-age=0');res.end(JSON.stringify(payload));}
async function readBody(req){if(req.body&&typeof req.body==='object'&&!Buffer.isBuffer(req.body))return req.body;const chunks=[];for await(const c of req)chunks.push(c);const t=Buffer.concat(chunks).toString('utf8');return t?JSON.parse(t):{};}
module.exports=async function handler(req,res){
  if(req.method!=='POST')return json(res,405,{error:'Use POST /api/interfaces.'});
  try{const body=await readBody(req);if(!body.prediction_id)return json(res,400,{error:'prediction_id is required.'});const raw=await loadPredictionStructure(body.prediction_id,body.sample_index);const structure=parseStructure(raw.structure,raw.format);const result=analyzeInterfaces(structure,{computeBsa:body.compute_bsa!==false,sasa:{points:Number(body.sasa_points)||48,maxAtoms:12000}});return json(res,200,{prediction_id:body.prediction_id,sample_index:raw.sampleIndex,model_native_metrics:raw.metrics||null,...result,scientific_note:'Interface geometry is derived from predicted coordinates. Contacts, approximate buried surface area and close polar/charged/hydrophobic atom pairs are not experimental binding evidence or binding affinity.'});}catch(error){return json(res,Number(error?.statusCode)||500,{error:error?.message||'Unable to analyze interfaces.'});}
};
