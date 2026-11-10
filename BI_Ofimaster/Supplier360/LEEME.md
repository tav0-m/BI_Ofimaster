# Supplier 360 — entrega de trabajo

Leer primero [RESULTADOS.md](RESULTADOS.md) para hallazgos medidos y [DISENO_Y_REGLAS.md](DISENO_Y_REGLAS.md) para el modelo, fuentes, métricas, páginas y pendientes de información.

## Abrir el proyecto generado

Abrir `PowerBI/Supplier360.pbip` en Power BI Desktop y pulsar **Actualizar**. El proyecto contiene 5 páginas, 41 visuales, 10 tablas, 14 relaciones y 29 medidas, sin caché de datos. El parámetro `pRutaModelo` apunta a los CSV de esta carpeta; ajustarlo si se mueve el proyecto. Revisar la carga y los visuales antes de guardar como `.pbix`.

Se validaron 51 archivos del proyecto contra los esquemas JSON oficiales de Microsoft, sin errores. Eso verifica la estructura, no sustituye ejecutar Power Query, DAX y los visuales en Desktop. La apertura, el refresco y la revisión visual **quedan pendientes**: no había una sesión conectada de control de documentos para operarlo.

Referencia de formato: [proyectos de Power BI](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview), [modelo semántico y carga sin caché](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset).

## Alternativa: carga manual en Power BI Desktop

1. Crear un informe en blanco. En Transformar datos, crear una consulta en blanco llamada `pRutaModelo`; pegar el contenido de `powerquery/pRutaModelo.pq` en el Editor avanzado. Ajustar la ruta si se mueve la carpeta y conservar la barra final.
2. Crear una consulta por archivo `.pq` restante con el mismo nombre del archivo. Pegar su código en el Editor avanzado. Desactivar carga para `MapProveedorNC` (plantilla de trabajo). `ControlCarga` puede quedar como tabla desconectada de auditoría.
3. Cerrar y aplicar. Crear las relaciones 1:* del documento de diseño; dirección simple, sin relaciones entre hechos. Desactivar detección automática de relaciones si propone cruces distintos. Marcar DimFecha como tabla de fechas. Verificar que OC, posiciones, RUT, códigos y claves son texto.
4. Crear las medidas de `medidas.dax` individualmente. Formatear razones como porcentajes; importes como decimales y mostrar siempre la moneda. Puede ser necesario adaptar separadores DAX a la configuración regional del equipo.
5. Construir las cinco páginas descritas en el diseño. En NC usar DimProveedorNC, no el selector SAP, hasta completar el mapeo. En compras seleccionar moneda y unidad para los indicadores que lo requieren.
6. Comprobar los totales con `diagnostico/validacion.json`, revisar con Compras/Finanzas y guardar el `.pbix`. No publicar OTIF ni tránsito confirmado mientras no se resuelvan sus requisitos.

Las páginas iniciales están definidas en el proyecto editable. El archivo `.pbix` y la validación de ejecución requieren Power BI Desktop; no se han generado ni abierto mediante esta entrega. La base procesada sí está generada con los datos disponibles. El diseño funcional describe también mejoras posteriores, como drillthrough, gráficos de antigüedad y filtros conformados, que no están todos implementados en las páginas iniciales.

## Actualizar los archivos preparados

Desde la raíz `BI_Ofimaster`, con Python 3.10 o superior y sin paquetes adicionales:

```powershell
python Supplier360/scripts/inspect_data.py
python Supplier360/scripts/build_model.py
python Supplier360/scripts/package_and_validate.py
python Supplier360/scripts/build_pbip.py
```

Ejecutar en ese orden y detenerse ante cualquier error. `build_model.py` vuelve a generar los CSV y la plantilla de mapeo: guardar acuerdos de mapeo en una copia separada hasta implementar su aplicación. No se cambian los archivos originales. Los scripts pueden tardar por el tamaño de EKET y el perfilado; MKPF se muestrea.

## Contenido

- `modelo/`: hechos y dimensiones en CSV UTF-8, separador coma, decimales con punto y fechas ISO.
- `PowerBI/`: proyecto PBIP editable con modelo y cinco páginas iniciales.
- `powerquery/`: consultas M tipadas, listas para pegar.
- `medidas.dax`: medidas iniciales y controles de disponibilidad.
- `diagnostico/`: inventario completo de campos, perfil, calidad y controles ejecutados.
- `scripts/`: transformación reproducible sin dependencias externas.
- `DISENO_Y_REGLAS.md`: especificación funcional y técnica, relaciones, layout y backlog.

Las cifras de compras son históricas al corte de la extracción. La guía distingue lo calculado, lo propuesto y lo que necesita datos adicionales; no presenta los campos candidatos como validaciones del negocio.

Validación opcional del formato del proyecto: `python Supplier360/scripts/validate_pbip.py`. Usa `jsonschema` instalado únicamente en `.validation_deps` y los esquemas descargados en `diagnostico/schemas`; no cambia la instalación global de Python.
