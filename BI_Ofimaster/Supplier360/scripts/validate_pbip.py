import sys,json,urllib.request,urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.validation_deps'))
from jsonschema import Draft7Validator
from referencing import Registry,Resource
from referencing.jsonschema import DRAFT7
cache=ROOT/'diagnostico/schemas'; cache.mkdir(exist_ok=True)
def retrieve(uri):
    uri=uri.split('#')[0]
    if not uri.startswith('https://developer.microsoft.com/json-schemas/'): raise ValueError(uri)
    path=cache/uri.removeprefix('https://developer.microsoft.com/json-schemas/').replace('/','_')
    if path.exists(): data=json.loads(path.read_text(encoding='utf-8'))
    else:
        data=json.load(urllib.request.urlopen(uri)); path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    return Resource.from_contents(data,default_specification=DRAFT7)
registry=Registry(retrieve=retrieve); count=0; errors=[]
for p in (ROOT/'PowerBI').rglob('*'):
    if not p.is_file(): continue
    obj=json.loads(p.read_text(encoding='utf-8'))
    if '$schema' not in obj: continue
    uri=obj['$schema']; resource=retrieve(uri); validator=Draft7Validator(resource.contents,registry=registry.with_resource(uri,resource))
    for e in validator.iter_errors(obj): errors.append({'file':str(p.relative_to(ROOT)),'path':str(list(e.path)),'error':e.message})
    count+=1
result={'archivos_validados_con_esquema_microsoft':count,'errores':errors,'limite':'Validacion estructural JSON. No valida renderizado, DAX ni refresco M en Desktop.'}
(ROOT/'diagnostico/validacion_pbip.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
if errors: raise SystemExit(1)
