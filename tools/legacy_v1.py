#!/usr/bin/env python3
"""Local-first snapshot, review validation and static publishing. No network writes."""
from __future__ import annotations
import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}")
HASH = re.compile(r"[0-9a-f]{64}")
MARKDOWN = "markdown-smart-raw_html-raw_tex-yaml_metadata_block"

class ProjectError(ValueError):
    pass

def check(condition: bool, message: str) -> None:
    if not condition:
        raise ProjectError(message)

def canonical(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def object_hash(obj: Any) -> str:
    return digest(canonical(obj))

def pairs(items: list) -> dict:
    result = {}
    for key, value in items:
        check(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result

def invalid_constant(value: str) -> None:
    raise ProjectError(f"Non-finite JSON number: {value}")

def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=invalid_constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProjectError(f"Cannot read {path}: {exc}") from exc

def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")

def nonempty(obj: dict, field: str) -> str:
    value = obj.get(field)
    check(isinstance(value, str) and bool(value.strip()), f"Missing/empty {field}")
    return value

def ident(value: Any) -> str:
    check(isinstance(value, str) and bool(ID.fullmatch(value)), f"Invalid identifier: {value!r}")
    return value

def schema(obj: Any) -> None:
    check(isinstance(obj, dict), "Expected an object")
    check(type(obj.get("schema_version")) is int and obj["schema_version"] == 1, "Expected schema_version 1")

def source_file(base: Path, relative: str) -> Path:
    check(isinstance(relative, str), "File path must be a string")
    path = Path(relative)
    check(not path.is_absolute() and ".." not in path.parts, f"Unsafe path: {relative}")
    target = (base/path).resolve()
    check(target.is_relative_to(base.resolve()), f"Path escapes directory: {relative}")
    check(target.suffix == ".md" and target.is_file(), f"Missing Markdown file: {relative}")
    return target

def read_markdown(path: Path) -> str:
    try:
        text = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise ProjectError(f"Cannot read UTF-8 source {path}: {exc}") from exc
    check(bool(text.strip()), f"Empty text: {path}")
    check("\x00" not in text and not text.startswith("\ufeff"), f"NUL/BOM in {path}")
    check(not text.lstrip().startswith("REPLACE"), f"Unfilled template: {path}")
    return text

def validate_metadata(meta: dict, edition: bool = False) -> None:
    schema(meta)
    ident(meta.get("id"))
    for key in ("title", "language", "rights_note"):
        nonempty(meta, key)
    check(bool(re.fullmatch(r"[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*", meta["language"])), "Invalid language tag")
    if edition:
        check(meta.get("direction") in ("ltr", "rtl"), "direction must be ltr or rtl")
        check(meta.get("kind") in ("translation", "modernization"), "Invalid edition kind")
        check(meta.get("status") in ("draft", "ready"), "Invalid edition status")
        nonempty(meta, "label")
        nonempty(meta, "description")
        check(isinstance(meta.get("production"), dict), "production must be an object")
    else:
        for key in ("author", "source_edition", "source_provenance"):
            nonempty(meta, key)
    check(isinstance(meta.get("sections"), list), "sections must be an array")
    check(edition or bool(meta["sections"]), "A work needs a source inventory")
    ids = []
    for section in meta["sections"]:
        check(isinstance(section, dict), "Section must be an object")
        ids.append(ident(section.get("id")))
        nonempty(section, "title")
        nonempty(section, "file")
    check(len(ids) == len(set(ids)), "Duplicate section IDs")

def check_inventory(work: dict, edition: dict) -> list[str]:
    expected = [s["id"] for s in work["sections"]]
    present = [s["id"] for s in edition["sections"]]
    check(all(s in expected for s in present), "Unknown source section ID")
    check(present == [s for s in expected if s in present], "Target sections out of source order")
    missing = [s for s in expected if s not in present]
    check(edition["status"] != "ready" or not missing, "Ready edition has missing sections")
    return missing

def load_work(work_dir: Path, edition_id: str) -> tuple[dict, dict, Path]:
    ident(edition_id)
    work_dir = work_dir.resolve()
    work = read_json(work_dir/"work.json")
    validate_metadata(work)
    check(work["id"] == work_dir.name, "Work directory must match ID")
    ed_dir = work_dir/"editions"/edition_id
    check(ed_dir.resolve().is_relative_to(work_dir), "Edition path escapes work")
    ed = read_json(ed_dir/"edition.json")
    validate_metadata(ed, True)
    check(ed["id"] == edition_id, "Edition directory must match ID")
    for meta, base in ((work, work_dir), (ed, ed_dir)):
        for s in meta["sections"]:
            read_markdown(source_file(base, s["file"]))
    check_inventory(work, ed)
    return work, ed, ed_dir

class SafeHTML(HTMLParser):
    TAGS = {"p", "em", "strong", "a", "span", "blockquote", "ul", "ol", "li", "hr", "br", "h1", "h2", "h3", "h4", "h5", "h6", "code", "pre", "sup", "sub", "del", "section", "div"}
    ATTRS = {"id", "class", "href", "title", "role", "aria-label", "start", "type"}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
    def handle_starttag(self, tag, attrs):
        check(tag in self.TAGS, f"Unsupported/unsafe HTML tag: {tag}")
        for key, value in attrs:
            check(key in self.ATTRS, f"Unsupported/unsafe HTML attribute: {key}")
            if key == "id":
                check(bool(value) and value.startswith("ctp-prose-"), "Unnamespaced prose HTML ID")
            if key == "href":
                val = value or ""
                check(val.startswith("#") or urlparse(val).scheme.lower() in ("http", "https", "mailto"), "Unsafe/unsupported link")
                check(not any(ord(c) < 32 for c in val), "Control character in URL")
    def handle_endtag(self, tag):
        check(tag in self.TAGS, f"Unsupported closing HTML tag: {tag}")
    def handle_data(self, data):
        self.parts.append(data)
    def handle_comment(self, data):
        raise ProjectError("Comments are unsupported in frozen HTML")
    def handle_decl(self, decl):
        raise ProjectError("Unexpected declaration in frozen HTML")

def html_text(fragment: str) -> str:
    parser = SafeHTML()
    parser.feed(fragment)
    parser.close()
    return "".join(parser.parts)

def pandoc(*args: str, text: str = "") -> str:
    check(shutil.which("pandoc") is not None, "Install Pandoc 3.x and retry")
    try:
        return subprocess.run(["pandoc", *args], input=text, encoding="utf-8", text=True, capture_output=True, timeout=120, check=True).stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ProjectError(f"Pandoc failed: {getattr(exc, 'stderr', '') or exc}") from exc

def render(text: str, namespace: str = "render") -> str:
    output = pandoc("--sandbox", f"--from={MARKDOWN}", "--to=html5", "--wrap=none", f"--id-prefix=ctp-prose-{namespace}-", text=text)
    # Pandoc leaves its footnotes container unprefixed even with --id-prefix.
    output = output.replace('id="footnotes"', f'id="ctp-prose-{namespace}-footnotes"')
    html_text(output)
    return output

def git_context(root: Path) -> str | None:
    proc = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else None

def freeze(work_dir: Path, edition_id: str, root: Path = ROOT) -> tuple[str, Path]:
    work, ed, ed_dir = load_work(work_dir, edition_id)
    check(bool(ed["sections"]), "No target sections to snapshot")
    source, target = [], []
    for meta, base, output in ((work, work_dir, source), (ed, ed_dir, target)):
        for s in meta["sections"]:
            text = read_markdown(source_file(base, s["file"]))
            fragment = render(text, ("source-" if output is source else "target-") + s["id"])
            output.append({"id":s["id"], "title":s["title"], "markdown":text, "markdown_sha256":digest(text.encode("utf-8")), "html":fragment, "text":html_text(fragment)})
    obj = {"schema_version":1, "work":work, "edition":ed, "source_sections":source, "sections":target, "missing_sections":check_inventory(work,ed), "renderer":{"name":"pandoc", "version":pandoc("--version").splitlines()[0], "input_format":MARKDOWN, "html_format":"html5", "wrap":"none"}, "git_context":git_context(root)}
    revision = object_hash(obj)
    path = root/"revisions"/work["id"]/ed["id"]/(revision+".json")
    validate_snapshot(obj, revision)
    if path.exists():
        check(read_json(path) == obj, "Archive path contains different data")
    else:
        write_json(path,obj)
    return revision,path

def validate_snapshot(obj: dict, revision: str) -> None:
    schema(obj)
    check(bool(HASH.fullmatch(revision)), "Expected full SHA-256 revision")
    check(object_hash(obj) == revision, "Snapshot hash mismatch: frozen records must not change")
    validate_metadata(obj["work"])
    validate_metadata(obj["edition"],True)
    check(obj["missing_sections"] == check_inventory(obj["work"],obj["edition"]), "Incorrect missing inventory")
    for key,meta in (("source_sections",obj["work"]),("sections",obj["edition"])):
        sections = obj[key]
        check(isinstance(sections,list), "Frozen sections must be arrays")
        check([s["id"] for s in sections] == [s["id"] for s in meta["sections"]], "Frozen inventory mismatch")
        for s in sections:
            check(s["markdown_sha256"] == digest(s["markdown"].encode("utf-8")), "Markdown hash mismatch")
            check(s["text"] == html_text(s["html"]), "HTML/text anchor representation mismatch")

def snapshot_path(root: Path, work: str, edition: str, revision: str) -> Path:
    ident(work); ident(edition)
    check(isinstance(revision,str) and bool(HASH.fullmatch(revision)), "Invalid revision")
    return root/"revisions"/work/edition/(revision+".json")

def load_snapshot(root: Path, work: str, edition: str, revision: str) -> dict:
    obj = read_json(snapshot_path(root,work,edition,revision))
    validate_snapshot(obj,revision)
    check(obj["work"]["id"] == work and obj["edition"]["id"] == edition, "Snapshot/path identity mismatch")
    return obj

def load_catalog(root: Path, demo: bool = False) -> list[tuple[dict,dict]]:
    paths = [root/"catalog.json"] + ([root/"examples/catalog.json"] if demo else [])
    output,seen = [],set()
    for path in paths:
        data=read_json(path); schema(data)
        check(isinstance(data.get("revisions"),list), "Catalogue revisions must be an array")
        for rec in data["revisions"]:
            nonempty(rec,"approved_by"); nonempty(rec,"approval_note")
            check(rec.get("audience") in ("review","readers"), "Invalid audience")
            check(type(rec.get("listed")) is bool, "listed must be boolean")
            check(rec["revision"] not in seen, "Duplicate catalogue revision")
            seen.add(rec["revision"])
            obj=load_snapshot(root,rec["work"],rec["edition"],rec["revision"])
            if rec["audience"] == "readers":
                check(obj["edition"]["status"] == "ready" and not obj["missing_sections"], "Reader listing requires ready, complete section inventory")
            output.append((rec,obj))
    return output

def validate_project(root: Path = ROOT) -> dict:
    config=read_json(root/"project.json"); schema(config); nonempty(config,"name")
    check(bool(re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",config.get("repository",""))), "repository must be owner/name")
    editions=0
    for base in (root/"books",root/"examples"):
        for path in base.glob("*/work.json"):
            meta=read_json(path); validate_metadata(meta)
            for s in meta["sections"]:
                read_markdown(source_file(path.parent,s["file"]))
            for ed in (path.parent/"editions").glob("*/edition.json"):
                load_work(path.parent,ed.parent.name); editions+=1
    snapshots=0
    for path in (root/"revisions").glob("*/*/*.json"):
        load_snapshot(root,path.parents[1].name,path.parent.name,path.stem); snapshots+=1
    load_catalog(root)
    if (root/"examples/catalog.json").exists():load_catalog(root,True)
    return {"editable_editions":editions,"frozen_snapshots":snapshots,"note":"Structural checks only; not semantic or literary review."}

def utf16_slice(text: str,start: int,end: int) -> str:
    check(type(start) is int and type(end) is int,"Offsets must be integer UTF-16 code units")
    data=text.encode("utf-16-le")
    check(0<=start<=end<=len(data)//2,"Offsets outside section")
    try:return data[2*start:2*end].decode("utf-16-le")
    except UnicodeError as exc:raise ProjectError("Anchor splits a surrogate pair") from exc

def validate_review(report: dict,root: Path = ROOT) -> dict:
    schema(report);nonempty(report,"report_id");nonempty(report,"created_at")
    check(report.get("repository")==read_json(root/"project.json")["repository"],"Report belongs to another repository")
    snap=load_snapshot(root,report["work"],report["edition"],report["revision"])
    sections={s["id"]:s for s in snap["sections"]}
    notes=report.get("annotations")
    check(isinstance(notes,list) and bool(notes),"No annotations")
    ids=set()
    for note in notes:
        nid=nonempty(note,"id");check(nid not in ids,"Duplicate annotation ID");ids.add(nid)
        nonempty(note,"comment")
        check(note.get("section") in sections,"Unknown section")
        check(note.get("scope") in ("text","section"),"Unknown annotation scope")
        if note["scope"]=="section":
            check(note.get("anchor") is None,"Section comment must have null anchor");continue
        a=note.get("anchor");check(isinstance(a,dict),"Missing anchor")
        check(a.get("unit")=="utf16-code-units","Unknown offset unit")
        text=sections[note["section"]]["text"]
        selected=utf16_slice(text,a["start"],a["end"])
        check(bool(selected) and selected==a.get("exact"),"Quotation mismatch")
        check(isinstance(a.get("prefix"),str) and isinstance(a.get("suffix"),str),"Missing context")
        check(utf16_slice(text,0,a["start"]).endswith(a["prefix"]),"Prefix mismatch")
        check(utf16_slice(text,a["end"],len(text.encode("utf-16-le"))//2).startswith(a["suffix"]),"Suffix mismatch")
    return {"revision":report["revision"],"annotations":len(notes),"anchors":"valid"}

def esc(value: Any) -> str:
    return html.escape(str(value),quote=True)

def js_data(value: Any) -> str:
    return json.dumps(value,ensure_ascii=False).replace("<","\\u003c").replace("&","\\u0026")

def page(title: str,body: str,css: str,language: str="en",direction: str="ltr",tail: str="") -> str:
    return f'<!doctype html>\n<html lang="{esc(language)}" dir="{direction}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="referrer" content="no-referrer"><title>{esc(title)}</title><style>{css}</style></head><body>{body}{tail}</body></html>\n'

def build_reader(obj: dict,revision: str,config: dict,css: str) -> str:
    ed,work=obj["edition"],obj["work"]
    toc="".join(f'<li><a href="#s-{esc(s["id"])}">{esc(s["title"])}</a></li>' for s in obj["sections"])
    chapters="".join(f'<section class="reading-section" id="s-{esc(s["id"])}"><h2>{esc(s["title"])}</h2>{s["html"]}</section>' for s in obj["sections"])
    body=f'''<header class="sitebar"><a href="../../../../index.html">{esc(config['name'])}</a><a href="review.html">Contributor view</a></header>
<main class="reading"><p class="eyebrow">{esc(ed['label'])}</p><h1>{esc(ed['title'])}</h1><p class="byline">{esc(work['author'])}</p><p class="notice">{esc(ed['description'])}</p><p class="meta">{esc(ed['status'])} · {esc(ed['language'])} · revision {revision[:12]}</p>
<details><summary>Edition information</summary><p>Source: {esc(work['source_edition'])}</p><p>{esc(work['source_provenance'])}</p><p>AI involvement: {esc(ed['production'].get('ai_use','unknown'))}</p><p>Rights/distribution note: {esc(ed['rights_note'])}</p><p class="hash">Full revision: {revision}</p></details><nav aria-label="Contents"><ol>{toc}</ol></nav>{chapters}</main>'''
    return page(ed['title'],body,css,ed['language'],ed['direction'])

def build_reviewer(obj: dict,revision: str,config: dict,css: str,script: str,demo: bool) -> str:
    ed=obj['edition']
    # The book remains the focus. Provenance and help live behind the menu.
    author = '' if demo else f'<p class="byline">{esc(obj["work"]["author"])}</p>'
    status = 'Sample' if demo else esc(ed['status'].capitalize())
    body=f'''<header class="sitebar"><a href="../../../../contribute/index.html">{esc(config['name'])}</a><a href="read.html">Reader view</a></header>
<main class="review-main"><header class="bookhead"><h1>{esc(ed['title'])}</h1>{author}<p class="meta">{status} <span aria-hidden="true">·</span> {esc(ed['language'])} <span aria-hidden="true">·</span> <span title="Revision {revision}">{revision[:10]}</span></p></header>
<div id="storage-warning" class="notice warning" role="status" hidden></div>
<div class="toolbar" role="group" aria-label="Reading controls" dir="ltr"><button id="previous" class="toolbar-icon" aria-label="Previous chapter" title="Previous chapter">←</button><label class="sr-only" for="section-select">Chapter</label><select id="section-select"></select><button id="next" class="toolbar-icon" aria-label="Next chapter" title="Next chapter">→</button><span class="toolbar-space"></span><button id="toggle-notes" aria-expanded="false" aria-controls="notes-panel">Notes <span id="note-count">0</span></button><details class="reader-menu" id="reader-menu"><summary aria-label="More options" title="More options">···</summary><div class="reader-menu-content"><button id="general" type="button">Chapter note</button><button id="annotate" type="button">Comment on selection</button><details class="help-details"><summary>Help</summary><p>Select text to comment. Tap an underline to revisit a note. Use Notes to prepare a GitHub report.</p><p>Notes stay in this browser and belong to this exact revision; they are not submitted automatically.</p></details></div></details></div>
<p id="message" class="statusline" role="status" aria-live="polite" dir="ltr"></p><h2 id="section-heading" class="section-heading"></h2><article id="chapter-text" class="reading-text" lang="{esc(ed['language'])}" dir="{ed['direction']}"></article>
<details id="source-details" class="source-details"><summary>Original</summary><div id="source-text" dir="auto" lang="{esc(obj['work']['language'])}"></div></details><footer class="reading-footer"><button id="next-bottom">Next chapter →</button></footer></main>
<aside id="notes-panel" class="notes-panel" aria-label="Review notes" hidden dir="ltr"><div class="panel-heading"><h2>Notes <span class="small">· {revision[:10]}</span></h2><button id="close-notes">Close</button></div><div id="note-list"></div><div class="actions"><button id="prepare">Prepare report</button><button id="download">Download JSON</button></div><label class="import-label">Import JSON <input id="import-file" type="file" accept="application/json,.json"></label><div id="export-panel" hidden><label for="report-text">GitHub report</label><textarea id="report-text" rows="10" readonly></textarea><div class="actions"><button id="copy">Copy report</button><a id="github-issue" class="button" target="_blank" rel="noopener noreferrer">Open GitHub Issues</a></div><p id="report-size-note" class="small"></p><label for="issue-url">Submitted Issue URL (optional)</label><input id="issue-url" type="url" placeholder="https://github.com/…/issues/123"><button id="record-submitted">Record submission</button></div></aside>
<div id="comment-popover" class="comment-popover" role="dialog" aria-label="Annotation" hidden dir="ltr"><div id="popover-choice" hidden></div><form id="comment-form"><p id="selected-quote" class="popover-quote"></p><label class="sr-only" for="comment-text">Comment</label><textarea id="comment-text" rows="3" required maxlength="20000" placeholder="Comment…"></textarea><div class="popover-actions"><button type="button" id="remove-comment" class="subtle" hidden>Remove</button><span class="toolbar-space"></span><button id="cancel-comment" type="button" class="subtle">Cancel</button><button type="submit" class="primary-action">Save</button></div></form></div>
<noscript><p class="notice">Annotations require JavaScript.</p></noscript>'''
    data={'snapshot':obj,'revision':revision,'repository':config['repository'],'demo':demo}
    tail=f'<script id="review-data" type="application/json">{js_data(data)}</script><script>{script}</script>'
    return page(ed['title']+' — contributor reading',body,css,tail=tail)

def build_epub(obj: dict,revision: str,path: Path,root: Path) -> None:
    ed,work=obj['edition'],obj['work']
    info=f'<h1>About this edition</h1><p>{esc(ed["description"])}</p><p>Revision: {revision}</p><p>Status: {esc(ed["status"])}</p><p>Source: {esc(work["source_edition"])}</p><p>{esc(work["source_provenance"])}</p><p>AI involvement: {esc(ed["production"].get("ai_use","unknown"))}</p><p>Rights/distribution note: {esc(ed["rights_note"])}</p>'
    chapters=''.join(f'<h1 id="s-{esc(s["id"])}">{esc(s["title"])}</h1>{s["html"]}' for s in obj['sections'])
    text=f'<html lang="{esc(ed["language"])}" dir="{ed["direction"]}"><body>{info}{chapters}</body></html>'
    pandoc('--from=html','--to=epub3','--standalone','--toc','--epub-chapter-level=1','--metadata',f'title={ed["title"]}','--metadata',f'author={work["author"]}','--metadata',f'lang={ed["language"]}','--metadata',f'dir={ed["direction"]}','--metadata',f'identifier=urn:sha256:{revision}','--css',str(root/'site/epub.css'),'--output',str(path),text=text)

def build(root: Path=ROOT,demo: bool=False,epub: bool=False) -> Path:
    validate_project(root)
    records=load_catalog(root,demo)
    config=read_json(root/'project.json')
    css=(root/'site/site.css').read_text(encoding='utf-8')
    script=(root/'site/review.js').read_text(encoding='utf-8')
    out=root/'dist'
    check(not out.is_symlink(),'Refusing to delete symlinked dist')
    if out.exists():shutil.rmtree(out)
    out.mkdir();(out/'.nojekyll').touch()
    readers,reviews=[],[]
    for rec,obj in records:
        revision=rec['revision'];ed=obj['edition']
        relative=Path('revisions')/rec['work']/rec['edition']/revision
        folder=out/relative;folder.mkdir(parents=True)
        (folder/'read.html').write_text(build_reader(obj,revision,config,css),encoding='utf-8')
        (folder/'review.html').write_text(build_reviewer(obj,revision,config,css,script,demo),encoding='utf-8')
        write_json(folder/'snapshot.json',obj)
        if epub:build_epub(obj,revision,folder/'edition.epub',root)
        if not rec['listed']:continue
        link=relative.as_posix()
        epub_link=f' · <a href="{link}/edition.epub">EPUB</a>' if epub else ''
        if rec['audience']=='readers':
            readers.append(f'<li class="book-row"><h2>{esc(ed["title"])}</h2><p>{esc(obj["work"]["author"])}</p><p class="meta">{esc(ed["language"])} · {esc(ed["label"])}</p><p><a href="{link}/read.html">Read HTML</a>{epub_link}</p></li>')
        reviews.append(f'<li class="book-row"><h2>{esc(ed["title"])}</h2><p class="meta">{esc(ed["language"])} · {esc(ed["status"])} · {len(obj["sections"])} chapters · {revision[:10]}</p><p><a class="button" href="../{link}/review.html">Read and annotate</a></p></li>')
    banner=''
    listing='<ul class="book-list">'+''.join(readers)+'</ul>' if readers else '<p class="empty-state">No reader editions have been published yet. Review drafts have their own entrance.</p>'
    body=f'<header class="sitebar"><span>{esc(config["name"])}</span><a href="contribute/index.html">Contributor workbench</a></header><main class="catalogue"><p class="eyebrow">THE LIBRARY</p><h1>Old books.<br>Contemporary language.</h1><p class="intro">{esc(config["description"])}</p>{banner}<h2>Available editions</h2>{listing}<p><a href="contribute/index.html">Visit the contributor workbench →</a></p></main>'
    (out/'index.html').write_text(page(config['name'],body,css),encoding='utf-8')
    empty='' if reviews else '<p class="empty-state">No review drafts are listed yet.</p>'
    body=f'<header class="sitebar"><a href="../index.html">{esc(config["name"])}</a><span>Contributor workbench</span></header><main class="catalogue"><p class="eyebrow">READ · NOTICE · COMMENT</p><h1>Read with a pencil.</h1><p class="intro">Choose a draft, collect observations, and leave editorial decisions to the maintainer and their AI.</p>{banner}<ul class="book-list">{"".join(reviews)}</ul>{empty}</main>'
    (out/'contribute').mkdir();(out/'contribute/index.html').write_text(page('Contributor workbench',body,css),encoding='utf-8')
    write_json(out/'build-manifest.json',{'schema_version':1,'demo':demo,'revisions':[r['revision'] for r,_ in records],'epub':epub})
    return out

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('validate',help='Structural checks, not literary approval')
    p=sub.add_parser('snapshot',help='Freeze locally; never publish');p.add_argument('work_directory',type=Path);p.add_argument('edition_id')
    p=sub.add_parser('build',help='Build explicit catalogue to dist/');p.add_argument('--demo',action='store_true');p.add_argument('--epub',action='store_true')
    p=sub.add_parser('check-review',help='Validate without applying or submitting');p.add_argument('report',type=Path)
    args=parser.parse_args()
    try:
        if args.command=='validate':print(json.dumps(validate_project(),indent=2))
        elif args.command=='snapshot':
            revision,path=freeze(args.work_directory,args.edition_id);print(f'Revision: {revision}\nSaved: {path}\nNot listed or published.')
        elif args.command=='build':print(f'Built: {build(demo=args.demo,epub=args.epub)}\nNo deployment performed.')
        else:print(json.dumps(validate_review(read_json(args.report)),indent=2))
        return 0
    except (ProjectError,KeyError,TypeError,OSError) as exc:
        print(f'Error: {exc}',file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
