"""Prepara PDF locales para revisión. No registra recepciones ni ejecuta OCR."""
from hashlib import sha256
from contextlib import closing
import argparse
import json
import os
from pathlib import Path
import uuid

from app.nucleo.configuracion import Configuracion
from app.repositorios.bloqueo_libro import bloqueo_libro


def preparar(ruta: Path, salida: Path) -> dict:
    # La preparación nunca toca Excel, revisiones humanas ni confirmaciones.
    with ruta.open('rb') as archivo:
        contenido = archivo.read(50 * 1024 * 1024 + 1)
    if not contenido or len(contenido) > 50 * 1024 * 1024 or not contenido.startswith(b'%PDF-'):
        raise ValueError('Se requiere un PDF válido de hasta 50 MB.')
    identidad = sha256(contenido).hexdigest()
    with bloqueo_libro(salida / (identidad + '.preparacion')):
        return _preparar(ruta, salida, contenido)


def _preparar(ruta: Path, salida: Path, contenido: bytes) -> dict:
    import pypdfium2 as pdfium

    if len(contenido) > 50 * 1024 * 1024 or not contenido.startswith(b"%PDF-"):
        raise ValueError("Se requiere un PDF válido de hasta 50 MB.")
    huella = sha256(contenido).hexdigest()
    destino = salida / huella
    manifiesto = destino / 'documento.json'
    if manifiesto.is_file():
        existente = json.loads(manifiesto.read_text(encoding='utf-8'))
        if existente.get('sha256') != huella:
            raise ValueError('El manifiesto existente no coincide con el PDF.')
        paginas = existente.get('paginas', [])
        if paginas and all((destino / f'pagina_{p["pagina"]:03d}.png').is_file()
                           and (destino / f'pagina_{p["pagina"]:03d}.txt').is_file() for p in paginas):
            return existente
    with pdfium.PdfDocument(contenido) as documento:
        if not 1 <= len(documento) <= 30:
            raise ValueError("El piloto admite entre 1 y 30 páginas por documento.")
        destino.mkdir(parents=True, exist_ok=True)
        paginas = []
        for indice in range(len(documento)):
            with closing(documento[indice]) as pagina:
                with closing(pagina.get_textpage()) as lector:
                    texto = lector.get_text_bounded()
                ancho, alto = pagina.get_size()
                if ancho <= 0 or alto <= 0:
                    raise ValueError("Página sin dimensiones válidas.")
                escala = min(2, 2400 / max(ancho, alto))
                nombre = f"pagina_{indice + 1:03d}"
                with closing(pagina.render(scale=escala)) as bitmap:
                    imagen = bitmap.to_pil()
                    try:
                        imagen.save(destino / f"{nombre}.png")
                    finally:
                        imagen.close()
                (destino / f"{nombre}.txt").write_text(texto, encoding="utf-8")
                paginas.append({"pagina": indice + 1, "caracteres_texto": len(texto.strip()),
                                "imagen": f"{nombre}.png", "texto": f"{nombre}.txt",
                                "estado": "CON_TEXTO_PARA_REVISAR" if texto.strip() else "REQUIERE_OCR"})
        informe = {"archivo": ruta.name, "sha256": huella, "paginas": paginas,
                   "estado": "PENDIENTE_REVISION", "registro_operacional": False}
        temporal = destino / f'.documento_{uuid.uuid4().hex}.tmp'
        temporal.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temporal, manifiesto)
    return informe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--carpeta', type=Path, help='Raíz documental; por defecto DOCUMENTOS_RECEPCION_PATH.')
    args = parser.parse_args()
    raiz = (args.carpeta or Configuracion().ruta_documentos_recepcion).resolve()
    (raiz / 'entrada').mkdir(parents=True, exist_ok=True)
    (raiz / 'resultados').mkdir(parents=True, exist_ok=True)
    archivos = sorted(p for p in (raiz / "entrada").iterdir() if p.suffix.lower() == ".pdf")
    for ruta in archivos:
        informe = preparar(ruta, raiz / "resultados")
        print(json.dumps(informe, ensure_ascii=False))
    if not archivos:
        print("No hay PDF en data/documentos_recepcion/entrada.")


if __name__ == "__main__":
    main()
