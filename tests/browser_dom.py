"""Offline Chromium DOM tests for selection-anchored comments and revision-bound reports.
Uses an in-memory localStorage stub; this does not test actual cross-reload persistence.
No network, GitHub writes, or external resources.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import ctp

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chromium',default=shutil.which('chromium'))
    parser.add_argument('--output',type=Path,default=ctp.ROOT/'dist/dom-test')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    from playwright.sync_api import sync_playwright
    record=ctp.read_json(ctp.ROOT/'examples/catalog.json')['revisions'][0]
    obj=ctp.load_snapshot(ctp.ROOT,record['work'],record['edition'],record['revision'])
    rendered=ctp.build_reviewer(obj,record['revision'],ctp.read_json(ctp.ROOT/'project.json'),
        (ctp.ROOT/'site/site.css').read_text(),(ctp.ROOT/'site/review.js').read_text(),True)
    with sync_playwright() as p:
        options={'headless':True,'args':['--no-sandbox']}
        if args.chromium:options['executable_path']=args.chromium
        browser=p.chromium.launch(**options)
        page=browser.new_page(viewport={'width':1280,'height':900})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.evaluate('''() => {
          const store=new Map();
          Object.defineProperty(window,'localStorage',{configurable:true,value:{
            getItem:k=>store.has(k)?store.get(k):null,
            setItem:(k,v)=>store.set(k,String(v)),
            removeItem:k=>store.delete(k),
            key:i=>[...store.keys()][i]||null,
            get length(){return store.size;}
          }});
        }''')
        page.set_content(rendered,wait_until='load')
        assert not page.locator('#storage-warning').is_visible()
        assert page.locator('#chapter-text').text_content()==obj['sections'][0]['text']
        assert not page.locator('#comment-popover').is_visible()
        assert not page.locator('.intro').count()
        def select(quote,section=None):
            if section:page.locator('#section-select').select_option(section)
            page.evaluate('''quote=>{
              const root=document.getElementById('chapter-text');const start=root.textContent.indexOf(quote),end=start+quote.length;
              if(start<0)throw new Error('Quote not found');
              const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
              let n,pos=0,sn=null,en=null,so,eo;
              while(n=walker.nextNode()){
                const next=pos+n.length;
                if(sn===null && start>=pos && start<next){sn=n;so=start-pos;}
                if(end>pos && end<=next){en=n;eo=end-pos;break;}
                pos=next;
              }
              const range=document.createRange();range.setStart(sn,so);range.setEnd(en,eo);
              const selection=getSelection();selection.removeAllRanges();selection.addRange(range);
            }''',quote)
            page.locator('#comment-popover').wait_for(state='visible',timeout=2500)
            assert page.locator('#selected-quote').text_content()==quote
        def annotate(quote,comment,section=None):
            select(quote,section)
            page.locator('#comment-text').fill(comment)
            page.get_by_role('button',name='Save',exact=True).click()
            assert page.locator('#comment-popover').is_hidden()
        select('Leno')
        page.screenshot(path=str(args.output/'selection-desktop.png'),full_page=True)
        page.locator('#comment-text').fill('Was the name different later?')
        page.get_by_role('button',name='Save',exact=True).click()
        assert page.locator('#chapter-text').text_content()==obj['sections'][0]['text']
        assert page.locator('.ctp-annotation-mark').count()>0
        page.screenshot(path=str(args.output/'annotated-desktop.png'),full_page=True)
        page.locator('.ctp-annotation-mark').first.click()
        assert page.locator('#comment-text').input_value()=='Was the name different later?'
        page.locator('#comment-text').fill('The ferryman has another name later.')
        page.get_by_role('button',name='Save',exact=True).click()
        annotate('ferryman, Leno','Check description against the original.')
        page.locator('.ctp-annotation-mark').filter(has_text='Leno').first.click()
        assert page.locator('.annotation-choice').count()==2
        page.screenshot(path=str(args.output/'overlap-desktop.png'),full_page=True)
        page.locator('#popover-choice').get_by_role('button',name='Close').click()
        text=obj['sections'][0]['text'];start=text.index('letter she had promised');end=text.index('river.')+6
        annotate(text[start:end],'Cross-paragraph observation.')
        annotate('🚢','Unicode anchor.')
        annotate('Reno','Name consistency.',section='chapter-02')
        page.locator('#reader-menu > summary').click()
        page.locator('#general').click()
        page.locator('#comment-text').fill('Whole chapter note.')
        page.get_by_role('button',name='Save',exact=True).click()
        page.locator('#toggle-notes').click();page.locator('#prepare').click()
        raw=page.locator('#report-text').input_value()
        report=json.loads(raw.split('```json\n',1)[1].rsplit('\n```',1)[0])
        assert len(report['annotations'])==6
        ctp.validate_review(report)
        ctp.write_json(args.output/'dom-report.json',report)
        page.locator('#close-notes').click()
        page.locator('#section-select').select_option('chapter-01')
        page.set_viewport_size({'width':390,'height':844})
        page.locator('.ctp-annotation-mark').first.click()
        rect=page.locator('#comment-popover').bounding_box()
        assert rect['x']>=0 and rect['y']>=0 and rect['x']+rect['width']<=390 and rect['y']+rect['height']<=844,rect
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
        page.screenshot(path=str(args.output/'annotated-mobile.png'),full_page=True)
        page.locator('#remove-comment').click()
        assert page.locator('#note-count').text_content()=='5'
        assert page.locator('#chapter-text').text_content()==obj['sections'][0]['text']
        assert not errors,errors
        # Actual mouse drag selection, rather than injecting a DOM Range.
        pointer=browser.new_page(viewport={'width':1280,'height':900})
        pointer.evaluate("Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:()=>null,setItem:()=>{}}})")
        pointer.set_content(rendered)
        boxes=pointer.evaluate('''() => {
          const p=[...document.querySelectorAll('#chapter-text p')].find(n=>n.textContent.includes('Leno'));
          const n=p.firstChild,i=n.textContent.indexOf('Leno');
          const start=document.createRange(),end=document.createRange();
          start.setStart(n,i);start.setEnd(n,i+1);
          end.setStart(n,i+3);end.setEnd(n,i+4);
          return {start:start.getBoundingClientRect().toJSON(),end:end.getBoundingClientRect().toJSON()};
        }''')
        start,end=boxes['start'],boxes['end']
        pointer.mouse.move(start['left']+1,start['top']+start['height']/2)
        pointer.mouse.down()
        pointer.mouse.move(end['right']-1,end['top']+end['height']/2,steps=8)
        pointer.mouse.up()
        pointer.locator('#comment-popover').wait_for(state='visible',timeout=2500)
        assert pointer.locator('#selected-quote').text_content()=='Leno'
        pointer.close()
        result={'browser':'system Chromium via Playwright set_content','result':'passed',
            'covered':['selection opens popup automatically','comment saves underline','clicking underline reopens comment','edit existing comment',
                       'overlapping annotation chooser','cross-paragraph selection','cross-chapter notes','Unicode emoji anchor',
                       'chapter-level note in menu','revision-bound report validated by Python','390px popover bounds','remove restores original text','real mouse drag selection','no page errors'],
            'not_covered':['real localStorage persistence','HTTP navigation','GitHub submission','Safari/iPad']}
        ctp.write_json(args.output/'dom-results.json',result);print(json.dumps(result,indent=2));browser.close()
if __name__=='__main__':main()
