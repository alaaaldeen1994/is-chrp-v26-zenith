'use strict';
const assert=require('node:assert/strict');
const {parseStructure,compareProteinStructures,analyzeInterfaces,preliminaryGeometryQc,summarizeEnsemble}=require('../lib/structure-analysis');

const pdbA=`ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00 90.00           N\nATOM      2  CA  ALA A   1       1.450   0.000   0.000  1.00 90.00           C\nATOM      3  C   ALA A   1       2.000   1.420   0.000  1.00 90.00           C\nATOM      4  O   ALA A   1       1.400   2.400   0.000  1.00 90.00           O\nATOM      5  N   GLY A   2       3.300   1.500   0.000  1.00 90.00           N\nATOM      6  CA  GLY A   2       3.950   2.800   0.000  1.00 90.00           C\nATOM      7  C   GLY A   2       5.450   2.700   0.000  1.00 90.00           C\nATOM      8  O   GLY A   2       6.100   3.700   0.000  1.00 90.00           O\nATOM      9  N   SER A   3       6.000   1.500   0.000  1.00 90.00           N\nATOM     10  CA  SER A   3       7.430   1.300   0.000  1.00 90.00           C\nATOM     11  C   SER A   3       8.000   2.720   0.000  1.00 90.00           C\nATOM     12  O   SER A   3       7.400   3.700   0.000  1.00 90.00           O\nEND\n`;
const pdbB=pdbA.split('\n').map(line=>{
  if(!line.startsWith('ATOM'))return line;
  const x=parseFloat(line.slice(30,38))+10,y=parseFloat(line.slice(38,46))-4,z=parseFloat(line.slice(46,54))+2;
  return line.slice(0,30)+x.toFixed(3).padStart(8)+y.toFixed(3).padStart(8)+z.toFixed(3).padStart(8)+line.slice(54);
}).join('\n');
const a=parseStructure(pdbA,'pdb'),b=parseStructure(pdbB,'pdb');
assert.equal(a.chains[0].sequence,'AGS');
const cmp=compareProteinStructures(a,b);assert.ok(cmp.rmsd_angstrom<1e-5);assert.ok(cmp.tm_score_sequence_mapped>0.999);

const ifacePdb=pdbA + pdbA.replace(/ A /g,' B ').split('\n').map(line=>{
  if(!line.startsWith('ATOM'))return line;
  const y=parseFloat(line.slice(38,46))+3.5;return line.slice(0,38)+y.toFixed(3).padStart(8)+line.slice(46);
}).join('\n');
const iface=parseStructure(ifacePdb,'pdb');const ia=analyzeInterfaces(iface,{computeBsa:false});assert.ok(ia.interfaces.length>=1);assert.ok(ia.interfaces[0].heavy_atom_contacts>0);
const qc=preliminaryGeometryQc(a);assert.equal(qc.molprobity_equivalent,false);assert.equal(qc.missing_backbone_residues,0);
const ens=summarizeEnsemble([a,b],[{structure_confidence:.8},{structure_confidence:.9}]);assert.equal(ens.sample_count,2);assert.ok(ens.mean_pairwise_tm_score>.99);

// Multi-model structures must default to the first model rather than merging
// experimental/NMR conformers into one physically impossible coordinate set.
const multiModel=`MODEL        1\n${pdbA}ENDMDL\nMODEL        2\n${pdbB}ENDMDL\n`;
const mm=parseStructure(multiModel,'pdb');
assert.equal(mm.chains[0].sequence,'AGS');
assert.equal(mm.atoms.length,a.atoms.length);
assert.ok(Math.abs(mm.chains[0].proteinResidues[0].atomMap.CA.x-a.chains[0].proteinResidues[0].atomMap.CA.x)<1e-6);


// Preliminary overlap QC must not treat solvent as a protein clash.
const withWater=pdbA.replace('END\n','')+`HETATM   99  O   HOH W   1       1.450   0.000   0.000  1.00 20.00           O\nEND\n`;
const waterQc=preliminaryGeometryQc(parseStructure(withWater,'pdb'));
assert.equal(waterQc.severe_nonbonded_overlaps,qc.severe_nonbonded_overlaps);
assert.match(waterQc.overlap_scope,/protein heavy atoms only/i);

// Canonical Cys SG–SG covalent disulfide must not be counted as a nonbonded clash.
const disulfide=`ATOM      1  N   CYS A   1       0.000   0.000   0.000  1.00 90.00           N\nATOM      2  CA  CYS A   1       1.450   0.000   0.000  1.00 90.00           C\nATOM      3  C   CYS A   1       2.000   1.420   0.000  1.00 90.00           C\nATOM      4  O   CYS A   1       1.400   2.400   0.000  1.00 90.00           O\nATOM      5  SG  CYS A   1       1.500  -2.000   0.000  1.00 90.00           S\nATOM      6  N   GLY A   2       3.300   1.500   0.000  1.00 90.00           N\nATOM      7  CA  GLY A   2       3.950   2.800   0.000  1.00 90.00           C\nATOM      8  C   GLY A   2       5.450   2.700   0.000  1.00 90.00           C\nATOM      9  O   GLY A   2       6.100   3.700   0.000  1.00 90.00           O\nATOM     10  N   CYS A   3       6.000   1.500   0.000  1.00 90.00           N\nATOM     11  CA  CYS A   3       7.430   1.300   0.000  1.00 90.00           C\nATOM     12  C   CYS A   3       8.000   2.720   0.000  1.00 90.00           C\nATOM     13  O   CYS A   3       7.400   3.700   0.000  1.00 90.00           O\nATOM     14  SG  CYS A   3       3.550  -2.000   0.000  1.00 90.00           S\nEND\n`;
const ssQc=preliminaryGeometryQc(parseStructure(disulfide,'pdb'));
assert.equal(ssQc.severe_overlap_examples.some(x=>x.a.atom==='SG'&&x.b.atom==='SG'),false);

console.log('Scientific analysis unit tests: PASS');
