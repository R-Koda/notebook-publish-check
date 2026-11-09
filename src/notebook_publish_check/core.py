"""Conservative, non-executing notebook publication checks. No safety certification."""
import copy
import json
import re

PATH = re.compile(r'(?:/(?:Users|home|private|mnt)/[^\s\"\'<>]+|[A-Za-z]:\\(?:Users|Documents and Settings)\\[^\r\n\"<>]+)')
SECRET = re.compile(r'(?i)(?:\b(?:api[_-]?key|access[_-]?token|password|secret)\b[\"\']?\s*[:=]\s*[\"\']?([^\s\"\'<>]{8,})|\b(?:gh[pousr]_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16}|sk-[A-Za-z0-9_-]{20,}))')

def validate(nb):
    if not isinstance(nb,dict) or nb.get('nbformat') != 4 or not isinstance(nb.get('cells'),list):
        raise ValueError('Expected a Jupyter nbformat 4 notebook with a cells array')
    if not isinstance(nb.get('metadata',{}),dict):
        raise ValueError('Notebook metadata must be an object')
    for i,c in enumerate(nb['cells']):
        if not isinstance(c,dict) or c.get('cell_type') not in ('code','markdown','raw'):
            raise ValueError(f'Invalid cell {i+1}')
        if not isinstance(c.get('source',''),(str,list)) or (isinstance(c.get('source'),list) and not all(isinstance(x,str) for x in c['source'])):
            raise ValueError(f'Invalid source in cell {i+1}')
        if not isinstance(c.get('metadata',{}),dict) or not isinstance(c.get('outputs',[]),list):
            raise ValueError(f'Invalid metadata/outputs in cell {i+1}')
        for o in c.get('outputs',[]):
            if not isinstance(o,dict): raise ValueError(f'Invalid output in cell {i+1}')
    return nb

def strings(value,path=''):
    if isinstance(value,str): yield path,value
    elif isinstance(value,list):
        # Jupyter multiline text is often an array: join to catch split tokens.
        if all(isinstance(x,str) for x in value): yield path,''.join(value)
        else:
            for i,x in enumerate(value): yield from strings(x,f'{path}[{i}]')
    elif isinstance(value,dict):
        for k,v in value.items():
            if k in ('image/png','image/jpeg','image/gif','image/webp','application/pdf'):
                continue
            yield from strings(v,f'{path}.{k}' if path else k)

def scan(nb,max_output_bytes=100_000):
    validate(nb)
    if max_output_bytes < 1: raise ValueError('Output threshold must be positive')
    findings=[]
    def add(cell,area,rule,severity,detail):
        findings.append({'cell':cell,'area':area,'rule':rule,'severity':severity,'detail':detail})
    def inspect(value,cell,area):
        for path,s in strings(value):
            if SECRET.search(s): add(cell,area,'possible-secret','high',f'Credential-like pattern in {path or area}; value omitted. Review manually.')
            if PATH.search(s): add(cell,area,'absolute-path','review',f'Local absolute path in {path or area}; value omitted.')
    inspect(nb.get('metadata',{}),None,'metadata')
    for i,c in enumerate(nb['cells']):
        inspect(c.get('source',''),i,'source')
        inspect(c.get('metadata',{}),i,'metadata')
        inspect(c.get('attachments',{}),i,'attachments')
        outputs=c.get('outputs',[])
        inspect(outputs,i,'outputs')
        size=len(json.dumps(outputs,ensure_ascii=False).encode('utf-8'))
        if outputs and size>max_output_bytes:
            add(i,'outputs','large-output','review',f'{size:,} serialized UTF-8 bytes exceeds {max_output_bytes:,}.')
        for o in outputs:
            data=o.get('data',{})
            if isinstance(data,dict) and any(k.startswith('image/') or k in ('text/html','application/javascript','application/pdf') for k in data):
                add(i,'outputs','manual-media-review','review','Rich output may contain identifying content; images are not OCR-scanned and HTML/JavaScript is never executed in the report.')
        if c.get('attachments'):
            add(i,'attachments','manual-attachment-review','review','Embedded attachments need manual review; attachments are retained in exported copies.')
    return findings

def sanitize(nb,remove_outputs=(),remove_metadata=()):
    validate(nb)
    out=copy.deepcopy(nb)
    for i in remove_outputs:
        if not isinstance(i,int) or i < 0 or i>=len(out['cells']) or out['cells'][i]['cell_type']!='code':
            raise ValueError('Output selection must refer to a code cell index')
        out['cells'][i]['outputs']=[]
        out['cells'][i]['execution_count']=None
    for i in remove_metadata:
        if i=='notebook': out['metadata']={}
        elif isinstance(i,int) and 0<=i<len(out['cells']): out['cells'][i]['metadata']={}
        else: raise ValueError('Invalid metadata selection')
    return out
