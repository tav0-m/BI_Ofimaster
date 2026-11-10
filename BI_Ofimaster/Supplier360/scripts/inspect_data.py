import csv, json, re, collections, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Supplier360' / 'diagnostico'
OUT.mkdir(parents=True, exist_ok=True)
profiles=[]
for p in sorted((ROOT/'Data/data_DWH').glob('*.csv')):
    with p.open(encoding='utf-8-sig', errors='strict', newline='') as f:
        reader=csv.DictReader(f)
        cols=reader.fieldnames
        nulls=collections.Counter(); samples={c:[] for c in cols}; n=0; bad=0
        limit=10000 if p.stat().st_size>100_000_000 else None
        for row in reader:
            n+=1
            if None in row: bad+=1
            for c in cols:
                v=row[c]
                if v is None or not v.strip(): nulls[c]+=1
                elif len(samples[c])<3 and v not in samples[c]: samples[c].append(v)
            if limit and n>=limit: break
        profiles.append(dict(file=p.name,bytes=p.stat().st_size,rows_examined=n,scope='first_10000' if limit else 'full', malformed=bad,columns=[dict(name=c,nulls=nulls[c],samples=samples[c]) for c in cols]))
(OUT/'perfil_tablas.json').write_text(json.dumps(profiles,ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'inventario_campos.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f); w.writerow(['Archivo','Bytes','Filas_examinadas','Alcance','Campo','Vacios','Porcentaje_vacio'])
    for p in profiles:
        for c in p['columns']: w.writerow([p['file'],p['bytes'],p['rows_examined'],p['scope'],c['name'],c['nulls'],round(100*c['nulls']/max(1,p['rows_examined']),2)])
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(ROOT/'Data/NC/NC PROVEEDORES.xlsx') as z:
    strings=[]
    if 'xl/sharedStrings.xml' in z.namelist():
        strings=[''.join(x.itertext()) for x in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',ns)]
    wb=ET.fromstring(z.read('xl/workbook.xml'))
    sheets=[]
    for name in z.namelist():
        if re.fullmatch(r'xl/worksheets/sheet\d+.xml',name):
            rows=[]
            for row in ET.fromstring(z.read(name)).findall('s:sheetData/s:row',ns):
                vals={}
                for cell in row:
                    v=cell.find('s:v',ns); val=v.text if v is not None else ''
                    if cell.get('t')=='s': val=strings[int(val)] if val else ''
                    if cell.get('t')=='inlineStr': val=''.join(cell.find('s:is',ns).itertext())
                    vals[cell.get('r')]=val
                rows.append(vals)
            sheets.append(dict(file=name,rows=len(rows),sample=rows[:12]))
    (OUT/'perfil_excel_nc.json').write_text(json.dumps({'sheets':[s.attrib for s in wb.findall('s:sheets/s:sheet',ns)],'data':sheets},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'files':len(profiles),'xlsx':sheets},ensure_ascii=False))
