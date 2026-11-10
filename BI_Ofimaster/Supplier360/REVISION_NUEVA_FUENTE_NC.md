# Nueva fuente: FACTURAS Y NCR OFIMASTER 09.11.2026.xlsx

Se inspeccionó el contenido de la hoja Data sin modificar el libro. Esta fuente tiene una estructura distinta del Excel operacional `NC PROVEEDORES.xlsx` revisado inicialmente: sus consultas deben adaptarse a los encabezados reales, no a Prov/Factura/Resolucion.

## Resultado del filtro

- Sociedad 8000 y Tipo de DTE 61: 93 filas de detalle.
- 49 documentos candidatos únicos por Sociedad + Rut del emisor + Tipo de DTE + Nro de Folio.
- 12 proveedores; todos tienen coincidencia de Interloc.comercial con id_proveedor del maestro local para sociedad 8000, después de normalizar ceros. Los RUT también coinciden.
- 13 documentos tienen más de una fila; máximo 11 filas por documento.
- Fechas de emisión: 27/03/2026 a 04/11/2026.
- Moneda informada de cabecera: CLP. Las seis columnas repetidas de moneda de cabecera son iguales en el subconjunto revisado.
- 22 filas no tienen material; conservarlas para la vista financiera e identificar su falta de clasificación de producto.
- 2 filas no tienen Folio Referencia. Ninguna referencia coincide con las OC de la extracción local; no se probó su significado como factura original ni su asociación a OC.

## Columnas quitadas

- Un.medida venta: completamente vacía en el archivo. Se puede excluir; la cantidad del detalle no podrá agregarse con unidades asumidas.
- Moneda del documento: aparece dos veces y ambas están completamente vacías. Se pueden excluir esas dos columnas. Mantener una moneda de cabecera confirmada.
- URI: tiene datos en las 93 filas de NC. Su exclusión es aceptable si no se usará el acceso a respaldos; no debe describirse como columna vacía.
- No existe una columna llamada literalmente Monto documento en este libro. Distinguir Moneda del documento (vacía) de Monto (con datos). Conservar Monto y Valor neto hasta terminar la validación.

## Importe de cabecera frente a detalle

Los montos de cabecera están repetidos por línea. No sumar Monto neto, IVA ni Monto Total directamente sobre las 93 filas.

En los 49 documentos: Monto neto de cabecera = 100 × suma de Monto de sus líneas. La representación numérica almacenada tiene esa diferencia; no se explica solamente por que Power BI muestre o no decimales. No se corrigió automáticamente. Validar al menos una NC de una línea y otra de varias líneas contra el documento fiscal o la fuente antes de aprobar una escala.

Valor neto y Monto son diferentes: cantidad × Valor neto coincide con Monto, con tolerancia de 1, en 70 filas y difiere en 23. No certificar Valor neto como precio unitario ni Monto como neto de línea definitivo sin revisar esas diferencias.

Esta fuente identifica documentos de NC mejor que el registro operacional inicial, pero no contiene prueba de compensación/aplicación contable ni fecha de resolución de un reclamo.

## Procedimiento para Power Query

1. Conservar src_DTE como lectura de la fuente y filtro de sociedad 8000. Mantener todos los tipos DTE allí si se analizarán facturas posteriormente.
2. Crear stg_NC como Referencia de src_DTE y aplicar Tipo de DTE = 61. Si ya se filtró en la consulta actual, no es necesario reconstruirla para revisar NC; separar la fuente al preparar la ampliación a facturas.
3. Usar texto en folios, DTE, RUT, interlocutor, sociedad, material y referencias. Fecha Emisión como fecha; confirmar importación correcta del serial Excel. Cantidades y montos como decimales.
4. Conservar las columnas de identificación, referencias, fecha, moneda, Monto neto, IVA, Monto Total, exento, no facturable, material, descripción, cantidad, Valor neto y Monto. Renombrar monedas duplicadas según su columna original antes de excluir redundancias.
5. Crear ClaveNC con sociedad, RUT emisor normalizado, tipo DTE y folio. No utilizar solo el folio. Mantener los datos originales.
6. Crear FactNC_Cabecera como Referencia. Seleccionar Sociedad, Rut del emisor, Tipo de DTE, Nro de Folio, Interloc.comercial, Razón social, Fecha Emisión, moneda principal, Monto neto, Monto no afecto o exento, Tasa IVA, IVA, Monto Total, Monto no Facturable y ClaveNC. Comprobar que esos atributos sean consistentes dentro de cada clave y quitar solo duplicados exactos de esa proyección. Resultado esperado local: 49 filas. Mantener importes crudos sin corregir escala hasta validar.
7. Crear FactNC_Detalle como Referencia. Conservar clave, Folio Referencia, material, descripción, cantidad, Valor neto y Monto. Conservar las 93 filas; no quitar duplicados por material ni folio. Falta número de posición persistente en origen; un índice solo identifica filas de esta extracción.
8. Vincular proveedor usando Sociedad + Interloc.comercial normalizado, contrastando el RUT. Preparar dimensiones antes de crear relaciones simples a cada hecho; no relacionar directamente hechos de NC y compras para intentar resolver referencias.
9. Usar COUNTROWS(FactNC_Cabecera) para documentos, no COUNTROWS(FactNC_Detalle). No sumar netos de cabecera sobre el detalle. Mantener la página de importes en validación hasta confirmar la escala y significado.

Evidencia reproducible: diagnostico/nuevo_excel_auditoria.json. Los conteos provienen del libro entregado; comparar con el CSV que efectivamente se importó a Power BI antes de exigir igualdad.

Referencia de DTE 61: [formato DTE del SII](https://www.sii.cl/factura_electronica/formato_dte.pdf).
