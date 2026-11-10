# Operación y pruebas del escáner

## 1. Preparar el entorno

En PowerShell, desde la raíz:

```powershell
cd "C:\Users\gustavo.chuquiviguel\Downloads\ofimaster-gestion-nc"
.\.venv\Scripts\Activate.ps1
```

Solo si faltan dependencias:

```powershell
python -m pip install -r escaner/requisitos.txt
```

El OCR procesa localmente. Instalar dependencias requiere descargar paquetes;
no autoriza enviar documentos a terceros. El motor exige modelos locales.

## 2. Abrir la demostración existente

```powershell
python -m escaner iniciar --nombre escaner-sap-20261013-v1 --puerto 8002
```

Abrir `http://127.0.0.1:8002` → Abastecimiento → Documentos de recepción.
Mantener la terminal abierta y detener con Ctrl+C. Si el puerto está ocupado,
cerrar el piloto anterior o elegir otro puerto. No cambiar `.env` para este modo.
Sin login corporativo, solo localhost: no exponer el piloto a la red.

El piloto es una copia histórica. Confirmar el corte mostrado; no implica
datos SAP de hoy. Los originales y los libros del piloto no se sincronizan.

## 3. Agregar un PDF

Cargarlo desde el panel web o colocarlo en:

`data/pilotos_reales/escaner-sap-20261013-v1/documentos_recepcion/entrada/`

Para PDF colocados en carpeta, preparar las páginas:

```powershell
python -m escaner preparar --carpeta data/pilotos_reales/escaner-sap-20261013-v1/documentos_recepcion
```

La carga web ya prepara páginas. Después ejecutar OCR desde otra terminal:

```powershell
python -m escaner extraer --carpeta data/pilotos_reales/escaner-sap-20261013-v1/documentos_recepcion
```

La lectura es manual por comando, no automática al subir el archivo. Límite:
50 MB/30 páginas; OCR acotado a 90 segundos por página, configurable con
`--tiempo-maximo` (10 a 300). Un reintento conserva páginas válidas; para repetir
inferencia usar `--reprocesar`. No reemplaza revisiones humanas ni confirma nada.

## 4. Revisar en la web

Actualizar documentos y lectura. Comparar imagen/texto; identificar el RUT del
emisor, no del cliente. Verificar folio, OC, posición, material, unidad y cantidades
de esta entrega. Si hay varias facturas, separarlas de manera controlada.
Guardar borrador no registra una entrega. Solo confirmar tras revisar evidencias.
No usar una factura antigua para demostrar una nueva recepción como si fuera real.

## 5. Probar sin contaminar la demostración

```powershell
python -m escaner verificar --nombre escaner-controles-20261015-v1
```

Usar un nombre nuevo en cada ejecución. Este comando crea libros y PDF ficticios
en `data/pilotos_locales/NOMBRE/` y sí escribe cantidades únicamente en esos libros.
Informe: `reportes/verificacion_escaner.json`. No hace falta iniciar la web aparte.
No certifica precisión OCR ni acceso Microsoft en vivo.

Para auditar las copias reales y sus originales (sin confirmar recepciones):

```powershell
python -m escaner evaluar --nombre escaner-sap-20261013-v1
```

Si informa un original cambiado, comparar cortes y preparar otro piloto; no
modificar el manifiesto para que el control pase.

## 6. Preparar un piloto nuevo

```powershell
python -m escaner crear-piloto --nombre escaner-presentacion-nueva
```

Copia los Excel configurados, los PDF y las revisiones de lectura. No copia
borradores ni confirmaciones documentales. Después extraer usando su carpeta e
iniciar con ese nombre. Nunca sobrescribe un piloto existente.

## Despliegue

La imagen Docker incluye el paquete de código `escaner`, pero el Dockerfile
actual no instala las dependencias opcionales PDF/OCR. Antes de desplegar este
módulo, TI debe preparar y probar una imagen que instale `escaner/requisitos.txt`,
sus bibliotecas nativas y modelos. No asumir que el piloto Windows valida Docker.
