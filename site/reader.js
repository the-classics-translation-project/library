(() => {
  'use strict';
  const C=globalThis.CTPAnnotations,$=id=>document.getElementById(id),data=JSON.parse($('edition-data').textContent);
  const rootId=data.tree.id,key=`ctp:reader:v2:${data.repository}:${data.work}:${data.edition}:${data.revision}`;
  const tree=[],parents={};
  function flatten(n,parent=null,depth=0){tree.push({...n,depth});parents[n.id]=parent;for(const child of n.children||[])flatten(child,n.id,depth+1);}
  flatten(data.tree);
  const items=tree.filter(n=>n.id!==rootId && (data.fields[n.id+':label']||data.fields[n.id+':text']));
  if(data.fields[rootId+':text']||!items.length)items.unshift(tree[0]);
  let state={section:items[0].id,notes:[],draft:null,margins:true},storageOK=true,captured=null,down=false,ignoreSelection=false;
  let popupRect=null,selectionTimer=null,layoutFrame=null;
  function message(s,error=false){$('message').textContent=s;$('message').classList.toggle('has-error',error);}
  function warn(s){$('warning').hidden=false;$('warning').textContent=s;}
  function safe(fn){return (...args)=>{try{return fn(...args);}catch(e){message(e.message,true);}};}
  try{
    const saved=localStorage.getItem(key);
    if(saved){const v=JSON.parse(saved);C.check(Array.isArray(v.notes),'Invalid saved notebook.');if(v.notes.length)C.report(v.notes,data);if(v.draft)C.report([{...v.draft,comment:v.draft.comment||'unfinished note'}],data);state={...state,...v};}
  }catch(e){storageOK=false;warn('Saved notes could not be loaded. They have not been overwritten. New notes are in memory only; export them before leaving.');}
  function persist(){
    if(!storageOK)return;
    try{localStorage.setItem(key,JSON.stringify(state));}catch(e){storageOK=false;warn('Browser storage is unavailable. Export notes before leaving this page.');}
  }
  function label(nid){return data.fields[nid+':label']?.text||`Section ${tree.findIndex(n=>n.id===nid)+1}`;}
  function editable(tag,field,className=''){
    const el=document.createElement(tag),f=data.fields[field];if(!f)return null;
    el.dataset.editable=field;el.className=className;el.innerHTML=f.html;C.check(el.textContent===f.text,'Snapshot rendering mismatch.');return el;
  }
  const titleField=data.fields[rootId+':label'];
  if(titleField){$('book-title').dataset.editable=rootId+':label';$('book-title').textContent=titleField.text;}else $('book-title').hidden=true;
  const credit=data.fields[rootId+':credit'];
  if(credit?.text){$('book-credit').dataset.editable=rootId+':credit';$('book-credit').textContent=credit.text;}else $('book-credit').hidden=true;
  $('workbench').lang=data.language;$('section-content').dir=data.direction;
  $('edition-info').textContent=`${data.status} · ${data.language}. ${data.description} ${data.missing.length ? data.missing.length+' untranslated fields remain.' : ''}`;
  $('revision-info').textContent='Revision '+data.revision;
  for(const n of items){const o=document.createElement('option');o.value=n.id;o.textContent='\u00a0'.repeat(Math.min(n.depth,4)*2)+label(n.id);$('sections').append(o);}
  function hasPendingChange(){
    if(!state.draft)return false;
    const old=state.notes.find(n=>n.id===state.draft.id);
    return state.draft.comment.trim() && (!old||old.comment!==state.draft.comment);
  }
  function abandon(){if(hasPendingChange()&&!window.confirm('Discard the unfinished comment?'))return false;state.draft=null;$('composer').hidden=true;persist();return true;}
  function navigate(id,scroll=false){
    if(!items.some(n=>n.id===id))id=items[0].id;
    if(state.draft && id!==state.section && !abandon()){$('sections').value=state.section;return false;}
    state.section=id;$('sections').value=id;captured=null;
    const content=$('section-content');content.replaceChildren();
    let parent=parents[id],anc=[];while(parent&&parent!==rootId){anc.unshift(parent);parent=parents[parent];}
    for(const p of anc){const e=editable('p',p+':label','part-label');if(e)content.append(e);}
    if(id!==rootId){const h=editable('h2',id+':label','section-heading');if(h)content.append(h);}
    const body=editable('article',id+':text','reading-text');if(body)content.append(body);
    const src=data.source_nodes[id]||{};$('source').replaceChildren();$('source').lang=data.source_language;$('source').dir='auto';
    if(src.label){const h=document.createElement('h3');h.textContent=src.label;$('source').append(h);}
    if(src.text){const div=document.createElement('div');div.innerHTML=src.text.html;$('source').append(div);}
    $('source').parentElement.open=false;
    const i=items.findIndex(n=>n.id===id);$('prev').disabled=i===0;$('next').disabled=$('next-bottom').disabled=i===items.length-1;
    paint();renderNotes();persist();
    try{history.replaceState(null,'','#'+encodeURIComponent(id));}catch{}
    if(scroll)$('section-content').scrollIntoView({block:'start'});
    return true;
  }
  function move(d){const next=items[items.findIndex(n=>n.id===state.section)+d];if(next)navigate(next.id,true);}
  $('prev').addEventListener('click',safe(()=>move(-1)));$('next').addEventListener('click',safe(()=>move(1)));$('next-bottom').addEventListener('click',safe(()=>move(1)));
  $('sections').addEventListener('change',safe(e=>navigate(e.target.value,true)));
  function allFields(){return [...$('workbench').querySelectorAll('[data-editable]')];}
  function fieldElement(key){return allFields().find(el=>el.dataset.editable===key);}
  function noteKey(n){return `${n.node}:${n.field}`;}
  function rangeFor(el,a){
    if(!el||!a)return null;
    const walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);let n,pos=0,start=null,end=null,so=0,eo=0;
    while((n=walker.nextNode())){const next=pos+n.length;if(!start&&a.start>=pos&&a.start<next){start=n;so=a.start-pos;}if(a.end>pos&&a.end<=next){end=n;eo=a.end-pos;break;}pos=next;}
    if(!start||!end)return null;const r=document.createRange();r.setStart(start,so);r.setEnd(end,eo);return r;
  }
  function rectFor(n){const el=fieldElement(noteKey(n));if(!el)return null;const r=rangeFor(el,n.anchor);return r?[...r.getClientRects()].find(x=>x.width>0)||el.getBoundingClientRect():el.getBoundingClientRect();}
  function paint(){
    ignoreSelection=true;
    for(const el of allFields()){
      const f=data.fields[el.dataset.editable];el.innerHTML=f.html;
      const notes=state.notes.filter(n=>noteKey(n)===el.dataset.editable && n.scope==='text');
      const walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT),parts=[];let node,pos=0;
      while((node=walker.nextNode())){parts.push({node,start:pos,end:pos+node.length});pos+=node.length;}
      for(const {node,start,end} of parts){
        const overlap=notes.filter(n=>n.anchor.start<end&&n.anchor.end>start);if(!overlap.length)continue;
        const cuts=new Set([0,node.length]);for(const n of overlap){cuts.add(Math.max(0,n.anchor.start-start));cuts.add(Math.min(node.length,n.anchor.end-start));}
        const sorted=[...cuts].sort((a,b)=>a-b),frag=document.createDocumentFragment();
        for(let i=0;i<sorted.length-1;i++){
          const a=sorted[i],b=sorted[i+1],ids=overlap.filter(n=>n.anchor.start<start+b&&n.anchor.end>start+a).map(n=>n.id),s=node.data.slice(a,b);
          if(!ids.length){frag.append(document.createTextNode(s));continue;}
          const mark=document.createElement('span');mark.className='ctp-annotation-mark';mark.dataset.ids=ids.join(' ');mark.textContent=s;frag.append(mark);
        }
        node.replaceWith(frag);
      }
      C.check(el.textContent===f.text,'Highlighting changed the text.');
      const seen=new Set();for(const mark of el.querySelectorAll('[data-ids]')){const id=mark.dataset.ids.split(' ')[0];if(!seen.has(id)){mark.tabIndex=0;mark.setAttribute('role','button');mark.setAttribute('aria-label',state.notes.find(n=>n.id===id).comment);seen.add(id);}}
    }
    requestAnimationFrame(()=>{ignoreSelection=false;});scheduleLayout();
  }
  function scheduleLayout(){cancelAnimationFrame(layoutFrame);layoutFrame=requestAnimationFrame(safe(layoutNotes));}
  function layoutNotes(){
    $('reader-shell').classList.toggle('margin-off',!state.margins);$('margin').replaceChildren();$('connectors').replaceChildren();
    $('show-margins').textContent=state.margins?'Hide margin notes':'Show margin notes';
    if(!state.margins||getComputedStyle($('margin')).display==='none')return;
    const shell=$('reader-shell').getBoundingClientRect(),rail=$('margin').getBoundingClientRect();let bottom=0;
    const notes=state.notes.map(n=>({n,r:rectFor(n)})).filter(x=>x.r).sort((a,b)=>a.r.top-b.r.top);
    for(const {n,r} of notes){
      const b=document.createElement('button');b.className='margin-note';b.dataset.note=n.id;b.title=n.comment;b.setAttribute('aria-label',n.comment);
      const excerpt=document.createElement('span');excerpt.textContent=n.comment;b.append(excerpt);
      const wanted=Math.max(0,r.top-rail.top),top=Math.max(wanted,bottom);b.style.top=top+'px';$('margin').append(b);bottom=top+b.getBoundingClientRect().height+10;
      b.addEventListener('click',safe(()=>openSaved(n)));
      b.addEventListener('mouseenter',()=>highlightActive(n.id));b.addEventListener('mouseleave',()=>highlightActive(null));
      const path=document.createElementNS('http://www.w3.org/2000/svg','path'),x1=Math.min(r.right-shell.left+5,rail.left-shell.left-10),y1=r.top-shell.top+r.height/2,x2=rail.left-shell.left,y2=rail.top-shell.top+top+16;
      path.setAttribute('d',`M${x1},${y1} C${x2-18},${y1} ${x2-18},${y2} ${x2},${y2}`);$('connectors').append(path);
    }
    $('margin').style.minHeight=bottom+'px';$('connectors').setAttribute('viewBox',`0 0 ${shell.width} ${Math.max($('reader-shell').scrollHeight,bottom)}`);$('connectors').style.height=Math.max($('reader-shell').scrollHeight,bottom)+'px';
  }
  function highlightActive(id){for(const m of $('workbench').querySelectorAll('[data-ids]'))m.classList.toggle('active-note',Boolean(id&&m.dataset.ids.split(' ').includes(id)));}
  function findField(node){return (node.nodeType===Node.ELEMENT_NODE?node:node.parentElement)?.closest('[data-editable]');}
  function captureSelection(){
    if(ignoreSelection)return null;
    const sel=window.getSelection();if(!sel||sel.isCollapsed||!sel.rangeCount)return null;
    const r=sel.getRangeAt(0),a=findField(r.startContainer),b=findField(r.endContainer);
    if(!a||a!==b)return null;
    const pre=r.cloneRange();pre.selectNodeContents(a);pre.setEnd(r.startContainer,r.startOffset);
    const start=pre.toString().length,end=start+r.toString().length,f=data.fields[a.dataset.editable];
    if(!r.toString().trim())return null;
    return {id:C.id(),node:f.node,field:f.field,scope:'text',anchor:C.anchor(f.text,start,end),comment:'',rect:[...r.getClientRects()].filter(x=>x.width>0).pop()||r.getBoundingClientRect()};
  }
  function position(){
    if($('composer').hidden)return;
    const p=$('composer'),v=window.visualViewport,left=v?.offsetLeft||0,top=v?.offsetTop||0,w=v?.width||innerWidth,h=v?.height||innerHeight;
    const r=state.draft?rectFor(state.draft):popupRect;
    const anchor=r||popupRect||{left:left+w/2,top:top+h/3,bottom:top+h/3};
    p.style.left=Math.max(left+8,Math.min(anchor.left,left+w-p.offsetWidth-8))+'px';
    const below=anchor.bottom+10,above=anchor.top-p.offsetHeight-10;
    p.style.top=Math.max(top+8,Math.min(below+p.offsetHeight<top+h-8?below:above,top+h-p.offsetHeight-8))+'px';
  }
  function open(note,rect=null,focus=false){
    if(state.draft&&state.draft.id!==note.id&&!abandon())return;
    state.draft=C.clone(note);delete state.draft.rect;popupRect=rect||rectFor(note);$('quote').textContent=note.anchor?.exact||label(note.node);
    $('comment').value=note.comment;$('delete').hidden=!state.notes.some(n=>n.id===note.id);$('composer').hidden=false;persist();requestAnimationFrame(()=>{position();if(focus)$('comment').focus({preventScroll:true});});
  }
  function showSelection(){
    const note=captureSelection();if(!note)return;
    if(state.draft?.anchor?.start===note.anchor.start&&state.draft?.anchor?.end===note.anchor.end&&noteKey(state.draft)===noteKey(note))return;
    captured=note;open(note,note.rect,false);
  }
  document.addEventListener('pointerdown',event=>{down=true;if(event.target.closest('#composer,#notebook,.margin-note'))clearTimeout(selectionTimer);});
  document.addEventListener('pointerup',event=>{down=false;if(event.target.closest('[data-editable]')){clearTimeout(selectionTimer);selectionTimer=setTimeout(safe(showSelection),100);}});
  document.addEventListener('selectionchange',()=>{clearTimeout(selectionTimer);if(!ignoreSelection&&!down && document.activeElement!==$('comment'))selectionTimer=setTimeout(safe(showSelection),450);});
  $('comment').addEventListener('input',()=>{if(state.draft){state.draft.comment=$('comment').value;persist();}});
  $('comment-form').addEventListener('submit',safe(e=>{
    e.preventDefault();C.check(state.draft,'Select some text.');const n={...state.draft,comment:$('comment').value.trim(),include:state.draft.include!==false};C.report([n],data);
    const i=state.notes.findIndex(x=>x.id===n.id);if(i<0)state.notes.push(n);else state.notes[i]=n;
    state.draft=null;$('composer').hidden=true;window.getSelection()?.removeAllRanges();persist();paint();renderNotes();
  }));
  $('cancel').addEventListener('click',safe(()=>abandon()));
  $('delete').addEventListener('click',safe(()=>{if(!state.draft)return;state.notes=state.notes.filter(n=>n.id!==state.draft.id);state.draft=null;$('composer').hidden=true;persist();paint();renderNotes();}));
  function openSaved(n){
    if(!fieldElement(noteKey(n))){if(!navigate(items.some(x=>x.id===n.node)?n.node:items[0].id))return;}
    fieldElement(noteKey(n))?.scrollIntoView({block:'center'});open(n,rectFor(n),true);
  }
  function clickMark(e){const m=e.target.closest('[data-ids]');if(!m)return;if(!window.getSelection()?.isCollapsed)return;const ids=m.dataset.ids.split(' ');const candidates=state.notes.filter(n=>ids.includes(n.id));if(candidates.length===1)openSaved(candidates[0]);else{toggleNotebook(true);renderNotes(ids);}}
  $('workbench').addEventListener('click',safe(clickMark));
  $('workbench').addEventListener('keydown',safe(e=>{if((e.key==='Enter'||e.key===' ')&&e.target.closest('[data-ids]')){e.preventDefault();clickMark(e);}}));
  $('whole-note').addEventListener('click',safe(()=>{const f=data.fields[state.section+':text']||data.fields[state.section+':label']||data.fields[rootId+':label'];C.check(f,'No edition field available.');$('menu').open=false;open({id:C.id(),node:f.node,field:f.field,scope:'field',anchor:null,comment:''},null,true);}));
  $('show-margins').addEventListener('click',()=>{state.margins=!state.margins;persist();scheduleLayout();});
  function toggleNotebook(open){$('notebook').hidden=!open;if(open){renderNotes();$('close-notes').focus();}}
  $('notes-toggle').addEventListener('click',()=>toggleNotebook($('notebook').hidden));$('close-notes').addEventListener('click',()=>toggleNotebook(false));
  function renderNotes(filter=null){
    $('count').textContent=state.notes.length;$('notes').replaceChildren();
    for(const n of state.notes){
      if(filter&&!filter.includes(n.id))continue;
      const card=document.createElement('section');card.className='note';const l=document.createElement('label'),cb=document.createElement('input');cb.type='checkbox';cb.checked=n.include!==false;cb.addEventListener('change',()=>{n.include=cb.checked;persist();});l.append(cb,document.createTextNode(label(n.node)+(n.field==='label'?' · heading':'')));card.append(l);
      if(n.anchor){const q=document.createElement('blockquote');q.textContent=n.anchor.exact;card.append(q);}
      const p=document.createElement('p');p.className='comment';p.textContent=n.comment;const b=document.createElement('button');b.textContent='Open';b.addEventListener('click',safe(()=>{toggleNotebook(false);openSaved(n);}));card.append(p,b);$('notes').append(card);
    }
  }
  function selectedReport(){return C.report(state.notes.filter(n=>n.include!==false),data);}
  function download(object){const url=URL.createObjectURL(new Blob([JSON.stringify(object,null,2)+'\n'],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=`review-${data.work}-${data.revision.slice(0,12)}.json`;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  $('export').addEventListener('click',safe(()=>download(selectedReport())));
  $('report').addEventListener('click',safe(()=>{
    const report=selectedReport();state.lastReport=report;persist();let body=`# Reading feedback\n\n${data.title}\nRevision: ${data.revision}\n\n`;
    report.annotations.forEach((n,i)=>{body+=`## ${i+1}. ${n.node} · ${n.field}\n\n`+(n.anchor?n.anchor.exact.split('\n').map(s=>'> '+s).join('\n')+'\n\n':'')+n.comment+'\n\n';});
    const serialized=JSON.stringify(report,null,2),fence='`'.repeat(Math.max(3,...(serialized.match(/`+/g)||[]).map(x=>x.length+1)));
    body+=`## Machine-readable report\n\n${fence}json\n${serialized}\n${fence}\n`;
    if(body.length>50000){download(report);body=`# Reading feedback\n\n${data.title}\nRevision: ${data.revision}\n\nAttach the exported JSON report (${report.annotations.length} notes).\n`;}
    $('report-body').value=body;$('submission').hidden=false;
    const link=$('issue-link'),base=`https://github.com/${data.repository}/issues/new?title=${encodeURIComponent(`[Reading feedback] ${data.title} — ${data.revision.slice(0,12)}`)}`;
    const complete=base+'&body='+encodeURIComponent(body);link.href=complete.length<7000?complete:base;
    link.textContent=complete.length<7000?'Open GitHub form':'Open GitHub form (paste report)';
    if(data.demo){link.removeAttribute('href');link.textContent='GitHub submission disabled for sample';link.setAttribute('aria-disabled','true');}
  }));
  $('copy-report').addEventListener('click',async()=>{try{await navigator.clipboard.writeText($('report-body').value);}catch{$('report-body').focus();$('report-body').select();message('Use Copy to copy the selected report.');}});
  $('import').addEventListener('click',()=>$('import-file').click());
  $('import-file').addEventListener('change',async e=>{try{const f=e.target.files[0];if(!f)return;C.check(f.size<=8*1024*1024,'Report exceeds 8 MiB.');const report=JSON.parse(await f.text());const merged=C.merge(state.notes,report,data);state.notes=merged;persist();paint();renderNotes();}catch(error){message(error.message,true);}finally{e.target.value='';}});
  addEventListener('resize',()=>{scheduleLayout();position();});addEventListener('scroll',()=>position(),{passive:true});window.visualViewport?.addEventListener('resize',position);document.fonts?.ready.then(scheduleLayout);
  document.addEventListener('keydown',safe(e=>{if(e.key==='Escape'){if(!$('composer').hidden)abandon();else toggleNotebook(false);}if((e.ctrlKey||e.metaKey)&&e.altKey&&e.key.toLowerCase()==='m'){e.preventDefault();showSelection();$('comment').focus();}}));
  addEventListener('beforeunload',e=>{if(!storageOK&&(state.notes.length||state.draft)){e.preventDefault();e.returnValue='';}});
  try{const savedDraft=state.draft;state.draft=null;const hash=decodeURIComponent(location.hash.slice(1));navigate(items.some(n=>n.id===hash)?hash:state.section);if(savedDraft){state.draft=savedDraft;open(savedDraft);}}catch(e){warn('The reader could not start safely: '+e.message);}
})();
