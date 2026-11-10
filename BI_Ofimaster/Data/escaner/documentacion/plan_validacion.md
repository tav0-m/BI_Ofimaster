# Próximos pasos: del piloto a la operación

## 1. Acordar qué documento prueba la recepción

Recepción y Abastecimiento deben distinguir factura, guía de despacho y acta
con diferencias físicas. Acordar dónde se anotan aceptadas/rechazadas y quién
confirma la fecha y el estado. Cantidad facturada no demuestra cantidad recibida.

Impacto: evita automatizar una interpretación incorrecta del proceso.

## 2. Crear la referencia humana

Copiar `escaner/plantillas/validacion_campos.csv` a los reportes del piloto.
Una persona completa lo esperado leyendo el original, antes de comparar OCR.
Otra puede revisar campos críticos. No rellenar expectativas con el propio OCR.

Campos: emisor, folio, OC, posición/material, unidad, fecha, recibidas,
aceptadas, rechazadas y motivo. Si no se puede demostrar un dato, marcarlo como
pendiente; ausencia no significa cero. No guardar datos reales en la plantilla
versionada del código.

Impacto: permite medir exactitud y descubrir formatos problemáticos.

## 3. Medir y corregir la lectura

Usar estados EXACTO, INCORRECTO, NO_LEIDO, NO_APLICA o PENDIENTE en la copia.
Medir por campo/proveedor y separar impreso de manuscrito. Excluir NO_APLICA
del denominador y reportar PENDIENTE aparte. La confianza del modelo no es
la exactitud observada. Medir también tiempo e intervención humana.

Los candidatos actuales de OC buscan números con prefijo 45; otras clases
requieren ampliar y validar el detector. RUT reconocido puede ser del cliente.
La salida actual es texto/candidatos, no una tabla de cantidades ya interpretada.

Impacto: dirige las siguientes mejoras hacia los errores reales, no supuestos.

## 4. Estructurar productos y diferencias

Tras validar ejemplos, proponer líneas con evidencia de página y texto original.
Cruzar OC + posición + material; dejar coincidencias ambiguas para el usuario.
Verificar unidades y equivalencias; nunca aplicar cantidades facturadas como
físicas, ni deducir aceptadas por diferencia si no están confirmadas.

Impacto: reduce digitación conservando trazabilidad y control.

## 5. Automatizar el procesamiento, no la confirmación

Cuando se apruebe la precisión, añadir cola de trabajos, estado visible,
reintentos limitados y seguimiento de fallos. El OCR actual ya tiene procesos
acotados por página, pero no existe un trabajador desatendido ni cola operativa.
Mantener confirmación humana; no permitir que OCR cierre OC o cree NC por sí solo.

Impacto: elimina ejecutar comandos manualmente y evita bloquear la web.

## 6. Validar con TI y usuarios

Aprobar motor/modelos/licencias, roles Microsoft, límites de archivos, antimalware,
retención, respaldo conjunto y restauración de Excel + documentos. Definir criterios
de aceptación con responsables y ensayar el despliegue antes de producción.
Probar duplicados, parciales, rechazo, concurrencia, unidades y recuperación.

Estado actual: piloto asistido disponible; aceptación operacional pendiente.
