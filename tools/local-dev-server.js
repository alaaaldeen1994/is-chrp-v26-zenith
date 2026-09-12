#!/usr/bin/env node
'use strict';

const http=require('node:http');
const fs=require('node:fs');
const path=require('node:path');
const {URL}=require('node:url');

const ROOT=path.resolve(__dirname,'..');
const PORT=Number(process.env.NILUS_PORT||3001);
const HOST=process.env.NILUS_HOST||'127.0.0.1';

function loadEnvFile(file){
  if(!fs.existsSync(file))return {loaded:false,count:0};
  const text=fs.readFileSync(file,'utf8'); let count=0;
  for(const raw of text.split(/\r?\n/)){
    const line=raw.trim(); if(!line||line.startsWith('#'))continue;
    const eq=line.indexOf('='); if(eq<=0)continue;
    const key=line.slice(0,eq).trim(); if(!/^[A-Za-z_][A-Za-z0-9_]*$/.test(key))continue;
    let value=line.slice(eq+1).trim();
    if((value.startsWith('"')&&value.endsWith('"'))||(value.startsWith("'")&&value.endsWith("'")))value=value.slice(1,-1);
    if(process.env[key]==null){process.env[key]=value;count++;}
  }
  return {loaded:true,count};
}
const envInfo=loadEnvFile(path.join(ROOT,'.env.local'));

const apiRoutes={
  '/api/boltz':require('../api/boltz'),
  '/api/pae':require('../api/pae'),
  '/api/alphafold':require('../api/alphafold'),
  '/api/references':require('../api/references'),
  '/api/compare':require('../api/compare'),
  '/api/interfaces':require('../api/interfaces'),
  '/api/qc':require('../api/qc'),
  '/api/ensemble':require('../api/ensemble')
};

const MIME={'.html':'text/html; charset=utf-8','.js':'application/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.md':'text/markdown; charset=utf-8','.txt':'text/plain; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.ico':'image/x-icon'};
function json(res,status,payload){res.statusCode=status;res.setHeader('content-type','application/json; charset=utf-8');res.setHeader('cache-control','no-store');res.end(JSON.stringify(payload));}
function queryObject(searchParams){const q={};for(const [k,v] of searchParams.entries()){if(q[k]===undefined)q[k]=v;else if(Array.isArray(q[k]))q[k].push(v);else q[k]=[q[k],v];}return q;}
function safeStaticPath(pathname){
  let rel=decodeURIComponent(pathname||'/'); 
  if(rel==='/'||rel==='') rel=fs.existsSync(path.join(ROOT,'structure.html'))?'/structure.html':'/index.html';
  if(rel==='/structure') rel='/structure.html';
  rel=rel.replace(/^\/+/, ''); const full=path.resolve(ROOT,rel);
  if(full!==ROOT&&!full.startsWith(ROOT+path.sep))return null;
  return full;
}

const server=http.createServer(async(req,res)=>{
  const u=new URL(req.url||'/',`http://${req.headers.host||`${HOST}:${PORT}`}`);
  req.query=queryObject(u.searchParams);
  if(u.pathname==='/__nilus/health'){
    const pkg=require('../package.json');
    return json(res,200,{ok:true,service:'Nilus Lab local dev server',version:pkg.version,port:PORT,boltz_key_configured:!!process.env.BOLTZ_API_KEY,env_file_loaded:envInfo.loaded,api_routes:Object.keys(apiRoutes)});
  }
  const handler=apiRoutes[u.pathname];
  if(handler){
    try{return await handler(req,res);}catch(e){if(!res.headersSent)return json(res,500,{error:e?.message||'Unhandled local API error.'});try{res.end();}catch{}}
  }
  if(!['GET','HEAD'].includes(req.method||'GET'))return json(res,405,{error:'Method not allowed.'});
  const file=safeStaticPath(u.pathname); if(!file)return json(res,403,{error:'Forbidden path.'});
  try{
    const stat=fs.statSync(file); if(!stat.isFile())return json(res,404,{error:'Not found.'});
    res.statusCode=200;res.setHeader('content-type',MIME[path.extname(file).toLowerCase()]||'application/octet-stream');res.setHeader('cache-control','no-store, max-age=0');
    if(req.method==='HEAD')return res.end();
    fs.createReadStream(file).pipe(res);
  }catch{return json(res,404,{error:'Not found.'});}
});

server.on('error',err=>{
  if(err.code==='EADDRINUSE'){
    console.error(`\n[NILUS] Port ${PORT} is already in use.`);
    console.error(`Close the existing dev server or use: $env:NILUS_PORT=3002; npm run dev\n`);
    process.exit(1);
  }
  console.error(err);process.exit(1);
});
server.listen(PORT,HOST,()=>{
  console.log('\n====================================================');
  console.log(' Nilus Lab All-Phases Dev · stabilized local server');
  console.log(` Version        : ${require('../package.json').version}`);
  console.log(` URL            : http://localhost:${PORT}`);
  console.log(` BOLTZ_API_KEY  : ${process.env.BOLTZ_API_KEY?'configured':'MISSING'}`);
  console.log(' Stable ALAA    : http://localhost:3000');
  console.log('====================================================\n');
});
function shutdown(){console.log('\n[NILUS] Shutting down cleanly…');server.close(()=>process.exit(0));setTimeout(()=>process.exit(0),1500).unref();}
process.on('SIGINT',shutdown);process.on('SIGTERM',shutdown);
