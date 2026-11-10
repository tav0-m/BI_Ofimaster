import json,collections,datetime as dt,zipfile,xml.etree.ElementTree as ET
from decimal import Decimal,InvalidOperation
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'diagnostico'
rows=json.loads((OUT/'nuevo_excel_filas.json').read_text(encoding='utf-8'))['Data']
headers=rows[0]['cells']; data=rows[1:]
def val(r,i):return r['cells'].get(str(i),'').strip()
def dec(v):
    try:return Decimal(v) if v else None
    except InvalidOperation:return None
def key(r):return tuple(val(r,i) for i in (6,3,2,1))
selected=[r for r in data if val(r,2)=='61' and val(r,6)=='8000']
groups=collections.defaultdict(list)
for r in selected:groups[key(r)].append(r)
profile=[]
for i,name in headers.items():
    idx=int(i); nonempty=[val(r,idx) for r in selected if val(r,idx)]
    profile.append({'index':idx,'field':name,'nonempty_all':sum(bool(val(r,idx)) for r in data),'nonempty_nc':len(nonempty),'distinct_nc':len(set(nonempty))})
conflicts=[]; ratio=collections.Counter(); sums={i:Decimal(0) for i in [8,13,15,25,27]}; details=[]
for k,rs in groups.items():
    inconsistent=[headers[str(i)]+'@'+str(i) for i in [4,5,7,8,9,10,11,12,13,14,15,16,17,18,19] if len({val(r,i) for r in rs})>1]
    if inconsistent:conflicts.append({'key':k,'fields':inconsistent})
    net=dec(val(rs[0],8)); line=sum((dec(val(r,27)) or Decimal(0) for r in rs),Decimal(0))
    unit=sum((dec(val(r,25)) or Decimal(0) for r in rs),Decimal(0))
    if net is not None and line:ratio[str((net/line).quantize(Decimal('.0001')))]+=1
    for i in [8,13,15]:sums[i]+=dec(val(rs[0],i)) or Decimal(0)
    for i in [25,27]:sums[i]+=sum((dec(val(r,i)) or Decimal(0) for r in rs),Decimal(0))
    details.append({'key':k,'rows':len(rs),'header_net_raw':str(net),'line_monto_sum_raw':str(line),'line_valorneto_sum_raw':str(unit)})
ratematches=0; mismatches=0; filled=0
for r in selected:
    q,p,a=[dec(val(r,i)) for i in [23,25,27]]
    if all(x is not None for x in (q,p,a)):
        filled+=1
        if abs(q*p-a)<=Decimal('1'):ratematches+=1
        else:mismatches+=1
# Coincidencias candidatas de interlocutor y RUT en maestro local.
import csv
prov=list(csv.DictReader((ROOT.parent/'Data/data_DWH/prov_202610061552.csv').open(encoding='utf-8-sig')))
norm=lambda v:(v.strip().lstrip('0') or '0')
master={(norm(r['sociedad']),norm(r['id_proveedor'])):r for r in prov}
missing=set(); rutconflicts=set()
for r in selected:
    k=(norm(val(r,6)),norm(val(r,4))); p=master.get(k)
    if p is None:missing.add(k)
    elif val(r,3).upper().replace('.','').replace('-','')!=p['STCD1'].upper().replace('.','').replace('-',''):rutconflicts.add(k)
serials=[dec(val(r,7)) for r in selected if dec(val(r,7)) is not None]
dates=[(dt.date(1899,12,30)+dt.timedelta(days=int(s))).isoformat() for s in serials]
result={'rows_all':len(data),'sociedades':dict(collections.Counter(val(r,6) for r in data)),'dte':dict(collections.Counter(val(r,2) for r in data)),'rows_nc_8000':len(selected),'documents_nc_8000':len(groups),'suppliers_nc_8000':len({val(r,3) for r in selected}),'documents_multiline':sum(len(rs)>1 for rs in groups.values()),'max_lines_document':max((len(rs) for rs in groups.values()),default=0),'date_min':min(dates,default=''),'date_max':max(dates,default=''),'header_conflicts':conflicts,'columns':profile,'header_net_to_sum_line_monto_ratios':dict(ratio),'sums_raw_not_validated':{headers[str(i)]+'@'+str(i):str(v) for i,v in sums.items()},'line_q_times_valorneto_matches_monto':ratematches,'line_q_times_valorneto_mismatches':mismatches,'line_q_times_valorneto_evaluated':filled,'supplier_missing_local':sorted(missing),'supplier_rut_conflicts_local':sorted(rutconflicts),'reference_blank':sum(not val(r,0) for r in selected),'reference_distinct':len({val(r,0) for r in selected}),'nc_reference_matches_oc_local':None}
ocs={norm(r['EBELN']) for r in csv.DictReader((ROOT.parent/'Data/data_DWH/SAP_EKKO_202610081740.csv').open(encoding='utf-8-sig'))}
result['nc_reference_matches_oc_local']=sum(norm(val(r,0)) in ocs for r in selected)
result['currencies_nc']=sorted({val(r,9) for r in selected})
result['header_currency_columns_equal']=all(len({val(r,i) for i in [9,11,14,16,18,19]})==1 for r in selected)
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(Path(r'C:\Users\gustavo.chuquiviguel\Downloads\FACTURAS Y NCR OFIMASTER 09.11.2026.xlsx')) as z:
    styles=ET.fromstring(z.read('xl/styles.xml')); xfs=styles.find('s:cellXfs',ns)
    formats={x.get('numFmtId'):x.get('formatCode') for x in styles.findall('s:numFmts/s:numFmt',ns)}
    root=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
    sample=next(r for r in root.findall('s:sheetData/s:row',ns) if int(r.get('r'))==selected[0]['row'])
    result['numeric_format_sample']=[{'cell':c.get('r'),'format':formats.get(xfs[int(c.get('s','0'))].get('numFmtId'),xfs[int(c.get('s','0'))].get('numFmtId'))} for c in sample if ''.join(x for x in c.get('r') if x.isalpha()) in ['H','I','N','P','X','Z','AB']]
(OUT/'nuevo_excel_auditoria.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'nuevo_excel_documentos_control.json').write_text(json.dumps(details,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=True,indent=2))
