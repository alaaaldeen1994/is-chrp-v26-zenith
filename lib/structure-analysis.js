'use strict';

/*
 * Nilus Lab structural analysis primitives.
 *
 * Scientific scope:
 * - Parsing: PDB and common mmCIF atom_site loops.
 * - Comparison: sequence-guided rigid-body least-squares superposition using
 *   Horn's quaternion method; TM-score is calculated over the mapped C-alpha
 *   pairs. This is NOT a TM-align structural-search implementation.
 * - Interface analysis: coordinate-derived contact geometry and approximate
 *   Shrake-Rupley buried surface area.
 * - QC: preliminary coordinate-geometry checks only; NOT MolProbity-equivalent.
 */

const AA3_TO_1 = Object.freeze({
  ALA:'A',ARG:'R',ASN:'N',ASP:'D',CYS:'C',GLN:'Q',GLU:'E',GLY:'G',HIS:'H',ILE:'I',
  LEU:'L',LYS:'K',MET:'M',PHE:'F',PRO:'P',SER:'S',THR:'T',TRP:'W',TYR:'Y',VAL:'V',
  MSE:'M',SEC:'U',PYL:'O',ASX:'B',GLX:'Z',UNK:'X'
});
const NUC_TO_1 = Object.freeze({
  A:'A',C:'C',G:'G',U:'U',T:'T',DA:'A',DC:'C',DG:'G',DT:'T',DU:'U',DI:'I'
});
const HYDROPHOBIC = new Set(['ALA','VAL','ILE','LEU','MET','PHE','TRP','TYR','PRO']);
const POSITIVE_ATOMS = Object.freeze({LYS:new Set(['NZ']),ARG:new Set(['NE','NH1','NH2'])});
const NEGATIVE_ATOMS = Object.freeze({ASP:new Set(['OD1','OD2']),GLU:new Set(['OE1','OE2'])});
const VDW = Object.freeze({H:1.20,C:1.70,N:1.55,O:1.52,F:1.47,P:1.80,S:1.80,CL:1.75,BR:1.85,I:1.98,FE:1.80,ZN:1.39,MG:1.73,CA:2.31});

function finite(v){ const n=Number(v); return Number.isFinite(n)?n:null; }
function normElement(value, atomName=''){
  let e=String(value||'').trim().toUpperCase().replace(/[^A-Z]/g,'');
  if(!e){
    e=String(atomName||'').trim().replace(/^\d+/,'').slice(0,2).toUpperCase();
    if(e.length===2 && !VDW[e]) e=e[0];
  }
  return e || 'C';
}
function residueKey(a){ return `${a.chain}|${a.resi}|${a.icode||''}|${a.resn}`; }
function atomKey(a){ return `${residueKey(a)}|${a.name}`; }

function parsePdb(text){
  const atoms=[]; const lines=String(text||'').split(/\r?\n/);
  const hasModels=lines.some(line=>line.startsWith('MODEL '));
  let selectedModel=null, active=!hasModels;
  for(const line of lines){
    if(line.startsWith('MODEL ')){
      const parsed=Number.parseInt(line.slice(10,14).trim(),10);
      const model=Number.isFinite(parsed)?parsed:1;
      if(selectedModel==null)selectedModel=model;
      active=model===selectedModel;
      continue;
    }
    if(line.startsWith('ENDMDL')){
      if(hasModels&&active)break;
      active=false; continue;
    }
    if(hasModels&&!active)continue;
    if(!(line.startsWith('ATOM  ')||line.startsWith('HETATM'))) continue;
    const alt=(line.slice(16,17)||'').trim();
    if(alt && alt!=='A' && alt!=='.') continue;
    const x=finite(line.slice(30,38)), y=finite(line.slice(38,46)), z=finite(line.slice(46,54));
    if(x==null||y==null||z==null) continue;
    const name=line.slice(12,16).trim();
    const resn=line.slice(17,20).trim().toUpperCase();
    const chain=(line.slice(21,22).trim()||'_');
    const resi=Number.parseInt(line.slice(22,26).trim(),10);
    atoms.push({
      group:line.slice(0,6).trim(), serial:Number.parseInt(line.slice(6,11).trim(),10)||atoms.length+1,
      name,resn,chain,resi:Number.isFinite(resi)?resi:0,icode:line.slice(26,27).trim(),
      x,y,z,occ:finite(line.slice(54,60)),b:finite(line.slice(60,66)),
      element:normElement(line.slice(76,78),name)
    });
  }
  return atoms;
}

function cifTokens(text){
  const s=String(text||'');
  const out=[]; let i=0; let lineStart=true;
  while(i<s.length){
    const c=s[i];
    if(c==='\n' || c==='\r'){ lineStart=true; i++; continue; }
    if(/\s/.test(c)){ i++; continue; }
    if(c==='#'){
      while(i<s.length && s[i]!=='\n') i++;
      continue;
    }
    if(c===';' && lineStart){
      i++;
      if(s[i]==='\r') i++;
      if(s[i]==='\n') i++;
      const start=i;
      let end=s.length;
      while(i<s.length){
        const nl=s.indexOf('\n',i);
        if(nl<0){ i=s.length; break; }
        const next=nl+1;
        if(s[next]===';'){
          end=nl;
          i=next+1;
          while(i<s.length && s[i]!=='\n') i++;
          break;
        }
        i=next;
      }
      out.push(s.slice(start,end)); lineStart=false; continue;
    }
    lineStart=false;
    if(c==='\'' || c==='"'){
      const q=c; i++; const start=i;
      while(i<s.length && s[i]!==q) i++;
      out.push(s.slice(start,i)); if(i<s.length)i++; continue;
    }
    const start=i;
    while(i<s.length && !/\s/.test(s[i]) && s[i]!=='#') i++;
    out.push(s.slice(start,i));
    if(s[i]==='#') while(i<s.length && s[i]!=='\n') i++;
  }
  return out;
}

function parseCif(text){
  const tokens=cifTokens(text); const atoms=[];
  for(let i=0;i<tokens.length;i++){
    if(tokens[i]!=='loop_') continue;
    let j=i+1; const tags=[];
    while(j<tokens.length && tokens[j].startsWith('_')){ tags.push(tokens[j]); j++; }
    if(!tags.length || !tags.some(t=>t.startsWith('_atom_site.'))) continue;
    const idx={}; tags.forEach((t,k)=>idx[t]=k);
    const getIndex=(...names)=>{ for(const n of names) if(idx[n]!=null)return idx[n]; return -1; };
    const igroup=getIndex('_atom_site.group_PDB');
    const iname=getIndex('_atom_site.auth_atom_id','_atom_site.label_atom_id');
    const iresn=getIndex('_atom_site.auth_comp_id','_atom_site.label_comp_id');
    const ichain=getIndex('_atom_site.auth_asym_id','_atom_site.label_asym_id');
    const iresi=getIndex('_atom_site.auth_seq_id','_atom_site.label_seq_id');
    const iicode=getIndex('_atom_site.pdbx_PDB_ins_code');
    const ix=getIndex('_atom_site.Cartn_x'), iy=getIndex('_atom_site.Cartn_y'), iz=getIndex('_atom_site.Cartn_z');
    const ib=getIndex('_atom_site.B_iso_or_equiv');
    const iocc=getIndex('_atom_site.occupancy');
    const ielem=getIndex('_atom_site.type_symbol');
    const ialt=getIndex('_atom_site.label_alt_id','_atom_site.auth_alt_id');
    const imodel=getIndex('_atom_site.pdbx_PDB_model_num');
    const iserial=getIndex('_atom_site.id');
    if(iname<0||iresn<0||ichain<0||iresi<0||ix<0||iy<0||iz<0) continue;
    const n=tags.length; let selectedModel=null;
    while(j+n<=tokens.length){
      if(tokens[j]==='loop_' || tokens[j].startsWith('data_') || tokens[j].startsWith('save_') || tokens[j]==='stop_') break;
      if(tokens[j].startsWith('_') && (j-i)%n===0) break;
      const row=tokens.slice(j,j+n);
      if(row.length<n) break;
      const modelValue=imodel>=0?String(row[imodel]||'1'):'1';
      if(selectedModel==null)selectedModel=modelValue;
      if(modelValue!==selectedModel){j+=n;continue;}
      const x=finite(row[ix]),y=finite(row[iy]),z=finite(row[iz]);
      if(x!=null&&y!=null&&z!=null){
        const alt=ialt>=0?String(row[ialt]||'').trim():'';
        if(!alt || alt==='.' || alt==='?' || alt==='A'){
          const name=String(row[iname]||'').replace(/^['"]|['"]$/g,'').trim();
          const resn=String(row[iresn]||'').toUpperCase();
          const chain=String(row[ichain]||'_');
          const rawResi=String(row[iresi]||'0');
          const resi=Number.parseInt(rawResi,10);
          atoms.push({
            group:igroup>=0?String(row[igroup]||'ATOM'):'ATOM',
            serial:iserial>=0?(Number.parseInt(row[iserial],10)||atoms.length+1):atoms.length+1,
            name,resn,chain,resi:Number.isFinite(resi)?resi:atoms.length+1,
            icode:iicode>=0 && !['.','?'].includes(row[iicode])?String(row[iicode]):'',
            x,y,z,b:ib>=0?finite(row[ib]):null,occ:iocc>=0?finite(row[iocc]):null,
            element:normElement(ielem>=0?row[ielem]:'',name)
          });
        }
      }
      j+=n;
    }
    if(atoms.length) break;
  }
  return atoms;
}

function detectFormat(text,format=''){
  const f=String(format||'').toLowerCase();
  if(f.includes('pdb')) return 'pdb';
  if(f.includes('cif')) return 'cif';
  return /^(ATOM  |HETATM|HEADER|MODEL )/m.test(String(text||'').slice(0,6000))?'pdb':'cif';
}

function buildStructure(atoms){
  const residues=[]; const resMap=new Map(); const chains=new Map();
  for(const a of atoms){
    const k=residueKey(a); let r=resMap.get(k);
    if(!r){
      r={key:k,chain:a.chain,resi:a.resi,icode:a.icode||'',resn:a.resn,atoms:[],atomMap:{},kind:'other'};
      if(AA3_TO_1[a.resn]) r.kind='protein'; else if(NUC_TO_1[a.resn]) r.kind='nucleic';
      resMap.set(k,r); residues.push(r);
      if(!chains.has(a.chain)) chains.set(a.chain,{id:a.chain,residues:[],atoms:[],proteinResidues:[],nucleicResidues:[]});
      chains.get(a.chain).residues.push(r);
      if(r.kind==='protein') chains.get(a.chain).proteinResidues.push(r);
      if(r.kind==='nucleic') chains.get(a.chain).nucleicResidues.push(r);
    }
    r.atoms.push(a); if(!r.atomMap[a.name])r.atomMap[a.name]=a;
    chains.get(a.chain).atoms.push(a);
  }
  for(const c of chains.values()){
    c.sequence=c.proteinResidues.map(r=>AA3_TO_1[r.resn]||'X').join('');
    c.nucleicSequence=c.nucleicResidues.map(r=>NUC_TO_1[r.resn]||'N').join('');
    c.type=c.proteinResidues.length>=c.nucleicResidues.length && c.proteinResidues.length?'protein':(c.nucleicResidues.length?'nucleic':'other');
  }
  return {atoms,residues,chains:[...chains.values()],chainMap:chains};
}

function parseStructure(text,format=''){
  const detected=detectFormat(text,format);
  const atoms=detected==='pdb'?parsePdb(text):parseCif(text);
  if(!atoms.length) throw Object.assign(new Error(`No atoms could be parsed from ${detected.toUpperCase()} coordinates.`),{statusCode:422});
  const structure=buildStructure(atoms); structure.format=detected; return structure;
}

function selectProteinChain(structure,requested){
  if(requested && structure.chainMap.has(requested) && structure.chainMap.get(requested).proteinResidues.length) return structure.chainMap.get(requested);
  return [...structure.chains].filter(c=>c.proteinResidues.length).sort((a,b)=>b.proteinResidues.length-a.proteinResidues.length)[0]||null;
}

function needlemanWunsch(a,b,{match=2,mismatch=-1,gap=-2}={}){
  const n=a.length,m=b.length; const cols=m+1;
  const score=new Int32Array((n+1)*(m+1)); const trace=new Int8Array((n+1)*(m+1));
  for(let i=1;i<=n;i++){score[i*cols]=i*gap;trace[i*cols]=1;}
  for(let j=1;j<=m;j++){score[j]=j*gap;trace[j]=2;}
  for(let i=1;i<=n;i++) for(let j=1;j<=m;j++){
    const diag=score[(i-1)*cols+j-1]+(a[i-1]===b[j-1]?match:mismatch);
    const up=score[(i-1)*cols+j]+gap, left=score[i*cols+j-1]+gap;
    let best=diag,t=0; if(up>best){best=up;t=1;} if(left>best){best=left;t=2;}
    score[i*cols+j]=best; trace[i*cols+j]=t;
  }
  let i=n,j=m; const pairs=[]; let matches=0;
  while(i>0||j>0){
    const t=trace[i*cols+j];
    if(i>0&&j>0&&t===0){ pairs.push([i-1,j-1]); if(a[i-1]===b[j-1])matches++; i--;j--; }
    else if(i>0&&(j===0||t===1)){i--;}
    else {j--;}
  }
  pairs.reverse();
  return {pairs,matches,identity:pairs.length?matches/pairs.length:0,score:score[n*cols+m]};
}

function centroid(points){
  const c=[0,0,0]; if(!points.length)return c;
  for(const p of points){c[0]+=p[0];c[1]+=p[1];c[2]+=p[2];}
  return c.map(v=>v/points.length);
}
function matVec4(M,v){return M.map(r=>r[0]*v[0]+r[1]*v[1]+r[2]*v[2]+r[3]*v[3]);}
function normalize4(v){const d=Math.hypot(...v)||1;return v.map(x=>x/d);}
function quaternionRotation(P,Q){
  const cp=centroid(P),cq=centroid(Q); let Sxx=0,Sxy=0,Sxz=0,Syx=0,Syy=0,Syz=0,Szx=0,Szy=0,Szz=0;
  for(let i=0;i<P.length;i++){
    const px=P[i][0]-cp[0],py=P[i][1]-cp[1],pz=P[i][2]-cp[2];
    const qx=Q[i][0]-cq[0],qy=Q[i][1]-cq[1],qz=Q[i][2]-cq[2];
    Sxx+=px*qx;Sxy+=px*qy;Sxz+=px*qz;Syx+=py*qx;Syy+=py*qy;Syz+=py*qz;Szx+=pz*qx;Szy+=pz*qy;Szz+=pz*qz;
  }
  const tr=Sxx+Syy+Szz;
  const K=[
    [tr,Syz-Szy,Szx-Sxz,Sxy-Syx],
    [Syz-Szy,Sxx-Syy-Szz,Sxy+Syx,Szx+Sxz],
    [Szx-Sxz,Sxy+Syx,-Sxx+Syy-Szz,Syz+Szy],
    [Sxy-Syx,Szx+Sxz,Syz+Szy,-Sxx-Syy+Szz]
  ];
  // Power iteration on a positively shifted symmetric Davenport matrix.
  // The shift preserves eigenvectors while making the largest algebraic
  // eigenvalue the dominant-magnitude eigenvalue for stable iteration.
  const shift=Math.max(...K.map(r=>r.reduce((sum,v)=>sum+Math.abs(v),0)))+1;
  const Ks=K.map((r,i)=>r.map((v,j)=>v+(i===j?shift:0)));
  let q=[1,0,0,0];
  for(let k=0;k<100;k++) q=normalize4(matVec4(Ks,q));
  const [w,x,y,z]=q;
  const R=[
    [1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
    [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
    [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]
  ];
  const rc=[R[0][0]*cp[0]+R[0][1]*cp[1]+R[0][2]*cp[2],R[1][0]*cp[0]+R[1][1]*cp[1]+R[1][2]*cp[2],R[2][0]*cp[0]+R[2][1]*cp[1]+R[2][2]*cp[2]];
  const t=[cq[0]-rc[0],cq[1]-rc[1],cq[2]-rc[2]];
  return {rotation:R,translation:t,mobile_centroid:cp,reference_centroid:cq};
}
function transformPoint(p,T){const R=T.rotation,t=T.translation;return [R[0][0]*p[0]+R[0][1]*p[1]+R[0][2]*p[2]+t[0],R[1][0]*p[0]+R[1][1]*p[1]+R[1][2]*p[2]+t[1],R[2][0]*p[0]+R[2][1]*p[1]+R[2][2]*p[2]+t[2]];}
function dist(a,b){return Math.hypot(a[0]-b[0],a[1]-b[1],a[2]-b[2]);}

function compareProteinStructures(mobile,reference,options={}){
  const mc=selectProteinChain(mobile,options.mobileChain), rc=selectProteinChain(reference,options.referenceChain);
  if(!mc||!rc) throw Object.assign(new Error('A protein chain with C-alpha coordinates is required in both structures.'),{statusCode:422});
  const al=needlemanWunsch(mc.sequence,rc.sequence);
  const mapped=[];
  for(const [mi,ri] of al.pairs){
    const mr=mc.proteinResidues[mi], rr=rc.proteinResidues[ri]; const ma=mr?.atomMap?.CA, ra=rr?.atomMap?.CA;
    if(ma&&ra) mapped.push({mi,ri,mr,rr,p:[ma.x,ma.y,ma.z],q:[ra.x,ra.y,ra.z],same:(AA3_TO_1[mr.resn]||'X')===(AA3_TO_1[rr.resn]||'X')});
  }
  if(mapped.length<3) throw Object.assign(new Error('At least three mapped C-alpha atom pairs are required for structural superposition.'),{statusCode:422});
  const T=quaternionRotation(mapped.map(x=>x.p),mapped.map(x=>x.q));
  let sum2=0; const deviations=[];
  for(const x of mapped){
    const moved=transformPoint(x.p,T),d=dist(moved,x.q);sum2+=d*d;
    deviations.push({mobile_chain:mc.id,mobile_resi:x.mr.resi,mobile_resn:x.mr.resn,reference_chain:rc.id,reference_resi:x.rr.resi,reference_resn:x.rr.resn,distance_angstrom:Number(d.toFixed(4)),sequence_match:x.same});
  }
  const rmsd=Math.sqrt(sum2/mapped.length);
  const Lref=Math.max(1,rc.proteinResidues.length);
  const d0=Math.max(0.5,1.24*Math.cbrt(Math.max(1,Lref-15))-1.8);
  const tm=deviations.reduce((s,x)=>s+1/(1+(x.distance_angstrom/d0)**2),0)/Lref;
  const mappedMatches=mapped.reduce((s,x)=>s+(x.same?1:0),0);
  return {
    method:'sequence-guided rigid-body least-squares superposition (Horn quaternion); TM-score computed over mapped C-alpha pairs; not a TM-align search',
    mobile_chain:mc.id, reference_chain:rc.id,
    mobile_length:mc.proteinResidues.length,reference_length:rc.proteinResidues.length,
    aligned_residues:mapped.length,sequence_identity:mapped.length?mappedMatches/mapped.length:0,
    mobile_coverage:mapped.length/Math.max(1,mc.proteinResidues.length),reference_coverage:mapped.length/Lref,
    rmsd_angstrom:Number(rmsd.toFixed(4)),tm_score_sequence_mapped:Number(tm.toFixed(5)),tm_normalization_length:Lref,tm_d0_angstrom:Number(d0.toFixed(4)),
    transform:{rotation:T.rotation.map(r=>r.map(v=>Number(v.toFixed(9)))),translation:T.translation.map(v=>Number(v.toFixed(9)))},
    deviations
  };
}

function cellKey(x,y,z,size){return `${Math.floor(x/size)},${Math.floor(y/size)},${Math.floor(z/size)}`;}
function makeGrid(atoms,size){const g=new Map();for(const a of atoms){const k=cellKey(a.x,a.y,a.z,size);if(!g.has(k))g.set(k,[]);g.get(k).push(a);}return g;}
function neighborAtoms(grid,a,size){
  const ix=Math.floor(a.x/size),iy=Math.floor(a.y/size),iz=Math.floor(a.z/size),out=[];
  for(let dx=-1;dx<=1;dx++)for(let dy=-1;dy<=1;dy++)for(let dz=-1;dz<=1;dz++){const v=grid.get(`${ix+dx},${iy+dy},${iz+dz}`);if(v)out.push(...v);}return out;
}
function atomDistance(a,b){return Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z);}
function heavyAtoms(atoms){return atoms.filter(a=>a.element!=='H' && !String(a.name).startsWith('H'));}
function pairLabel(a,b){return a<b?`${a}|${b}`:`${b}|${a}`;}

function chargedSign(a){
  const p=POSITIVE_ATOMS[a.resn]; if(p&&p.has(a.name))return 1;
  const n=NEGATIVE_ATOMS[a.resn]; if(n&&n.has(a.name))return -1;
  return 0;
}
function isHydrophobicAtom(a){return HYDROPHOBIC.has(a.resn)&&a.element==='C';}
function isPolarAtom(a){return ['N','O','S'].includes(a.element);}

function spherePoints(n=48){
  const pts=[]; const phi=Math.PI*(3-Math.sqrt(5));
  for(let i=0;i<n;i++){const y=1-(i/(n-1))*2;const r=Math.sqrt(Math.max(0,1-y*y));const t=phi*i;pts.push([Math.cos(t)*r,y,Math.sin(t)*r]);}
  return pts;
}
function approximateSasa(atoms,{probe=1.4,points=48,maxAtoms=12000}={}){
  const A=heavyAtoms(atoms); if(A.length>maxAtoms)return {area:null,reason:`SASA skipped above ${maxAtoms} heavy atoms.`};
  const pts=spherePoints(points),grid=makeGrid(A,6.0); let area=0;
  for(const a of A){
    const ra=(VDW[a.element]||1.7)+probe; const neigh=neighborAtoms(grid,a,6.0).filter(b=>b!==a && atomDistance(a,b)<ra+(VDW[b.element]||1.7)+probe);
    let open=0;
    pointLoop: for(const p of pts){
      const sx=a.x+p[0]*ra,sy=a.y+p[1]*ra,sz=a.z+p[2]*ra;
      for(const b of neigh){const rb=(VDW[b.element]||1.7)+probe;const dx=sx-b.x,dy=sy-b.y,dz=sz-b.z;if(dx*dx+dy*dy+dz*dz<rb*rb)continue pointLoop;}
      open++;
    }
    area += 4*Math.PI*ra*ra*(open/pts.length);
  }
  return {area,probe,points_per_atom:points,method:'approximate Shrake-Rupley'};
}

function analyzeInterfaces(structure,options={}){
  const contactCut=Number(options.contactCutoff||4.0), polarCut=Number(options.polarCutoff||3.5), hydroCut=Number(options.hydrophobicCutoff||4.5), saltCut=Number(options.saltBridgeCutoff||4.0);
  const atoms=heavyAtoms(structure.atoms); const grid=makeGrid(atoms,Math.max(contactCut,polarCut,hydroCut,saltCut)); const pairs=new Map(); const seenAtomPairs=new Set();
  for(const a of atoms){
    for(const b of neighborAtoms(grid,a,Math.max(contactCut,polarCut,hydroCut,saltCut))){
      if(a.chain===b.chain || a.serial>=b.serial)continue;
      const apk=`${Math.min(a.serial,b.serial)}:${Math.max(a.serial,b.serial)}`; if(seenAtomPairs.has(apk))continue; seenAtomPairs.add(apk);
      const d=atomDistance(a,b); const key=pairLabel(a.chain,b.chain); let p=pairs.get(key);
      if(!p){const [left,right]=key.split('|');p={left_chain:left,right_chain:right,min_distance:Infinity,atom_contacts:0,polar_close_contacts:0,salt_bridges:0,hydrophobic_contacts:0,residuePairs:new Map(),leftResidues:new Set(),rightResidues:new Set()};pairs.set(key,p);}
      const left=a.chain===p.left_chain?a:b, right=a.chain===p.left_chain?b:a;
      p.min_distance=Math.min(p.min_distance,d);
      if(d<=contactCut){p.atom_contacts++;const rk=`${left.resi}${left.icode||''}:${right.resi}${right.icode||''}`;const prev=p.residuePairs.get(rk);if(!prev||d<prev.distance)p.residuePairs.set(rk,{left:{chain:left.chain,resi:left.resi,resn:left.resn},right:{chain:right.chain,resi:right.resi,resn:right.resn},distance:d});p.leftResidues.add(residueKey(left));p.rightResidues.add(residueKey(right));}
      if(d<=polarCut && isPolarAtom(a)&&isPolarAtom(b))p.polar_close_contacts++;
      const sa=chargedSign(a),sb=chargedSign(b); if(d<=saltCut && sa*sb===-1)p.salt_bridges++;
      if(d<=hydroCut && isHydrophobicAtom(a)&&isHydrophobicAtom(b))p.hydrophobic_contacts++;
    }
  }
  const results=[];
  for(const p of pairs.values()){
    const ca=structure.chainMap.get(p.left_chain)?.atoms||[], cb=structure.chainMap.get(p.right_chain)?.atoms||[];
    let bsa=null,bsaMeta=null;
    if(options.computeBsa!==false){
      const sa=approximateSasa(ca,options.sasa||{}), sb=approximateSasa(cb,options.sasa||{}), sc=approximateSasa([...ca,...cb],options.sasa||{});
      if(sa.area!=null&&sb.area!=null&&sc.area!=null){bsa=Math.max(0,sa.area+sb.area-sc.area);bsaMeta={method:sa.method,probe_angstrom:sa.probe,points_per_atom:sa.points_per_atom};}
      else bsaMeta={method:'approximate Shrake-Rupley',reason:sa.reason||sb.reason||sc.reason};
    }
    results.push({
      left_chain:p.left_chain,right_chain:p.right_chain,
      min_distance_angstrom:Number((Number.isFinite(p.min_distance)?p.min_distance:0).toFixed(3)),
      heavy_atom_contacts:p.atom_contacts,interface_residue_pairs:p.residuePairs.size,
      interface_residues_left:p.leftResidues.size,interface_residues_right:p.rightResidues.size,
      polar_close_contacts:p.polar_close_contacts,potential_salt_bridge_atom_pairs:p.salt_bridges,hydrophobic_atom_contacts:p.hydrophobic_contacts,
      buried_surface_area_angstrom2_approx:bsa==null?null:Number(bsa.toFixed(1)),bsa_method:bsaMeta,
      top_residue_contacts:[...p.residuePairs.values()].sort((x,y)=>x.distance-y.distance).slice(0,100).map(x=>({...x,distance_angstrom:Number(x.distance.toFixed(3))}))
    });
  }
  return {
    method_notes:{contacts:`heavy-atom distance ≤${contactCut} Å`,polar_close_contacts:`N/O/S atom pairs ≤${polarCut} Å; not hydrogen-bond assignment`,salt_bridges:`oppositely charged side-chain atom pairs ≤${saltCut} Å`,hydrophobic_contacts:`hydrophobic-residue carbon pairs ≤${hydroCut} Å`,bsa:'approximate Shrake-Rupley solvent-accessible surface area; derived geometry, not binding affinity'},
    chain_count:structure.chains.length,interfaces:results.sort((a,b)=>b.heavy_atom_contacts-a.heavy_atom_contacts)
  };
}

function dihedral(a,b,c,d){
  if(!a||!b||!c||!d)return null;
  const p0=[a.x,a.y,a.z],p1=[b.x,b.y,b.z],p2=[c.x,c.y,c.z],p3=[d.x,d.y,d.z];
  const sub=(u,v)=>u.map((x,i)=>x-v[i]); const dot=(u,v)=>u.reduce((s,x,i)=>s+x*v[i],0); const cross=(u,v)=>[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]; const scale=(u,s)=>u.map(x=>x*s); const unit=u=>{const n=Math.hypot(...u)||1;return u.map(x=>x/n);};
  const b0=scale(sub(p0,p1),-1),b1=sub(p2,p1),b2=sub(p3,p2),ub1=unit(b1);
  const v=sub(b0,scale(ub1,dot(b0,ub1))),w=sub(b2,scale(ub1,dot(b2,ub1)));
  const x=dot(v,w),y=dot(cross(ub1,v),w); return Math.atan2(y,x)*180/Math.PI;
}

function preliminaryGeometryQc(structure){
  const missing=[]; const breaks=[]; const peptide=[]; const phiPsi=[];
  for(const chain of structure.chains){
    const rs=chain.proteinResidues;
    for(let i=0;i<rs.length;i++){
      const r=rs[i],need=['N','CA','C','O'],miss=need.filter(n=>!r.atomMap[n]); if(miss.length)missing.push({chain:chain.id,resi:r.resi,resn:r.resn,missing:miss});
      const prev=rs[i-1],next=rs[i+1];
      if(prev){
        const c=prev.atomMap.C,n=r.atomMap.N; if(c&&n){const d=atomDistance(c,n);if(d<1.15||d>1.55)breaks.push({chain:chain.id,left_resi:prev.resi,right_resi:r.resi,c_n_distance_angstrom:Number(d.toFixed(3))});}
        const om=dihedral(prev.atomMap.CA,prev.atomMap.C,r.atomMap.N,r.atomMap.CA); if(om!=null){const a=Math.abs(om);const cls=a<30?'cis-like':a<150?'twisted':'trans-like';if(cls!=='trans-like'||r.resn==='PRO')peptide.push({chain:chain.id,resi:r.resi,resn:r.resn,omega_deg:Number(om.toFixed(1)),class:cls,proline:r.resn==='PRO'});}
      }
      const phi=prev?dihedral(prev.atomMap.C,r.atomMap.N,r.atomMap.CA,r.atomMap.C):null;
      const psi=next?dihedral(r.atomMap.N,r.atomMap.CA,r.atomMap.C,next.atomMap.N):null;
      if(phi!=null&&psi!=null)phiPsi.push({chain:chain.id,resi:r.resi,resn:r.resn,phi_deg:Number(phi.toFixed(1)),psi_deg:Number(psi.toFixed(1))});
    }
  }
  // Conservative protein-only overlap screen. Solvent, ions and ligands are excluded
  // because this preliminary QC does not implement full chemical topology. Known
  // peptide-neighbour contacts and canonical Cys disulfides are also excluded.
  const proteinAtoms=heavyAtoms(structure.chains.flatMap(c=>c.proteinResidues.flatMap(r=>r.atoms)));
  const A=proteinAtoms; const grid=makeGrid(A,4.2); let severe=0; const clashExamples=[]; const seen=new Set();
  for(const a of A){
    for(const b of neighborAtoms(grid,a,4.2)){
      if(a.serial>=b.serial)continue; const k=`${a.serial}:${b.serial}`;if(seen.has(k))continue;seen.add(k);
      if(a.chain===b.chain){const dr=Math.abs(a.resi-b.resi); if(dr<=1)continue;}
      const d=atomDistance(a,b);
      if(a.resn==='CYS'&&b.resn==='CYS'&&a.name==='SG'&&b.name==='SG'&&d<=2.3)continue;
      const cutoff=0.75*((VDW[a.element]||1.7)+(VDW[b.element]||1.7));
      if(d<cutoff){severe++;if(clashExamples.length<100)clashExamples.push({a:{chain:a.chain,resi:a.resi,resn:a.resn,atom:a.name},b:{chain:b.chain,resi:b.resi,resn:b.resn,atom:b.name},distance_angstrom:Number(d.toFixed(3)),threshold_angstrom:Number(cutoff.toFixed(3))});}
    }
  }
  const proteinResidues=structure.chains.reduce((n,c)=>n+c.proteinResidues.length,0);
  return {
    level:'preliminary_geometry_qc',molprobity_equivalent:false,
    warning:'These are Nilus coordinate-geometry checks, not MolProbity/Phenix validation and not a measure of prediction accuracy.',
    protein_residues:proteinResidues,missing_backbone_residues:missing.length,missing_backbone_examples:missing.slice(0,100),
    peptide_bond_distance_outliers:breaks.length,peptide_bond_examples:breaks.slice(0,100),
    severe_nonbonded_overlaps:severe,severe_overlap_examples:clashExamples,overlap_scope:'protein heavy atoms only; solvent/ions/ligands excluded; adjacent residues and canonical Cys disulfides excluded',
    omega_records:peptide.slice(0,200),phi_psi_available:phiPsi.length,phi_psi:phiPsi.slice(0,2000),
    not_yet_validated:['Ramachandran favored/outlier classification','rotamer outlier classification','bond/angle z-score validation','C-beta deviation validation','MolProbity clashscore']
  };
}

function unionFindClusters(matrix,threshold=0.80){
  const n=matrix.length,p=Array.from({length:n},(_,i)=>i); const find=x=>p[x]===x?x:(p[x]=find(p[x])); const unite=(a,b)=>{a=find(a);b=find(b);if(a!==b)p[b]=a;};
  for(let i=0;i<n;i++)for(let j=i+1;j<n;j++)if(Number(matrix[i][j])>=threshold)unite(i,j);
  const groups=new Map();for(let i=0;i<n;i++){const r=find(i);if(!groups.has(r))groups.set(r,[]);groups.get(r).push(i);}return [...groups.values()].sort((a,b)=>b.length-a.length);
}

function summarizeEnsemble(parsedSamples,metrics=[]){
  const n=parsedSamples.length; if(n<1)return {sample_count:0};
  const tm=Array.from({length:n},()=>Array(n).fill(1)),rmsd=Array.from({length:n},()=>Array(n).fill(0));
  for(let i=0;i<n;i++)for(let j=i+1;j<n;j++){
    try{const c=compareProteinStructures(parsedSamples[i],parsedSamples[j]);tm[i][j]=tm[j][i]=c.tm_score_sequence_mapped;rmsd[i][j]=rmsd[j][i]=c.rmsd_angstrom;}catch{tm[i][j]=tm[j][i]=null;rmsd[i][j]=rmsd[j][i]=null;}
  }
  const vals=[];for(let i=0;i<n;i++)for(let j=i+1;j<n;j++)if(Number.isFinite(tm[i][j]))vals.push(tm[i][j]);
  const clusters=unionFindClusters(tm.map(r=>r.map(v=>v==null?0:v)),0.80);
  const conf=metrics.map(m=>finite(m?.structure_confidence)).filter(v=>v!=null);
  return {
    sample_count:n,pairwise_tm_score_sequence_mapped:tm,pairwise_rmsd_angstrom:rmsd,
    mean_pairwise_tm_score:vals.length?Number((vals.reduce((a,b)=>a+b,0)/vals.length).toFixed(4)):null,
    clusters:clusters.map((members,i)=>({cluster:i+1,members,size:members.length})),
    structure_confidence_range:conf.length?[Math.min(...conf),Math.max(...conf)]:null,
    interpretation_note:'Ensemble spread reflects prediction-sample disagreement. It is not molecular dynamics, thermodynamic flexibility, or a calibrated posterior probability.'
  };
}

module.exports={
  AA3_TO_1,parseStructure,compareProteinStructures,analyzeInterfaces,preliminaryGeometryQc,summarizeEnsemble,
  needlemanWunsch,transformPoint
};
