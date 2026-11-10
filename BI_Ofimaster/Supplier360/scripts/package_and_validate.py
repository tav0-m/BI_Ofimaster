import csv,json,collections,datetime as dt
from pathlib import Path
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1]; MODEL=ROOT/'modelo'; PQ=ROOT/'powerquery'; PQ.mkdir(exist_ok=True)
def read(name):
    with (MODEL/(name+'.csv')).open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
checks=[]
def check(name,value):
    checks.append({'control':name,'ok':bool(value)})
    if not value: raise AssertionError(name)
currencies=sorted({r['Moneda'] for t in ['FactOC','FactRepartos','FactMovimientos'] for r in read(t)})
with (MODEL/'DimMoneda.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f); w.writerow(['Moneda']); w.writerows([[x] for x in currencies])
tables={p.stem:read(p.stem) for p in MODEL.glob('*.csv')}
for table,key in [('DimProveedor','ClaveProveedor'),('DimProducto','ClaveProducto'),('DimProveedorNC','ProveedorTexto'),('DimFecha','Fecha'),('FactOC','ClaveOC'),('FactRepartos','ClaveReparto'),('FactReclamosNC','IdCaso')]:
    rows=tables[table]; check(table+' clave unica',len(rows)==len({r[key] for r in rows}))
for table in ['FactOC','FactRepartos','FactMovimientos']:
    for dim,key in [('DimProveedor','ClaveProveedor'),('DimProducto','ClaveProducto')]:
        keys={r[key] for r in tables[dim]}; check(table+' integridad '+dim,all(r[key] in keys for r in tables[table]))
for r in tables['FactOC']:
    if r['ElegibleFillRate']=='1':
        checkname='Fill rate acotado y saldo no negativo'
        if not (Decimal(0)<=Decimal(r['CantidadCubierta'])<=Decimal(r['CantidadElegible']) and Decimal(r['CantidadPendienteAbierta'])>=0): raise AssertionError(checkname)
check('Fill rate acotado y saldo no negativo',True)
check('OTIF no fabricado',all(r['OTIFEvaluable']=='0' and r['OTIFCumple']=='' for r in tables['FactRepartos']))
check('NC no contabilizadas sin evidencia',all(r['ContabilizadaVerificada']=='0' and r['MontoNCContable']=='' for r in tables['FactReclamosNC']))
dates={r['Fecha'] for r in tables['DimFecha']}
for t,c in [('FactOC','FechaPedido'),('FactRepartos','FechaPromesa'),('FactMovimientos','FechaContable'),('FactReclamosNC','FechaCaso')]: check(t+' cobertura calendario',all(not r[c] or r[c] in dates for r in tables[t]))
# Conciliacion independiente de la transformacion contra EKPO y EKET via invariantes de salida.
byoc=collections.defaultdict(list)
for r in tables['FactRepartos']: byoc[r['ClaveOC']].append(r)
delta=[]
for r in tables['FactOC']:
    if r['ElegibleFillRate']=='1':
        children=byoc[r['ClaveOC']]
        check('Repartos cantidad pedida '+r['ClaveOC'],sum(Decimal(x['CantidadProgramada']) for x in children)==Decimal(r['CantidadPedida']))
        a=sum(Decimal(x['CantidadPendienteAbierta']) for x in children)
        if a!=Decimal(r['CantidadPendienteAbierta']): delta.append(r['ClaveOC'])
# No repetir miles de controles en el informe.
check('Pendiente reparto concilia posicion',not delta)
checks=[x for x in checks if not x['control'].startswith('Repartos cantidad pedida ')]
checks.append({'control':'Cantidades de repartos conciliadas con posiciones elegibles','ok':True})
numeric_exact={'Anio','Mes','Trimestre','FilaOrigen','Entrada','Salida','ImporteOrigen','MontoReclamado','MontoNCContable','SaldoNCContable','Borrada','EntregaFinal','ElegibleCompras','ElegibleFillRate','Repartos','DescuadreRepartos','ProveedorEnMaestro','ProductoEnMaestro','OTIFEvaluable','OTIFCumple','VencidoAlCorte','DiasAtraso','Elegible','ExisteMaestro','ContabilizadaVerificada'}
for name,rows in tables.items():
    fields=list(rows[0]) if rows else next(csv.reader((MODEL/(name+'.csv')).open(encoding='utf-8-sig')))
    transforms=[]
    for c in fields:
        kind='type date' if c.startswith('Fecha') else ('type number' if c.startswith(('Cantidad','Valor')) or c in numeric_exact else 'type text')
        if kind!='type text': transforms.append('        {"'+c+'", each if _ = "" then null else '+('Date.FromText(_, [Format="yyyy-MM-dd", Culture="en-US"])' if kind=='type date' else 'Number.FromText(_, "en-US")')+', '+kind+'}')
    text='let\n    Source = Csv.Document(File.Contents(pRutaModelo & "'+name+'.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),\n    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true])'
    if transforms: text+=',\n    Typed = Table.TransformColumns(Headers, {\n'+',\n'.join(transforms)+'\n    })\nin\n    Typed\n'
    else: text+='\nin\n    Headers\n'
    (PQ/(name+'.pq')).write_text(text,encoding='utf-8')
(PQ/'pRutaModelo.pq').write_text('"'+str(MODEL)+'\\" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n',encoding='utf-8')
(ROOT/'diagnostico/validacion.json').write_text(json.dumps({'checks':checks,'filas_modelo':{k:len(v) for k,v in tables.items()}},ensure_ascii=False,indent=2),encoding='utf-8')
quality=json.loads((ROOT/'diagnostico/calidad_modelo.json').read_text(encoding='utf-8'))
lines=['# Resultados de la revisión local','', '| Indicador | Resultado |','|---|---|']
for k,v in quality.items():
    if not isinstance(v,(list,dict)): lines.append('| '+k+' | '+str(v)+' |')
lines+=['','## Tablas preparadas','']
for k,v in tables.items(): lines.append('- '+k+': '+str(len(v))+' filas.')
lines+=['','## Alcance de validación','','Claves únicas, integridad referencial, calendario, cantidades por reparto, límites del fill rate, conciliación de pendientes y ausencia de OTIF/NC contables inventados: controles ejecutados en Python. Power Query y DAX preparados; no ejecutados en Power BI Desktop.','', '## Cobertura de movimientos','','Fechas KARDEX: '+quality['kardex_fecha_min']+' a '+quality['kardex_fecha_max']+'. Comparar con fecha de corte de OC; no asumir historia completa por disponer de algunas recepciones.','','Tipos vinculados a OC: `'+json.dumps(quality['kardex_tipos_vinculados'])+'`. Su semántica y tratamiento deben validarse antes de usarlos en OTIF.']
(ROOT/'RESULTADOS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'checks':checks,'filas_modelo':{k:len(v) for k,v in tables.items()}},ensure_ascii=False,indent=2))
