'use strict';

const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const file = fs.existsSync(path.join(__dirname, '..', 'structure.html'))
  ? path.join(__dirname, '..', 'structure.html')
  : path.join(__dirname, '..', 'index.html');
const html = fs.readFileSync(file, 'utf8');

const ids = [...html.matchAll(/\bid\s*=\s*["']([^"']+)["']/gi)].map(m => m[1]);
const seen = new Set();
const duplicateIds = [...new Set(ids.filter(id => seen.has(id) || !seen.add(id)))];
if (duplicateIds.length) throw new Error(`Duplicate HTML ids: ${duplicateIds.join(', ')}`);

const idSet = new Set(ids);
const refs = new Set();
for (const m of html.matchAll(/\$\(\s*["']#([A-Za-z0-9_-]+)["']\s*\)/g)) refs.add(m[1]);
for (const m of html.matchAll(/getElementById\(\s*["']([A-Za-z0-9_-]+)["']\s*\)/g)) refs.add(m[1]);
const missing = [...refs].filter(id => !idSet.has(id)).sort();
if (missing.length) throw new Error(`JavaScript references missing HTML ids: ${missing.join(', ')}`);

const inlineScripts = [];
for (const m of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
  if (/\bsrc\s*=/.test(m[1])) continue;
  inlineScripts.push(m[2]);
}
new vm.Script(inlineScripts.join('\n'), { filename: 'index.inline.js' });

// Critical runtime startup functions must exist. Syntax-only checking cannot
// detect a missing function reference such as initTabs().
const criticalStartupFunctions = [
  'initInputModes',
  'renderEntities',
  'initViewer',
  'initViewerControls',
  'initTabs',
  'initAdvancedIntelligence',
  'renderRecent',
  'renderResidueIntelligence',
  'renderProvenance',
  'renderEnsemble',
  'renderExperimentalReference',
  'updateContextualTabs',
  'checkBackend',
  'openPhaseWorkspace',
  'showEvidenceWorkspace',
  'showComparisonSuite',
  'runStructureComparisonAdvanced',
  'showAdvancedInterfaces',
  'renderInterfaceViewer',
  'showAdvancedQc',
  'showAdvancedEnsemble'
];

const jsText = inlineScripts.join('\n');
const missingStartupFunctions = criticalStartupFunctions.filter(name => {
  const fn = new RegExp(`\\bfunction\\s+${name}\\s*\\(`);
  const assigned = new RegExp(`\\b(?:const|let|var)\\s+${name}\\s*=`);
  return !fn.test(jsText) && !assigned.test(jsText);
});
if (missingStartupFunctions.length) {
  throw new Error(`Missing critical startup functions: ${missingStartupFunctions.join(', ')}`);
}

if (!/async function init\(\)\{\s*await checkBackend\(\);/.test(jsText)) {
  throw new Error('Backend health check must run before noncritical UI initialization.');
}

console.log(`Frontend integrity: PASS (${ids.length} ids, ${refs.size} static id references, ${inlineScripts.length} inline script block${inlineScripts.length === 1 ? '' : 's'})`);
