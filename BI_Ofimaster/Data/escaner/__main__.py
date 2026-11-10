"""Acceso único: python -m escaner COMANDO --help (desde la raíz del proyecto)."""
import importlib
import sys


COMANDOS = {
    'preparar': ('escaner.herramientas.preparar_documentos_recepcion', []),
    'extraer': ('escaner.herramientas.extraer_documentos_recepcion', []),
    'crear-piloto': ('escaner.herramientas.piloto_escaner', []),
    'verificar': ('escaner.herramientas.verificar_escaner', []),
    'evaluar': ('escaner.herramientas.evaluar_escaner_piloto', []),
    'separar': ('escaner.herramientas.separar_facturas_revisadas', []),
    'iniciar': ('automatizacion.piloto_real', ['iniciar']),
}


def main():
    if len(sys.argv) == 1 or sys.argv[1] in {'-h', '--help'}:
        print(__doc__)
        print('Comandos: ' + ', '.join(COMANDOS))
        print('OCR propone; solo la confirmación humana registra cantidades.')
        return
    comando = sys.argv[1]
    if comando not in COMANDOS:
        raise SystemExit('Comando desconocido. Usa python -m escaner --help.')
    modulo, prefijo = COMANDOS[comando]
    originales = sys.argv[:]
    try:
        sys.argv = [f'escaner {comando}', *prefijo, *originales[2:]]
        importlib.import_module(modulo).main()
    finally:
        sys.argv = originales


if __name__ == '__main__':
    main()
