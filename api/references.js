'use strict';
function json(res,status,payload){res.statusCode=status;res.setHeader('content-type','application/json; charset=utf-8');res.setHeader('cache-control','public, max-age=300, s-maxage=1800');res.end(JSON.stringify(payload));}
function bad(msg,statusCode=400){return Object.assign(new Error(msg),{statusCode});}
async function fetchJson(url,options={}){const r=await fetch(url,{...options,headers:{accept:'application/json','content-type':'application/json',...(options.headers||{})},signal:options.signal||AbortSignal.timeout(15000)});if(!r.ok)throw bad(`RCSB service returned HTTP ${r.status}.`,502);return r.json();}
module.exports=async function handler(req,res){
  if(req.method!=='GET')return json(res,405,{error:'Use GET /api/references?accession=<UniProt-accession>.'});
  try{
    const accession=String(Array.isArray(req.query?.accession)?req.query.accession[0]:req.query?.accession||'').trim().toUpperCase();
    if(!/^[A-Z0-9][A-Z0-9-]{4,19}$/.test(accession))throw bad('A valid UniProt accession is required.');
    const query={query:{type:'group',logical_operator:'and',nodes:[
      {type:'terminal',service:'text',parameters:{attribute:'rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession',operator:'exact_match',value:accession}},
      {type:'terminal',service:'text',parameters:{attribute:'rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_name',operator:'exact_match',value:'UniProt'}}
    ]},return_type:'polymer_entity',request_options:{paginate:{start:0,rows:24}}};
    const search=await fetchJson('https://search.rcsb.org/rcsbsearch/v2/query',{method:'POST',body:JSON.stringify(query)});
    const ids=(search?.result_set||[]).map(x=>String(x.identifier||'')).filter(Boolean).slice(0,24);
    const rows=await Promise.all(ids.map(async ident=>{
      const [pdbId,entityId]=ident.split('_'); if(!pdbId||!entityId)return null;
      try{
        const [entry,entity]=await Promise.all([
          fetchJson(`https://data.rcsb.org/rest/v1/core/entry/${encodeURIComponent(pdbId)}`),
          fetchJson(`https://data.rcsb.org/rest/v1/core/polymer_entity/${encodeURIComponent(pdbId)}/${encodeURIComponent(entityId)}`)
        ]);
        const chains=entity?.rcsb_polymer_entity_container_identifiers?.auth_asym_ids||entity?.rcsb_polymer_entity_container_identifiers?.asym_ids||[];
        return {pdb_id:pdbId.toUpperCase(),entity_id:entityId,chains,method:entry?.exptl?.map(x=>x.method).filter(Boolean).join('; ')||null,resolution_angstrom:Array.isArray(entry?.rcsb_entry_info?.resolution_combined)?entry.rcsb_entry_info.resolution_combined[0]??null:null,title:entry?.struct?.title||null,release_date:entry?.rcsb_accession_info?.initial_release_date||null,sequence:entity?.entity_poly?.pdbx_seq_one_letter_code_can?.replace(/\s+/g,'')||null,source_url:`https://www.rcsb.org/structure/${pdbId.toUpperCase()}`};
      }catch{return {pdb_id:pdbId.toUpperCase(),entity_id:entityId,chains:[],method:null,resolution_angstrom:null,title:null,source_url:`https://www.rcsb.org/structure/${pdbId.toUpperCase()}`};}
    }));
    const refs=rows.filter(Boolean).sort((a,b)=>{const ar=Number(a.resolution_angstrom),br=Number(b.resolution_angstrom);if(Number.isFinite(ar)&&Number.isFinite(br))return ar-br;if(Number.isFinite(ar))return -1;if(Number.isFinite(br))return 1;return 0;});
    return json(res,200,{accession,experimental_references:refs,count:refs.length,source:'RCSB PDB Search/Data APIs',note:'References are experimental PDB entries mapped to the UniProt accession. Construct boundaries, mutations, ligands, oligomeric state and conformational state must be reviewed before interpreting structural deviations.'});
  }catch(error){return json(res,Number(error?.statusCode)||500,{error:error?.message||'Unable to search RCSB PDB references.'});}
};
