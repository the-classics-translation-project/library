/* No account tokens, network writes, model calls or automatic Issue submission. */
(() => {
  "use strict";
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  const clone = value => JSON.parse(JSON.stringify(value));
  const uuid = () => globalThis.crypto?.randomUUID?.() || `local-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  function makeAnchor(text, start, end) {
    assert(Number.isInteger(start) && Number.isInteger(end) && start >= 0 && end > start && end <= text.length, "Invalid text selection.");
    return {unit: "utf16-code-units", start, end, exact: text.slice(start, end),
      prefix: Array.from(text.slice(0, start)).slice(-40).join(""),
      suffix: Array.from(text.slice(end)).slice(0, 40).join("")};
  }
  function validateReport(report, data) {
    assert(report?.schema_version === 1, "Unknown review report format.");
    assert(report.repository === data.repository && report.revision === data.revision &&
      report.work === data.snapshot.work.id && report.edition === data.snapshot.edition.id,
      "This report belongs to a different repository, edition or revision. Open that revision instead.");
    assert(typeof report.report_id === "string" && report.report_id.length > 0, "Missing report ID.");
    assert(typeof report.created_at === "string" && report.created_at.length > 0, "Missing report date.");
    assert(Array.isArray(report.annotations) && report.annotations.length > 0, "There are no annotations.");
    const ids = new Set();
    for (const note of report.annotations) {
      assert(typeof note.id === "string" && note.id && !ids.has(note.id), "Missing or duplicate annotation ID."); ids.add(note.id);
      assert(typeof note.comment === "string" && note.comment.trim(), "An annotation has no comment.");
      const section = data.snapshot.sections.find(s => s.id === note.section);
      assert(section, "The annotation refers to an unknown chapter.");
      assert(note.scope === "text" || note.scope === "section", "Unknown annotation scope.");
      if (note.scope === "section") { assert(note.anchor === null, "A chapter note must not have a text anchor."); continue; }
      const a = note.anchor, text = section.text;
      assert(a && a.unit === "utf16-code-units" && Number.isInteger(a.start) && Number.isInteger(a.end) &&
        a.start >= 0 && a.end > a.start && a.end <= text.length, "Invalid anchor positions.");
      // A boundary between a high and low surrogate is not a valid text boundary.
      for (const p of [a.start, a.end]) {
        const before = text.charCodeAt(p-1), after = text.charCodeAt(p);
        assert(!(before >= 0xD800 && before <= 0xDBFF && after >= 0xDC00 && after <= 0xDFFF), "Anchor splits a Unicode character.");
      }
      assert(text.slice(a.start, a.end) === a.exact, "The quote does not match this frozen revision.");
      assert(typeof a.prefix === "string" && typeof a.suffix === "string" &&
        text.slice(0, a.start).endsWith(a.prefix) && text.slice(a.end).startsWith(a.suffix), "The quotation context does not match.");
    }
    return report;
  }
  function publicNote(note) {
    return {id: note.id, section: note.section, scope: note.scope, anchor: clone(note.anchor), comment: note.comment};
  }
  function reportFor(notes, data, reportId = uuid(), created = new Date().toISOString()) {
    return validateReport({schema_version: 1, report_id: reportId, repository: data.repository,
      work: data.snapshot.work.id, edition: data.snapshot.edition.id, revision: data.revision,
      created_at: created, annotations: notes.map(publicNote)}, data);
  }
  const core = {makeAnchor, validateReport, publicNote, reportFor};
  if (typeof module !== "undefined" && module.exports) module.exports = core;
  globalThis.CTPReviewCore = core;
  if (typeof document === "undefined") return;

  const $ = id => document.getElementById(id);
  const data = JSON.parse($("review-data").textContent);
  const snap = data.snapshot;
  const key = `ctp:review:v1:${data.repository}:${snap.work.id}:${snap.edition.id}:${data.revision}`;
  let state = {notes: [], section: snap.sections[0].id, composer: null, lastPrepared: null};
  let storageBlocked = false, captured = null;
  function warning(message) { $("storage-warning").hidden = false; $("storage-warning").textContent = message; }
  function say(message, error = false) {
    $("message").textContent = message;
    $("message").classList.toggle("has-error", error);
  }
  try {
    const saved = localStorage.getItem(key);
    if (saved) {
      const candidate = JSON.parse(saved);
      assert(Array.isArray(candidate.notes), "Stored notes have an invalid format.");
      if (candidate.notes.length) reportFor(candidate.notes, data, "local-validation");
      if (candidate.composer) {
        reportFor([{...candidate.composer, comment: candidate.composer.comment || "unfinished note"}], data, "composer-validation");
      }
      state = {...state, ...candidate};
    }
  } catch (error) {
    storageBlocked = true;
    warning("Saved browser data could not be loaded. New notes are in memory only; export JSON before leaving. Existing saved data was not overwritten.");
    $("storage-warning").title = error.message;
  }
  function save() {
    if (storageBlocked) return;
    try { localStorage.setItem(key, JSON.stringify(state)); }
    catch (error) { storageBlocked = true; warning("Browser storage is unavailable or full. Notes are in memory only; export JSON before leaving."); $("storage-warning").title = error.message; }
  }
  function guard(fn) { return (...args) => { try { return fn(...args); } catch (error) { say(error.message, true); } }; }
  const article = $("chapter-text"), popover = $("comment-popover");
  let popupRect = null, selectionTimer = null;
  for (const section of snap.sections) {
    const option = document.createElement("option"); option.value = section.id; option.textContent = section.title;
    $("section-select").append(option);
  }
  function current() { return snap.sections.find(s => s.id === state.section) || snap.sections[0]; }
  function renderChapter(sectionId, scroll = false) {
    const section = snap.sections.find(s => s.id === sectionId) || snap.sections[0];
    if (state.composer && !popover.hidden && section.id !== state.section) {
      say("Save or cancel the current note before changing chapters.", true);
      $("section-select").value = state.section;
      return;
    }
    state.section = section.id; captured = null;
    popover.hidden = true;
    article.innerHTML = section.html; // Build-time allowlisted, immutable markup only.
    assert(article.textContent === section.text, "Rendered text differs from the snapshot. Annotation has been disabled; report a tooling problem.");
    paintAnchors();
    $("section-heading").textContent = section.title;
    $("section-select").value = section.id;
    const source = snap.source_sections.find(s => s.id === section.id);
    $("source-text").innerHTML = source ? source.html : "";
    $("source-details").open = false;
    const i = snap.sections.indexOf(section);
    $("previous").disabled = i === 0; $("next").disabled = $("next-bottom").disabled = i === snap.sections.length - 1;
    try { history.replaceState(null, "", `#${encodeURIComponent(section.id)}`); } catch { /* file: URL restrictions */ }
    save(); say("");
    if (scroll) $("section-heading").scrollIntoView({block: "start"});
  }
  function move(delta) { const i = snap.sections.indexOf(current()) + delta; if (snap.sections[i]) renderChapter(snap.sections[i].id, true); }
  $("section-select").addEventListener("change", guard(e => renderChapter(e.target.value, true)));
  $("previous").addEventListener("click", guard(() => move(-1)));
  $("next").addEventListener("click", guard(() => move(1)));
  $("next-bottom").addEventListener("click", guard(() => move(1)));

  // Each saved annotation concerns frozen UTF-16 offsets in the *plain text*.
  // Repaint leaf text nodes instead of surrounding whole paragraphs. This keeps
  // original markup and textContent intact, even with cross-paragraph/overlapping notes.
  function paintAnchors() {
    const notes = state.notes.filter(n => n.scope === "text" && n.section === state.section);
    const nodes = [];
    const walk = document.createTreeWalker(article, NodeFilter.SHOW_TEXT);
    let node, pos = 0;
    while ((node = walk.nextNode())) {
      nodes.push({node, start: pos, end: pos + node.length}); pos += node.length;
    }
    assert(pos === current().text.length, "Cannot attach annotations to altered text.");
    for (const {node, start, end} of nodes) {
      const covering = notes.filter(n => n.anchor.start < end && n.anchor.end > start);
      if (!covering.length) continue;
      const bounds = new Set([0, node.length]);
      for (const n of covering) {
        bounds.add(Math.max(0, n.anchor.start - start));
        bounds.add(Math.min(node.length, n.anchor.end - start));
      }
      const cuts = [...bounds].sort((a, b) => a - b), fragment = document.createDocumentFragment();
      for (let i = 0; i < cuts.length - 1; i++) {
        const from = cuts[i], to = cuts[i + 1];
        if (from === to) continue;
        const segment = node.data.slice(from, to);
        const overlapping = covering.filter(n => n.anchor.start < start + to && n.anchor.end > start + from);
        if (!overlapping.length) { fragment.append(document.createTextNode(segment)); continue; }
        const span = document.createElement("span");
        span.className = "ctp-annotation-mark";
        span.dataset.noteIds = overlapping.map(n => n.id).join(" ");
        span.textContent = segment;
        fragment.append(span);
      }
      node.replaceWith(fragment);
    }
    assert(article.textContent === current().text, "Annotation decoration must not change source text.");
    applyMarkAccessibility();
  }
  function rangeForAnchor(anchor) {
    if (!anchor) return null;
    const walk = document.createTreeWalker(article, NodeFilter.SHOW_TEXT);
    let n, pos = 0, startNode = null, endNode = null, startOffset = 0, endOffset = 0;
    while ((n = walk.nextNode())) {
      const after = pos + n.length;
      if (startNode === null && anchor.start >= pos && anchor.start < after) {startNode = n; startOffset = anchor.start - pos;}
      if (anchor.end > pos && anchor.end <= after) {endNode = n; endOffset = anchor.end - pos; break;}
      pos = after;
    }
    if (!startNode || !endNode) return null;
    const range = document.createRange();
    range.setStart(startNode, startOffset); range.setEnd(endNode, endOffset);
    return range;
  }
  function capture() {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || !selection.rangeCount) { captured = null; return; }
    const range = selection.getRangeAt(0);
    if (!article.contains(range.startContainer) || !article.contains(range.endContainer)) { captured = null; return; }
    const pre = document.createRange(); pre.selectNodeContents(article); pre.setEnd(range.startContainer, range.startOffset);
    const start = pre.toString().length, end = start + range.toString().length;
    captured = end > start && current().text.slice(start, end).trim()
      ? {section: current().id, anchor: makeAnchor(current().text, start, end), rect: range.getBoundingClientRect()} : null;
  }
  function anchorRect(note) {
    if (note.scope !== "text") return $("section-heading").getBoundingClientRect();
    const range = rangeForAnchor(note.anchor);
    if (!range) return $("section-heading").getBoundingClientRect();
    const rects = [...range.getClientRects()].filter(r => r.width && r.height);
    return rects.length ? rects[0] : range.getBoundingClientRect();
  }
  function positionPopover(rect) {
    if (!rect) rect = $("section-heading").getBoundingClientRect();
    popupRect = {left:rect.left, right:rect.right, top:rect.top, bottom:rect.bottom, width:rect.width};
    // Measure after unhiding. Clamp to viewport for long selections and small screens.
    const width = popover.offsetWidth, height = popover.offsetHeight;
    const vw = document.documentElement.clientWidth, vh = window.innerHeight;
    const center = (rect.left + rect.right) / 2;
    let left = Math.max(8, Math.min(center - width / 2, vw - width - 8));
    let top = rect.bottom + 10;
    if (top + height > vh - 8) top = rect.top - height - 10;
    if (top < 8) top = Math.max(8, vh - height - 8);
    popover.style.left = `${left}px`; popover.style.top = `${top}px`;
  }
  function closePopover(clearComposer = false) {
    popover.hidden = true;
    $("popover-choice").hidden = true;
    $("comment-form").hidden = false;
    popupRect = null;
    if (clearComposer) { state.composer = null; save(); }
  }
  function openComposer(note, rect = null) {
    closePopover();
    state.composer = clone(note); save();
    $("popover-choice").hidden = true;
    $("comment-form").hidden = false;
    $("selected-quote").textContent = note.anchor?.exact || current().title;
    $("comment-text").value = note.comment || "";
    $("remove-comment").hidden = !state.notes.some(n => n.id === note.id);
    popover.hidden = false;
    positionPopover(rect || anchorRect(note));
  }
  function annotate() {
    capture();
    assert(captured && captured.section === current().id, "Select text in this chapter first.");
    if (state.composer) {
      if (popover.hidden) say("Finish the previous note before starting another.", true);
      return;
    }
    openComposer({id:uuid(), section:captured.section, scope:"text", anchor:captured.anchor, comment:""}, captured.rect);
  }
  function fromSelection() {
    if (state.composer && !popover.hidden) return;
    if (state.composer && popover.hidden) {
      say("Finish the previous note before starting another.", true);
      return;
    }
    capture();
    if (!captured) return;
    annotate();
  }
  function queueSelection() {
    clearTimeout(selectionTimer);
    if (!state.composer || popover.hidden) selectionTimer = setTimeout(guard(fromSelection), 230);
  }
  document.addEventListener("selectionchange", guard(queueSelection));
  article.addEventListener("pointerup", guard(() => setTimeout(guard(fromSelection), 0)));
  article.addEventListener("keyup", guard(event => { if (event.shiftKey || event.key === "Enter") queueSelection(); }));
  $("annotate").addEventListener("click", guard(() => {$("reader-menu").open = false; annotate();}));
  $("general").addEventListener("click", guard(event => {
    $("reader-menu").open = false;
    openComposer({id:uuid(), section:current().id, scope:"section", anchor:null, comment:""}, event.target.getBoundingClientRect());
  }));
  $("comment-text").addEventListener("input", () => {
    if (state.composer) { state.composer.comment = $("comment-text").value; save(); }
  });
  $("cancel-comment").addEventListener("click", () => closePopover(true));
  $("comment-form").addEventListener("submit", guard(event => {
    event.preventDefault();
    assert(state.composer, "No comment is being edited.");
    const note = {...state.composer, comment: $("comment-text").value.trim(), selected:true};
    reportFor([note], data);
    const index = state.notes.findIndex(n => n.id === note.id);
    if (index === -1) state.notes.push(note); else state.notes[index] = note;
    closePopover(true); captured = null;
    window.getSelection()?.removeAllRanges();
    save();
    // Reconstruct from pristine HTML so adding overlapping notes stays deterministic.
    article.innerHTML = current().html;
    paintAnchors(); renderNotes(); say("");
  }));
  $("remove-comment").addEventListener("click", guard(() => {
    const id = state.composer?.id;
    assert(state.notes.some(n => n.id === id), "This note has not been saved.");
    state.notes = state.notes.filter(n => n.id !== id);
    closePopover(true); captured = null; save();
    article.innerHTML = current().html;
    paintAnchors(); renderNotes(); say("");
  }));
  function showExisting(ids, rect) {
    const notes = ids.map(id => state.notes.find(n => n.id === id)).filter(Boolean);
    if (!notes.length) return;
    if (notes.length === 1) { openComposer(notes[0], rect); return; }
    closePopover(true);
    $("comment-form").hidden = true;
    const wrap = $("popover-choice"); wrap.replaceChildren(); wrap.hidden = false;
    const title = document.createElement("p"); title.textContent = `${notes.length} notes`; wrap.append(title);
    for (const note of notes) {
      const card = document.createElement("div"); card.className = "annotation-choice";
      const p = document.createElement("p"); p.textContent = note.comment; card.append(p);
      const b = document.createElement("button"); b.textContent = "Edit";
      b.addEventListener("click", () => openComposer(note, rect)); card.append(b);
      wrap.append(card);
    }
    const done = document.createElement("button"); done.textContent = "Close";
    done.addEventListener("click", () => closePopover(true)); wrap.append(done);
    popover.hidden = false; positionPopover(rect);
  }
  article.addEventListener("click", guard(event => {
    // Selecting existing highlighted text takes precedence over opening a note.
    if (window.getSelection() && !window.getSelection().isCollapsed) return;
    const mark = event.target.closest(".ctp-annotation-mark");
    if (!mark || (state.composer && !popover.hidden)) return;
    showExisting(mark.dataset.noteIds.split(" "), mark.getBoundingClientRect());
  }));
  article.addEventListener("keydown", guard(event => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const mark = event.target.closest(".ctp-annotation-mark");
    if (!mark) return;
    event.preventDefault();
    showExisting(mark.dataset.noteIds.split(" "), mark.getBoundingClientRect());
  }));
  // One keyboard focus target per annotation, even when it spans many text nodes.
  function applyMarkAccessibility() {
    const focused = new Set();
    article.querySelectorAll(".ctp-annotation-mark").forEach(mark => {
      const id = mark.dataset.noteIds.split(" ")[0];
      if (!focused.has(id)) {
        mark.tabIndex = 0; mark.setAttribute("role", "button");
        mark.setAttribute("aria-label", "Open annotation"); focused.add(id);
      }
    });
  }

  function toggleNotes(open) {
    $("notes-panel").hidden = !open; $("toggle-notes").setAttribute("aria-expanded", String(open));
    if (open) $("close-notes").focus();
  }
  $("toggle-notes").addEventListener("click", () => toggleNotes($("notes-panel").hidden));
  $("close-notes").addEventListener("click", () => { toggleNotes(false); $("toggle-notes").focus(); });
  function button(label, action) { const b = document.createElement("button"); b.textContent = label; b.addEventListener("click", guard(action)); return b; }
  function renderNotes() {
    $("note-count").textContent = String(state.notes.length);
    $("note-list").replaceChildren();
    if (!state.notes.length) { const p = document.createElement("p"); p.textContent = "No notes."; $("note-list").append(p); }
    for (const note of state.notes) {
      const card = document.createElement("section"); card.className = "note";
      const label = document.createElement("label"), include = document.createElement("input"); include.type = "checkbox"; include.checked = note.selected !== false;
      include.addEventListener("change", () => { note.selected = include.checked; save(); });
      label.append(include, document.createTextNode(snap.sections.find(s => s.id === note.section).title + " — include in report")); card.append(label);
      if (note.anchor) { const quote = document.createElement("blockquote"); quote.textContent = note.anchor.exact; card.append(quote); }
      const comment = document.createElement("p"); comment.className = "comment"; comment.textContent = note.comment; card.append(comment);
      if (note.submitted_url) { const receipt = document.createElement("p"); receipt.className = "small"; receipt.textContent = `User-confirmed submission: ${note.submitted_url}`; card.append(receipt); }
      const actions = document.createElement("div"); actions.className = "actions";
      actions.append(button("Go to text", () => {
        renderChapter(note.section, true); toggleNotes(false);
        if (note.anchor) {
          const r = rangeForAnchor(note.anchor);
          r?.startContainer?.parentElement?.scrollIntoView({block: "center", behavior: "instant"});
          openComposer(note, anchorRect(note));
        }
      }), button("Edit note", () => {
        renderChapter(note.section, false); toggleNotes(false);
        const range = rangeForAnchor(note.anchor);
        range?.startContainer?.parentElement?.scrollIntoView({block: "center", behavior: "instant"});
        openComposer(note, anchorRect(note));
      }), button("Remove", () => {
        if (!window.confirm("Remove this local note? Exported files and GitHub Issues will not be changed.")) return;
        state.notes = state.notes.filter(n => n.id !== note.id); save(); renderNotes();
        article.innerHTML = current().html; paintAnchors();
      })); card.append(actions); $("note-list").append(card);
    }
  }
  function selectedNotes() { const notes = state.notes.filter(n => n.selected !== false); assert(notes.length, "Select at least one note to include."); return notes; }
  function prepare() {
    const notes = selectedNotes();
    const report = reportFor(notes, data);
    state.lastPrepared = report; save();
    let body = `# Reading feedback\n\nWork: ${snap.work.title}\nEdition: ${snap.edition.id}\nRevision: ${data.revision}\nReport ID: ${report.report_id}\n\n`;
    for (let i = 0; i < report.annotations.length; i++) {
      const n = report.annotations[i];
      body += `## ${i + 1}. ${n.section}\n\n`;
      if (n.anchor) body += n.anchor.exact.split("\n").map(line => `> ${line}`).join("\n") + "\n\n";
      body += n.comment + "\n\n";
    }
    const serialized = JSON.stringify(report, null, 2);
    const runs = serialized.match(/`+/g) || [];
    const fence = "`".repeat(Math.max(3, ...runs.map(s => s.length + 1)));
    body += `## Machine-readable report\n\n${fence}json\n${serialized}\n${fence}\n`;
    const large = body.length > 50000;
    if (large) body = `# Reading feedback\n\nWork: ${snap.work.title}\nEdition: ${snap.edition.id}\nRevision: ${data.revision}\nReport ID: ${report.report_id}\n\n${report.annotations.length} observations. Attach the downloaded JSON report; this batch is too large for the starter's conservative inline limit.\n`;
    $("report-text").value = body; $("export-panel").hidden = false;
    $("report-size-note").textContent = large ? "Download JSON and attach it to the Issue. The inline report is intentionally a summary." : "The report includes the exact revision, quotations and machine-readable anchors.";
    say("Report prepared. Copy it or download JSON, then submit it on GitHub.");
    return report;
  }
  $("prepare").addEventListener("click", guard(prepare));
  function downloadObject(object, filename) {
    const url = URL.createObjectURL(new Blob([JSON.stringify(object, null, 2) + "\n"], {type: "application/json"}));
    const a = document.createElement("a"); a.href = url; a.download = filename; document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  $("download").addEventListener("click", guard(() => {
    const selected = selectedNotes().map(publicNote);
    const report = state.lastPrepared && JSON.stringify(state.lastPrepared.annotations) === JSON.stringify(selected) ? state.lastPrepared : prepare();
    downloadObject(report, `review-${snap.work.id}-${data.revision.slice(0,12)}.json`);
  }));
  $("copy").addEventListener("click", async () => {
    try { await navigator.clipboard.writeText($("report-text").value); say("Report copied. Paste it into the GitHub Issue form and submit there."); }
    catch { $("report-text").focus(); $("report-text").select(); say("Clipboard access was unavailable. The report is selected; use your browser's Copy command."); }
  });
  $("github-issue").href = `https://github.com/${data.repository}/issues/new?template=review.md&title=${encodeURIComponent(`[Reading feedback] ${snap.edition.title} — ${data.revision.slice(0,12)}`)}`;
  if (data.demo) {
    $("github-issue").removeAttribute("href");
    $("github-issue").setAttribute("aria-disabled", "true");
    $("github-issue").textContent = "GitHub form disabled in demo";
  }
  $("record-submitted").addEventListener("click", guard(() => {
    assert(state.lastPrepared, "Prepare a report first.");
    const url = new URL($("issue-url").value.trim());
    const expected = `/${data.repository}/issues/`;
    assert(url.protocol === "https:" && url.hostname === "github.com" && url.pathname.startsWith(expected) && /^[1-9][0-9]*\/?$/.test(url.pathname.slice(expected.length)), "Enter an actual Issue URL from this repository.");
    const clean = `https://github.com${url.pathname.replace(/\/$/, "")}`;
    let matched = 0;
    for (const original of state.lastPrepared.annotations) {
      const currentNote = state.notes.find(n => n.id === original.id);
      if (currentNote && JSON.stringify(publicNote(currentNote)) === JSON.stringify(original)) {
        currentNote.submitted_url = clean; currentNote.selected = false; matched++;
      }
    }
    save(); renderNotes(); say(`Recorded a local submission receipt for ${matched} unchanged notes. GitHub has not been queried. Notes were retained.`);
  }));
  $("import-file").addEventListener("change", async event => {
    try {
      const file = event.target.files[0]; if (!file) return;
      assert(file.size <= 8 * 1024 * 1024, "Report exceeds the 8 MiB import limit.");
      const report = validateReport(JSON.parse(await file.text()), data);
      let added = 0;
      for (const note of report.annotations) {
        const old = state.notes.find(n => n.id === note.id);
        if (old) assert(JSON.stringify(publicNote(old)) === JSON.stringify(publicNote(note)), "An imported note ID conflicts with an existing note. Nothing has been overwritten.");
      }
      for (const note of report.annotations) if (!state.notes.some(n => n.id === note.id)) { state.notes.push({...publicNote(note), selected: true}); added++; }
      save(); renderNotes(); article.innerHTML = current().html; paintAnchors(); say(`Imported ${added} notes.`);
    } catch (error) { say(`Import not applied: ${error.message}`, true); }
    finally { event.target.value = ""; }
  });
  document.addEventListener("keydown", guard(event => {
    if ((event.ctrlKey || event.metaKey) && event.altKey && event.key.toLowerCase() === "m") { event.preventDefault(); annotate(); }
    if (event.key === "Escape") {
      if (!popover.hidden) closePopover(true);
      else { toggleNotes(false); $("reader-menu").open = false; }
    }
  }));
  try {
    const fromHash = decodeURIComponent(location.hash.slice(1));
    renderChapter(snap.sections.some(s => s.id === fromHash) ? fromHash : state.section);
    renderNotes();
    if (state.composer) {
      const pending = clone(state.composer);
      if (pending.section !== current().id) renderChapter(pending.section);
      openComposer(pending, anchorRect(pending)); say("Restored an unfinished note.");
    }
  } catch (error) {
    $("annotate").disabled = $("general").disabled = true;
    warning(`The workbench could not start safely: ${error.message}`);
  }
})();
