"""Local Chromium interaction tests. No Issue is submitted and no model is called."""
from pathlib import Path
import json
import argparse
import sys
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import ctp
parser=argparse.ArgumentParser();parser.add_argument('--dom',action='store_true',help='Use isolated DOM and a simulated in-memory Storage object; not a navigation/persistence test');args=parser.parse_args()
root=ctp.ROOT
out=root/'build/browser-v2';out.mkdir(parents=True,exist_ok=True)
records=ctp.read_json(root/'examples/catalog.json')['revisions']
rec=next(r for r in records if r['work']=='tree-work' and r['edition']=='en-modern')
file=root/'dist/revisions'/rec['work']/rec['edition']/rec['revision']/'review.html'
checks=[]
def ok(name):checks.append(name);print('PASS',name)
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
    context=browser.new_context(viewport={'width':1280,'height':900},device_scale_factor=1)
    page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    saved_storage={}
    def load_html(path):
        global page
        if not args.dom:
            page.goto(path.as_uri());return
        viewport=page.viewport_size
        page.close()
        page=context.new_page()
        page.set_viewport_size(viewport)
        page.on('pageerror',lambda e:errors.append(str(e)))
        stub='<script>window.__testStorage='+json.dumps(saved_storage)+';Object.defineProperty(window,"localStorage",{configurable:true,value:{getItem(k){return window.__testStorage[k]??null;},setItem(k,v){window.__testStorage[k]=String(v);},removeItem(k){delete window.__testStorage[k];},clear(){window.__testStorage={};}}});</script>'
        page.set_content(path.read_text().replace('<head>','<head>'+stub,1))
    load_html(file);page.wait_for_selector('[data-editable="n0001:label"]')
    assert not page.locator('#warning').is_visible(),page.locator('#warning').inner_text()
    page.select_option('#sections','n0004');ok('Open a nested section')
    def select(key,start,end):
        page.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
        page.evaluate('''([key,start,end])=>{const el=[...document.querySelectorAll('[data-editable]')].find(e=>e.dataset.editable===key),w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);let n,pos=0,sn,en,so,eo;while(n=w.nextNode()){const p=pos+n.length;if(!sn&&start>=pos&&start<p){sn=n;so=start-pos;}if(end>pos&&end<=p){en=n;eo=end-pos;break;}pos=p;}const r=document.createRange();r.setStart(sn,so);r.setEnd(en,eo);const s=getSelection();s.removeAllRanges();s.addRange(r);document.dispatchEvent(new Event('selectionchange'));}''',[key,start,end])
        page.wait_for_selector('#composer:not([hidden])',timeout=5000)
    select('n0001:label',4,14);page.fill('#comment','Would a different Japanese title preserve the tone better?');page.locator('#comment-form button[type=submit]').click()
    page.wait_for_selector('.margin-note');assert page.locator('#book-title .ctp-annotation-mark').count()>0;ok('Book-title selection, popup and permanent margin note')
    select('n0004:label',4,8);page.fill('#comment','Keep this heading consistent with the other translation.');page.locator('#comment-form button[type=submit]').click();page.wait_for_function("document.querySelectorAll('.margin-note').length === 2");ok('Section-heading annotation')
    # First sentence selected with a real mouse drag, not only DOM Range injection.
    points=page.evaluate('''()=>{const p=document.querySelector('[data-editable="n0004:text"] p'),n=p.firstChild,r=document.createRange();r.setStart(n,0);r.setEnd(n,12);const a=[...r.getClientRects()][0];return [a.left+1,a.top+a.height/2,a.right-1,a.top+a.height/2];}''')
    page.mouse.move(points[0],points[1]);page.mouse.down();page.mouse.move(points[2],points[3],steps=15);page.mouse.up();page.wait_for_selector('#composer:not([hidden])');page.fill('#comment','Check the narrator’s voice here.');page.locator('#comment-form button[type=submit]').click();ok('Mouse selection opens a comment popover')
    select('n0004:text',4,195);page.fill('#comment','An overlapping comment across paragraphs.');page.locator('#comment-form button[type=submit]').click();assert page.locator('[data-ids*=" "]').count()>0;ok('Overlapping and cross-paragraph highlights')
    page.screenshot(path=str(out/'desktop-notes.png'),full_page=True)
    # A visible margin card opens the original note for editing.
    page.locator('.margin-note').first.click();assert page.locator('#comment').input_value().startswith('Would a');page.fill('#comment','Title translation needs another look.');page.locator('#comment-form button[type=submit]').click();ok('Margin-note click edits the attached comment')
    if args.dom:
        saved_storage=page.evaluate('window.__testStorage');load_html(file)
    else:page.reload()
    page.wait_for_selector('#count');assert page.locator('#count').inner_text()=='4';ok('Notes restore from simulated storage' if args.dom else 'Notes persist across reload')
    page.select_option('#sections','n0005');select('n0005:text',0,4);page.fill('#comment','Was this name different at the quay?');page.locator('#comment-form button[type=submit]').click()
    page.click('#notes-toggle');page.click('#report')
    report=page.evaluate('''()=>{const data=JSON.parse(document.getElementById('edition-data').textContent);return JSON.parse(localStorage.getItem(`ctp:reader:v2:${data.repository}:${data.work}:${data.edition}:${data.revision}`)).lastReport;}''')
    ctp.validate_review(report,root);ctp.write_json(out/'report.json',report);assert len(report['annotations'])==5;ok('Multi-section report passes the Python validator')
    assert page.locator('#issue-link').get_attribute('href') is None;ok('Fixture cannot submit a real Issue')
    page.click('#close-notes');page.select_option('#sections','n0004')
    page.set_viewport_size({'width':834,'height':1112});page.wait_for_timeout(150);assert page.locator('.margin-note').first.is_visible();page.screenshot(path=str(out/'tablet-notes.png'),full_page=True);ok('Tablet-width margin notes remain visible')
    page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(100);assert not page.locator('#margin').is_visible();assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1');page.screenshot(path=str(out/'mobile-reader.png'),full_page=True);ok('Phone-width reader uses highlights without horizontal overflow')
    page.set_viewport_size({'width':1280,'height':900});load_html(root/'dist/admin/index.html');page.fill('#search','frank');page.wait_for_selector('.search-result');assert page.locator('.search-result').count()==3;page.locator('.search-result').first.click();page.locator('#targets input[value="ja"]').check();link=page.locator('#prepare-issue').get_attribute('href');assert 'github.com/the-classics-translation-project/library/issues/new?' in link
    from urllib.parse import urlparse,parse_qs
    from intake import parse_issue
    payload=parse_qs(urlparse(link).query)['body'][0];req=parse_issue({'number':99,'state':'open','user':{'login':'hiroshi-manabe'},'body':payload},ctp.read_json(root/'project.json'));assert req['targets']==['ja'];ok('Catalogue selection generates a valid authorized intake request')
    page.screenshot(path=str(out/'admin.png'),full_page=True)
    page.fill('#search','123456');page.wait_for_selector('.search-result');assert '#123456' in page.locator('.search-result').first.inner_text();ok('Gutenberg ID fallback works without the full catalogue')
    assert not errors,errors
    browser.close()
ctp.write_json(out/'results.json',{'checks':checks,'passed':len(checks),'page_errors':errors,'scope':('Isolated Chromium DOM with simulated storage; real navigation/storage could not be tested' if args.dom else 'Chromium file navigation and local storage')+'; not physical iPad/Safari or live GitHub'})
print(len(checks),'browser checks passed')
