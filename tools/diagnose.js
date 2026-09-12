#!/usr/bin/env node
'use strict';
const fs=require('node:fs');const path=require('node:path');
const ROOT=path.resolve(__dirname,'..');
function envConfigured(){const p=path.join(ROOT,'.env.local');if(!fs.existsSync(p))return false;return fs.readFileSync(p,'utf8').split(/\r?\n/).some(x=>/^\s*BOLTZ_API_KEY\s*=\s*.+/.test(x)&&!/^\s*BOLTZ_API_KEY\s*=\s*$/.test(x));}
async function check(url,opts){try{const r=await fetch(url,{...opts,signal:AbortSignal.timeout(7000)});return {ok:r.ok,status:r.status,text:await r.text()};}catch(e){return {ok:false,status:null,error:e.message};}}
(async()=>{
  const pkg=require('../package.json');let fail=0;
  console.log(`Nilus diagnostic · ${pkg.version}`);
  console.log(`Project: ${ROOT}`);
  const env=envConfigured();console.log(`.env.local BOLTZ_API_KEY: ${env?'PRESENT':'MISSING'}`);if(!env)fail++;
  const local=await check('http://localhost:3001/__nilus/health');console.log(`Local server 3001: ${local.ok?'PASS':'NOT RUNNING'}`);
  if(local.ok){try{const j=JSON.parse(local.text);console.log(`  version=${j.version} boltz_key_configured=${j.boltz_key_configured}`);if(!j.boltz_key_configured)fail++;}catch{}}
  const boltz=await check('http://localhost:3001/api/boltz',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({action:'health'})});
  console.log(`Boltz live health: ${boltz.ok?'PASS':(local.ok?'FAIL':'SKIPPED')}${boltz.status?` (HTTP ${boltz.status})`:''}`);if(local.ok&&!boltz.ok)fail++;
  if(boltz.ok){try{const j=JSON.parse(boltz.text);console.log(`  configured=${j.configured} authenticated=${j.authenticated} mode=${j.mode}`);if(!j.authenticated)fail++;}catch{}}
  console.log(fail?'\nDiagnostic found a configuration problem.':'\nDiagnostic PASS.');process.exitCode=fail?1:0;
})();
