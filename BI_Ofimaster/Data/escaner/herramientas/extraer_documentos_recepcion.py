"""Extrae documentos localmente fuera del servidor web, sin escribir en Excel."""
import argparse
import json
from pathlib import Path

from app.nucleo.configuracion import Configuracion
from app.servicios.documentos_recepcion import DocumentosRecepcion
from app.servicios.extraccion_documental import extraer, MotorConLimite


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--carpeta', type=Path)
    parser.add_argument('--identidad', help='Documento específico; por defecto todos los preparados.')
    parser.add_argument('--pagina', type=int)
    parser.add_argument('--modo', choices=('auto', 'texto', 'ocr'), default='auto')
    parser.add_argument('--reprocesar', action='store_true')
    parser.add_argument('--tiempo-maximo', type=int, default=90, help='Segundos máximos por página OCR (10–300).')
    args = parser.parse_args()
    if args.pagina is not None and not args.identidad:
        parser.error('--pagina requiere --identidad.')
    if not 10 <= args.tiempo_maximo <= 300:
        parser.error('--tiempo-maximo debe estar entre 10 y 300.')
    documentos = DocumentosRecepcion(args.carpeta or Configuracion().ruta_documentos_recepcion)
    ids = [args.identidad] if args.identidad else [d['id'] for d in documentos.listar()['items']]
    motor = MotorConLimite(args.tiempo_maximo)
    # Reutilizar imágenes idénticas (vista individual / conjunto) sin repetir OCR.
    for d in documentos.listar()['items']:
        try:
            anteriores = documentos.extraccion(d['id']).get('paginas', [])
        except (ValueError, OSError, KeyError):
            anteriores = []  # Reprocesar las imágenes nuevas, no usar texto obsoleto.
        for p in anteriores:
            if p['metodo'] == 'RAPIDOCR_LOCAL' and not args.reprocesar:
                motor.cache[p['sha256_imagen']] = p['lineas']
    errores = 0
    for identidad in ids:
        try:
            informe = extraer(documentos, identidad, motor=motor, pagina=args.pagina, modo=args.modo,
                reprocesar=args.reprocesar, progreso=lambda pagina, metodo: print(
                    json.dumps({'id': identidad, 'pagina': pagina, 'metodo': metodo}), flush=True))
            print(json.dumps({'id': identidad, 'paginas': len(informe['paginas']),
                'lineas': sum(len(p['lineas']) for p in informe['paginas']),
                'estado': informe['estado'], 'registro_operacional': False}), flush=True)
        except Exception as error:
            errores += 1
            print(json.dumps({'id': identidad, 'estado': 'ERROR', 'detalle': str(error)}), flush=True)
    if errores:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
