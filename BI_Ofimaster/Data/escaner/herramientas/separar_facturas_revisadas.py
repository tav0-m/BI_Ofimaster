"""Crea revisiones individuales por página desde un índice humano ya revisado.

Conserva el PDF original: genera vistas documentales, no nuevos movimientos Excel
ni PDF independientes. No detecta automáticamente límites entre facturas.
"""
import argparse
from hashlib import sha256
import json
import os
import shutil

from app.nucleo.configuracion import Configuracion
from app.servicios.documentos_recepcion import DocumentosRecepcion
from app.repositorios.bloqueo_libro import bloqueo_libro


def separar(raiz, identidad):
    servicio = DocumentosRecepcion(raiz)
    origen = servicio.obtener(identidad)
    revision = origen.get("revision") or {}
    facturas = revision.get("facturas", [])
    if not revision.get("requiere_separacion") or not facturas:
        raise ValueError("Se requiere un índice humano de facturas con separación pendiente.")
    paginas = [f.get("pagina") for f in facturas]
    if any(type(p) is not int for p in paginas) or sorted(paginas) != list(range(1, len(origen["paginas"]) + 1)):
        raise ValueError("Este separador exige una factura revisada por página, sin omisiones ni repeticiones.")
    if any(not f.get("proveedor") or not f.get("folio") for f in facturas):
        raise ValueError("Cada factura necesita proveedor y folio revisados.")
    original = servicio._ruta("entrada", origen["archivo"])
    if sha256(original.read_bytes()).hexdigest() != identidad:
        raise ValueError("El PDF original no coincide con su huella. No se separó.")
    # Validar todas las imágenes antes de generar ninguna vista.
    imagenes = {p: servicio.imagen(identidad, p) for p in paginas}
    bloqueo = servicio._ruta("revisiones", identidad + ".borrador.json")
    resultados = []
    with bloqueo_libro(bloqueo):
        if bloqueo.exists():
            raise ValueError("El conjunto tiene un borrador previo. Revisar su historial antes de separar.")
        for factura in facturas:
            pagina = factura["pagina"]
            clave = sha256(f"factura-pagina-v1:{identidad}:{pagina}".encode()).hexdigest()
            destino = servicio._ruta("resultados", clave)
            destino.mkdir(parents=True, exist_ok=True)
            manifiesto = destino / "documento.json"
            referencia = {"id": identidad, "archivo": origen["archivo"], "pagina": pagina,
                          "tipo_identificador": "SHA256 de referencia a página, no de un PDF nuevo"}
            if manifiesto.exists():
                existente = json.loads(manifiesto.read_text(encoding="utf-8"))
                if existente.get("origen") != referencia:
                    raise ValueError("Existe una vista con origen distinto. No se reemplazó.")
                resultados.append(clave)
                continue  # Nunca reemplazar revisiones o borradores existentes.
            shutil.copyfile(imagenes[pagina], destino / "pagina_001.png")
            lectura = servicio._ruta("revisiones", clave + ".json")
            if not lectura.exists():
                datos_revision = {
                    "metodo": "Separación por índice humano; lectura visual asistida, no OCR automático.",
                    "proveedor": factura["proveedor"], "tipo_documento": "Factura", "folio": factura["folio"],
                    "fecha_emision": "Pendiente de verificar", "oc": factura.get("oc_candidata", ""),
                    "origen_oc": "OC propuesta en la revisión del conjunto; verificar contra el pedido activo.",
                    "observaciones": [factura.get("detalle", ""),
                        "Comprobar que esta factura no esté registrada por otro escaneo o por ingreso manual.",
                        "No se extrajeron cantidades por línea. Confirmar material, unidad y entrega antes de guardar."],
                    "lineas": [], "evidencia_cruce": revision.get("evidencia_cruce", ""),
                    "requiere_separacion": False,
                }
                with lectura.open("x", encoding="utf-8") as salida:
                    json.dump(datos_revision, salida, ensure_ascii=False, indent=2)
            datos = {"sha256": clave, "archivo": f"{factura['proveedor']} - factura {factura['folio']} - página {pagina}",
                "origen": referencia, "paginas": [{"pagina": 1, "estado": "REQUIERE_OCR"}],
                "registro_operacional": False, "estado": "PENDIENTE_REVISION"}
            temporal = manifiesto.with_suffix(".tmp")
            temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(temporal, manifiesto)
            resultados.append(clave)
    return resultados


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("identidad", help="SHA256 del conjunto ya preparado y revisado")
    args = parser.parse_args()
    ids = separar(Configuracion().ruta_documentos_recepcion, args.identidad)
    print(f"{len(ids)} vistas individuales disponibles. Sin registros en Excel.")


if __name__ == "__main__":
    main()
