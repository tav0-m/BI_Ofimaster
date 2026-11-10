"""Prepara una demostración documental con copias, sin copiar confirmaciones."""
import argparse
import json
from pathlib import Path

from app.nucleo.configuracion import Configuracion
from app.servicios.documentos_recepcion import DocumentosRecepcion
from automatizacion.piloto_real import preparar, ruta_piloto, copiar_estable, huella
from escaner.herramientas.preparar_documentos_recepcion import preparar as preparar_pdf


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nombre', required=True, help='Nombre nuevo, nunca un piloto existente.')
    args = parser.parse_args()
    config = Configuracion()
    fuente = config.ruta_documentos_recepcion.resolve()
    entradas = sorted((fuente / 'entrada').glob('*.pdf'))
    if not entradas:
        raise ValueError('No hay PDF en la entrada documental configurada.')
    if any(p.is_symlink() or not p.resolve().is_relative_to(fuente) for p in entradas):
        raise ValueError('No se copian enlaces ni rutas externas desde la entrada documental.')
    manifiesto = preparar(args.nombre, config)
    raiz = ruta_piloto(args.nombre) / 'documentos_recepcion'
    for carpeta in ('entrada', 'resultados', 'revisiones', 'plantillas'):
        (raiz / carpeta).mkdir(exist_ok=True)
    firmas = {}
    for original in entradas:
        datos = copiar_estable(original, raiz / 'entrada' / original.name)
        identidad = datos['sha256_inicial']
        firmas[original.name] = identidad
        preparar_pdf(raiz / 'entrada' / original.name, raiz / 'resultados')
        # Índices humanos de lectura, nunca .borrador.json ni confirmaciones.
        revision = fuente / 'revisiones' / (identidad + '.json')
        if revision.is_file():
            if revision.is_symlink() or not revision.resolve().is_relative_to(fuente):
                raise ValueError('Revisión externa no permitida.')
            copiar_estable(revision, raiz / 'revisiones' / revision.name)
            contenido = json.loads(revision.read_text(encoding='utf-8'))
            if contenido.get('requiere_separacion'):
                from escaner.herramientas.separar_facturas_revisadas import separar
                separar(raiz, identidad)
        print(json.dumps({'archivo': original.name, 'preparado': True}), flush=True)
    intactos = all(huella(Path(d['origen'])) == d['sha256_inicial']
                   for d in manifiesto['archivos'].values())
    intactos = intactos and all(huella(fuente / 'entrada' / n) == firma for n, firma in firmas.items())
    if not intactos:
        raise ValueError('Un original cambió durante la preparación. Revisar el piloto.')
    informe = {'nombre': args.nombre, 'documentos': DocumentosRecepcion(raiz).listar()['items'],
        'originales_intactos': intactos, 'confirmaciones_copiadas': False,
        'alcance': 'Demostración documental en copias. No volver a registrar documentos ya recibidos en operación.'}
    (ruta_piloto(args.nombre) / 'reportes' / 'piloto_escaner.json').write_text(
        json.dumps(informe, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'nombre': args.nombre, 'documentos': len(informe['documentos']),
        'originales_intactos': intactos, 'confirmaciones_copiadas': False}))


if __name__ == '__main__':
    main()
