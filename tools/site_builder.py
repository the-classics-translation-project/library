"""Static readers, a revision-bound annotation workbench and a token-free admin UI."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import json
import shutil
import zipfile
import xml.etree.ElementTree as ET
import ctp as c
from source_import import walk


def title(obj):
    if not c.is_tree(obj):return obj['edition']['title']
    return obj['target_nodes'].get(obj['tree']['id'],{}).get('label',obj['work']['id'])

def navigation(config,where=''):
    return f'<header class="sitebar"><a href="{where}index.html">{c.esc(config["name"])}</a><nav><a href="{where}contribute/index.html">Workbench</a> <a href="{where}admin/index.html">Admin</a></nav></header>'

def reader(obj,rev,config,css):
    fields=c.field_map(obj); ed=obj['edition']; rootid=obj['tree']['id']
    def section(n,depth):
        nid=n['id'];target=obj['target_nodes'].get(nid,{})
        body=''
        if depth and 'label' in target:body+=f'<h{min(depth+1,6)}>{c.esc(target["label"])}</h{min(depth+1,6)}>'
        if 'text' in target:body+=target['text']['html']
        body+=''.join(section(child,depth+1) for child in n.get('children',[]))
        return f'<section class="reading-section" id="s-{nid}">{body}</section>' if body else ''
    toc=''.join(f'<li style="margin-inline-start:{depth}em"><a href="#s-{n["id"]}">{c.esc(obj["target_nodes"][n["id"]].get("label",f"Section {i+1}"))}</a></li>'
                for i,(n,depth) in enumerate(walk(obj['tree'])) if n['id'] in obj['target_nodes'])
    title_heading=f'<h1>{c.esc(title(obj))}</h1>' if 'label' in obj['target_nodes'].get(rootid,{}) else ''
    body=navigation(config,'../../../../')+f'''<main class="reading">{title_heading}<p class="byline">{c.esc(ed.get('author_credit',obj['work']['author']))}</p>
<details><summary>{'Draft · ' if ed['status']=='draft' else ''}Edition information</summary><p>{c.esc(ed['description'])}</p><p>{len(obj['missing'])} source fields not yet translated.</p><p>{c.esc(obj['work']['source_provenance'])}</p><p>{c.esc(ed['rights_note'])}</p><p class="hash">Revision {rev}</p></details>
<details><summary>Contents</summary><ol class="tree-toc">{toc}</ol></details>{section(obj['tree'],0)}<p><a href="review.html">Annotate this revision</a> · <a href="edition.epub">EPUB</a></p></main>'''
    return c.page(title(obj),body,css,ed['language'],ed['direction'])

def reviewer(obj,rev,config,css,root,demo):
    data={'schema_version':2,'repository':config['repository'],'revision':rev,'work':obj['work']['id'],'edition':obj['edition']['id'],
          'title':title(obj),'language':obj['edition']['language'],'direction':obj['edition']['direction'], 'tree':obj['tree'],
          'fields':c.field_map(obj),'source_nodes':obj['source_nodes'],'source_language':obj['work']['language'],
          'status':obj['edition']['status'],'missing':obj['missing'],'demo':demo,'description':obj['edition']['description']}
    body=navigation(config,'../../../../')+'''<div class="reader-shell" id="reader-shell"><main class="workbench" id="workbench">
<header class="bookhead"><h1 id="book-title"></h1><p class="byline" id="book-credit"></p></header>
<div class="toolbar" aria-label="Reading controls" dir="ltr"><button id="prev" aria-label="Previous section">←</button><select id="sections" aria-label="Section"></select><button id="next" aria-label="Next section">→</button><span class="toolbar-space"></span><button id="notes-toggle">Notes <span id="count">0</span></button><details class="reader-menu" id="menu"><summary aria-label="More options">···</summary><div class="reader-menu-content"><button id="whole-note">Section note</button><button id="show-margins">Hide margin notes</button><details><summary>About / Help</summary><p>Select any edition text to comment. Click a margin note or highlight to edit it. Notes can span paragraphs, but not two distinct labelled fields.</p><p>Notes stay in this browser. Export a report to back them up; preparing a GitHub form does not submit it.</p><p id="edition-info"></p><p id="revision-info" class="hash"></p><a href="read.html">Reader view</a> · <a href="edition.epub">EPUB</a></details></div></details></div>
<p id="warning" class="notice warning" role="status" hidden></p><p id="message" role="status" class="statusline"></p>
<div id="section-content"></div><details class="source-details"><summary>Original</summary><div id="source" class="reading-text"></div></details>
<footer class="reading-footer"><button id="next-bottom">Next →</button></footer></main><aside id="margin" class="margin-rail" aria-label="Margin notes"></aside><svg class="note-connectors" id="connectors" aria-hidden="true"></svg></div>
<div id="composer" class="comment-popover" role="dialog" aria-label="Comment" hidden><form id="comment-form"><p id="quote" class="popover-quote"></p><label class="sr-only" for="comment">Comment</label><textarea id="comment" rows="3" maxlength="20000" required placeholder="Comment…"></textarea><div class="popover-actions"><button id="delete" type="button" class="subtle" hidden>Remove</button><span class="toolbar-space"></span><button id="cancel" type="button" class="subtle">Cancel</button><button type="submit" class="primary-action">Save</button></div></form></div>
<aside id="notebook" class="notes-panel" aria-label="Notes" hidden><div class="panel-heading"><h2>Notes</h2><button id="close-notes">Close</button></div><div id="notes"></div><div class="actions"><button id="export">Export JSON</button><button id="report">Prepare Issue</button><button id="import">Import</button><input id="import-file" type="file" accept=".json" hidden></div><div id="submission" hidden><textarea id="report-body" rows="10" readonly aria-label="Issue report"></textarea><div class="actions"><button id="copy-report">Copy</button><a id="issue-link" class="button" target="_blank" rel="noopener noreferrer">Open GitHub form</a></div></div></aside>'''
    scripts=(root/'site/annotation-core.js').read_text()+'\n'+(root/'site/reader.js').read_text()
    return c.page(title(obj)+' · Workbench',body,css,tail=f'<script type="application/json" id="edition-data">{c.js_data(data)}</script><script>{scripts}</script>')

def epub(obj,rev,path,root):
    """Small EPUB 3 writer: tree-shaped TOC, no dependency on sentence structure."""
    from html import escape
    t=title(obj); ed=obj['edition']; ns='http://www.w3.org/1999/xhtml'
    included=[]
    def keep(n):return n['id'] in obj['target_nodes'] or any(keep(x) for x in n.get('children',[]))
    def nav(n):
        if not keep(n):return ''
        nid=n['id'];target=obj['target_nodes'].get(nid,{})
        label=target.get('label',f'Section {nid[1:].lstrip("0") or "0"}')
        children=''.join(nav(ch) for ch in n.get('children',[]))
        heading=f'<a href="{nid}.xhtml">{escape(label)}</a>' if target else f'<span>{escape(label)}</span>'
        return f'<li>{heading}{"<ol>"+children+"</ol>" if children else ""}</li>' 
    def xhtml(title,body):
        text=f'<?xml version="1.0" encoding="utf-8"?><html xmlns="{ns}" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{ed["language"]}" lang="{ed["language"]}" dir="{ed["direction"]}"><head><title>{escape(title)}</title><link rel="stylesheet" href="style.css" type="text/css"/></head><body>{body}</body></html>'
        # Pandoc's HTML5 writer uses XML-compatible void tags for our allowed subset.
        ET.fromstring(text)
        return text.encode()
    docs={}
    for n,depth in walk(obj['tree']):
        if n['id'] not in obj['target_nodes']:continue
        nid=n['id'];target=obj['target_nodes'].get(nid,{})
        label=target.get('label','')
        body=f'<h1>{escape(label)}</h1>' if label else ''
        if 'text' in target:body+=target['text']['html']
        if depth==0:
            body+=f'<p>{escape(ed.get("author_credit",obj["work"]["author"]))}</p><p>{escape(ed["description"])}</p><p>Status: {ed["status"]}. {len(obj["missing"])} source fields remain untranslated.</p>'
        docs[nid+'.xhtml']=xhtml(label or t,body);included.append(nid)
    docs['nav.xhtml']=xhtml(t,f'<nav epub:type="toc" id="toc"><h1>Contents</h1><ol>{nav(obj["tree"])}</ol></nav>')
    docs['about.xhtml']=xhtml('Edition information',f'<h1>Edition information</h1><p>{escape(obj["work"]["source_edition"])}</p><p>{escape(obj["work"]["source_provenance"])}</p><p>{escape(ed["rights_note"])}</p><p>AI involvement: {escape(ed["production"].get("ai_use","recorded in repository"))}</p><p>Revision: {rev}</p>')
    now=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    manifest='<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/><item id="style" href="style.css" media-type="text/css"/><item id="about" href="about.xhtml" media-type="application/xhtml+xml"/>'
    manifest+=''.join(f'<item id="{nid}" href="{nid}.xhtml" media-type="application/xhtml+xml"/>' for nid in included)
    spine=''.join(f'<itemref idref="{nid}"/>' for nid in included)+'<itemref idref="about"/>'
    creator=ed.get('author_credit',obj['work']['author'])
    creator_xml=f'<dc:creator>{escape(creator)}</dc:creator>' if creator else ''
    opf=f'''<?xml version="1.0" encoding="UTF-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="uid">urn:sha256:{rev}</dc:identifier><dc:title>{escape(t)}</dc:title><dc:language>{ed['language']}</dc:language>{creator_xml}<dc:description>{escape(ed['description'])}</dc:description><meta property="dcterms:modified">{now}</meta></metadata><manifest>{manifest}</manifest><spine page-progression-direction="{ed['direction']}">{spine}</spine></package>'''
    ET.fromstring(opf)
    container=b'<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/></rootfiles></container>'
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype','application/epub+zip',compress_type=zipfile.ZIP_STORED)
        z.writestr('META-INF/container.xml',container);z.writestr('EPUB/package.opf',opf)
        z.writestr('EPUB/style.css',(root/'site/epub.css').read_bytes())
        for name,data in docs.items():z.writestr('EPUB/'+name,data)

def admin(root,config,css):
    from intake import queue_status
    from translation_jobs import prompt_catalogue, _guide
    catalogue_path=root/'data/gutenberg-catalogue.json'
    cat=c.read_json(catalogue_path) if catalogue_path.exists() else {'kind':'unavailable','records':[],'source':''}
    rows=queue_status(root)
    def summary_tree(node):
        # Only public labels and mechanical IDs go to Admin, never full prose.
        return {'id':node['id'], **({'label':node['label']} if 'label' in node else {}),
                'has_text':'text' in node,
                'children':[summary_tree(child) for child in node.get('children',[])]}
    sources=[]
    requests=c.read_json(root/'queue.json')['works'] if (root/'queue.json').exists() else []
    for request in requests:
        wd=root/'books'/request['id']
        related=next((row for row in rows if row['work']==request['id']),None)
        item={'work':request['id'], 'source_id':request['source']['id'],
              'stage':related['stage'] if related else 'source needed',
              'targets':request['targets']}
        if (wd/'structure.json').exists() and (wd/'work.json').exists():
            work,tree=c.validate_work(wd)
            item.update(author=work['author'],tree=summary_tree(tree),
                        source_fingerprint=c.source_fingerprint(wd))
            coverage={}
            for path in (wd/'editions').glob('*/edition.json'):
                ed=c.read_json(path)
                c.validate_tree_edition(tree,ed,path.parent)
                coverage[ed['language']]={nid:sorted(fields)
                                         for nid,fields in ed['nodes'].items()}
            item['coverage']=coverage
            work_guide=wd/'reference/current.json'
            if work_guide.exists(): _guide(work_guide.parent)
            languages=[]
            for pointer in sorted((wd/'editions').glob('*/reference/current.json')):
                _guide(pointer.parent)
                languages.append(pointer.parents[1].name)
            item['guides']={'work':work_guide.exists(),'targets':languages}
            # Only approved catalogue revisions may expose translated prose
            # on public Pages. Other draft history stays in Git/local tools.
            item['history']=[]
            for rec,snap in c.load_catalog(root,False):
                if rec['work']!=request['id'] or not c.is_tree(snap):continue
                if snap['edition']['language'] not in {t['id'] for t in config['targets']}:
                    continue
                item['history'].append({
                    'revision':rec['revision'],'edition':rec['edition'],
                    'target':snap['edition']['language'],'audience':rec['audience'],
                    'node_ids':sorted(snap['target_nodes']),
                    'model':snap['production_runs'][-1]['model_label']
                            if snap.get('production_runs') else 'unknown'})
            item['history'].reverse()
        sources.append(item)
    guide_prompt=root/'prompts/whole-work-guide.md'
    data={'repository':config['repository'],'targets':config.get('targets',[]),
          'catalogue':cat,'queue':rows,'sources':sources,'prompts':prompt_catalogue(root),
          'guide_prompt_sha256':c.digest(guide_prompt.read_bytes())
                               if guide_prompt.is_file() else None}
    body=navigation(config,'../')+'''<main class="catalogue admin"><h1>Add a work</h1><label class="sr-only" for="search">Search title, author or Gutenberg number</label><input id="search" class="catalogue-search" type="search" placeholder="Title, author, or Gutenberg number" autocomplete="off"><p id="catalogue-status" class="small"></p><div id="results" role="list"></div><section id="selection" hidden><h2 id="selected-title"></h2><p id="selected-author" class="meta"></p><fieldset id="targets"><legend>Target languages</legend></fieldset><div class="actions"><a id="prepare-issue" class="button primary-action" target="_blank" rel="noopener noreferrer">Prepare GitHub Issue</a></div><p id="request-warning" class="small"></p><details><summary>Request data</summary><textarea id="request-data" rows="8" readonly></textarea></details></section><h2 class="queue-heading">Work queue</h2><div id="queue"></div><h2 class="queue-heading">Source trees</h2><p class="small">Select source nodes to request translation or retranslation. Draft coverage is informational; historical text on Pages appears only for explicitly approved revisions.</p><div id="source-trees"></div><details class="admin-help"><summary>Help</summary><p>The form prepares a request; submit it on GitHub. Only configured maintainers' requests are imported into the queue. No credentials are stored here. A queued request does not authorize a public book release or paid model calls.</p><p>Requested Gutenberg sources are checked automatically for US/Japan source admission. Passing sources are saved to the repository; held sources show the reason below. This does not approve a translated edition for publication.</p><p>To refresh all Gutenberg titles, run <code>./ctp catalogue-refresh</code> or the catalogue workflow.</p></details></main>'''
    return c.page('Admin · '+config['name'],body,css,tail=f'<script id="admin-data" type="application/json">{c.js_data(data)}</script><script>{(root/"site/admin.js").read_text()}</script><script>{(root/"site/translation-admin.js").read_text()}</script>')

def build_site(root: Path,demo: bool=False,make_epub: bool=False) -> Path:
    c.validate_project(root)
    config=c.read_json(root/'project.json');records=c.load_catalog(root,demo)
    css=(root/'site/site.css').read_text();script=(root/'site/review.js').read_text()
    out=root/'dist';c.check(not out.is_symlink(),'Refusing symlinked build directory')
    # Stage the complete build before replacing any previous good site.
    staging=root/'build/site-next';c.check(not staging.is_symlink(),'Refusing symlinked staging directory')
    if staging.exists():shutil.rmtree(staging)
    staging.mkdir(parents=True);(staging/'.nojekyll').touch()
    readers,reviews=[],[]
    for rec,obj in records:
        rev=rec['revision'];ed=obj['edition'];relative=Path('revisions')/rec['work']/rec['edition']/rev
        folder=staging/relative;folder.mkdir(parents=True)
        is_demo=bool(obj['work'].get('fixture')) or rec['work'].startswith('demo-')
        if c.is_tree(obj):
            read_html=reader(obj,rev,config,css);review_html=reviewer(obj,rev,config,css,root,is_demo)
            if make_epub:epub(obj,rev,folder/'edition.epub',root)
        else:
            read_html=c.legacy.build_reader(obj,rev,config,css)
            review_html=c.legacy.build_reviewer(obj,rev,config,css,script,is_demo)
            if make_epub:c.legacy.build_epub(obj,rev,folder/'edition.epub',root)
        if not make_epub:
            read_html=read_html.replace('<a href="edition.epub">EPUB</a>','')
            review_html=review_html.replace('<a href="edition.epub">EPUB</a>','')
        (folder/'read.html').write_text(read_html,encoding='utf-8');(folder/'review.html').write_text(review_html,encoding='utf-8')
        c.write_json(folder/'snapshot.json',obj)
        if not rec['listed']:continue
        link=relative.as_posix();t=c.esc(title(obj))
        if rec['audience']=='readers':
            epub_link=f' · <a href="{link}/edition.epub">EPUB</a>' if make_epub else ''
            readers.append(f'<li class="book-row"><h2>{t}</h2><p class="meta">{c.esc(ed["language"])}</p><a href="{link}/read.html">Read HTML</a>{epub_link}</li>')
        status='Sample' if is_demo else ed['status'].capitalize()
        reviews.append(f'<li class="book-row"><h2>{t}</h2><p class="meta">{c.esc(ed["language"])} · {status}</p><a href="../{link}/review.html">Read and annotate</a></li>')
    listing='<ul class="book-list">'+''.join(readers)+'</ul>' if readers else '<p class="empty-state">No finished editions yet.</p>'
    body=navigation(config)+f'<main class="catalogue"><h1>The library</h1><p class="intro">{c.esc(config["description"])}</p>{listing}</main>'
    (staging/'index.html').write_text(c.page(config['name'],body,css),encoding='utf-8')
    (staging/'contribute').mkdir()
    body=navigation(config,'../')+'<main class="catalogue"><h1>Workbench</h1>'+(('<ul class="book-list">'+''.join(reviews)+'</ul>') if reviews else '<p class="empty-state">No review drafts yet.</p>')+'</main>'
    (staging/'contribute/index.html').write_text(c.page('Workbench',body,css),encoding='utf-8')
    (staging/'admin').mkdir();(staging/'admin/index.html').write_text(admin(root,config,css),encoding='utf-8')
    c.write_json(staging/'build-manifest.json',{'schema_version':1,'project_version':c.VERSION,'demo':demo,'epub':make_epub,'revisions':[r['revision'] for r,_ in records]})
    if out.exists():shutil.rmtree(out)
    staging.replace(out)
    return out
