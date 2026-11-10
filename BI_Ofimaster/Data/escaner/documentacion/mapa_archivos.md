# Mapa completo del escáner

## Centralizado en escaner/

| Ubicación | Responsabilidad |
|---|---|
| `herramientas/preparar_documentos_recepcion.py` | PDF a páginas y texto digital |
| `herramientas/extraer_documentos_recepcion.py` | Lote de extracción local |
| `herramientas/motor_ocr_local.py` | Inferencia aislada por página |
| `herramientas/piloto_escaner.py` | Copias reales para demostración |
| `herramientas/verificar_escaner.py` | Pruebas ficticias del circuito |
| `herramientas/evaluar_escaner_piloto.py` | Auditoría de preparación/originales |
| `herramientas/separar_facturas_revisadas.py` | Vistas individuales por índice humano |
| `requisitos.txt` | Dependencias PDF y OCR |
| `documentacion/` | Operación, reglas y próximos pasos |
| `plantillas/validacion_campos.csv` | Referencia humana vacía |

## Integrados en la aplicación (no se duplican ni trasladan)

- [API documental](../../app/api/documentos_recepcion.py).
- [Consulta/carga de documentos](../../app/servicios/documentos_recepcion.py).
- [Extracción y motor acotado](../../app/servicios/extraccion_documental.py).
- [Borrador y confirmación](../../app/servicios/revision_documental.py).
- [Recepción física](../../app/servicios/recepciones_fisicas.py).
- [Consulta de materiales/unidades](../../app/servicios/consulta_material_documental.py).
- [Visor React](../../interfaz/fuente/modulos/abastecimiento/DocumentosRecepcion.tsx).
- [Lectura OCR en React](../../interfaz/fuente/modulos/abastecimiento/LecturaDocumento.tsx).
- [Formulario de revisión](../../interfaz/fuente/modulos/abastecimiento/RevisionRecepcion.tsx).
- [Cálculo de cantidades](../../interfaz/fuente/modulos/abastecimiento/CalculoCantidadesDocumento.tsx).
- [Propuesta de conversión](../../interfaz/fuente/modulos/abastecimiento/PropuestaConversion.tsx).

Mantener estos archivos en la estructura backend/frontend permite reutilizar
roles, pedidos, bloqueos de Excel y registro físico de la aplicación completa.

## Evidencia y resultados (no se trasladaron)

- Operación: `data/documentos_recepcion/`, salvo otra ruta configurada en `.env`.
- Entrada: `entrada/` con PDF originales.
- Preparación/OCR: `resultados/ID/` con imágenes, texto, manifiesto y extracción.
- Revisión y estado: `revisiones/`; BORRADOR/CONFIRMANDO/REGISTRADO no son temporales.
- Demostración: `data/pilotos_reales/escaner-sap-20261013-v1/`.
- Pruebas ficticias: `data/pilotos_locales/NOMBRE/`.
- Informes: `reportes/` dentro de cada piloto.
- Modelos OCR: instalados por la dependencia en `.venv`, no duplicados en el código.

Los accesos antiguos en `automatizacion/` y `requirements-escaner.txt` se
conservan por compatibilidad y delegan a esta carpeta central.
