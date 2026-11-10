# Escáner de recepciones · Ofimaster

Carpeta central de desarrollo del escáner. Leer primero
[operación y pruebas](documentacion/operacion.md) y después
[plan de validación](documentacion/plan_validacion.md).

```text
escaner/
  README.md                         Punto de entrada
  __main__.py                       Comandos: python -m escaner
  requisitos.txt                    Dependencias PDF/OCR
  herramientas/                     Implementación de las siete herramientas
  documentacion/
    operacion.md                    Cómo iniciar y procesar documentos
    guia_tecnica.md                 Reglas, seguridad y antecedentes del piloto
    plan_validacion.md              Próximos pasos y criterios de revisión
    mapa_archivos.md                Ubicación de código, documentos e informes
  plantillas/
    validacion_campos.csv           Plantilla vacía; no contiene resultados reales
```

## Comandos

Ejecutar **desde la raíz del proyecto**, no desde esta carpeta:

```powershell
python -m escaner --help
python -m escaner iniciar --nombre escaner-sap-20261013-v1 --puerto 8002
```

Comandos: `preparar`, `extraer`, `crear-piloto`, `iniciar`, `verificar`, `evaluar`,
`separar`. Consultar opciones con `python -m escaner COMANDO --help`.
Los comandos anteriores de `automatizacion/` siguen funcionando: son accesos
compatibles, no otra copia de la implementación.

## Qué está disponible y qué no

Disponible: carga PDF, visor, texto/OCR local, candidatos de cabecera, revisión,
borrador y confirmación controlada. OCR no acredita cantidades físicas ni calidad.
No se conecta al dispositivo físico del escáner: recibe sus PDF.

Pendiente: medir precisión real por campo/manuscrito, extracción estructurada
de líneas, automatización desatendida, aprobación TI y aceptación operacional.
La validación del 13-10-2026 fue un piloto; no equivale a autorización productiva.

## Datos y aplicación

Los datos no se trasladaron: PDF, imágenes y estados se mantienen en
`data/documentos_recepcion/` o en la ruta `DOCUMENTOS_RECEPCION_PATH`.
El piloto usa `data/pilotos_reales/escaner-sap-20261013-v1/documentos_recepcion/`.
Backend y React conservan sus carpetas para no romper la arquitectura de la app.
El [mapa de archivos](documentacion/mapa_archivos.md) enlaza todas las piezas.

No borrar borradores, estados CONFIRMANDO, historiales ni evidencia para reintentar.
No copiar confirmaciones reales a otro libro para repetir recepciones.
