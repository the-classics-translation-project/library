/* Pure revision-bound annotation operations. No DOM, network, or model calls. */
(function(root){
  'use strict';
  const check=(v,m)=>{if(!v)throw new Error(m);};
  const clone=v=>JSON.parse(JSON.stringify(v));
  function boundary(text,p){
    check(Number.isInteger(p)&&p>=0&&p<=text.length,'Invalid text position.');
    const a=text.charCodeAt(p-1),b=text.charCodeAt(p);
    check(!(a>=0xD800&&a<=0xDBFF&&b>=0xDC00&&b<=0xDFFF),'Selection splits a Unicode character.');
  }
  function anchor(text,start,end){
    boundary(text,start);boundary(text,end);check(end>start,'Select some text first.');
    return {unit:'utf16-code-units',start,end,exact:text.slice(start,end),prefix:Array.from(text.slice(0,start)).slice(-32).join(''),suffix:Array.from(text.slice(end)).slice(0,32).join('')};
  }
  function publicNote(n){return {id:n.id,node:n.node,field:n.field,scope:n.scope,anchor:clone(n.anchor),comment:n.comment};}
  function validate(report,data){
    check(report?.schema_version===2,'Unsupported report version.');
    for(const key of ['repository','work','edition','revision'])check(report[key]===data[key],'This report belongs to a different edition or revision.');
    check(typeof report.report_id==='string'&&report.report_id&&typeof report.created_at==='string'&&report.created_at,'Missing report identity/date.');
    check(Array.isArray(report.annotations)&&report.annotations.length>0,'There are no notes in this report.');
    const ids=new Set();
    for(const n of report.annotations){
      check(typeof n.id==='string'&&/^[A-Za-z0-9_-]{1,100}$/.test(n.id)&&!ids.has(n.id),'Invalid or duplicate note ID.');ids.add(n.id);
      check(typeof n.comment==='string'&&n.comment.trim()&&n.comment.length<=20000,'A comment is empty or too long.');
      const f=data.fields[`${n.node}:${n.field}`];check(f,'Unknown edition field.');
      check(n.scope==='text'||n.scope==='field','Unknown observation scope.');
      if(n.scope==='field'){check(n.anchor===null,'A whole-field comment must not have text offsets.');continue;}
      const a=n.anchor;check(a&&a.unit==='utf16-code-units','Missing text anchor.');boundary(f.text,a.start);boundary(f.text,a.end);
      check(a.end>a.start&&f.text.slice(a.start,a.end)===a.exact,'Selected text no longer matches this revision.');
      check(typeof a.prefix==='string'&&typeof a.suffix==='string'&&f.text.slice(0,a.start).endsWith(a.prefix)&&f.text.slice(a.end).startsWith(a.suffix),'Quotation context does not match.');
    }
    return report;
  }
  function id(){return 'note-'+(root.crypto?.randomUUID?.()||`${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`);}
  function report(notes,data,reportId=id()){
    return validate({schema_version:2,report_id:reportId,created_at:new Date().toISOString(),repository:data.repository,work:data.work,edition:data.edition,revision:data.revision,annotations:notes.map(publicNote)},data);
  }
  function merge(existing,incoming,data){
    validate(incoming,data);const result=clone(existing);
    for(const n of incoming.annotations){const old=result.find(x=>x.id===n.id);if(old)check(JSON.stringify(publicNote(old))===JSON.stringify(publicNote(n)),'An imported note conflicts with a saved note. No notes were changed.');else result.push({...publicNote(n),include:true});}
    return result;
  }
  const api={check,clone,anchor,publicNote,validate,report,merge,id};
  root.CTPAnnotations=api;if(typeof module!=='undefined')module.exports=api;
})(globalThis);
