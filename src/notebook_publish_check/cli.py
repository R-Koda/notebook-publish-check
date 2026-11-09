import argparse
import json
from pathlib import Path
from .core import scan

def report(nb,findings):
    # The local report intentionally embeds the original to export chosen copies.
    # JSON escapes prevent notebook strings from closing the script container.
    data=json.dumps({'notebook':nb,'findings':findings},ensure_ascii=True).replace('<','\\u003c')
    return TEMPLATE.replace('__DATA__',data)

def main(argv=None):
    p=argparse.ArgumentParser(description='Read-only Jupyter publication review. HTML embeds the original notebook; keep it private.')
    p.add_argument('notebook'); p.add_argument('--output',default='notebook-review.html')
    p.add_argument('--json',dest='json_output',help='Finding summary without matched values')
    p.add_argument('--max-output-kb',type=int,default=100)
    args=p.parse_args(argv)
    try:
        source=Path(args.notebook)
        if source.stat().st_size>20_000_000: raise ValueError('Prototype limit: 20 MB notebook')
        nb=json.loads(source.read_text(encoding='utf-8'))
        findings=scan(nb,args.max_output_kb*1000)
        outputs=[Path(args.output)]+([Path(args.json_output)] if args.json_output else [])
        if len({x.resolve() for x in outputs})!=len(outputs) or any(x.resolve()==source.resolve() or x.exists() for x in outputs):
            raise ValueError('Outputs must be distinct new files, separate from the notebook')
        html=report(nb,findings)
        for x in outputs: x.parent.mkdir(parents=True,exist_ok=True)
        Path(args.output).write_text(html,encoding='utf-8')
        if args.json_output: Path(args.json_output).write_text(json.dumps(findings,indent=2),encoding='utf-8')
        print(f'{len(findings)} findings. Private local report: {args.output}. Original unchanged.')
        return 1 if findings else 0
    except (ValueError,OSError,TypeError) as e: p.exit(2,f'Error: {e}\n')

TEMPLATE=r'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Notebook Publish Check</title><style>
body{font:16px system-ui;color:#192a35;background:#f4f7f8;margin:0}main{max-width:1100px;margin:auto;padding:40px 24px}h1{font-size:32px}header p{max-width:800px;color:#526372}.tag{font-size:12px;letter-spacing:2px;color:#197465}section{background:white;border:1px solid #d8e1e4;border-radius:12px;padding:24px;margin:20px 0}.notice{border-left:4px solid #ac682a;background:#fff8ee;padding:18px}button{font:inherit;background:#176c61;color:white;border:0;border-radius:6px;padding:12px 20px;cursor:pointer}label{display:block;margin:12px 0}input{margin-right:8px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f1f5f7;padding:14px;font-size:13px;max-height:250px;overflow:auto}img{max-width:100%;max-height:300px;border:1px solid #ddd}li{margin:10px 0}.high{color:#a73832}.muted{color:#526372}.row{display:flex;justify-content:space-between;gap:16px;align-items:center;flex-wrap:wrap}summary{cursor:pointer;padding:10px 0}.status{font-weight:600;color:#176c61}</style>
<main><header><div class="tag">LOCAL REVIEW · NO NOTEBOOK EXECUTION</div><h1>Notebook Publish Check</h1><p>Review findings, keep useful figures, and choose which cell outputs to remove. Download a separate copy after reviewing your selections.</p></header>
<div class="notice"><b>This report contains the original notebook.</b> Keep this HTML private. Findings are heuristics, not proof of safe publication. Source code and attachments are retained. No OCR or general personal-information detection is performed.</div>
<section><div class="row"><h2>Review summary</h2><span id="summary"></span></div><ul id="global"></ul><label><input type="checkbox" id="nbmeta">Remove notebook metadata from exported copy (including kernel information)</label><details><summary>Review notebook metadata</summary><pre id="notebook-metadata"></pre></details><p id="selection" class="status" aria-live="polite"></p><button id="download">Download selected copy (.ipynb)</button><p class="muted">The selected notebook is downloaded as a separate file. Your original file is never edited. Re-run this checker on the exported copy before sharing it.</p></section>
<div id="cells"></div><footer>Prototype 0.1 · Scans source, text outputs and metadata for selected credential patterns, absolute paths and output size. Rich HTML/SVG/JavaScript is displayed as text, never executed.</footer></main>
<script type="application/json" id="data">__DATA__</script><script>
const data=JSON.parse(document.getElementById('data').textContent), nb=data.notebook, removed=new Set(), metadata=new Set();
function el(tag,text,parent){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(parent)parent.append(n);return n}
function text(v){return Array.isArray(v)?v.join(''):String(v??'')}
function finding(f,parent){const li=el('li',f.rule+' · '+f.area+' — '+f.detail,parent);if(f.severity==='high')li.className='high'}
document.getElementById('summary').textContent=nb.cells.length+' cells · '+data.findings.length+' findings';
document.getElementById('notebook-metadata').textContent=JSON.stringify(nb.metadata||{},null,2);
data.findings.filter(f=>f.cell===null).forEach(f=>finding(f,document.getElementById('global')));
function update(){document.getElementById('selection').textContent=removed.size+' cells: outputs removed · '+metadata.size+' cells: metadata removed'+(document.getElementById('nbmeta').checked?' · notebook metadata removed':'')}
nb.cells.forEach((c,i)=>{const s=el('section',undefined,document.getElementById('cells'));const row=el('div',undefined,s);row.className='row';el('h2','Cell '+(i+1)+' · '+c.cell_type,row);const ff=data.findings.filter(f=>f.cell===i);el('span',ff.length?ff.length+' findings':'No selected patterns detected',row);const list=el('ul',undefined,s);ff.forEach(f=>finding(f,list));
const source=el('details',undefined,s);el('summary','Review source (retained in export)',source);el('pre',text(c.source),source);
if(c.cell_type==='code' && c.outputs?.length){const l=el('label',undefined,s);const cb=el('input',undefined,l);cb.type='checkbox';l.append(document.createTextNode('Remove all outputs and execution count from this cell'));cb.onchange=()=>{cb.checked?removed.add(i):removed.delete(i);preview.hidden=cb.checked;update()}; const preview=el('div',undefined,s);el('h3','Output preview',preview);c.outputs.forEach(o=>{if(o.text)el('pre',text(o.text).slice(0,6000)+(text(o.text).length>6000?'\n[Preview truncated; full output remains in export unless removed.]':''),preview);if(o.traceback)el('pre',text(o.traceback),preview);for(const [mime,v] of Object.entries(o.data||{})){if(['image/png','image/jpeg','image/gif','image/webp'].includes(mime)){const encoded=text(v).replace(/\s/g,'');if(/^[A-Za-z0-9+/]*={0,2}$/.test(encoded)){const img=el('img',undefined,preview);img.alt='Cell '+(i+1)+' output: manually inspect for identifying content';img.src='data:'+mime+';base64,'+encoded}}else{el('pre',mime+'\n'+text(v).slice(0,6000),preview)}}});}
if(Object.keys(c.metadata||{}).length){const l=el('label',undefined,s);const cb=el('input',undefined,l);cb.type='checkbox';l.append(document.createTextNode('Remove cell metadata (may remove tags or presentation settings)'));cb.onchange=()=>{cb.checked?metadata.add(i):metadata.delete(i);update()};const d=el('details',undefined,s);el('summary','Review cell metadata',d);el('pre',JSON.stringify(c.metadata,null,2),d)}
});
document.getElementById('nbmeta').onchange=update;
function download(value,name,type){const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)+'\n'],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
function selectedCopy(original,outputs,cellMetadata,notebookMetadata){const out=JSON.parse(JSON.stringify(original));outputs.forEach(i=>{out.cells[i].outputs=[];out.cells[i].execution_count=null});cellMetadata.forEach(i=>{out.cells[i].metadata={}});if(notebookMetadata)out.metadata={};return out}
document.getElementById('download').onclick=()=>{download(selectedCopy(nb,removed,metadata,document.getElementById('nbmeta').checked),'reviewed-copy.ipynb','application/x-ipynb+json')};update();
</script></html>'''
