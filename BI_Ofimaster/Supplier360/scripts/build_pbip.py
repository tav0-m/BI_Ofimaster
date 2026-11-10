"""Genera proyecto Power BI editable; requiere refresco y revision en Desktop."""
import csv,json,re,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; PROJECT=ROOT/'PowerBI'; SEM=PROJECT/'Supplier360.SemanticModel'; REPORT=PROJECT/'Supplier360.Report'; DEF=REPORT/'definition'
BASE='https://developer.microsoft.com/json-schemas/fabric/'
def save(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
save(PROJECT/'Supplier360.pbip',{'$schema':BASE+'pbip/pbipProperties/1.0.0/schema.json','version':'1.0','artifacts':[{'report':{'path':'Supplier360.Report'}}],'settings':{'enableAutoRecovery':True}})
save(SEM/'definition.pbism',{'version':'1.0','settings':{}})
save(REPORT/'definition.pbir',{'$schema':BASE+'item/report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../Supplier360.SemanticModel'}}})
tables=[]
for p in sorted((ROOT/'modelo').glob('*.csv')):
    if p.stem=='MapProveedorNC': continue
    with p.open(encoding='utf-8-sig',newline='') as f: fields=next(csv.reader(f))
    m=(ROOT/'powerquery'/(p.stem+'.pq')).read_text(encoding='utf-8')
    cols=[]
    for c in fields:
        dtype='dateTime' if '{"'+c+'", each' in m and c.startswith('Fecha') else ('double' if '{"'+c+'", each' in m else 'string')
        col={'name':c,'dataType':dtype,'sourceColumn':c,'summarizeBy':'none'}
        if dtype=='dateTime': col['formatString']='yyyy-MM-dd'
        if c.startswith('Clave'): col['isHidden']=True
        cols.append(col)
    tables.append({'name':p.stem,'columns':cols,'partitions':[{'name':p.stem,'mode':'import','source':{'type':'m','expression':m.splitlines()}}]})
measures=[]
for line in (ROOT/'medidas.dax').read_text(encoding='utf-8').splitlines():
    if not line.strip() or line.startswith('//'): continue
    name,expr=line.split(' = ',1); measure={'name':name,'expression':expr}
    if any(x in name for x in ('Fill Rate','Porcentaje','Cobertura')) or name=='OTIF repartos': measure['formatString']='0.0%'
    elif name=='Fecha corte compras': measure['formatString']='yyyy-MM-dd'
    else: measure['formatString']='#,0.##'
    measures.append(measure)
measures.extend([{'name':'Estado OTIF','expression':'"No evaluable: falta validar historia y promesa"'},{'name':'Estado transito','expression':'"Sin evidencia de embarque en las fuentes"'},{'name':'Estado NC','expression':'"Reclamos; referencias NC sin conciliacion contable"'}])
next(t for t in tables if t['name']=='FactOC')['measures']=measures
rels=[]
def rel(fact,column,dim,target):
    rels.append({'name':str(uuid.uuid5(uuid.NAMESPACE_URL,fact+column+dim+target)),'fromTable':fact,'fromColumn':column,'toTable':dim,'toColumn':target,'crossFilteringBehavior':'oneDirection','fromCardinality':'many','toCardinality':'one'})
for f in ['FactOC','FactRepartos','FactMovimientos']:
    rel(f,'ClaveProveedor','DimProveedor','ClaveProveedor'); rel(f,'ClaveProducto','DimProducto','ClaveProducto')
    rel(f,'Moneda','DimMoneda','Moneda')
for f,c in [('FactOC','FechaPedido'),('FactRepartos','FechaPromesa'),('FactMovimientos','FechaContable'),('FactReclamosNC','FechaCaso')]: rel(f,c,'DimFecha','Fecha')
rel('FactReclamosNC','ProveedorTexto','DimProveedorNC','ProveedorTexto')
save(SEM/'model.bim',{'name':'Supplier360','compatibilityLevel':1567,'model':{'culture':'es-CL','defaultPowerBIDataSourceVersion':'powerBI_V3','sourceQueryCulture':'en-US','tables':tables,'relationships':rels,'expressions':[{'name':'pRutaModelo','kind':'m','expression':(ROOT/'powerquery/pRutaModelo.pq').read_text(encoding='utf-8').strip()}]}})
save(DEF/'version.json',{'$schema':BASE+'item/report/definition/versionMetadata/1.0.0/schema.json','version':'4.0.0'})
save(DEF/'report.json',{'$schema':BASE+'item/report/definition/report/3.0.0/schema.json','themeCollection':{}})
pages=[('resumen','01 Resumen compras'),('pendientes','02 Pendientes y transito'),('nc','03 Reclamos y NC'),('supplier','04 Supplier 360'),('calidad','05 Calidad de datos')]
save(DEF/'pages/pages.json',{'$schema':BASE+'item/report/definition/pagesMetadata/1.0.0/schema.json','pageOrder':[p[0] for p in pages],'activePageName':'resumen'})
for name,label in pages: save(DEF/'pages'/name/'page.json',{'$schema':BASE+'item/report/definition/page/2.0.0/schema.json','name':name,'displayName':label,'displayOption':'FitToPage','height':900,'width':1440})
def field(table,name,measure=False): return {'field':{'Measure' if measure else 'Column':{'Expression':{'SourceRef':{'Entity':table}},'Property':name}},'queryRef':table+'.'+name,'nativeQueryRef':name}
def literal(s): return {'expr':{'Literal':{'Value':"'"+s.replace("'","''")+"'"}}}
count=0
def visual(page,kind,title,roles,x,y,w,h):
    global count
    count+=1; name=f'visual{count:03d}'
    v={'visualType':kind,'query':{'queryState':{role:{'projections':fields} for role,fields in roles.items()}},'visualContainerObjects':{'title':[{'properties':{'show':{'expr':{'Literal':{'Value':'true'}}},'text':literal(title)}}]}}
    save(DEF/'pages'/page/'visuals'/name/'visual.json',{'$schema':BASE+'item/report/definition/visualContainer/2.4.0/schema.json','name':name,'position':{'x':x,'y':y,'width':w,'height':h,'z':count,'tabOrder':count},'visual':v})
def card(page,name,x,y,w=330,h=120): visual(page,'card',name,{'Values':[field('FactOC',name,True)]},x,y,w,h)
def slicer(page,table,col,x,y,w=330): visual(page,'slicer',col,{'Values':[field('DimMoneda' if col=='Moneda' else table,col)]},x,y,w,110)
def table(page,title,fields,x,y,w,h): visual(page,'tableEx',title,{'Values':[field(*f) for f in fields]},x,y,w,h)
for i,m in enumerate(['OC distintas','Proveedores con OC','Fill Rate promedio posiciones','Fecha corte compras']): card('resumen',m,20+i*355,20)
slicer('resumen','DimProveedor','Nombre',20,150,680); slicer('resumen','FactOC','Moneda',730,150); slicer('resumen','FactOC','UnidadOC',1085,150)
table('resumen','Desempeno acumulado por proveedor — seleccionar moneda y unidad',[('DimProveedor','Nombre'),('FactOC','Posiciones OC',True),('FactOC','Fill Rate promedio posiciones',True),('FactOC','Valor OC moneda origen',True),('FactOC','Cobertura datos Fill Rate',True)],20,280,1400,390)
card('resumen','Estado OTIF',20,700,680); card('resumen','Estado transito',730,700,690)
for i,m in enumerate(['Repartos pendientes','Repartos vencidos','Valor pendiente moneda origen','Maximo atraso dias']): card('pendientes',m,20+i*355,20)
slicer('pendientes','DimProveedor','Nombre',20,150,680); slicer('pendientes','FactRepartos','Moneda',730,150); slicer('pendientes','FactRepartos','VencidoAlCorte',1085,150)
table('pendientes','Pendiente de recepcion al corte; transito no confirmado',[('FactRepartos','ClaveOC'),('FactRepartos','FechaPromesa'),('FactRepartos','UnidadOC'),('FactRepartos','CantidadPendienteAbierta'),('FactRepartos','DiasAtraso'),('FactRepartos','Moneda'),('FactRepartos','ValorPendienteMonedaOC')],20,280,1400,570)
for i,m in enumerate(['Casos reclamo','Casos con referencia NC','Casos sin resolucion informada']): card('nc',m,20+i*470,20,450)
slicer('nc','DimProveedorNC','ProveedorTexto',20,150,680); slicer('nc','FactReclamosNC','EstadoDocumental',730,150,690)
table('nc','Casos documentales — importes y proveedor SAP pendientes de validar',[('FactReclamosNC','IdCaso'),('FactReclamosNC','ProveedorTexto'),('FactReclamosNC','FechaCaso'),('FactReclamosNC','FacturaReferencia'),('FactReclamosNC','Motivo'),('FactReclamosNC','NCReferencia'),('FactReclamosNC','ResolucionTexto')],20,280,1400,570)
slicer('supplier','DimProveedor','Nombre',20,20,680); slicer('supplier','FactOC','Moneda',730,20); slicer('supplier','FactOC','UnidadOC',1085,20)
for i,m in enumerate(['Fill Rate promedio posiciones','Porcentaje posiciones completas','Valor pendiente vencido','OTIF repartos']): card('supplier',m,20+i*355,150)
table('supplier','Ficha de proveedor SAP',[('DimProveedor','Nombre'),('DimProveedor','RUT'),('DimProveedor','Sociedad'),('DimProveedor','PlazoPago'),('DimProveedor','BloqueoCompra')],20,290,1400,160)
table('supplier','Compra por producto; NC no integradas hasta validar mapeo',[('DimProducto','Descripcion'),('DimProducto','Marca'),('FactOC','Posiciones OC',True),('FactOC','Fill Rate promedio posiciones',True),('FactOC','Valor OC moneda origen',True)],20,470,1400,370)
for i,m in enumerate(['Cobertura datos Fill Rate','Posiciones sin proveedor maestro','Posiciones con descuadre','Repartos evaluables OTIF']): card('calidad',m,20+i*355,20)
table('calidad','Archivos usados en el modelo',[('ControlCarga','Archivo')],20,160,1400,330)
for i,m in enumerate(['Estado OTIF','Estado transito','Estado NC']): card('calidad',m,20,510+i*120,1400,110)
save(ROOT/'diagnostico/proyecto_powerbi.json',{'paginas':len(pages),'visuales':count,'tablas':len(tables),'relaciones':len(rels),'medidas':len(measures),'validacion_desktop':'Pendiente; proyecto sin cache de datos. Actualizar al abrir.'})
print(f'Proyecto generado: {len(pages)} paginas, {count} visuales, {len(measures)} medidas.')
