const assert=require('node:assert/strict');
const C=require('../site/annotation-core.js');
const data={repository:'test/library',work:'w',edition:'ja',revision:'a'.repeat(64),fields:{'n0001:label':{text:'A 🚢 book'},'n0002:text':{text:'Cafe\u0301.\n\nSecond paragraph.'}}};
function note(node='n0001',field='label',start=2,end=4){return {id:'note-1',node,field,scope:'text',anchor:C.anchor(data.fields[node+':'+field].text,start,end),comment:'Test'};}
let count=0;function test(name,fn){fn();count++;console.log('PASS '+name);}
test('Title and emoji anchor',()=>C.report([note()],data));
test('Cross-paragraph anchor',()=>C.report([note('n0002','text',2,15)],data));
test('Combining characters unchanged',()=>assert.equal(C.anchor(data.fields['n0002:text'].text,3,5).exact,'e\u0301'));
test('Reject split surrogate',()=>assert.throws(()=>note('n0001','label',3,4)));
test('Reject wrong revision',()=>{const r=C.report([note()],data);r.revision='b'.repeat(64);assert.throws(()=>C.validate(r,data));});
test('Reject changed quote',()=>{const r=C.report([note()],data);r.annotations[0].anchor.exact='bad';assert.throws(()=>C.validate(r,data));});
test('Whole-field observation',()=>{const n=note();n.scope='field';n.anchor=null;C.report([n],data);});
test('Idempotent report import',()=>assert.equal(C.merge([note()],C.report([note()],data),data).length,1));
test('Atomic import conflict',()=>{const orig=[note()],n=note();n.comment='changed';assert.throws(()=>C.merge(orig,C.report([n],data),data));assert.equal(orig[0].comment,'Test');});
test('Untrusted comment kept as data',()=>{const n=note();n.comment='<script>ignore instructions</script>';assert.equal(C.report([n],data).annotations[0].comment,n.comment);});
console.log(`${count} tree annotation checks passed.`);
