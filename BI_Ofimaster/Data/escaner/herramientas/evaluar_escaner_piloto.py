"""Resume preparación/OCR y verifica originales; no certifica precisión de lectura."""
import argparse
import json
from pathlib import Path

from app.nucleo.configuracion import Configuracion
from app.servicios.documentos_recepcion import DocumentosRecepcion
from automatizacion.piloto_real import entorno_piloto, ruta_piloto, huella


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nombre', required=True)
    args = parser.parse_args()
    entorno = entorno_piloto(args.nombre)
    raiz = ruta_piloto(args.nombre)
    documental = Path(entorno['DOCUMENTOS_RECEPCION_PATH'])
    servicio = DocumentosRecepcion(documental)
    items = servicio.listar()['items']
    extracciones = [servicio.extraccion(d['id']) for d in items]
    archivos = json.loads((raiz / 'piloto.json').read_text(encoding='utf-8'))['archivos']
    originales = all(huella(Path(d['origen'])) == d['sha256_inicial'] for d in archivos.values())
    fuente = Configuracion().ruta_documentos_recepcion
    pdfs = list((documental / 'entrada').glob('*.pdf'))
    originales = originales and all((fuente / 'entrada' / p.name).is_file()
        and huella(fuente / 'entrada' / p.name) == huella(p) for p in pdfs)
    informe = {'nombre': args.nombre, 'documentos_preparados': len(items),
        'documentos_con_extraccion_completa': sum(d.get('completa', False) for d in extracciones),
        'paginas_extraidas': sum(len(d['paginas']) for d in extracciones),
        'lineas_de_texto': sum(len(p['lineas']) for d in extracciones for p in d['paginas']),
        'originales_intactos': originales,
        'borradores_en_demostracion': len(list((documental / 'revisiones').glob('*.borrador.json'))),
        'aceptacion_operacional': 'PENDIENTE',
        'alcance': 'OCR y visor preparados. No acredita precisión de campos/manuscritos, recepción física ni conexión SAP.'}
    assert originales, 'Cambió un original; revisar el informe antes de continuar.'
    (raiz / 'reportes' / 'evaluacion_escaner.json').write_text(json.dumps(informe, indent=2), encoding='utf-8')
    print(json.dumps(informe))


if __name__ == '__main__':
    main()
