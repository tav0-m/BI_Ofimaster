"""Inspeccion de solo lectura del nuevo Excel aportado por el usuario."""
import zipfile, xml.etree.ElementTree as ET, json, collections, re, posixpath
from pathlib import Path
SOURCE=Path(r'C:\Users\gustavo.chuquiviguel\Downloads\FACTURAS Y NCR OFIMASTER 09.11.2026.xlsx')
OUT=Path(__file__).resolve().parents[1]/'diagnostico'
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def colindex(ref):
    n=0
    for c in re.sub('[0-9]','',ref): n=n*26+ord(c)-64
    return n-1
with zipfile.ZipFile(SOURCE) as z:
    shared=[]
    if 'xl/sharedStrings.xml' in z.namelist():
        shared=[''.join(t.text or '' for t in si.findall('.//s:t',NS)) for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',NS)]
    rels={r.get('Id'):r.get('Target') for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    wb=ET.fromstring(z.read('xl/workbook.xml')); results=[]; extracted={}
    for s in wb.findall('s:sheets/s:sheet',NS):
        target=rels[s.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')]
        path=target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
        root=ET.fromstring(z.read(path)); rows=[]; formulas=0
        for row in root.findall('s:sheetData/s:row',NS):
            cells={}
            for c in row.findall('s:c',NS):
                value=c.find('s:v',NS); v=value.text or '' if value is not None else ''
                if c.get('t')=='s': v=shared[int(v)] if v else ''
                elif c.get('t')=='inlineStr': v=''.join(t.text or '' for t in c.findall('.//s:t',NS))
                if c.find('s:f',NS) is not None: formulas+=1
                idx=colindex(c.get('r'))
                cells[idx]='[URI omitida]' if idx==20 and v and int(row.get('r'))!=1 else v
            if any(v.strip() for v in cells.values()): rows.append({'row':int(row.get('r')),'cells':cells})
        result={'sheet':s.get('name'),'nonempty_rows':len(rows),'formula_cells':formulas,'sample':rows[:7]}
        results.append(result); extracted[s.get('name')]=rows
    (OUT/'nuevo_excel_estructura.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'nuevo_excel_filas.json').write_text(json.dumps(extracted,ensure_ascii=False),encoding='utf-8')
    print(json.dumps([{'sheet':r['sheet'],'nonempty_rows':r['nonempty_rows'],'headers':r['sample'][0]} for r in results],ensure_ascii=True,indent=2))
