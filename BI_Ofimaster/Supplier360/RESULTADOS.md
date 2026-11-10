# Resultados de la revisión local

| Indicador | Resultado |
|---|---|
| EKKO_duplicados_exactos | 0 |
| EKPO_duplicados_exactos | 0 |
| oc_duplicados_exactos | 0 |
| prov_duplicados_exactos | 13 |
| mat_duplicados_exactos | 0 |
| cabeceras | 2131 |
| posiciones | 13793 |
| oc_vista | 13793 |
| proveedores | 199 |
| materiales | 2903 |
| eket_filas_total | 3581755 |
| eket_filas_con_posicion | 13793 |
| eket_claves_seleccionadas | 13793 |
| eket_duplicados_exactos | 0 |
| kardex_filas | 118726 |
| kardex_fecha_min | 2025-02-27 |
| kardex_fecha_max | 2026-09-29 |
| kardex_movimientos_vinculados | 12935 |
| movimientos_unidad_distinta | 655 |
| posiciones_sin_cabecera | 0 |
| proveedores_clave_sin_maestro | 0 |
| productos_clave_sin_maestro | 1 |
| posiciones_sin_repartos | 0 |
| posiciones_descuadre_repartos | 0 |
| posiciones_elegibles_fillrate | 5273 |
| posiciones_sin_proveedor_maestro | 0 |
| posiciones_con_fecha_embarque_candidata | 0 |
| nc_casos | 119 |
| nc_con_referencia | 45 |
| nc_sin_oc | 119 |
| nc_sin_fecha | 55 |

## Tablas preparadas

- ControlCarga: 7 filas.
- DimFecha: 1084 filas.
- DimMoneda: 2 filas.
- DimProducto: 2904 filas.
- DimProveedor: 199 filas.
- DimProveedorNC: 12 filas.
- FactMovimientos: 12935 filas.
- FactOC: 13793 filas.
- FactReclamosNC: 119 filas.
- FactRepartos: 13793 filas.
- MapProveedorNC: 12 filas.

## Alcance de validación

Claves únicas, integridad referencial, calendario, cantidades por reparto, límites del fill rate, conciliación de pendientes y ausencia de OTIF/NC contables inventados: controles ejecutados en Python. Power Query y DAX preparados; no ejecutados en Power BI Desktop.

## Cobertura de movimientos

Fechas KARDEX: 2025-02-27 a 2026-09-29. Comparar con fecha de corte de OC; no asumir historia completa por disponer de algunas recepciones.

Tipos vinculados a OC: `{"101": 12851, "102": 81, "161": 3}`. Su semántica y tratamiento deben validarse antes de usarlos en OTIF.
