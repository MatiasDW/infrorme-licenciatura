# YouTube Transcript Console

Plataforma web para transcripción y consulta de videos públicos de YouTube con:

- Backend en `FastAPI`
- Frontend en `React + Vite`
- Persistencia en `PostgreSQL`
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
  "video_id": "xxxxxxxxxxx",
  "message": "¿Qué se dijo sobre presupuesto?",
  "history": [
    {
      "role": "user",
      "content": "Resumen general"
    }
  ]
}
```

## Comportamiento implementado

- El scrapeo de canal combina `videos` y `streams`
- El scrapeo masivo pagina las respuestas públicas de YouTube hasta alcanzar el límite
- El filtro por título es accent-insensitive y acepta términos alternativos separados por `|` o `,`
- La deduplicación se hace por `video_id`
- Cada resultado se persiste inmediatamente en PostgreSQL, incluyendo los videos sin transcript
- Los videos que ya tienen transcript válido se reutilizan; usa `refresh_existing: true` para forzar su actualización
- El historial principal excluye videos sin transcript real
- Si el scrapeo del canal encuentra transcripts válidos, el frontend carga automáticamente el primero
- El chat envía `video_id`, `message` y `history` al backend
- El backend puede ejecutar tools locales sobre el transcript antes de responder

## Desarrollo frontend local

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5174
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
- Se guardan también videos sin transcript, pero quedan fuera del historial principal
