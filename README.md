# YouTube Transcript Console

Plataforma web para transcripción y consulta de videos públicos de YouTube con:

- Backend en `FastAPI`
- Frontend en `React + Vite`
- Persistencia en `PostgreSQL`
- Warehouse derivado en PostgreSQL con particiones hash para segmentos y chunks
- Chat LLM sobre transcript vía `OpenRouter`
- Procesamiento de video individual y scrapeo masivo de canal

## Stack

- Python
- FastAPI
- PostgreSQL
- Docker / docker compose
- React + Vite
- `youtube-transcript-api`
- `yt-dlp`
- OpenRouter

## Estructura

```text
backend/
  app/
frontend/
docker-compose.yml
Dockerfile
requirements.txt
```

## Variables de entorno

Copia `.env.example` a `.env` y define al menos:

- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `OPENROUTER_API_KEY`

`DATABASE_URL` debe apuntar a tu Postgres y puede usar las mismas variables definidas en `.env`.

Valores por defecto relevantes:

- Frontend en `http://localhost:5174`
- API en `http://localhost:8000`
- PostgreSQL expuesto en host por `5433`

## Levantar el proyecto

```bash
docker compose up --build -d
```

## Endpoints principales

- `GET /api/health`
- `GET /api/transcripts`
- `GET /api/reports?q=&date_from=&date_to=`
- `GET /api/transcripts/{video_id}`
- `POST /api/transcripts`
- `POST /api/channels/scrape`
- `POST /api/channels/scrape-all`
- `POST /api/v1/chat/message`

## Payloads

Video individual:

```json
{
  "url": "https://www.youtube.com/watch?v=..."
}
```

Canal:

```json
{
  "url": "https://www.youtube.com/@IMunicipalidadLoBarnechea",
  "title_query": "sesion ordinaria",
  "max_videos": 20
}
```

Scrapeo masivo de sesiones y comisiones de Pudahuel:

```json
{
  "url": "https://www.youtube.com/channel/UCJTRTxPkNZtnhyDpyPeVggQ",
  "title_query": "concejo|sesion|reunion|comision",
  "max_videos": 1000,
  "refresh_existing": false
}
```

Para procesar literalmente todo el contenido del canal, incluyendo videos que no sean del
Concejo Municipal:

```json
{
  "url": "https://www.youtube.com/channel/UCJTRTxPkNZtnhyDpyPeVggQ",
  "all_content": true,
  "max_videos": 5000
}
```

Chat:

```json
{
  "video_id": null,
  "message": "¿Qué se dijo sobre presupuesto?",
  "history": [
    {
      "role": "user",
      "content": "Resumen general"
    }
  ]
}
```

`video_id` es opcional. Con `null`, el asistente busca evidencia en todo el archivo; con un ID,
queda acotado a una sesión. El catálogo `/api/reports` incluye también registros pendientes de
transcript y permite filtrar por tema, título, canal y rango de fechas.

## Comportamiento implementado

- El scrapeo de canal combina `videos` y `streams`
- El scrapeo masivo pagina las respuestas públicas de YouTube hasta alcanzar el límite
- El filtro por título es accent-insensitive y acepta términos alternativos separados por `|` o `,`
- La deduplicación se hace por `video_id`
- Cada resultado se persiste inmediatamente en PostgreSQL, incluyendo los videos sin transcript
- Los videos que ya tienen transcript válido se reutilizan; usa `refresh_existing: true` para forzar su actualización
- El warehouse separa segmentos y chunks derivados en tablas particionadas por `video_id`
- El chat global consulta el warehouse completo y el chat de sesión puede acotar la búsqueda a un video
- El historial principal conserva el catálogo completo, incluidos videos sin transcript real
- Si el scrapeo del canal encuentra transcripts válidos, el frontend carga automáticamente el primero
- El chat envía `video_id` opcional, `message` y `history` al backend
- El backend puede ejecutar tools locales sobre el transcript antes de responder

## Warehouse y contexto LLM

La tabla `youtube_videos` conserva el registro raw y operacional. Al iniciar el API se crea el
schema `warehouse` con `fact_transcript_segments` y `fact_transcript_chunks`, ambas distribuidas
en 16 particiones hash por `video_id`. Los chunks tienen un tamaño aproximado de 3.200 caracteres
para entregar evidencia acotada al chat sin cargar el transcript completo.

Las búsquedas por video pueden podar particiones por `video_id`; las búsquedas globales usan los
índices GIN de texto completo y devuelven solo las filas de evidencia relevantes, aplicando las
fechas sobre `youtube_videos` antes de construir el contexto.

Los resultados de las tools del chat se serializan con
[`toon_format`](https://github.com/toon-format/toon-python), un formato compacto para estructuras
tabulares orientadas a LLM. TOON se usa como transporte de contexto, no como fuente canónica: la
fuente de verdad continúa siendo PostgreSQL y se puede regenerar el warehouse.

## Desarrollo frontend local

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5174
```

## Inspeccionar la base desde Docker

```bash
docker ps
docker start florence-pudahuel-db florence-pudahuel-api
docker exec -it florence-pudahuel-db psql -U postgres -d youtube_transcripts
```

Dentro de `psql`:

```sql
\dt public.*
\dt warehouse.*
SELECT COUNT(*) AS videos,
       COUNT(*) FILTER (WHERE transcript_text IS NOT NULL AND length(transcript_text) > 0) AS con_transcript,
       COUNT(*) FILTER (WHERE transcript_text IS NULL OR length(transcript_text) = 0) AS pendientes
FROM public.youtube_videos;
SELECT video_id, title, publish_date, transcript_error
FROM public.youtube_videos
WHERE transcript_text IS NULL OR length(transcript_text) = 0
ORDER BY publish_date DESC NULLS LAST;
SELECT COUNT(*) FROM warehouse.fact_transcript_segments;
SELECT COUNT(*) FROM warehouse.fact_transcript_chunks;
\q
```

Para exportar el catálogo y los transcripts a archivos locales:

```bash
docker exec florence-pudahuel-db psql -U postgres -d youtube_transcripts -At -F $'\t' -c \
  'SELECT video_id, publish_date, title, transcript_text FROM public.youtube_videos ORDER BY publish_date DESC NULLS LAST' \
  > pudahuel-transcripts.tsv
docker exec florence-pudahuel-db pg_dump -U postgres -d youtube_transcripts > pudahuel-backup.sql
```

## Build frontend

```bash
cd frontend
npm install
npm run build
```

## Notas

- No se usa Selenium
- `yt-dlp` se usa para descubrimiento de videos del canal
- `youtube-transcript-api` se usa para obtener transcripts
- Si esa API recibe un bloqueo de YouTube, el backend intenta recuperar subtítulos con `yt-dlp` usando el cliente Android
- Se guardan también videos sin transcript, pero quedan fuera del historial principal
