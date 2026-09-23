# Arquitectura general de ingesta, warehouse y decisiones

## Objetivo

Construir una plataforma municipal multi-fuente que descubra documentos públicos, conserve la fuente original, extraiga evidencia textual, clasifique cada documento y entregue al asistente solo el contexto necesario.

La arquitectura debe funcionar para distintos municipios, canales, sitios web y formatos. Pudahuel es el primer caso de ingesta, no el límite del diseño.

## Principios

- La fuente raw es inmutable y PostgreSQL es la fuente de verdad.
- Descubrimiento, extracción de transcript, clasificación y consulta son etapas separadas.
- Una falla de YouTube no debe impedir guardar el video como documento catalogado.
- Las etiquetas temáticas son datos derivados, no particiones físicas.
- Cada resultado derivado debe registrar versión de modelo, fecha y estado.
- El LLM nunca recibe el warehouse completo: recibe evidencia filtrada y serializada en TOON.

## Capas

```
Fuentes públicas
  YouTube, sitios municipales, PDFs, actas, transmisiones
          |
          v
Descubrimiento y catálogo
  source_document + source_locator + metadata raw
          |
          v
Extracción
  transcript, OCR, texto de PDF, segmentos y errores
          |
          v
Enriquecimiento y decisiones
  Laya + reglas + revisión humana + etiquetas versionadas
          |
          v
Warehouse
  facts particionadas + dimensiones + índices de búsqueda
          |
          v
Recuperación
  filtros de fecha/tipo/tema + full-text + top-k de evidencia
          |
          v
Contexto LLM
  TOON compacto -> asistente documental
```

## Catálogo e ingesta

La primera etapa solo descubre y persiste documentos. Debe ser posible almacenar un video aunque no exista transcript, el canal esté temporalmente bloqueado o el documento requiera OCR.

Estados recomendados para cada fuente:

```
discovered -> cataloged -> extraction_pending -> extracted
                                      |-> blocked
                                      |-> not_available
                                      |-> failed
```

La operación debe ser idempotente por `source_type + source_id`. En YouTube, `video_id` es la clave natural. El contenido y metadata descargados deben conservarse junto con `discovered_at`, `fetched_at`, `source_url`, `extractor_version` y el error normalizado.

En el caso Pudahuel, el descubrimiento filtrado encontró 741 videos y `all_content=true` encontró 774. El inventario visual adjunto contiene 202 entradas, pero no incluye `video_id`; por lo tanto se usa como control de cobertura, no como identificador primario.

## Laya como capa de decisiones

Laya debe vivir como un worker de enriquecimiento, no dentro de la ruta HTTP del asistente. El paquete ejecuta un modelo de decisión ONNX y devuelve respuestas tipadas como `choice`, `score` y `noul`; no es un transcriptor ni un generador de texto. Referencia: [receptron/laya](https://github.com/receptron/laya).

### Entrada

Cada documento se convierte en un estado acotado, por ejemplo:

```json
{
  "source": "youtube",
  "municipality": "pudahuel",
  "title": "Reunión Ordinaria del Concejo Municipal",
  "published_at": "2026-09-09",
  "description": "...",
  "transcript_excerpt": "..."
}
```

No se debe enviar un transcript completo a Laya. Se usa título, metadata, una muestra o resumen determinístico y, cuando exista, señales estructurales del documento.

### Salida

Las decisiones deben ser generales y reutilizables entre municipios:

```
document_type: council_session | committee | public_account | ceremony | announcement | other
area: finance | health | security | education | infrastructure | social | other
importance: low | medium | high
needs_review: true | false
```

Cada salida debe persistirse con `model_name`, `model_revision`, `classification_version`, probabilidades, `classified_at` y `review_status`. La confianza no reemplaza la revisión humana: los casos ambiguos deben quedar en una cola de revisión.

### Lo que Laya no debe hacer

- Descubrir videos o decidir qué páginas del canal faltan.
- Reemplazar `youtube-transcript-api`, `yt-dlp`, OCR u otros extractores.
- Crear particiones PostgreSQL por tema o categoría.
- Ser la fuente canónica del contenido.
- Resumir transcripts largos dentro de la solicitud HTTP del usuario.

## Warehouse y particiones

El modelo físico debe separar:

- Raw: documentos, URLs, metadata original y estados de extracción.
- Dimensiones: municipio, fuente, tipo documental, área, modelo y clasificación.
- Facts: segmentos, chunks, menciones y eventos derivados.

La implementación actual usa `warehouse.fact_transcript_segments` y `warehouse.fact_transcript_chunks`, ambas particionadas por HASH de `video_id`. Esa estrategia es adecuada para consultas acotadas a una sesión y mantiene distribución estable.

Los temas no deben convertirse en particiones físicas: son multivaluados, cambian con el tiempo y pueden generar particiones desbalanceadas. Se deben guardar como clasificación o relación de etiquetas y consultar con índices B-tree, GIN/full-text o una tabla puente. Una partición RANGE por fecha puede evaluarse cuando el volumen crezca mucho, pero no es necesaria para el tamaño actual.

## Recuperación y tokens

La consulta sigue este orden:

1. Filtrar por municipio, fechas, tipo documental y etiquetas.
2. Ejecutar búsqueda full-text sobre segmentos/chunks.
3. Ordenar por relevancia y limitar top-k.
4. Agregar metadata mínima y enlaces a la fuente.
5. Serializar solo ese resultado a TOON.
6. Enviar el contexto al LLM con trazabilidad de `video_id` y segmento.

TOON optimiza el transporte del contexto hacia el modelo; no reemplaza el warehouse ni reduce el costo de almacenar la fuente. Laya puede reducir aún más tokens al clasificar antes de buscar, pero la recuperación final siempre debe apoyarse en evidencia textual verificable.

## Despliegue recomendado

```
API FastAPI
  catálogo, filtros, consulta y estado de trabajos

Worker de ingesta
  descubrimiento, transcripts, OCR, reintentos y backoff

Worker de enriquecimiento
  Laya, reglas, clasificación y revisión

PostgreSQL
  raw + dimensiones + warehouse particionado

Frontend
  archivo, filtros, evidencia y asistente
```

Los workers deben tener reintentos con backoff, límites de concurrencia, métricas por fuente y persistencia del error. En YouTube esto es obligatorio: actualmente existen documentos catalogados sin transcript por bloqueos `HTTP 429`, y reintentar masivamente sin cambiar las condiciones de red solo repite el fallo.

## Roadmap técnico

1. Implementar descubrimiento/catalogación sin extracción para reconciliar todo el canal.
2. Separar la cola de extracción y habilitar proxy o una red no bloqueada para YouTube.
3. Agregar tabla de clasificaciones versionadas y un worker Laya independiente.
4. Añadir filtros por tipo, área y estado de revisión al endpoint de reportes.
5. Medir precisión de Laya con una muestra revisada manualmente antes de usar sus etiquetas para priorizar consultas.

