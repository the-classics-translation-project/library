(() => {
  'use strict';
  const data=JSON.parse(document.getElementById('admin-data').textContent), $=id=>document.getElementById(id);
  const fold=text=>String(text).normalize('NFKD').replace(/\p{M}/gu,'').toLocaleLowerCase();
  const records=data.catalogue.records.map(r=>({...r,key:fold(`${r.id} ${r.title} ${r.authors} ${r.languages}`)}));
  let chosen=null;
  $('catalogue-status').textContent=data.catalogue.kind==='full-csv' ? `${records.length.toLocaleString()} titles · catalogue ${data.catalogue.retrieved_at?.slice(0,10) || ''}` : `${records.length} cached titles; the full catalogue has not been downloaded. You can also enter a Gutenberg number.`;
  function search() {
    const q=fold($('search').value.trim()); $('results').replaceChildren();
    if(!q)return;
    const terms=q.split(/\s+/u), hits=records.filter(r=>terms.every(t=>r.key.includes(t))).slice(0,40);
    if(/^\d+$/.test(q) && +q>0 && +q<10000000 && !hits.some(r=>r.id===+q))hits.unshift({id:+q,title:`Project Gutenberg #${q}`,authors:'Metadata will be checked during import',languages:'',type:'Text'});
    for(const r of hits){
      const b=document.createElement('button');b.className='search-result';b.type='button';
      const title=document.createElement('strong');title.textContent=r.title;
      const meta=document.createElement('span');meta.textContent=`${r.authors} · ${r.languages || 'language not checked'} · #${r.id}`;
      b.append(title,meta);b.addEventListener('click',()=>select(r));$('results').append(b);
    }
    if(!hits.length){const p=document.createElement('p');p.className='small';p.textContent='No matches in this catalogue.';$('results').append(p);}
  }
  let timer; $('search').addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(search,120);});
  for(const t of data.targets){const l=document.createElement('label'),box=document.createElement('input');box.type='checkbox';box.value=t.id;box.addEventListener('change',request);l.append(box,document.createTextNode(t.label));$('targets').append(l);}
  function select(r){chosen=r;$('selection').hidden=false;$('selected-title').textContent=r.title;$('selected-author').textContent=`${r.authors} · #${r.id}`;$('results').replaceChildren();request();}
  function request(){
    if(!chosen)return;
    const targets=[...$('targets').querySelectorAll('input:checked')].map(x=>x.value);
    const req={schema_version:1,source:{type:'gutenberg',id:chosen.id},targets};
    const payload=JSON.stringify(req,null,2);$('request-data').value=payload;
    const body=`Work request: Gutenberg #${chosen.id}\n\n<!-- ctp:work-request:v1 -->\n\n\`\`\`json\n${payload}\n\`\`\`\n`;
    const link=$('prepare-issue');
    if(targets.length){link.href=`https://github.com/${data.repository}/issues/new?title=${encodeURIComponent(`[Work request] Gutenberg #${chosen.id}`)}&body=${encodeURIComponent(body)}`;link.removeAttribute('aria-disabled');}
    else{link.removeAttribute('href');link.setAttribute('aria-disabled','true');}
    $('request-warning').textContent=targets.length?'The request is added to the queue after it is submitted on GitHub and accepted by intake.':'Select a target language.';
  }
  if(!data.queue.length)$('queue').textContent='No work requested yet.';
  for(const r of data.queue){const row=document.createElement('div');row.className='queue-row';const name=document.createElement('span');name.textContent=`Gutenberg #${r.source_id} · ${r.target}`;const status=document.createElement('span');status.className='meta';status.textContent=r.stage+(r.total_fields!==null?` · ${r.completed_fields}/${r.total_fields} fields present`:'');if(r.rights_reasons?.length){const details=document.createElement('details'),summary=document.createElement('summary'),list=document.createElement('ul');summary.textContent='Why this source is on hold';for(const reason of r.rights_reasons){const item=document.createElement('li');item.textContent=reason;list.append(item);}details.append(summary,list);status.append(details);}row.append(name,status);$('queue').append(row);}
})();
