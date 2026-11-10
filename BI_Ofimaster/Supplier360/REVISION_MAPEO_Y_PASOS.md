# Revisión de Mapeo tablas.docx y guía para Power Query

## Evidencia y alcance

Se revisó el texto completo y la imagen incrustada de `C:\Users\gustavo.chuquiviguel\Downloads\Mapeo tablas.docx`. Sus descripciones se usan como información del proyecto; sus referencias a una app, escáner o contratos API no prueban que esas funciones existan en el Power BI. El documento repite parte de las secciones y contiene un apartado cortado de EINA. La referencia `reports/contrato_plataforma_20261016/Campos_DWH.csv` no está disponible en este workspace. No se certificó ese diccionario.

Se contrastaron las definiciones con los encabezados de los CSV disponibles y se ejecutó una comprobación adicional de EKKO, RUSA y KARDEX. Los resultados corresponden a extracciones locales; el servidor que está usando el usuario debe pasar los mismos controles.

### Hallazgos que cambian o precisan el procedimiento

1. Sociedad en EKKO: usar BUKRS. EKORG es organización de compras. En las 2.131 cabeceras locales BUKRS y EKORG valen 8000, pero esa coincidencia no permite sustituir sus significados.
2. La imagen propone centros RUSA 8000–8099. Es una regla candidata del negocio: validar el catálogo centro–sociedad antes de extenderla a fuentes sin sociedad. La extracción local de SAP_RUSA contiene solamente el centro 8001, con 259.581 filas.
3. XBLNR no debe usarse como clave general de OC: solo 23 de los 12.935 movimientos con EBELN informado tienen XBLNR igual a EBELN tras normalizar ceros/espacios. Puede contener referencias útiles, pero requieren validación específica. EBELN + EBELP es el vínculo principal disponible.
4. FOLIO es candidato de referencia comercial según el documento, no factura validada para cada movimiento. Está vacío en 7.696 de esos 12.935 movimientos.
5. ELIKZ significa cierre administrativo. No reemplaza la cantidad recibida ni conformidad física.
6. EKET.WEMNG es un acumulado de recepción registrado al corte. No prueba recepción puntual por sí solo. La fecha contable de KARDEX tampoco equivale necesariamente a llegada física.
7. DOC_TRIBUTARIO no está entre los archivos locales. Su sección del documento contiene campos de clientes; no usarla como fuente validada de NC de proveedores.
8. La fuente operacional de NC sigue siendo el Excel. Falta completar identidad SAP, moneda, fechas de resolución y estado contable cuando se requieran esos indicadores.
9. La clasificación y unidades actuales de maestros pueden cambiar. No usar una actualización del maestro como prueba automática de las condiciones históricas de una OC.

## Tablas para el primer modelo

Mantener las selecciones de columnas ya indicadas para EKKO, EKPO, EKET, KARDEX, prov, mat, oc, NC, MARM, T024 y T001L. No reconstruir todas las consultas por leer el documento: completar los siguientes apoyos.

| Fuente | Consulta | Columnas adicionales de apoyo |
|---|---|---|
| SAP_MARA | stg_MARA | MATNR, MEINS, BSTME, MATKL, MTART, LVORM, EAN11, BISMT, FECHA_PROCESO, ARCHIVO |
| SAP_MARM | stg_UnidadesMaterial | MATNR, MEINH, UMREZ, UMREN, EAN11, EANNR, FECHA_PROCESO, ARCHIVO |
| SAP_PARAM_TIPO_OC | stg_TipoOC | CODPARAM, DESCPARAM |

MARA da una referencia SAP de unidad base; no reemplaza la unidad de la OC. La incorporación de EAN de MARM apoya investigación de presentaciones; no habilita un escáner por sí misma.

### Fuentes para una segunda ampliación

- EINA: INFNR, LIFNR, MATNR, IDNLF, LOEKZ, MEINS, LMEIN, UMREZ, UMREN, FECHA_PROCESO, ARCHIVO. Usar para investigar códigos del proveedor del Excel. No resolver automáticamente varios candidatos. Limitar usando los registros info/proveedores del alcance y comprobar claves.
- PROVEEDOR_X_SOCIEDAD: SOCIEDAD, REGISTRO_INFO, MATERIAL, PROVEEDOR, PXS, BLOQUEADO, MWSKZ, FECHA_PROCESO. Es relación comercial, no historia de compras efectivas. PXS requiere definición.
- EINE/A017/A018/KONP: ampliar si se acuerda análisis de condiciones vigentes. Conservar organización, centro, unidad, moneda y vigencia. No sustituir precio histórico de EKPO por precio actual.
- MARD/RUSA: ampliar si se acuerda inventario actual/histórico. Filtrar centros con catálogo validado. No sumar snapshots como entradas de inventario ni equiparar traslado a tránsito de proveedores.
- PROV_PROD: referencia histórica de códigos. No asumir equivalencia RUTPRV = LIFNR.

## Secuencia de trabajo en Power Query

### 1. Preparación

Guardar copia de trabajo del PBIX. Entrar en Inicio > Transformar datos. Nombrar consultas de preparación con prefijo stg_. Mantener columnas originales y agregar columnas derivadas con nombres nuevos para conservar trazabilidad. Los cambios de Power Query no modifican tablas SQL de origen.

### 2. Alcance

| Consulta | Filtro |
|---|---|
| stg_EKKO | BUKRS = "8000" |
| stg_EKPO | BUKRS = "8000" |
| stg_Proveedor | sociedad = "8000" |
| stg_Material | sociedad = "8000" |
| stg_OC | Sociedad = "8000" |
| stg_KARDEX | SOCIEDAD = "8000" |

No imponer 8000 a MARA/MARM/T024/T001L: no es un campo de sociedad en esas tablas. EKET se limita con la lista única de posiciones de EKPO, no con una comparación de centro u organización.

### 3. Tipos, normalización y fechas

Identificadores siempre texto. Cantidades/factores/importes numéricos con cultura del origen verificada. Usar fnClaveSAP ya proporcionada para crear claves normalizadas; no sobreescribir RUT, factura ni códigos externos del proveedor. En todas las fuentes de un mismo cruce aplicar la misma función.

Crear OC_Key, Posicion_Key, Reparto_Key donde correspondan. Crear Proveedor_Key desde LIFNR o id_proveedor; Material_Key desde MATNR, CODPRO o material; Sociedad_Key desde el campo sociedad correspondiente. Para centro, almacén y grupo conservar texto recortado con el mismo formato en ambos lados.

Crear fechas convertidas junto a las originales. Si la fuente ya devuelve fecha/datetime, conservar su semántica. Si devuelve AAAAMMDD, convertir explícitamente; 00000000 y valores no válidos deben producir nulo más indicador de revisión. No reemplazar por fecha actual ni borrar filas silenciosamente. FECHA_PROCESO es corte/procesamiento, no llegada física. Separar año/mes de los roles de fecha adecuados.

### 4. Claves y errores antes de combinar

Crear referencias de control con Agrupar por > Contar filas. Verificar claves únicas de EKKO (OC), EKPO (OC/posición), EKET (OC/posición/reparto), MARA (material), MARM (material/unidad), T024 (grupo), T001L (centro/almacén), TipoOC (código). Si hay varios cortes concatenados, seleccionar el snapshot coherente antes de exigir una fila por clave. No conservar arbitrariamente la primera fila.

En proveedores y materiales, comparar valores de los atributos seleccionados. Duplicados exactos se pueden eliminar después de proyectar esos atributos. Si la misma clave tiene nombres/categorías/condiciones distintas, conservar el conflicto en una consulta de control y resolver con el responsable del maestro. Una dimensión con conflicto no se arregla seleccionando relación varios a varios.

### 5. Posiciones del alcance y repartos

Crear aux_PosicionesOfimaster como referencia de EKPO: conservar OC_Key/Posicion_Key y quitar duplicados sobre esas dos columnas. Combinar EKET contra esta lista mediante combinación interna por ambas claves; eliminar la columna anidada sin expandir. Registrar cuántas filas quedaron fuera del alcance.

Conservar esta consulta detallada a nivel reparto. No agruparla definitivamente: será la base de FactRepartos. Crear otra referencia ResumenRepartosOC que agrupe por OC_Key/Posicion_Key y calcule:

- CantidadProgramada = suma MENGE.
- CantidadRecibidaSAP = suma WEMNG.
- NumeroRepartos = conteo de filas.
- FechaPromesaMin y FechaPromesaMax = extremos de las fechas válidas, admitiendo nulo si todas faltan.

Verificar CantidadProgramada frente a EKPO.MENGE, con precisión/tolerancia de la unidad acordada. WEMNG sin registro de reparto no debe convertirse en cero recibido: marcar como falta de datos.

### 6. FactOC

Crear referencia de EKPO llamada FactOC. Combinar externa izquierda con EKKO por OC_Key. Expandir LIFNR/Proveedor_Key, BEDAT convertida, WAERS, WKURS, BSART, EKORG, EKGRP, ZTERM, LOEKZ de cabecera con prefijo diferente al de posición, y demás atributos requeridos. Comparar las sociedades de cabecera/posición. No aumentar el número de filas de EKPO.

Combinar externa izquierda con ResumenRepartosOC por OC_Key/Posicion_Key. Expandir los cinco resultados anteriores. No aumentar las filas. Controlar posiciones sin cabecera, sin repartos y con cantidades no conciliadas.

Agregar claves compuestas con valores normalizados:

- ClaveOC = OC_Key & "|" & Posicion_Key.
- ClaveProveedor = Sociedad_Key & "|" & Proveedor_Key.
- ClaveProducto = Sociedad_Key & "|" & Material_Key.

Definir elegibilidad con Compras: tipos OC, devoluciones, servicios, traslados, borrados y cantidades no positivas. Conservar los registros originales; calcular indicadores mediante banderas de elegibilidad. Entrega final con faltante: fuera del pendiente operativo, pero no automáticamente completa en fill rate.

### 7. FactRepartos

Crear referencia del EKET ya limitado al alcance. Combinar externa izquierda con una proyección única de FactOC por OC_Key/Posicion_Key para traer ClaveProveedor, ClaveProducto, sociedad, centro, almacén, moneda y unidad de pedido. FactOC depende solo de las consultas stg/ResumenRepartosOC, nunca de FactRepartos, evitando dependencia circular.

ClaveReparto = ClaveOC & "|" & Reparto_Key. Mantener una fila por reparto. No expandir recepciones individuales en esta tabla. Antes de sumar pendientes por reparto, revisar sobreentregas/reasignaciones entre repartos y conciliar contra el saldo de la posición.

### 8. Dimensiones

- DimProveedor: referencia de prov, con atributos de negocio y ClaveProveedor única. Mantener RUT. Resolver conflictos antes de relacionar.
- DimProducto: referencia de mat, con ClaveProducto única. Enriquecer mediante combinación izquierda con MARA, único por Material_Key; conservar unidad SAP y comercial por separado si difieren. Comparar y registrar discrepancias.
- DimMoneda: lista distinta de monedas del universo de hechos. Importes sin moneda válida permanecen no evaluables; no convertir con la moneda del maestro como reemplazo tácito.
- DimGrupoCompras: T024 con clave EKGRP única.
- DimAlmacen: T001L con clave centro|almacén única; conservar posibles almacenes no informados como excepción.
- DimTipoOC: catálogo por CODPARAM. Validar cuáles tipos entran en cada indicador.
- DimFecha: calendario continuo que cubra fechas de pedido, compromisos, movimientos y NC. Identificar los roles de fecha para no confundir cohortes de compras con compromisos del período.

Para claves de hechos ausentes en el maestro, agregar miembros de excepción con sus claves reales y nombre SIN MAESTRO; no eliminar compras por no tener descripción. Diagnosticar mediante combinación anti izquierda.

### 9. Recepciones y unidades

Crear FactMovimientos como referencia de KARDEX. Mantener las claves de OC/posición y documentos; validar identidad del movimiento antes de deduplicar. Clasificar CODGLOSA con responsable funcional; en local los movimientos vinculados incluyen 101, 102 y 161. Verificar signo una sola vez: ENTRA/SALE, DEBE_HABER e IMPORTE no son tres ajustes que deban aplicarse simultáneamente.

Comparar UM_BASE con unidad base SAP de MARA. Para convertir cantidad de pedido a base, validar en muestra el factor de la OC UMREZ/UMREN y denominador distinto de cero. MARM apoya conversiones alternativas actuales; no sustituye automáticamente el factor histórico de la OC. Nunca multiplicar movimientos al unir todas las unidades de un material: seleccionar material + unidad correcta y clave única.

Conciliar recepción neta al mismo corte con WEMNG convertido a base. Investigar brechas por historia incompleta, unidades, reversas o fechas antes de habilitar OTIF.

### 10. Notas de crédito

Crear FactReclamosNC desde el Excel preservando datos originales. Agregar ID provisional que conserve fila de origen; para operación estable incorporar ID persistente en la fuente. No borrar duplicados por factura ni por referencia NC: puede haber varios productos/casos.

Derivar estado documental y extraer referencia NC solo donde el texto lo permita. Separar sin resolución, referencia NC, redespacho y otras resoluciones; registrar casos ambiguos. No considerar toda resolución como NC aplicada.

Crear un mapeo validado ProveedorTexto -> ClaveProveedor con RUT/sociedad y responsable. No asignar por coincidencia aproximada sin revisión. Hasta completar el mapeo, utilizar DimProveedorNC textual separada. Si una referencia de NC aparece en varios casos, no sumar montos repetidos de documento como si fueran NC diferentes.

No calcular antigüedad sin Fecha válida, tiempo de resolución sin fecha de cierre, saldo contable sin importes/compensaciones ni monto consolidado sin moneda confirmada. EINA.IDNLF puede apoyar el mapeo de producto con proveedor como contexto; no dividir códigos por '/' y asumir correspondencias automáticas.

### 11. Modelo y controles

Crear relaciones uno a varios, simples, desde dimensiones hacia hechos. Ninguna relación directa FactOC–FactRepartos–FactMovimientos. Los cruces para preparar datos se hacen en Power Query; no requieren relaciones entre hechos en el modelo. Las tablas MARM y otras de apoyo pueden quedar solo en preparación.

Desactivar Habilitar carga para stg, aux, resúmenes y controles cuando las tablas finales dependan de ellas y el modelo ya no use las tablas stg directamente. Dejar cargadas las dimensiones y hechos finales. Cerrar y aplicar. Verificar cantidades y valores por sociedad, moneda, unidad y fecha de corte.

## Condiciones para publicar indicadores

| Indicador | Condiciones |
|---|---|
| Compras | Posiciones únicas y cabeceras correctas; importes separados por moneda |
| Pendiente | Cantidad conciliada; regla explícita para borrados/cierre y sobreentregas |
| Fill rate acumulado | Universo aprobado; cantidades comparables; numerador limitado por posición; no confundir con primera entrega o puntualidad |
| OTIF | Compromiso acordado y su historia, recepciones completas fechadas, asignación a repartos sin reutilizar cantidades, tolerancias y reversas validadas |
| Tránsito proveedor | Eventos de despacho/embarque, envío, OC/posición, cantidades, unidad y estado vigente; pendiente no es prueba de despacho |
| NC | Casos y referencias desde Excel; estado contable/recuperación solo con conciliación adicional |
| Calidad física | Recepción física, aceptación/rechazo y motivos efectivamente registrados; no inferirlos de ELIKZ/WEMNG |

## Referencias

- Evidencia local: `diagnostico/contraste_mapeo.json`, `diagnostico/calidad_modelo.json`, `diagnostico/mapeo_documento.txt` y la imagen extraída `diagnostico/mapeo_image1.png`.
- [Combinar consultas en Power Query](https://learn.microsoft.com/es-es/power-query/merge-queries-overview).
- [Combinación externa izquierda](https://learn.microsoft.com/es-es/power-query/merge-queries-left-outer).
- [Perfiles de datos](https://learn.microsoft.com/es-es/power-query/data-profiling-tools).
