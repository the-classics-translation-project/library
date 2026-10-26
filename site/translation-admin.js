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
    const materialRows=(data.materials||[]).filter(m=>!(m.tags||[]).includes('recipe'));
    const materialPanel=make('section',panel,null,'material-picker');
    make('h5',materialPanel,'Ordered materials');
    make('p',materialPanel,'Add reference or instruction documents in the order ChatGPT should receive them. Every item is removable. Full text is previewed locally after the request is accepted.','small');
    const materialSearchLabel=make('label',materialPanel,'Filter available materials','translation-option');
    const materialSearch=make('input',materialSearchLabel);materialSearch.type='search';
    const pools=make('div',materialPanel,null,'material-pools');
    const availableLabel=make('label',pools,'Available','translation-option');
    const available=make('select',availableLabel);available.size=7;
    available.setAttribute('aria-label','Available materials');
    const buttons=make('div',pools,null,'material-actions');
    const add=make('button',buttons,'Add →');add.type='button';
    const remove=make('button',buttons,'← Remove');remove.type='button';
    const up=make('button',buttons,'Move up');up.type='button';
    const down=make('button',buttons,'Move down');down.type='button';
    const appliedLabel=make('label',pools,'Applied in this order','translation-option');
    const applied=make('select',appliedLabel);applied.size=7;
    applied.setAttribute('aria-label','Applied materials in order');
    const materialNotice=make('p',materialPanel,'','small');
    const materialPreview=make('ol',materialPanel,null,'material-preview');
    const selectedMaterials=[];
    const instructionsLabel=make('label',panel,'Additional instructions (optional)','translation-option');
    const instructions=make('textarea',instructionsLabel);
    instructions.rows=2;instructions.maxLength=4000;
    instructions.placeholder='Specific instructions for this request';
    const status=make('p',panel,'','small');
    const link=make('a',panel,'Prepare translation Issue','button primary-action');
    link.target='_blank';link.rel='noopener noreferrer';

    const guides=make('section',section,null,'translation-request-panel guide-request-panel');
    make('h4',guides,'Whole-work glossary and translation guide');
    make('p',guides,'Ask ChatGPT to examine the entire original before translating chapters. The result is organized Markdown, not a rigid terminology database.','small');
    const guideTarget=labeledSelect(guides,'Target language for terminology',
        data.targets.map(t=>({value:t.id,label:t.label})));
    guideTarget.value=target.value;
    const guideState=make('p',guides,'','small');
    const guideLink=make('a',guides,'Prepare guide-generation Issue','button primary-action');
    guideLink.target='_blank';guideLink.rel='noopener noreferrer';
    make('p',guides,'After submitting the GitHub Issue, run guide-pending and guide-export --issue NUMBER locally, then use your existing ZIP relay.','small');
    function updateGuide(){
      const haveWork=!!work.guides?.work;
      const haveTarget=(work.guides?.targets||[]).includes(guideTarget.value);
      guideState.textContent='Work-level reference: '+(haveWork?'Saved':'Not generated')+
            ' · '+guideTarget.value+' terminology guide: '+(haveTarget?'Saved':'Not generated')+
            '. A new request may regenerate either guide.';
      if(!data.guide_prompt_sha256){
        guideLink.removeAttribute('href');guideLink.setAttribute('aria-disabled','true');
        return;
      }
      const request={schema_version:1,work:work.work,target:guideTarget.value,
        source_fingerprint:work.source_fingerprint,
        prompt_sha256:data.guide_prompt_sha256};
      const fence=String.fromCharCode(96).repeat(3);
      const body='Whole-work translation guide: '+work.work+' to '+guideTarget.value+
        '\n\n<!-- ctp:guide-request:v1 -->\n\n'+fence+'json\n'+
        JSON.stringify(request,null,2)+'\n'+fence+'\n';
      guideLink.href='https://github.com/'+data.repository+'/issues/new?title='+
        encodeURIComponent('[Guide] '+work.work+' → '+guideTarget.value)+
        '&body='+encodeURIComponent(body);
      guideLink.removeAttribute('aria-disabled');
    }
    guideTarget.addEventListener('change',updateGuide);
    target.addEventListener('change',()=>{
      guideTarget.value=target.value;
      updateGuide();
    });
    updateGuide();

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
    function materialApplies(m){
      return (!m.work||m.work===work.work)&&(!m.target||m.target===target.value);
    }
    function renderMaterials(){
      const previousAvailable=available.value,previousApplied=applied.value;
      available.replaceChildren();applied.replaceChildren();materialPreview.replaceChildren();
      const q=materialSearch.value.trim().toLocaleLowerCase();
      for(const m of materialRows){
        if(!materialApplies(m)||selectedMaterials.includes(m.id))continue;
        if(q&&!`${m.title} ${m.scope} ${m.kind} ${(m.tags||[]).join(' ')}`.toLocaleLowerCase().includes(q))continue;
        const option=make('option',available,m.title+' · '+m.scope+' · '+m.kind);
        option.value=m.id;
      }
      for(const id of selectedMaterials){
        const m=materialRows.find(x=>x.id===id);
        if(!m)continue;
        const option=make('option',applied,m.title+' · '+m.scope+' · '+m.kind);
        option.value=id;
        make('li',materialPreview,m.title+' · '+m.kind+' · '+m.sha256.slice(0,12));
      }
      if([...available.options].some(o=>o.value===previousAvailable))available.value=previousAvailable;
      if([...applied.options].some(o=>o.value===previousApplied))applied.value=previousApplied;
      materialNotice.textContent=selectedMaterials.length+
        ' material(s) selected. The Issue pins their order and exact versions.';
    }
    function moveMaterial(step){
      const index=selectedMaterials.indexOf(applied.value),next=index+step;
      if(index<0||next<0||next>=selectedMaterials.length)return;
      [selectedMaterials[index],selectedMaterials[next]]=[selectedMaterials[next],selectedMaterials[index]];
      renderMaterials();applied.value=selectedMaterials[next];update();
    }
    add.addEventListener('click',()=>{
      if(!available.value||selectedMaterials.includes(available.value))return;
      const id=available.value;selectedMaterials.push(id);renderMaterials();applied.value=id;update();
    });
    remove.addEventListener('click',()=>{
      const index=selectedMaterials.indexOf(applied.value);
      if(index<0)return;
      selectedMaterials.splice(index,1);renderMaterials();update();
    });
    up.addEventListener('click',()=>moveMaterial(-1));
    down.addEventListener('click',()=>moveMaterial(1));
    materialSearch.addEventListener('input',renderMaterials);
    available.addEventListener('dblclick',()=>add.click());
    applied.addEventListener('dblclick',()=>remove.click());
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
      if(selectedMaterials.length){
        request.schema_version=2;
        request.materials=selectedMaterials.map(id=>{
          const m=materialRows.find(x=>x.id===id);
          return {id:m.id,sha256:m.sha256};
        });
      }
      const fence=String.fromCharCode(96).repeat(3);
      const body='Translation request: '+work.work+' to '+target.value+
          '\n\n<!-- ctp:translation-request:v'+request.schema_version+' -->\n\n'+fence+'json\n'+
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
    target.addEventListener('change',()=>{
      refreshHistory();
      const removed=selectedMaterials.filter(id=>{
        const m=materialRows.find(x=>x.id===id);return !m||!materialApplies(m);
      });
      for(const id of removed)selectedMaterials.splice(selectedMaterials.indexOf(id),1);
      renderMaterials();
      if(removed.length)materialNotice.textContent='Removed '+removed.length+
        ' material(s) that do not apply to the new target.';
      update();
    });
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
    refreshHistory();renderMaterials();update();
  }
})();
