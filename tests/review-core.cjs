// DOM-independent tests. This does not claim to test browser selection behavior.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const core = require('../site/review.js');
const root = path.resolve(__dirname, '..');
const record = JSON.parse(fs.readFileSync(path.join(root, 'examples/catalog.json'))).revisions[0];
const snapshot = JSON.parse(fs.readFileSync(path.join(root, 'revisions', record.work, record.edition, `${record.revision}.json`)));
const data = {snapshot, revision: record.revision, repository: JSON.parse(fs.readFileSync(path.join(root, 'project.json'))).repository};
let checks = 0;
function test(name, fn) { fn(); checks++; console.log(`PASS ${name}`); }
function note(section, exact, id) {
  const text = snapshot.sections.find(s => s.id === section).text, start = text.indexOf(exact);
  assert(start >= 0);
  return {id, section, scope: 'text', anchor: core.makeAnchor(text, start, start + exact.length), comment: 'An observation.'};
}
test('Unicode exact anchor', () => {
  const n = note('chapter-01', '🚢', 'emoji'); assert.equal(n.anchor.end - n.anchor.start, 2);
  core.validateReport(core.reportFor([n], data), data);
});
test('Multi-chapter batch', () => {
  const r = core.reportFor([note('chapter-01','Leno','a'),note('chapter-02','Reno','b')], data);
  assert.equal(r.annotations.length,2);
});
test('Combining mark preserved', () => core.reportFor([note('chapter-01','é','a')],data));
test('Scope can be whole chapter', () => core.reportFor([{id:'a',section:'chapter-01',scope:'section',anchor:null,comment:'The tone seems odd.'}],data));
test('Wrong revision is not migrated', () => {
  const r=core.reportFor([note('chapter-01','Leno','a')],data);r.revision='0'.repeat(64);
  assert.throws(()=>core.validateReport(r,data));
});
test('Changed quote rejected', () => {
  const r=core.reportFor([note('chapter-01','Leno','a')],data);r.annotations[0].anchor.exact='Reno';
  assert.throws(()=>core.validateReport(r,data));
});
test('Duplicate IDs rejected', () => {
  assert.throws(()=>core.reportFor([note('chapter-01','Leno','a'),note('chapter-02','Reno','a')],data));
});
test('Surrogate split rejected', () => {
  const r=core.reportFor([note('chapter-01','🚢','a')],data);const a=r.annotations[0].anchor;a.end--;a.exact=a.exact.slice(0,1);
  assert.throws(()=>core.validateReport(r,data));
});
test('Comment is preserved as data', () => {
  const n=note('chapter-01','Leno','a');n.comment='</script><script>throw new Error("bad")</script>';
  assert.equal(core.reportFor([n],data).annotations[0].comment,n.comment);
});
const report=core.reportFor([note('chapter-01','🚢','a'),note('chapter-02','Reno','b')],data,'node-cross-language-test','2026-10-16T00:00:00Z');
if (process.env.CTP_REPORT_OUT) fs.writeFileSync(process.env.CTP_REPORT_OUT,JSON.stringify(report,null,2)+'\n');
console.log(`${checks} JavaScript core checks passed.`);
