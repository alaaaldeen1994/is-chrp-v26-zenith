'use strict';
const { getPrediction, downloadArtifact } = require('../lib/boltz-client');
const { detectStructureFormat } = require('../lib/prediction-source');
const { parseStructure, summarizeEnsemble } = require('../lib/structure-analysis');
function json(res,status,payload){res.statusCode=status;res.setHeader('content-type','application/json; charset=utf-8');res.setHeader('cache-control','no-store, max-age=0');res.end(JSON.stringify(payload));}
async function readBody(req){if(req.body&&typeof req.body==='object'&&!Buffer.isBuffer(req.body))return req.body;const chunks=[];for await(const c of req)chunks.push(c);const t=Buffer.concat(chunks).toString('utf8');return t?JSON.parse(t):{};}
module.exports=async function handler(req,res){
  if(req.method!=='POST')return json(res,405,{error:'Use POST /api/ensemble.'});
  try{
    const body=await readBody(req),id=body.prediction_id;if(!id)return json(res,400,{error:'prediction_id is required.'});
    const prediction=await getPrediction(id);if(prediction.status!=='succeeded')return json(res,409,{error:`Prediction status is ${prediction.status||'unknown'}.`});
    const samples=Array.isArray(prediction?.output?.all_sample_results)?prediction.output.all_sample_results:[];if(!samples.length)return json(res,404,{error:'No Boltz sample ensemble was returned for this prediction.'});
    const limit=Math.min(samples.length,Math.max(1,Math.min(10,Number(body.max_samples)||10)));
    const downloaded=await Promise.all(samples.slice(0,limit).map(async(s,i)=>{if(!s?.structure?.url)return null;const d=await downloadArtifact(s.structure.url,{maxBytes:35*1024*1024,timeoutMs:60000});const text=d.buffer.toString('utf8');return {index:i,parsed:parseStructure(text,detectStructureFormat(text,s.structure.url)),metrics:s.metrics||{}};}));
    const usable=downloaded.filter(Boolean);const summary=summarizeEnsemble(usable.map(x=>x.parsed),usable.map(x=>x.metrics));
    return json(res,200,{prediction_id:id,analyzed_sample_indexes:usable.map(x=>x.index),sample_metrics:usable.map(x=>({index:x.index,metrics:x.metrics})),...summary});
  }catch(error){return json(res,Number(error?.statusCode)||500,{error:error?.message||'Unable to analyze Boltz ensemble.'});}
};
