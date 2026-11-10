"""Proceso acotado de inferencia OCR; solo recibe una imagen local preparada."""
import argparse
import json
from pathlib import Path
from app.servicios.extraccion_documental import MotorLocal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--imagen', required=True, type=Path)
    parser.add_argument('--salida', required=True, type=Path)
    args = parser.parse_args()
    imagen = args.imagen.resolve(strict=True)
    salida = args.salida.resolve()
    if imagen.suffix != '.png' or salida.parent != imagen.parent or not salida.name.startswith('.ocr_') or salida.suffix != '.tmp':
        parser.error('Solo se admiten imagen preparada y resultado temporal en la misma carpeta.')
    lineas = MotorLocal().leer(imagen)
    with salida.open('x', encoding='utf-8') as archivo:
        json.dump(lineas, archivo, ensure_ascii=False)


if __name__ == '__main__':
    main()
