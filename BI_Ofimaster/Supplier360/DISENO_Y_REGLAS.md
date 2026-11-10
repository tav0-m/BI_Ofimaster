# Power BI — Compras, pendientes de recepción, NC y Supplier 360

## Alcance y estado

Base construida con los archivos locales de `Data/data_DWH` y `Data/NC`. Incluye proyecto PBIP editable con modelo semántico y cinco páginas iniciales, tablas procesadas, Power Query, medidas DAX y diseño del reporte. No es un `.pbix` ya validado en Power BI Desktop. La estructura JSON del proyecto fue validada con esquemas oficiales; refresco, DAX y apariencia quedan por validar en Desktop. Los archivos de origen no se modifican. Los datos representan extracciones históricas, no el estado actual del negocio.

Se selecciona la extracción de nombre más reciente por tabla, sin concatenar snapshots. Se guarda su procedencia en `modelo/ControlCarga.csv`. La fecha del nombre es una convención de selección, no garantía de frescura: conservar y revisar `FECHA_PROCESO` y fechas contables.

## Tablas que sirven y cómo se usan

| Fuente | Uso | Clave / precaución |
|---|---|---|
| SAP_EKKO | Cabecera, proveedor, sociedad, moneda, grupo compras, tipo OC | EBELN; LIFNR se cruza con proveedor por sociedad |
| SAP_EKPO | Posiciones, cantidades, unidad, monto, cierre, borrado | EBELN + EBELP; grano principal de compras |
| SAP_EKET | Repartos, fecha prevista y cantidades acumuladas | EBELN + EBELP + ETENR; filtrar a posiciones del universo y agregar antes de cruzar con EKPO |
| oc | Vista de comparación para cantidades y fechas | Documento_compras + posicion; no sumar junto con EKPO |
| KARDEX | Movimientos fechados con referencia OC/posición | EBELN + EBELP para asociación; documento, año y posición para validar identidad del movimiento |
| prov | Nombre, RUT, sociedad, condiciones de pago | sociedad + id_proveedor; proyectar campos de negocio antes de deduplicar; no importar datos bancarios |
| mat | Categoría, marca, descripción, unidad base | sociedad + material |
| SAP_MARM | Conversión de unidades | material + unidad; validar UMREZ/UMREN y vigencia |
| SAP_LFB1 / SAP_LFM1 | Extensión contable y de compras del proveedor | proveedor + sociedad / organización de compras; no unir ignorando el segundo componente |
| SAP_EINA / EINE / REG_Info | Relación material-proveedor y condiciones | INFNR y organización/centro; más de un registro puede ser legítimo |
| SAP_A017 / A018 / KONP | Condiciones y vigencias de precios | KNUMH más posición de condición; no mezclar precios de distinta vigencia |
| PROVEEDOR_X_SOCIEDAD / PROV_PROD | Puentes de suministro | no asignar todas las compras históricas a todos los proveedores posibles |
| SAP_T024 / T001L | Enriquecimiento grupo compras y almacén | EKGRP / WERKS + LGORT |
| SAP_MARC / MARD / STOCK_SAP_1H | Stock y campos candidatos de traslado | confirmar significado del stock en traslado; no equivale automáticamente a tránsito de proveedor |
| SAP_RUSA / RUSA_MENSUAL | Contexto de inventario histórico | material + centro + almacén + fecha + demás dimensiones del origen |
| NC PROVEEDORES.xlsx | Casos/reclamos, factura referida, motivo y resolución textual | fila de origen como identificador provisional; falta ID estable y conciliación contable |
| SAP_APORTES_PROVEEDOR | Candidato para investigar documentos y aportes de proveedores | no clasificar toda la tabla como NC; verificar cuenta, clase, signo, moneda, reversas y referencia |
| SAP_REGUP | Contexto de pagos | no es universo completo de NC ni prueba aislada de saldo pendiente |
| SAP_BSEG | Referencias limitadas | la extracción no incluye importes, proveedor ni todos los campos contables necesarios |
| SAP_MKPF | Cabeceras de documentos de material | no aporta por sí sola cantidades por posición de OC; extracción muy grande |
| FBL5N / sap_devoluciones | Campos orientados a clientes | no usar como notas de crédito de proveedor sin demostrar un proceso específico |
| STATUSFEDEX | Catálogo de estados | no contiene eventos de envío ni relación envío–OC |

El inventario completo de los 62 CSV y sus campos está en `diagnostico/inventario_campos.csv`. El perfil general examina completamente archivos de hasta 100 MB; en los mayores examina las primeras 10.000 filas. El constructor lee **todo el EKET seleccionado** para filtrar contra EKPO. MKPF no se perfila completamente. No confundir tamaños de muestra con totales.

## Modelo estrella

Relaciones activas 1:* con dirección simple desde dimensión a hecho:

| Dimensión | Clave | Hechos |
|---|---|---|
| DimProveedor | ClaveProveedor | FactOC, FactRepartos, FactMovimientos |
| DimProducto | ClaveProducto | FactOC, FactRepartos, FactMovimientos |
| DimMoneda | Moneda | FactOC, FactRepartos, FactMovimientos |
| DimFecha | Fecha | FactOC.FechaPedido; FactRepartos.FechaPromesa; FactMovimientos.FechaContable; FactReclamosNC.FechaCaso |
| DimProveedorNC | ProveedorTexto | FactReclamosNC.ProveedorTexto |

No relacionar hechos entre sí. DimMoneda permite filtrar compras, repartos y movimientos con un selector compartido. Para filtrar todos los hechos por sociedad/centro, crear dimensiones conformadas con claves únicas y relaciones simples; en el MVP usar los campos del hecho de la página. El filtro de fecha tiene significado distinto por hecho: etiquetar explícitamente cada página (pedido / compromiso / contabilización / reclamo), o duplicar calendarios por rol. No interpretar la misma selección como cohortes equivalentes.

FactOC tiene una fila por OC/posición; FactRepartos una por OC/posición/reparto. FactMovimientos conserva el movimiento de origen sin asumir que todo es recepción. FactReclamosNC representa casos, no documentos fiscales únicos. Un mismo número de NC puede aparecer en varios casos: el conteo de casos con referencia no es conteo de documentos NC.

Los identificadores se mantienen como texto; se normalizan ceros iniciales numéricos para los cruces. La normalización se aplica consistentemente en todas las fuentes. No convertir códigos alfanuméricos ni RUT a número. Los proveedores/productos ausentes en maestros tienen miembros `SIN MAESTRO`, conservando las filas de hechos. Conflictos de claves de OC provocan error; no se resuelven arbitrariamente.

`MapProveedorNC.csv` es una plantilla pendiente. Resolver nombres comerciales contra RUT/proveedor SAP y sociedad con validación del negocio. El constructor no aplica esta plantilla todavía: para integrarla, implementar un cruce validado 1:1 antes de escribir FactReclamosNC; rechazar mapeos ambiguos y registrar los no encontrados. Solo después activar DimProveedor → FactReclamosNC y retirar DimProveedorNC si corresponde. No presentar por ahora reclamos como un KPI integrado del mismo proveedor SAP.

## Definición de métricas

### Fill rate

El MVP calcula **fill rate acumulado a fecha de extracción**, no cumplimiento a tiempo ni fill rate de primera entrega:

`SUM(min(max(recibido,0),pedido)) / SUM(pedido)`.

El numerador se limita por posición para evitar que una sobreentrega compense otro faltante. El universo inicial exige material, cabecera, cantidad positiva, ausencia de borrado y ausencia de centro suministrador. Requiere repartos y cantidades programadas conciliadas con la posición. Validar adicionalmente la lista de tipos de OC de compras normales con Compras; el código no tiene todavía una lista aprobada. Las entregas finales con faltante conservan el incumplimiento en fill rate, aunque salen del pendiente operativo.

No sumar unidades de medida distintas. La medida por unidades queda vacía si hay más de una unidad; para ranking general se ofrece promedio de tasas por posición, claramente rotulado como promedio no ponderado. Incluso con igual unidad, interpretar con cuidado una mezcla de productos. Una alternativa futura es ponderación por valor a moneda común aprobada.

### OTIF

Grano recomendado: **reparto comprometido**. Denominador: repartos elegibles cuya fecha de compromiso ya venció al corte y con historia completa. Numerador: esos mismos repartos cuya cantidad completa se recibió hasta su fecha compromiso más la tolerancia acordada. No es `On Time % × In Full %`.

Conservar fecha original acordada con el proveedor y sus cambios. EINDT es candidato de fecha vigente y SLFDT de fecha estadística: validar semántica local; no asumir que cualquiera de ellas preserva la promesa original. Con múltiples repartos, asignar recepciones cronológicamente a demandas ordenadas por fecha de compromiso e ID de reparto, sin utilizar una recepción dos veces. Documentar el tratamiento de anticipos y parciales. Una reasignación/reversa debe deshacer la recepción correspondiente, no convertirse en un ingreso nuevo.

Validar tipos de movimiento, anulaciones, devoluciones, unidades y cobertura histórica antes de reconstruir cantidades hasta cada compromiso. Usar fecha física si el objetivo es llegada real; fecha contable solo como proxy declarado. Aprobar tolerancia de días, tolerancia de cantidad, días hábiles/calendario y tratamiento de cancelaciones. Propuesta inicial para validar: cero días de gracia, cantidad completa y calendario natural.

En esta entrega OTIFEvaluable=0 y OTIFCumple nulo. La medida devuelve vacío: **no se inventa OTIF a partir del recibido acumulado**. Publicar 0% sería incorrecto. Para OTIF por OC, cumplir todas las posiciones/repartos de la OC y evaluar solamente órdenes con todo su compromiso vencido, según política acordada.

### Pendiente y tránsito

Pendiente abierto = máximo(pedido − recibido acumulado, 0), excluyendo borrados y entregas finales. Vencido = fecha de reparto menor que fecha de corte. Antigüedad se calcula a ese corte histórico, no con TODAY(), para no presentar extracciones de octubre como situación de noviembre.

**En tránsito confirmado** requiere evento de embarque/despacho vigente, cantidad embarcada, unidad, OC/posición, envío y recepción asignada. Los campos Z de EKKO son candidatos, no confirmación. Las fechas inválidas (por ejemplo 09099999/00000000) se vuelven nulas. No multiplicar la cantidad total de OC por el número de envíos. Se necesita una FactEnvios a grano envío–posición, ETA vigente, fecha real despacho, estado y saldo embarcado no recibido. Hasta obtenerla, mostrar pendiente de recepción y estado `No verificable` para tránsito.

Valor pendiente estimado = valor neto de posición × pendiente / cantidad pedida. Es una asignación proporcional, no costo logístico puesto en bodega. No agregar monedas distintas. No utilizar WKURS ciegamente: validar dirección, factores y fecha de conversión; preparar tabla de tipo de cambio si se requiere CLP consolidado.

### Notas de crédito

Separar monto reclamado, NC emitida/verificada, contabilizada y aplicada/compensada. Una resolución textual con `NC nnn` solo acredita una referencia en el Excel. Redespacho, retiro o resolución sin NC no se clasifican automáticamente como recuperación monetaria. No calcular saldo contable como reclamo menos importe sin reconciliar.

Faltan en el Excel moneda confirmada, sociedad, ID SAP de proveedor, fecha de emisión/contabilización, importe contable, vínculo fiscal a factura y aplicación/compensación. Los campos financieros no confirmados permanecen nulos. Conservar descripción original y añadir clasificación de motivos validada; no sobrescribir textos. Se recomienda ID de caso persistente: el identificador por fila cambiará si se reordena el Excel.

## Páginas del reporte

1. **Resumen compras:** fecha de corte, proveedores, posiciones, valor OC y pendiente con moneda seleccionada, fill rate acumulado, cobertura evaluable; tarjetas OTIF y tránsito con estado de disponibilidad.
2. **Pendientes / tránsito:** matriz proveedor → OC → posición → reparto, fecha prometida, cantidades, saldo, atraso y cierre; barras de pendiente por proveedor y antigüedad 0/1–7/8–15/16–30/>30 días. Activar mapa de envíos solo con datos logísticos.
3. **Reclamos y NC:** casos por proveedor textual, factura, motivo, estado documental y referencia NC; detalle de resoluciones y faltantes. Importes ocultos hasta confirmar moneda. Conteos no implican saldo pendiente.
4. **Supplier 360:** drillthrough por ClaveProveedor, nombre/RUT, condiciones, mezcla de productos, volumen por moneda, fill rate, posiciones incompletas y pendiente vencido. Integrar NC después del mapeo. OTIF no disponible hasta validación. No construir un score mezclando KPIs faltantes como cero.
5. **Calidad de datos:** cobertura de maestros, faltantes de repartos, descuadres, movimientos disponibles, porcentaje evaluable, archivos y fechas de corte. Visible para responsables del reporte.

Filtros: proveedor, sociedad, categoría, marca, grupo compras, tipo OC, moneda, centro y fechas por rol. Colores: rojo para vencidos, ámbar para riesgos y gris para no evaluable. Mostrar causa del dato ausente en tooltip. No usar verde para datos no verificados.

## Datos adicionales y criterios de aceptación

| Prioridad | Requerimiento | Criterio verificable |
|---|---|---|
| P0 | Universo compras y reglas de cantidades | Tipos OC aprobados; OC anuladas/traslados/servicios separados; conciliación de cantidades con fuente |
| P0 | Recepciones completas y reversas | Historia de movimientos por OC/posición, documento/año/posición, tipo, cantidad, unidad, fecha física y contable; conciliación al mismo corte de EKET |
| P0 | Compromiso proveedor | Promesa original y cambios, parciales/repartos y tolerancias aprobadas; evitar mejora artificial por reprogramación |
| P0 | NC proveedores | Libro contable de proveedores con sociedad, año, documento, posición, proveedor, clase, signo, monedas/importes, referencias y compensación; conciliar muestra de casos Excel |
| P1 | Tránsito | Envío/ASN, OC/posición, cantidad embarcada y recibida, unidad, ETD/ETA, estado y eventos históricos |
| P1 | Mapeo NC | Cada nombre de proveedor resuelto a sociedad/proveedor SAP o excepción explícita |
| P1 | Cortes sincronizados | OC, repartos, movimientos y contabilidad con watermark acordado y trazabilidad |

## Entrega ágil y operación

Iteración 1: maestros, OC, pendientes y calidad; aceptar con claves únicas y conciliación por sociedad/moneda. Iteración 2: reclamos y conciliación NC con Finanzas. Iteración 3: OTIF con Compras/Logística y muestra reconstruida de parciales, atrasos, anulaciones y sobreentregas. Iteración 4: eventos de tránsito y publicación controlada. El orden puede cambiar según disponibilidad de datos; no depende de estimaciones de calendario inventadas.

Cada historia termina con revisión del dueño del dato y evidencia reproducible. Registrar causa raíz de incumplimientos, responsable, acción y fecha objetivo; revisar Pareto semanal de faltantes/atrasos y eficacia de acciones. ML no es necesario para esta primera versión. Considerar predicción de atrasos después de contar con etiquetas, eventos históricos y línea base, evaluando por tiempo y evitando fuga de información.

Producción: mover transformación a vistas/dataflows o ETL del DWH, mantener snapshots históricos y actualización incremental de eventos, configurar gateway según origen y credenciales de servicio, RLS por sociedad según usuarios autorizados y control de acceso a montos. No cargar MKPF de 2 GB directamente como punto de partida. Conservar la validación de duplicados y tipos en cada actualización.
