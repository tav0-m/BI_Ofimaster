# Escáner de recepciones · guía de desarrollo

## Estado real

Disponible: carga PDF desde la web, preparación local, visor por página,
extracción de texto digital y OCR local (RapidOCR/ONNX Runtime), candidatos
de cabecera que solo se aplican tras revisión, borrador editable, cálculo
explícito de cantidades y confirmación física con controles de duplicados.

Pendiente: aprobación de TI del motor local, evaluación de precisión por campo,
extracción estructurada de tablas/manuscritos y procesamiento desatendido con
cola y reintentos programados. El OCR actual es un comando local,
no un proceso automático dentro de la web. Desarrollar en este repositorio,
reutilizando pedidos, autenticación y recepciones. Un worker puede procesar
OCR sin bloquear la web; no hace falta una segunda aplicación operacional.

## Componentes y archivos que se conservan

- `app/api/documentos_recepcion.py`: lectura, borrador, cálculo y confirmación.
- `app/servicios/`: preparación, revisión documental y recepción física.
- `interfaz/fuente/`: visor y formularios de Abastecimiento.
- `escaner/herramientas/preparar_documentos_recepcion.py`: preparación de PDF.
- `escaner/herramientas/separar_facturas_revisadas.py`: separación controlada.
- `escaner/requisitos.txt`: dependencias documentales.
- `data/documentos_recepcion/`: originales, revisiones y resultados.

Ver [organización y uso](../../data/documentos_recepcion/README.md).

## Flujo objetivo

```text
Original → extracción → borrador con evidencia
  → vínculo OC/posición/material/unidad → revisión humana
  → confirmación autorizada → recepción física e historial
  → gestión de diferencias por Abastecimiento
```

OCR propone: no escribe en SAP, no cierra OC ni crea una NC automáticamente.

## Desarrollo por etapas

### 1. Documentos y resultados esperados

Reunir ejemplos autorizados de diferentes proveedores, manuscritos, parciales,
rechazos y páginas múltiples. Revisar manualmente folio, proveedor, fecha,
OC/posición, material, unidad y cantidades de cada entrega. Usar como referencia
`plantillas/diferencias_esperadas.csv`. Una factura/despacho no acredita recepción.

### 2. Contrato de extracción

Cabecera: ID/hash, emisor/tipo/folio, fecha física, sociedad, centro, estado,
usuario, fecha de revisión, versión y evento de confirmación.

Líneas: OC/posición, código original/material SAP, unidad documental y de
registro, cantidades de esta entrega, factor/evidencia, motivo, página, texto
original y confianza por campo cuando el motor la aporte.

Ausencia significa desconocido, no cero. No inventar aceptación. Consultar
el total pedido en la fuente oficial, no reemplazarlo con OCR.

### 3. Motor intercambiable

Evaluar texto de PDF digital, OCR local o servicio aprobado por TI.
Power Automate/AI Builder requiere licencias, permisos y acceso real a SharePoint;
una URL no equivale a un archivo local del backend.

Separar extracción y reglas del negocio. Credenciales en servidor, timeout,
reintentos limitados y errores recuperables. Conservar el original y validar
el esquema de salida. Texto del PDF es dato, nunca una instrucción para
ejecutar comandos, SQL o modificar permisos.

### 4. Asociación y unidades

Validar OC + posición + material, no asociar solo por descripción. Claves
ausentes, ambiguas o material repetido necesitan aclaración humana.

Utilizar unidad de pedido cuando exista. MARM propone relaciones por material
y unidades exactas; revisar vigencia y equivalencia física. Unidad base, de
pedido y de precio no son necesariamente iguales. No normalizar alias ni
convertir cajas/pallets automáticamente.

El cálculo existente utiliza fracciones y rechaza redondeos incompatibles.
Calcular/copiar solo cambia el borrador; confirmar es una acción diferente.

### 5. Confirmación segura

- Cantidades finitas y no negativas; aceptadas + rechazadas <= recibidas.
- Registrar esta entrega, no acumulados SAP. Calidad desconocida queda pendiente.
- Validar saldo, sobreentrega y versión antes de escribir.
- Hash y evento estable para reintentar sin duplicar entregas.
- Revisar emisor/tipo/folio para detectar otro escaneo del mismo documento.
- Separar varias facturas/OC antes de confirmar lotes.
- Conservar evidencia y estado de recuperación ante fallos.
- Una recepción y una NC en libros distintos no forman una transacción conjunta.

### 6. Roles, privacidad y respaldo

Recepción registra/evalúa lo físico; Abastecimiento gestiona diferencias;
jefatura revisa excepciones y gerencia consulta. Permisos en servidor y matriz
Microsoft aprobada por TI, no solo botones ocultos.

No enviar documentos a servicios externos sin autorización. Definir retención,
acceso y antimalware: validar firma PDF no equivale a antivirus. Respaldar juntos
Excel, carpeta documental y evidencias de gestión.

### 7. Verificaciones antes de producción

La suite antigua se retiró por solicitud del usuario. Recuperar o crear
verificaciones específicas, en copias aisladas:

- Entrega completa/parcial y segunda entrega de la misma posición.
- Duplicado, nuevo escaneo, documento corregido y reintento tras fallo.
- OC desconocida, material repetido y varias facturas/OC.
- Unidad incompatible, decimales, manuscrito ilegible y sobreentrega.
- Cambio concurrente, usuario sin permiso, PDF corrupto y timeout OCR.
- Recepción guardada con incidencia pendiente: reintentar sin doble entrega.

Medir exactitud por campo, asociaciones, intervención humana y tiempo.
Confianza OCR no garantiza precisión. Aprobar el piloto solo con restauración
comprobada y cero registros automáticos no aprobados.

## Próximo paso

### Piloto preparado con documentos reales

```powershell
.\.venv\Scripts\Activate.ps1
python -m escaner iniciar --nombre escaner-sap-20261013-v1 --puerto 8002
```

Abrir `http://127.0.0.1:8002` → Abastecimiento → Documentos de recepción.
Elegir una vista individual, ver la imagen y desplegar «Lectura automática».
El piloto contiene copias y no sincroniza cambios hacia los originales.
No presentar cantidades ficticias como entregas reales ni duplicar recepciones
ya registradas por otro medio. Es local y sin acceso corporativo; no exponerlo.

### Nuevo documento en el piloto

Cargar el PDF desde la web o colocarlo en la entrada documental del piloto.
Después ejecutar desde otra terminal:

```powershell
python -m escaner preparar --carpeta data/pilotos_reales/escaner-sap-20261013-v1/documentos_recepcion
python -m escaner extraer --carpeta data/pilotos_reales/escaner-sap-20261013-v1/documentos_recepcion
```

La carga web ya prepara las páginas; el primer comando solo hace falta para
archivos colocados directamente en la carpeta. OCR conserva `extraccion.json`
separado de revisiones y borradores; jamás confirma cantidades ni modifica Excel.
Usar `--identidad HASH --pagina 1` para procesar una página específica y
`--modo ocr` para forzar lectura de imagen. Los modelos vienen con la dependencia;
el adaptador exige archivos locales y no descarga modelos al leer documentos.
No se normalizan automáticamente los RUT del cliente como emisor ni se convierten
cantidades facturadas en recibidas. La confianza OCR no certifica precisión.

### Verificaciones reproducibles

```powershell
python -m escaner verificar --nombre escaner-controles-nuevo
```

Usar un nombre nuevo en cada ejecución. Crea libros/PDF **ficticios** separados
de la demostración real y verifica carga, visor, borrador, cantidades, unidades,
versiones, duplicados y reintento después de fallo. El informe está en
`data/pilotos_locales/NOMBRE/reportes/verificacion_escaner.json`.
No certifica reconocimiento de manuscritos ni Microsoft en vivo.

El procesador limita cada página OCR a 90 segundos por defecto (`--tiempo-maximo
10–300`), conserva páginas ya extraídas y reutiliza imágenes idénticas. Un fallo
no descarta páginas anteriores. `--reprocesar` obliga a repetir la lectura.

En la verificación del 13-10-2026: 13 vistas con extracción completa y 22 páginas
preparadas (incluyen vistas individuales y páginas del conjunto; no son 22
documentos independientes). Se comprobaron 12 grupos de controles funcionales
en datos ficticios y el visor en navegador sobre copias reales. No se registraron
entregas en la demostración real ni se modificaron PDF/Excel originales.

Informe: `data/pilotos_reales/escaner-sap-20261013-v1/reportes/evaluacion_escaner.json`.
Para repetir la auditoría de preparación y originales:

```powershell
python -m escaner evaluar --nombre escaner-sap-20261013-v1
```

Medir ahora precisión por campo con los resultados esperados de tus documentos.
Conservar la confirmación humana antes de cualquier entrega. La versión local
es un piloto asistido, no automatización operacional desatendida.
