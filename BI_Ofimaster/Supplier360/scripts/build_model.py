"""Modelo reproducible sin dependencias. No modifica los archivos originales."""
import csv, json, re, collections, datetime as dt, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
from decimal import Decimal, InvalidOperation
ROOT=Path(__file__).resolve().parents[2]; BASE=ROOT/'Data/data_DWH'; OUT=ROOT/'Supplier360/modelo'; OUT.mkdir(parents=True,exist_ok=True)
quality={}; manifest=[]
def source(prefix):
    p=sorted(BASE.glob(prefix+'_20*.csv'))[-1]; manifest.append(p.name); return p
def read(prefix):
    p=source(prefix)
    with p.open(encoding='utf-8-sig',newline='') as f: yield from csv.DictReader(f)
def key(v):
    s=(v or '').strip(); return (s.lstrip('0') or '0') if s.isdigit() else s
def num(v):
    try: return Decimal(v) if v and v.strip() else Decimal(0)
    except InvalidOperation: raise ValueError('Numero no interpretable: '+repr(v))
def date(v):
    v=(v or '').strip()
    for fmt in ('%Y%m%d','%Y-%m-%d','%Y-%m-%d %H:%M:%S.%f'):
        try: return dt.datetime.strptime(v,fmt).date().isoformat()
        except ValueError: pass
    return ''
def write(name,rows,fields=None):
    rows=list(rows)
    with (OUT/(name+'.csv')).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields or list(rows[0]),extrasaction='ignore'); w.writeheader(); w.writerows(rows)
def unique(rows,cols,label):
    result={}; duplicates=0
    for r in rows:
        k=tuple(key(r[c]) for c in cols)
        if k in result:
            duplicates+=1
            if result[k]!=r: raise ValueError(f'{label}: clave conflictiva {k}')
        result[k]=r
    quality[label+'_duplicados_exactos']=duplicates
    return result
headers=unique(read('SAP_EKKO'),['EBELN'],'EKKO')
items=unique(read('SAP_EKPO'),['EBELN','EBELP'],'EKPO')
oc=unique(read('oc'),['Documento_compras','posicion'],'oc')
prov_fields=['sociedad','id_proveedor','nombre','STCD1','pais','id_plazo_pago_prov','bloqueo_compra']
prov=unique(({c:r[c] for c in prov_fields} for r in read('prov')),['sociedad','id_proveedor'],'prov')
materials=unique(read('mat'),['sociedad','material'],'mat')
quality.update(cabeceras=len(headers),posiciones=len(items),oc_vista=len(oc),proveedores=len(prov),materiales=len(materials))
print('Maestros y OC leidos',flush=True)
schedule={}; n=0; matched=0; dup=0
for r in read('SAP_EKET'):
    n+=1; k=(key(r['EBELN']),key(r['EBELP']))
    if k not in items: continue
    matched+=1; sk=k+(key(r['ETENR']),)
    if sk in schedule:
        dup+=1
        if schedule[sk]!=r: raise ValueError('EKET conflictivo '+str(sk))
    schedule[sk]=r
quality.update(eket_filas_total=n,eket_filas_con_posicion=matched,eket_claves_seleccionadas=len(schedule),eket_duplicados_exactos=dup)
byitem=collections.defaultdict(list)
for sk,r in schedule.items(): byitem[sk[:2]].append(r)
print('EKET completo leido: '+str(n),flush=True)
movements=[]; movement_types=collections.Counter(); linked_types=collections.Counter(); dates=[]; unit_mismatch=0
for r in read('KARDEX'):
    movement_types[r['CODGLOSA']]+=1
    d=date(r['FECHA_CONTAB'])
    if d: dates.append(d)
    k=(key(r['EBELN']),key(r['EBELP']))
    if k not in items: continue
    linked_types[r['CODGLOSA']]+=1
    item=items[k]; h=headers.get((k[0],),{}); soc=key(item['BUKRS']); supplier=key(h.get('LIFNR'))
    if r['UM_BASE']!=item['MEINS']: unit_mismatch+=1
    movements.append(dict(ClaveOC='|'.join(k),ClaveProveedor=soc+'|'+supplier,ClaveProducto=soc+'|'+key(item['MATNR']),DocumentoMaterial=r['SECUEN'],PosicionMovimiento=r['ZEILE'],FechaContable=d,FechaDocumento=date(r['FECHA_DOC']),TipoMovimiento=r['CODGLOSA'],Glosa=r['GLOSA'],Entrada=num(r['ENTRA']),Salida=num(r['SALE']),CantidadNetaBase=num(r['ENTRA'])-num(r['SALE']),UnidadBase=r['UM_BASE'],UnidadOC=item['MEINS'],Centro=r['CENTRO'],Almacen=r['ALMACEN'],Moneda=r['MONEDA'],ImporteOrigen=num(r['IMPORTE']),FechaExtraccion=date(r['FECHA_BULK'])))
quality.update(kardex_filas=sum(movement_types.values()),kardex_fecha_min=min(dates,default=''),kardex_fecha_max=max(dates,default=''),kardex_movimientos_vinculados=len(movements),kardex_tipos=dict(movement_types),kardex_tipos_vinculados=dict(linked_types),movimientos_unidad_distinta=unit_mismatch)
facts=[]; schedules=[]; missingh=0; missingp=set(); missingm=set(); discrepancies=0
for k,r in items.items():
    h=headers.get((k[0],),{}); missingh+=not bool(h)
    soc=key(r['BUKRS']); supplier=key(h.get('LIFNR')); mat=key(r['MATNR']); sch=byitem[k]; view=oc.get(k,{})
    if (soc,supplier) not in prov: missingp.add((soc,supplier))
    if (soc,mat) not in materials: missingm.add((soc,mat))
    q=num(r['MENGE']); qs=sum((num(x['MENGE']) for x in sch),Decimal(0)); received=sum((num(x['WEMNG']) for x in sch),Decimal(0)) if sch else None
    discrepancy=bool(sch) and abs(qs-q)>Decimal('.00001'); discrepancies+=discrepancy
    deleted=bool((r['LOEKZ'] or '').strip() or (h.get('LOEKZ') or '').strip()); closed=r['ELIKZ']=='X'
    scope=bool(mat and h and not deleted and h.get('RESWK','') in ('','0000') and q>0)
    valid=scope and bool(sch) and not discrepancy and received>=0
    cutoff=date(r['FECHA_PROCESO']); due=sorted(date(x['EINDT']) for x in sch if date(x['EINDT']))
    pending=max(q-received,Decimal(0)) if received is not None else None
    shortage=max(q-min(max(received,Decimal(0)),q),Decimal(0)) if received is not None else None
    line=dict(ClaveOC='|'.join(k),OC=k[0],Posicion=k[1],ClaveProveedor=soc+'|'+supplier,ClaveProducto=soc+'|'+mat,Sociedad=soc,ProveedorSAP=supplier,Material=mat,Descripcion=r['TXZ01'],Centro=r['WERKS'],Almacen=r['LGORT'],TipoOC=h.get('BSART',''),GrupoCompras=h.get('EKGRP',''),FechaPedido=date(h.get('BEDAT')),FechaCorte=cutoff,FechaPromesaMin=due[0] if due else '',FechaPromesaMax=due[-1] if due else '',Moneda=h.get('WAERS',''),UnidadOC=r['MEINS'],CantidadPedida=q,CantidadProgramada=qs if sch else '',CantidadRecibidaAcumulada=received if received is not None else '',CantidadCubierta=min(max(received,Decimal(0)),q) if valid else '',CantidadElegible=q if valid else '',CantidadFaltante=shortage if valid else '',CantidadPendienteAbierta=pending if valid and not closed else (0 if valid else ''),ValorNetoOC=num(r['NETWR']),ValorPendienteMonedaOC=(num(r['NETWR'])*pending/q if valid and not closed else (0 if valid else '')),Borrada=int(deleted),EntregaFinal=int(closed),ElegibleCompras=int(scope),ElegibleFillRate=int(valid),Repartos=len(sch),DescuadreRepartos=int(discrepancy),ProveedorEnMaestro=int((soc,supplier) in prov),ProductoEnMaestro=int((soc,mat) in materials),CantidadEntregadaVista=num(view.get('Cantidad_entregada')) if view else '',FechaEmbarqueCandidata=date(h.get('ZZFEEMB')),FechaArriboCandidata=date(h.get('ZZFAEST')),EstadoTransito='No verificable',OTIFEvaluable=0,OTIFCumple='',MotivoOTIF='Pendiente validar cobertura historica, promesa original y movimientos')
    facts.append(line)
    for x in sch:
        d=date(x['EINDT']); quantity=num(x['MENGE']); recv=num(x['WEMNG']); pend=max(quantity-recv,Decimal(0))
        schedules.append(dict(ClaveReparto='|'.join(k+(key(x['ETENR']),)),ClaveOC='|'.join(k),ClaveProveedor=line['ClaveProveedor'],ClaveProducto=line['ClaveProducto'],Sociedad=soc,Moneda=line['Moneda'],UnidadOC=r['MEINS'],FechaCorte=cutoff,FechaPromesa=d,FechaPromesaEstadistica=date(x['SLFDT']),CantidadProgramada=quantity,CantidadRecibidaAcumulada=recv,CantidadPendienteAbierta=pend if valid and not closed else (0 if valid else ''),ValorPendienteMonedaOC=num(r['NETWR'])*pend/q if valid and not closed else (0 if valid else ''),VencidoAlCorte=int(bool(d and cutoff and d<cutoff)),DiasAtraso=max(0,(dt.date.fromisoformat(cutoff)-dt.date.fromisoformat(d)).days) if d and cutoff else '',Elegible=int(valid and not closed),OTIFEvaluable=0,OTIFCumple=''))
write('FactOC',facts); write('FactRepartos',schedules); write('FactMovimientos',movements)
dimprov=[dict(ClaveProveedor=s+'|'+p,ProveedorSAP=p,Sociedad=s,Nombre=r['nombre'],RUT=r['STCD1'],Pais=r['pais'],PlazoPago=r['id_plazo_pago_prov'],BloqueoCompra=r['bloqueo_compra'],ExisteMaestro=1) for (s,p),r in prov.items()]
dimprov.extend(dict(ClaveProveedor=s+'|'+p,ProveedorSAP=p,Sociedad=s,Nombre='SIN MAESTRO: '+p,RUT='',Pais='',PlazoPago='',BloqueoCompra='',ExisteMaestro=0) for s,p in sorted(missingp))
write('DimProveedor',dimprov)
dimprod=[dict(ClaveProducto=s+'|'+m,Sociedad=s,Material=m,Descripcion=r['descripcion'],Linea=r['linea'],Rubro=r['rubro'],Marca=r['marca'],UnidadBase=r['Unidad_medida_base'],Importado=r['Importado'],ExisteMaestro=1) for (s,m),r in materials.items()]
dimprod.extend(dict(ClaveProducto=s+'|'+m,Sociedad=s,Material=m,Descripcion='SIN MAESTRO: '+m,Linea='',Rubro='',Marca='',UnidadBase='',Importado='',ExisteMaestro=0) for s,m in sorted(missingm))
write('DimProducto',dimprod)
quality.update(posiciones_sin_cabecera=missingh,proveedores_clave_sin_maestro=len(missingp),productos_clave_sin_maestro=len(missingm),posiciones_sin_repartos=sum(not x['Repartos'] for x in facts),posiciones_descuadre_repartos=discrepancies,posiciones_elegibles_fillrate=sum(x['ElegibleFillRate'] for x in facts),posiciones_sin_proveedor_maestro=sum(not x['ProveedorEnMaestro'] for x in facts),posiciones_con_fecha_embarque_candidata=sum(bool(x['FechaEmbarqueCandidata']) for x in facts))
# El Excel contiene casos/reclamos, no un libro contable de NC.
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(ROOT/'Data/NC/NC PROVEEDORES.xlsx') as z:
    strings=[''.join(t.itertext()) for t in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',ns)] if 'xl/sharedStrings.xml' in z.namelist() else []
    rows=[]
    for row in ET.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('s:sheetData/s:row',ns)[1:]:
        cells={}
        for c in row:
            v=c.find('s:v',ns); val=v.text if v is not None else ''
            if c.get('t')=='s': val=strings[int(val)] if val else ''
            if c.get('t')=='inlineStr': val=''.join(c.find('s:is',ns).itertext())
            cells[re.sub(r'\d','',c.get('r'))]=val
        if not any(cells.get(k) for k in ('A','B','C','D','E','G','H','I')): continue
        rawdate=cells.get('B',''); d=''
        if rawdate:
            try: d=(dt.date(1899,12,30)+dt.timedelta(days=float(rawdate))).isoformat()
            except ValueError: d=date(rawdate)
        resolution=cells.get('I',''); refs=re.findall(r'\bNC\s*[:#-]?\s*(\d+)',resolution,re.I)
        rawamount=cells.get('G','').strip()
        try: amount=num(rawamount) if rawamount else ''
        except ValueError: amount=''
        rows.append(dict(IdCaso='EXCEL-'+row.get('r'),FilaOrigen=row.get('r'),ProveedorTexto=cells.get('A','').strip(),ClaveProveedor='',FechaCaso=d,FacturaReferencia=cells.get('C',''),Motivo=cells.get('D',''),ProductoTexto=cells.get('E',''),Descripcion=cells.get('F',''),MontoReclamado=amount,MontoOrigenTexto=rawamount,Moneda='SIN_CONFIRMAR',OCReferencia=cells.get('H',''),ResolucionTexto=resolution,NCReferencia='|'.join(refs),EstadoDocumental='Referencia NC sin conciliacion' if refs else ('Resolucion textual por validar' if resolution else 'Sin resolucion informada'),ContabilizadaVerificada=0,FechaContabilizacion='',MontoNCContable='',SaldoNCContable=''))
write('FactReclamosNC',rows)
write('MapProveedorNC',[dict(ProveedorTexto=x,ClaveProveedor='',Estado='PENDIENTE_VALIDACION') for x in sorted(set(r['ProveedorTexto'] for r in rows))])
quality.update(nc_casos=len(rows),nc_con_referencia=sum(bool(r['NCReferencia']) for r in rows),nc_sin_oc=sum(not r['OCReferencia'] for r in rows),nc_sin_fecha=sum(not r['FechaCaso'] for r in rows),nc_proveedores=sorted(set(r['ProveedorTexto'] for r in rows)))
write('DimProveedorNC',[dict(ProveedorTexto=x) for x in quality['nc_proveedores']])
all_dates=[x['FechaPedido'] for x in facts]+[x['FechaCorte'] for x in facts]+[x['FechaPromesa'] for x in schedules]+[x['FechaCaso'] for x in rows]+dates
all_dates=[dt.date.fromisoformat(x) for x in all_dates if x]; start=min(all_dates); end=max(all_dates)
write('DimFecha',[dict(Fecha=(d:=start+dt.timedelta(days=i)).isoformat(),Anio=d.year,Mes=d.month,AnioMes=d.strftime('%Y-%m'),Trimestre=(d.month-1)//3+1) for i in range((end-start).days+1)])
write('ControlCarga',[dict(Archivo=x) for x in sorted(set(manifest))])
(ROOT/'Supplier360/diagnostico/calidad_modelo.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(quality,ensure_ascii=False,indent=2))
