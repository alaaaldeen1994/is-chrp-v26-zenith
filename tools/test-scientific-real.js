#!/usr/bin/env node
'use strict';

const fs=require('node:fs');
const path=require('node:path');
const {
  parseStructure,compareProteinStructures,analyzeInterfaces,
  preliminaryGeometryQc,summarizeEnsemble
}=require('../lib/structure-analysis');

const ROOT=path.resolve(__dirname,'..');
const CACHE=path.join(__dirname,'.validation-cache');
const RESULTS=path.join(ROOT,'validation-results');
fs.mkdirSync(CACHE,{recursive:true});
fs.mkdirSync(RESULTS,{recursive:true});

const args=Object.fromEntries(process.argv.slice(2).map(x=>{
  const m=x.match(/^--([^=]+)(?:=(.*))?$/); return m?[m[1],m[2]??true]:[x,true];
}));
const baseUrl=String(args['base-url']||process.env.NILUS_BASE_URL||'').replace(/\/$/,'');
const refresh=!!args.refresh;

const tests=[];
function record(phase,name,status,details={},scientific_note=''){
  tests.push({phase,name,status,details,scientific_note});
  const icon=status==='PASS'?'✓':status==='WARN'?'!':'✗';
  console.log(`${icon} ${phase} · ${name} · ${status}`);
  if(details && Object.keys(details).length) console.log('   ',JSON.stringify(details));
}
function hard(condition,phase,name,details,note){
  record(phase,name,condition?'PASS':'FAIL',details,note); return !!condition;
}
function warn(condition,phase,name,details,note){
  record(phase,name,condition?'PASS':'WARN',details,note); return !!condition;
}
async function fetchText(url,name){
  const file=path.join(CACHE,name);
  if(!refresh && fs.existsSync(file)) return fs.readFileSync(file,'utf8');
  let last;
  for(let attempt=1;attempt<=3;attempt++){
    try{
      const r=await fetch(url,{headers:{'user-agent':'Nilus-Lab-Scientific-Validation/1.0','accept':'text/plain,*/*'},signal:AbortSignal.timeout(30000)});
      if(!r.ok)throw new Error(`HTTP ${r.status}`);
      const text=await r.text();
      if(text.length<200)throw new Error('Downloaded structure file was unexpectedly small.');
      fs.writeFileSync(file,text); return text;
    }catch(e){last=e;await new Promise(resolve=>setTimeout(resolve,600*attempt));}
  }
  throw new Error(`Unable to download ${url}: ${last?.message||last}`);
}
function splitPdbModels(text){
  const lines=String(text).split(/\r?\n/),models=[];let current=null;
  for(const line of lines){
    if(line.startsWith('MODEL ')){current=[];continue;}
    if(line.startsWith('ENDMDL')){if(current&&current.some(x=>x.startsWith('ATOM  ')))models.push(current.join('\n')+'\n');current=null;continue;}
    if(current)current.push(line);
  }
  return models.length?models:[text];
}
function rigidTransformPdb(text,variant=1){
  return String(text).split(/\r?\n/).map(line=>{
    if(!(line.startsWith('ATOM  ')||line.startsWith('HETATM')))return line;
    const x=Number(line.slice(30,38)),y=Number(line.slice(38,46)),z=Number(line.slice(46,54));
    if(![x,y,z].every(Number.isFinite))return line;
    let X,Y,Z;
    if(variant%3===1){X=-y+12;Y=x-7;Z=z+3;}
    else if(variant%3===2){X=z-5;Y=-x+18;Z=-y+6;}
    else {X=y+4;Y=z-9;Z=x+11;}
    return line.slice(0,30)+X.toFixed(3).padStart(8)+Y.toFixed(3).padStart(8)+Z.toFixed(3).padStart(8)+line.slice(54);
  }).join('\n');
}
function findResidue(structure,chain,resi){return structure.chainMap.get(chain)?.proteinResidues.find(r=>r.resi===resi);}

async function liveHealth(){
  if(!baseUrl)return;
  try{
    const r=await fetch(`${baseUrl}/api/boltz`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({action:'health'}),signal:AbortSignal.timeout(10000)});
    const j=await r.json();
    hard(r.ok&&j.configured===true&&j.authenticated===true,'P1 Evidence','live Boltz backend health',{http_status:r.status,configured:j.configured,authenticated:j.authenticated,mode:j.mode},'Confirms the development server is actually connected to the model backend; it does not validate prediction accuracy.');
  }catch(e){record('P1 Evidence','live Boltz backend health','FAIL',{error:e.message},'Run this test with the 3001 dev server active.');}
  try{
    const r=await fetch(`${baseUrl}/api/references?accession=P62942`,{signal:AbortSignal.timeout(20000)});const j=await r.json();
    hard(r.ok&&Array.isArray(j.experimental_references)&&j.experimental_references.length>0,'P2 Compare','live UniProt→RCSB reference service',{http_status:r.status,count:j.experimental_references?.length||0,example:j.experimental_references?.[0]?.pdb_id||null},'Validates real external-reference discovery through the local Nilus API.');
  }catch(e){record('P2 Compare','live UniProt→RCSB reference service','FAIL',{error:e.message},'Reference discovery is required before experimental comparison can be considered operational.');}
}

async function main(){
  console.log('\nNilus Lab real scientific validation\n====================================');
  console.log('Public reference structures: 1UBQ (X-ray ubiquitin), 1D3Z (10-model NMR ubiquitin), 1BRS biological assembly (barnase–barstar).');
  console.log('This suite validates software behaviour and scientific labelling; it does NOT validate Boltz as experimentally accurate.\n');

  // Phase 1
  const htmlFile = fs.existsSync(path.join(ROOT, 'structure.html')) ? path.join(ROOT, 'structure.html') : path.join(ROOT, 'index.html');
  const index = fs.readFileSync(htmlFile, 'utf8');
  hard(['MODEL','DERIVED','CURATED','EXPERIMENTAL','AI'].every(x=>index.includes(x)),'P1 Evidence','five evidence classes present',{},'Evidence classes prevent model output, derived geometry and experimental evidence from being silently conflated.');
  hard(index.includes("ctx.hasInterface?fmtMetric(m.iptm,3):'N/A'")||index.includes('ctx.hasInterface?fmtMetric(m.iptm,3):"N/A"'),'P1 Evidence','monomer ipTM applicability guard',{},'ipTM is an interface-focused metric and must be N/A when no inter-chain interface exists.');
  hard(index.includes("schema:'nilus-scientific-manifest-v1'")&&index.includes('run_config_hash'),'P1 Evidence','reproducibility manifest schema',{},'A reproducibility record should preserve the actual computational configuration, not only the molecular sequence.');
  await liveHealth();

  const ubq=await fetchText('https://files.rcsb.org/view/1UBQ.pdb','1UBQ.pdb');
  const nmr=await fetchText('https://files.rcsb.org/view/1D3Z.pdb','1D3Z.pdb');
  let brs;
  try{brs=await fetchText('https://files.rcsb.org/download/1BRS.pdb1','1BRS.pdb1');}
  catch{brs=await fetchText('https://files.rcsb.org/view/1BRS.pdb','1BRS.pdb');}
  const ubqS=parseStructure(ubq,'pdb');

  // Phase 2
  const moved=parseStructure(rigidTransformPdb(ubq,1),'pdb');
  const invariant=compareProteinStructures(ubqS,moved);
  hard(invariant.rmsd_angstrom<0.002&&invariant.tm_score_sequence_mapped>0.999&&invariant.sequence_identity>0.999,'P2 Compare','rigid-body invariance',{rmsd_angstrom:invariant.rmsd_angstrom,tm_score:invariant.tm_score_sequence_mapped,aligned:invariant.aligned_residues},'A correct rigid-body superposition must recover an identical structure after arbitrary rotation/translation.');

  const nmrModels=splitPdbModels(nmr);
  const nmr1=parseStructure(nmrModels[0],'pdb');
  const cross=compareProteinStructures(ubqS,nmr1);
  hard(cross.aligned_residues>=70&&cross.sequence_identity>=0.95&&cross.tm_score_sequence_mapped>=0.75&&cross.rmsd_angstrom<=3.0,'P2 Compare','real ubiquitin X-ray↔NMR agreement',{aligned:cross.aligned_residues,identity:Number(cross.sequence_identity.toFixed(3)),rmsd_angstrom:cross.rmsd_angstrom,tm_score:cross.tm_score_sequence_mapped},'Tests the sequence-guided comparator on two independently determined experimental ubiquitin structures. Thresholds are deliberately broad because NMR and crystallographic ensembles need not be identical.');
  hard(/not a TM-align/i.test(cross.method),'P2 Compare','method is not mislabelled as TM-align',{method:cross.method},'TM-align is sequence-independent and performs structural alignment search; Nilus currently uses sequence-guided correspondence.');

  // Phase 3
  const brsS=parseStructure(brs,'pdb');
  const iface=analyzeInterfaces(brsS,{computeBsa:true,sasa:{points:72,maxAtoms:12000}});
  const top=iface.interfaces[0]||null;
  hard(!!top&&top.heavy_atom_contacts>=20&&top.interface_residue_pairs>=8,'P3 Interfaces','barnase–barstar contact detection',{chains:brsS.chains.map(c=>c.id),top_pair:top?`${top.left_chain}↔${top.right_chain}`:null,heavy_atom_contacts:top?.heavy_atom_contacts||0,residue_pairs:top?.interface_residue_pairs||0},'1BRS is a canonical protein–protein complex; a scientifically useful interface engine must recover a substantial inter-chain contact surface.');
  warn(top?.buried_surface_area_angstrom2_approx==null||top.buried_surface_area_angstrom2_approx>=300,'P3 Interfaces','approximate buried surface area is physically plausible',{approx_bsa_angstrom2:top?.buried_surface_area_angstrom2_approx??null,method:top?.bsa_method?.method||null},'This is a numerical sanity check only. Nilus BSA is approximate Shrake–Rupley and is not a binding-affinity measurement.');
  warn((top?.potential_salt_bridge_atom_pairs||0)>0,'P3 Interfaces','charged-interface signal detected',{potential_salt_bridge_atom_pairs:top?.potential_salt_bridge_atom_pairs||0},'The 1BRS literature describes a strongly electrostatic interface; this test checks that the simple charged-contact heuristic is at least directionally sensitive.');
  hard(/not hydrogen-bond assignment/i.test(iface.method_notes.polar_close_contacts)&&/not binding affinity/i.test(iface.method_notes.bsa),'P3 Interfaces','scientific interface labels are conservative',{},'Close polar atom pairs must not be promoted to hydrogen bonds or affinity without validated chemistry/energetics.');

  // Phase 4
  const qcBase=preliminaryGeometryQc(parseStructure(ubq,'pdb'));
  hard(qcBase.molprobity_equivalent===false&&qcBase.missing_backbone_residues===0,'P4 Validate','high-quality 1UBQ baseline',{missing_backbone:qcBase.missing_backbone_residues,peptide_outliers:qcBase.peptide_bond_distance_outliers,severe_overlaps:qcBase.severe_nonbonded_overlaps,phi_psi_available:qcBase.phi_psi_available},'1UBQ is a high-resolution crystallographic structure. This checks baseline parsing and confirms Nilus does not falsely claim MolProbity equivalence.');
  hard(/protein heavy atoms only/i.test(qcBase.overlap_scope||''),'P4 Validate','overlap screen excludes solvent/ligand false positives',{overlap_scope:qcBase.overlap_scope},'The preliminary protein geometry screen must not interpret crystallographic waters, ions or ligands as protein stereochemical clashes.');

  const corrupted=parseStructure(ubq,'pdb');
  const r10=findResidue(corrupted,'A',10),r20=findResidue(corrupted,'A',20),r30=findResidue(corrupted,'A',30),r50=findResidue(corrupted,'A',50);
  if(r10?.atomMap?.O)delete r10.atomMap.O;
  if(r20?.atomMap?.N)r20.atomMap.N.x+=5.0;
  if(r30?.atomMap?.CA&&r50?.atomMap?.CA){r50.atomMap.CA.x=r30.atomMap.CA.x;r50.atomMap.CA.y=r30.atomMap.CA.y;r50.atomMap.CA.z=r30.atomMap.CA.z;}
  const qcBad=preliminaryGeometryQc(corrupted);
  hard(qcBad.missing_backbone_residues>qcBase.missing_backbone_residues,'P4 Validate','missing-backbone sensitivity',{baseline:qcBase.missing_backbone_residues,corrupted:qcBad.missing_backbone_residues},'Controlled corruption must increase the missing-backbone count.');
  hard(qcBad.peptide_bond_distance_outliers>qcBase.peptide_bond_distance_outliers,'P4 Validate','peptide-geometry sensitivity',{baseline:qcBase.peptide_bond_distance_outliers,corrupted:qcBad.peptide_bond_distance_outliers},'Controlled displacement of a peptide N atom must create a peptide C–N distance outlier.');
  hard(qcBad.severe_nonbonded_overlaps>qcBase.severe_nonbonded_overlaps,'P4 Validate','severe-overlap sensitivity',{baseline:qcBase.severe_nonbonded_overlaps,corrupted:qcBad.severe_nonbonded_overlaps},'Controlled coordinate collision must increase the conservative severe-overlap screen.');
  hard(qcBad.not_yet_validated.some(x=>/Ramachandran/.test(x))&&qcBad.not_yet_validated.some(x=>/MolProbity clashscore/.test(x)),'P4 Validate','unvalidated QC metrics are explicitly withheld',{},'Professional QC claims must wait for validated Ramachandran/rotamer/bond-angle/Cβ/clashscore benchmarking.');

  // Phase 5
  hard(nmrModels.length>=10,'P5 Ensemble','real 1D3Z NMR ensemble extracted',{models:nmrModels.length},'RCSB reports 10 submitted conformers for 1D3Z; using real conformers tests ensemble mathematics on non-identical experimental structures.');
  const parsedNmr=nmrModels.slice(0,10).map(x=>parseStructure(x,'pdb'));
  const ens=summarizeEnsemble(parsedNmr);
  hard(ens.sample_count===parsedNmr.length&&Number.isFinite(ens.mean_pairwise_tm_score)&&ens.mean_pairwise_tm_score>=0.75,'P5 Ensemble','real NMR ensemble similarity matrix',{samples:ens.sample_count,mean_pairwise_tm_score:ens.mean_pairwise_tm_score,clusters:ens.clusters.length},'This validates pairwise superposition and clustering on real conformers. It does not imply Boltz samples are an NMR or thermodynamic ensemble.');
  hard(ens.clusters.reduce((s,c)=>s+c.size,0)===ens.sample_count,'P5 Ensemble','cluster accounting is complete',{cluster_sizes:ens.clusters.map(c=>c.size)},'Every analyzed sample must belong to exactly one reported cluster.');

  const rigidEns=[0,1,2,3].map(i=>parseStructure(i?rigidTransformPdb(ubq,i):ubq,'pdb'));
  const rigidSummary=summarizeEnsemble(rigidEns);
  hard(rigidSummary.mean_pairwise_tm_score>0.999&&rigidSummary.clusters.length===1,'P5 Ensemble','rigid-transform ensemble invariance',{mean_pairwise_tm_score:rigidSummary.mean_pairwise_tm_score,clusters:rigidSummary.clusters.length},'Pure coordinate-frame changes must not create false structural diversity.');

  const counts={PASS:0,WARN:0,FAIL:0};tests.forEach(t=>counts[t.status]++);
  const report={schema:'nilus-real-scientific-validation-v1',generated_at:new Date().toISOString(),version:require('../package.json').version,base_url:baseUrl||null,public_references:{'1UBQ':'X-ray ubiquitin, 1.8 Å','1D3Z':'solution NMR ubiquitin, 10 submitted conformers','1BRS':'barnase–barstar protein complex, 2.0 Å'},summary:counts,tests};
  const stamp=report.generated_at.replace(/[:.]/g,'-');
  const jsonPath=path.join(RESULTS,`scientific-validation-${stamp}.json`);
  fs.writeFileSync(jsonPath,JSON.stringify(report,null,2));
  const md=[`# Nilus Lab real scientific validation`,``,`Generated: ${report.generated_at}`,`Build: ${report.version}`,``,`## Summary`,`- PASS: ${counts.PASS}`,`- WARN: ${counts.WARN}`,`- FAIL: ${counts.FAIL}`,``,...tests.flatMap(t=>[`### ${t.phase} — ${t.name}`,`**${t.status}**`,``, '```json',JSON.stringify(t.details,null,2),'```',``,t.scientific_note||'',``])].join('\n');
  const mdPath=path.join(RESULTS,`scientific-validation-${stamp}.md`);fs.writeFileSync(mdPath,md);
  console.log(`\nReport: ${jsonPath}`);console.log(`Report: ${mdPath}`);
  console.log(`\nSummary: ${counts.PASS} PASS · ${counts.WARN} WARN · ${counts.FAIL} FAIL`);
  if(counts.FAIL)process.exitCode=1;
}
main().catch(e=>{console.error('\nREAL SCIENTIFIC VALIDATION FAILED TO RUN:',e);process.exitCode=2;});
