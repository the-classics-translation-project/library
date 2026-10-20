(() => {
  'use strict';
  const data=JSON.parse(document.getElementById('admin-data').textContent);
  const allWorks=[...document.querySelectorAll('.source-work')];
  function make(tag,parent,content,cls){
    const el=document.createElement(tag);
    if(content!==undefined && content!==null)el.textContent=content;
    if(cls)el.className=cls;
    if(parent)parent.append(el);
    return el;
  }
  function labeledSelect(parent,text,values){
    const label=make('label',parent,text,'translation-option');
    const el=make('select',label);
    for(const v of values){
      const option=make('option',el,v.label);option.value=v.value;
    }
    return el;
  }
  function flatten(node){
    return [node,...(node.children||[]).flatMap(flatten)];
  }
  for(let index=0;index<(data.sources||[]).length;index++){
    const work=data.sources[index],section=allWorks[index];
    if(!section || !work.tree)continue;
    const nodes=flatten(work.tree);
    const selectors=[...section.querySelectorAll('input.node-pick')];
    const panel=make('section',section,null,'translation-request-panel');
    make('h4',panel,'Request translation');
    make('p',panel,'Select any nodes above, including already translated ones. Selecting a parent includes all descendants.','small');
    const target=labeledSelect(panel,'Target language',
        data.targets.map(t=>({value:t.id,label:t.label})));
    target.value=work.targets.includes('ja')?'ja':(work.targets[0]||data.targets[0].id);
    const prompt=labeledSelect(panel,'Translation recipe',
        (data.prompts||[]).map(p=>({value:p.id,label:p.title})));
    if((data.prompts||[]).some(p=>p.id==='contemporary'))prompt.value='contemporary';
    const scope=labeledSelect(panel,'Scope',[
      {value:'all',label:'Translate all selected content (including existing)'},
      {value:'missing',label:'Translate missing content only'}
    ]);
    const reference=labeledSelect(panel,'Earlier material',[
      {value:'none',label:'No previous translation or notes'},
      {value:'notes',label:'Editorial notes and terminology guides'},
      {value:'text',label:'Include exact earlier translated text'}
    ]);
    const revision=labeledSelect(panel,'Reference version',[]);
    const instructionsLabel=make('label',panel,'Additional instructions (optional)','translation-option');
    const instructions=make('textarea',instructionsLabel);
    instructions.rows=2;instructions.maxLength=4000;
    instructions.placeholder='Specific instructions for this request';
    const status=make('p',panel,'','small');
    const link=make('a',panel,'Prepare translation Issue','button primary-action');
    link.target='_blank';link.rel='noopener noreferrer';

    const history=make('section',section,null,'translation-history');
    make('h4',history,'Previous versions');
    const note=make('p',history,'Only versions explicitly approved for public review or reading are viewable here. Other draft snapshots remain in Git and can be used locally.','small');
    const versions=labeledSelect(history,'Frozen approved revision',[]);
    const view=make('button',history,'View selected node from version');
    view.type='button';
    const preview=make('pre',history,'','translation-preview');
    preview.hidden=true;
    const readerLink=make('a',history,'Open approved revision','small');
    readerLink.target='_blank';readerLink.rel='noopener noreferrer';

    function activeHistory(){
      return (work.history||[]).filter(h=>h.target===target.value);
    }
    function selectedIds(){
      return selectors.filter(x=>x.checked).map(x=>x.dataset.nodeId);
    }
    function refreshHistory(){
      revision.replaceChildren();versions.replaceChildren();
      const found=activeHistory();
      for(const item of found){
        for(const select of [revision,versions]){
          const opt=make('option',select,item.revision.slice(0,12)+' · '+item.audience+
                                     ' · '+item.model);
          opt.value=item.revision;
        }
      }
      const has=found.length>0;
      reference.querySelector('option[value="text"]').disabled=!has;
      if(!has && reference.value==='text')reference.value='none';
      revision.disabled=!has;versions.disabled=!has;view.disabled=!has;
      preview.hidden=true;readerLink.removeAttribute('href');
    }
    function refreshCoverage(){
      const coverage=(work.coverage||{})[target.value]||{};
      function count(node){
        const fields=(node.label!==undefined?1:0)+(node.has_text?1:0);
        const done=(node.label!==undefined && (coverage[node.id]||[]).includes('label')?1:0)+
                   (node.has_text && (coverage[node.id]||[]).includes('text')?1:0);
        return (node.children||[]).reduce((v,c)=>{
          const child=count(c);return [v[0]+child[0],v[1]+child[1]];
        },[done,fields]);
      }
      for(const n of nodes){
        const pick=selectors.find(e=>e.dataset.nodeId===n.id);
        if(!pick)continue;
        let mark=pick.parentElement.querySelector(':scope > .coverage-indicator');
        if(!mark)mark=make('span',pick.parentElement,'','coverage-indicator');
        const [done,total]=count(n);
        mark.textContent=' · '+(done===0?'Not translated':
                   done===total?'Translated draft':done+'/'+total+' fields drafted');
      }
    }
    function update(){
      refreshCoverage();
      const selected=selectedIds();
      const p=(data.prompts||[]).find(x=>x.id===prompt.value);
      const ref=reference.value;
      const old=ref==='text'?revision.value:null;
      const ready=selected.length>0 && !!p && (ref!=='text'||!!old);
      if(!ready){
        link.removeAttribute('href');link.setAttribute('aria-disabled','true');
        status.textContent=selected.length?'Select a valid recipe and reference version.':'Check one or more source nodes.';
        return;
      }
      const request={schema_version:1,work:work.work,target:target.value,
        nodes:selected,source_fingerprint:work.source_fingerprint,scope:scope.value,
        prompt:{id:p.id,sha256:p.sha256},
        reference:{mode:ref,revision:old},instructions:instructions.value};
      const fence=String.fromCharCode(96).repeat(3);
      const body='Translation request: '+work.work+' to '+target.value+
          '\n\n<!-- ctp:translation-request:v1 -->\n\n'+fence+'json\n'+
          JSON.stringify(request,null,2)+'\n'+fence+'\n';
      const url='https://github.com/'+data.repository+'/issues/new?title='+
          encodeURIComponent('[Translation] '+work.work+' → '+target.value)+
          '&body='+encodeURIComponent(body);
      link.href=url;link.removeAttribute('aria-disabled');
      status.textContent=selected.length+' source node(s) selected. Submitting the GitHub form is required.';
    }
    for(const pick of selectors){
      pick.addEventListener('change',()=>{
        if(pick.checked || !pick.checked){
          const li=pick.closest('li');
          if(li)for(const child of li.querySelectorAll('input.node-pick'))child.checked=pick.checked;
        }
        update();
      });
    }
    target.addEventListener('change',()=>{refreshHistory();update();});
    for(const input of [prompt,scope,reference,revision,instructions])
      input.addEventListener('input',update);
    versions.addEventListener('change',()=>{preview.hidden=true;});
    view.addEventListener('click',async()=>{
      const item=activeHistory().find(h=>h.revision===versions.value);
      if(!item)return;
      const selected=selectedIds();
      const nid=selected[0]||work.tree.id;
      preview.hidden=false;preview.textContent='Loading approved snapshot…';
      const base='../revisions/'+work.work+'/'+item.edition+'/'+item.revision+'/';
      try{
        const response=await fetch(base+'snapshot.json');
        if(!response.ok)throw Error('Snapshot unavailable');
        const obj=await response.json();
        const fields=obj.target_nodes && obj.target_nodes[nid];
        preview.textContent=fields?
          [(fields.label||''),(fields.text&&fields.text.markdown||'')].filter(Boolean).join('\n\n'):
          'This node was not translated in the selected revision.';
        readerLink.href=base+'read.html';
      }catch(_err){preview.textContent='Could not load the approved historical revision.';}
    });
    refreshHistory();update();
  }
})();
