"""Optional real-browser smoke test. Requires Playwright and a Chromium executable.
Runs only against a temporary local copy; never submits a GitHub Issue.
"""
from __future__ import annotations
import argparse
from functools import partial
import http.server
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import ctp

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chromium',default=os.environ.get('CTP_CHROMIUM') or shutil.which('chromium'))
    parser.add_argument('--output',type=Path,default=ctp.ROOT/'dist/browser-test')
    parser.add_argument('--file',action='store_true',help='Test self-contained file: pages instead of localhost HTTP')
    args=parser.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        parser.error('Install Playwright in a test environment; it is not a site/runtime dependency.')
    args.output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)/'library'
        shutil.copytree(ctp.ROOT,root,ignore=shutil.ignore_patterns('dist','__pycache__','.git','node_modules'))
        ctp.build(root,demo=True,epub=False)
        class QuietHandler(http.server.SimpleHTTPRequestHandler):
            def log_message(self,*_args):pass
        handler=partial(QuietHandler,directory=str(root/'dist'))
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{server.server_port}'
        try:
            with sync_playwright() as p:
                options={'headless':True,'args':['--no-sandbox']}
                if args.chromium:options['executable_path']=args.chromium
                browser=p.chromium.launch(**options)
                context=browser.new_context(viewport={'width':1280,'height':900},accept_downloads=True)
                page=context.new_page();errors=[]
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.goto((root/'dist/index.html').as_uri() if args.file else base)
                page.get_by_role('link',name='Contributor workbench',exact=True).click()
                page.get_by_role('link',name='Read and annotate').click()
                page.wait_for_function("document.getElementById('chapter-text').textContent.length > 0")
                assert not page.locator('#storage-warning').is_visible()
                page.screenshot(path=str(args.output/'contributor-desktop.png'),full_page=True)
                def select_text(quote):
                    page.evaluate('''quote => {
                      const root=document.getElementById('chapter-text');
                      const start=root.textContent.indexOf(quote), end=start+quote.length;
                      if(start<0)throw new Error('Quote not found');
                      const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
                      let pos=0,node,startNode,endNode,startOffset,endOffset;
                      while(node=walker.nextNode()){
                        const next=pos+node.textContent.length;
                        if(!startNode && start>=pos && start<next){startNode=node;startOffset=start-pos;}
                        if(end>pos && end<=next){endNode=node;endOffset=end-pos;break;}
                        pos=next;
                      }
                      const r=document.createRange();r.setStart(startNode,startOffset);r.setEnd(endNode,endOffset);
                      const selection=getSelection();selection.removeAllRanges();selection.addRange(r);
                    }''',quote)
                def annotate(quote,comment):
                    select_text(quote);page.locator('#comment-popover').wait_for(state='visible')
                    page.locator('#comment-text').fill(comment)
                    page.get_by_role('button',name='Save',exact=True).click()
                annotate('Leno','Was this name different later?')
                page.locator('#section-select').select_option('chapter-02')
                annotate('Reno','Compare the name in chapter 1.')
                page.reload();page.wait_for_function("document.getElementById('note-count').textContent === '2'")
                page.locator('#section-select').select_option('chapter-01')
                annotate('🚢','Unicode anchor test.')
                text=page.locator('#chapter-text').text_content()
                start=text.index('letter she had promised');end=text.index('river.')+len('river.')
                annotate(text[start:end],'A selection spanning paragraphs, not a sentence unit.')
                page.locator('#reader-menu > summary').click();page.locator('#general').click();page.locator('#comment-text').fill('Chapter-level observation.')
                page.get_by_role('button',name='Save',exact=True).click()
                page.locator('#toggle-notes').click();page.locator('#prepare').click()
                with page.expect_download() as download:
                    page.locator('#download').click()
                report_path=args.output/'browser-report.json';download.value.save_as(str(report_path))
                report=ctp.read_json(report_path);assert len(report['annotations'])==5
                ctp.validate_review(report,root)
                # Opening or preparing an Issue must not mark anything submitted.
                state=page.evaluate("JSON.parse(localStorage.getItem(Object.keys(localStorage).find(k=>k.startsWith('ctp:review:'))))")
                assert not any(n.get('submitted_url') for n in state['notes'])
                # Edit one note AFTER preparing the report. A receipt must not clear it.
                page.locator('.note').first.get_by_role('button',name='Edit note').click()
                page.locator('#comment-text').fill('A newer, not-yet-submitted comment.')
                page.get_by_role('button',name='Save',exact=True).click()
                repository=ctp.read_json(root/'project.json')['repository']
                page.locator('#issue-url').fill(f'https://github.com/{repository}/issues/999999')
                page.locator('#record-submitted').click()
                state=page.evaluate("JSON.parse(localStorage.getItem(Object.keys(localStorage).find(k=>k.startsWith('ctp:review:'))))")
                assert sum(bool(n.get('submitted_url')) for n in state['notes'])==4
                assert len(state['notes'])==5 and not state['notes'][0].get('submitted_url')
                wrong=json.loads(json.dumps(report));wrong['revision']='0'*64
                page.locator('#import-file').set_input_files({'name':'wrong.json','mimeType':'application/json','buffer':json.dumps(wrong).encode()})
                page.wait_for_function("document.getElementById('message').textContent.startsWith('Import not applied:')")
                assert page.locator('#note-count').text_content()=='5'
                page.locator('#close-notes').click()
                page.set_viewport_size({'width':390,'height':844})
                page.screenshot(path=str(args.output/'contributor-mobile.png'),full_page=True)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
                # Restore an unfinished comment after a reload.
                page.locator('#reader-menu > summary').click();page.locator('#general').click();page.locator('#comment-text').fill('Unfinished note survives reload.')
                page.reload();page.locator('#comment-popover').wait_for(state='visible')
                assert page.locator('#comment-text').input_value()=='Unfinished note survives reload.'
                page.locator('#cancel-comment').click()
                assert not errors, errors
                browser.close()
                result={'browser':'system Chromium via Playwright','transport':'file' if args.file else 'localhost HTTP','checks':'passed',
                    'covered':['reader/contributor navigation','text selection','cross-paragraph selection','multi-chapter notes',
                               'UTF-16 emoji anchor','chapter-level comment','reload persistence','unfinished composer recovery',
                               'JSON export validated by Python','no implicit submission','receipt preserves newer edits',
                               'wrong-revision import rejection','390px no horizontal overflow'],
                    'not_tested':['real GitHub submission','Safari/iPad','EPUBCheck','Kindle rendering']}
                ctp.write_json(args.output/'browser-results.json',result)
                print(json.dumps(result,indent=2))
        finally:server.shutdown();server.server_close()

if __name__=='__main__':main()
