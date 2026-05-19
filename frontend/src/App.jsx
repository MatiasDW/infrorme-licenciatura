import { useEffect, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const initialChannelForm = {
  url: "https://www.youtube.com/@IMunicipalidadLoBarnechea",
  title_query: "sesion ordinaria",
  max_videos: 20,
};

function formatDate(value) {
  if (!value) return "Sin fecha";
  return new Intl.DateTimeFormat("es-CL", {
    dateStyle: "long",
  }).format(new Date(value));
}

function formatDateTime(value) {
  if (!value) return "";
  return new Intl.DateTimeFormat("es-CL", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function App() {
  const [singleUrl, setSingleUrl] = useState("");
  const [channelForm, setChannelForm] = useState(initialChannelForm);
  const [library, setLibrary] = useState({ recent: [], items: [] });
  const [currentVideo, setCurrentVideo] = useState(null);
  const [channelResult, setChannelResult] = useState(null);
  const [pageError, setPageError] = useState("");
  const [loadingSingle, setLoadingSingle] = useState(false);
  const [loadingChannel, setLoadingChannel] = useState(false);
  const [loadingTranscript, setLoadingTranscript] = useState(false);
  const [chatOpen, setChatOpen] = useState(true);
  const [chatHistory, setChatHistory] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  const currentVideoId = currentVideo?.video_id || "";

  async function request(path, options = {}) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
      },
      ...options,
    });

    if (!response.ok) {
      let detail = "Request failed";
      try {
        const data = await response.json();
        detail = data.detail || detail;
      } catch {
        detail = await response.text();
      }
      throw new Error(detail);
    }

    return response.json();
  }

  async function loadLibrary() {
    const data = await request("/api/transcripts");
    setLibrary(data);
    return data;
  }

  async function loadTranscript(videoId) {
    if (!videoId) return;
    setLoadingTranscript(true);
    setPageError("");
    try {
      const data = await request(`/api/transcripts/${videoId}`);
      setCurrentVideo(data);
      setChatHistory([]);
    } catch (error) {
      setPageError(error.message);
    } finally {
      setLoadingTranscript(false);
    }
  }

  useEffect(() => {
    async function bootstrap() {
      setPageError("");
      try {
        const data = await loadLibrary();
        if (data.recent[0]?.video_id) {
          await loadTranscript(data.recent[0].video_id);
        }
      } catch (error) {
        setPageError(error.message);
      }
    }

    bootstrap();
  }, []);

  async function handleSingleSubmit(event) {
    event.preventDefault();
    setLoadingSingle(true);
    setPageError("");
    try {
      const video = await request("/api/transcripts", {
        method: "POST",
        body: JSON.stringify({ url: singleUrl }),
      });
      setCurrentVideo(video);
      setChatHistory([]);
      setSingleUrl("");
      await loadLibrary();
    } catch (error) {
      setPageError(error.message);
    } finally {
      setLoadingSingle(false);
    }
  }

  async function handleChannelSubmit(event) {
    event.preventDefault();
    setLoadingChannel(true);
    setPageError("");
    try {
      const result = await request("/api/channels/scrape", {
        method: "POST",
        body: JSON.stringify({
          ...channelForm,
          max_videos: Number(channelForm.max_videos),
        }),
      });
      setChannelResult(result);
      await loadLibrary();
      if (result.first_valid_video_id) {
        await loadTranscript(result.first_valid_video_id);
      }
    } catch (error) {
      setPageError(error.message);
    } finally {
      setLoadingChannel(false);
    }
  }

  async function handleChatSubmit(event) {
    event.preventDefault();
    if (!chatInput.trim() || !currentVideoId || chatLoading) return;

    const nextHistory = [...chatHistory, { role: "user", content: chatInput.trim() }];
    const nextMessage = chatInput.trim();
    setChatHistory(nextHistory);
    setChatInput("");
    setChatLoading(true);

    try {
      const data = await request("/api/v1/chat/message", {
        method: "POST",
        body: JSON.stringify({
          video_id: currentVideoId,
          message: nextMessage,
          history: chatHistory,
        }),
      });
      setChatHistory((history) => [...history, { role: "assistant", content: data.answer }]);
    } catch (error) {
      setChatHistory((history) => [
        ...history,
        { role: "assistant", content: `Error: ${error.message}` },
      ]);
    } finally {
      setChatLoading(false);
    }
  }

  const historyOptions = library.items || [];

  return (
    <div className="app-shell">
      <div className="page-backdrop" />
      <header className="page-header">
        <div>
          <p className="eyebrow">Transcripción y consulta de videos públicos</p>
          <h1>YouTube Transcript Console</h1>
          <p className="header-copy">
            Carga videos o canales de YouTube, guarda transcripts en PostgreSQL y consulta
            el contenido con chat sobre el material procesado.
          </p>
        </div>
      </header>

      <main className="page-grid">
        <section className="hero-card">
          <div className="hero-copy">
            <p className="section-label">Flujo principal</p>
            <h2>Procesamiento individual o por canal con historial reutilizable.</h2>
            <p>
              Un segmento es un bloque de texto asociado a un tiempo de inicio y duración.
              La vista actual muestra esos bloques para facilitar lectura, trazabilidad y
              consulta puntual.
            </p>
          </div>

          <div className="history-panel">
            <p className="section-label">Historial</p>
            <div className="recent-buttons">
              {library.recent.map((video) => (
                <button
                  key={video.video_id}
                  className="history-chip"
                  onClick={() => loadTranscript(video.video_id)}
                  type="button"
                >
                  {video.title}
                </button>
              ))}
              {library.recent.length === 0 && <span className="muted">Sin transcripts guardados.</span>}
            </div>

            <label className="dropdown-label">
              Transcripts anteriores
              <select
                value={currentVideoId}
                onChange={(event) => loadTranscript(event.target.value)}
              >
                <option value="">Seleccionar transcript</option>
                {historyOptions.map((video) => (
                  <option key={video.video_id} value={video.video_id}>
                    {video.title}
                  </option>
                ))}
              </select>
            </label>
          </div>
        </section>

        <section className="forms-grid">
          <form className="panel" onSubmit={handleSingleSubmit}>
            <p className="section-label">Video individual</p>
            <h3>Extraer metadata y transcript</h3>
            <label>
              URL de YouTube
              <input
                value={singleUrl}
                onChange={(event) => setSingleUrl(event.target.value)}
                placeholder="https://www.youtube.com/watch?v=..."
                required
                type="url"
              />
            </label>
            <button className="primary-button" disabled={loadingSingle} type="submit">
              {loadingSingle ? "Procesando..." : "Cargar video"}
            </button>
          </form>

          <form className="panel" onSubmit={handleChannelSubmit}>
            <p className="section-label">Canal</p>
            <h3>Buscar en pestañas videos y streams</h3>
            <label>
              URL de canal
              <input
                value={channelForm.url}
                onChange={(event) =>
                  setChannelForm((state) => ({ ...state, url: event.target.value }))
                }
                required
                type="url"
              />
            </label>
            <label>
              Filtro por título
              <input
                value={channelForm.title_query}
                onChange={(event) =>
                  setChannelForm((state) => ({ ...state, title_query: event.target.value }))
                }
                required
                type="text"
              />
            </label>
            <label>
              Máximo de videos
              <input
                min="1"
                max="100"
                value={channelForm.max_videos}
                onChange={(event) =>
                  setChannelForm((state) => ({ ...state, max_videos: event.target.value }))
                }
                required
                type="number"
              />
            </label>
            <button className="primary-button" disabled={loadingChannel} type="submit">
              {loadingChannel ? "Scrapeando..." : "Procesar canal"}
            </button>
          </form>
        </section>

        {pageError && <section className="error-banner">{pageError}</section>}

        {channelResult && (
          <section className="panel channel-results">
            <p className="section-label">Resultado del canal</p>
            <div className="stats-row">
              <div>
                <span>Filtro aplicado</span>
                <strong>{channelResult.title_query}</strong>
              </div>
              <div>
                <span>Límite aplicado</span>
                <strong>{channelResult.max_videos}</strong>
              </div>
              <div>
                <span>Videos cargados</span>
                <strong>{channelResult.processed_count}</strong>
              </div>
              <div>
                <span>Con transcript</span>
                <strong>{channelResult.videos_with_transcript}</strong>
              </div>
              <div>
                <span>Sin transcript</span>
                <strong>{channelResult.videos_without_transcript}</strong>
              </div>
            </div>

            <div className="channel-list">
              {channelResult.videos.map((video) => (
                <article className="channel-item" key={video.video_id}>
                  <div>
                    <h4>{video.title}</h4>
                    <p>
                      {video.channel_name || "Canal sin nombre"} · {video.source_tab} ·{" "}
                      {video.publish_date ? formatDate(video.publish_date) : "Sin fecha"}
                    </p>
                  </div>
                  <span className={video.has_transcript ? "pill success" : "pill muted-pill"}>
                    {video.has_transcript ? "Con transcript" : "Sin transcript"}
                  </span>
                </article>
              ))}
            </div>
          </section>
        )}

        <section className="panel transcript-panel">
          <div className="transcript-header">
            <div>
              <p className="section-label">Resultado actual</p>
              <h2>{currentVideo?.title || "Aún no hay transcript cargado"}</h2>
              {currentVideo && (
                <p className="transcript-meta">
                  {currentVideo.channel_name || "Canal desconocido"} ·{" "}
                  {formatDate(currentVideo.publish_date)} · guardado {formatDateTime(currentVideo.scraped_at)}
                </p>
              )}
            </div>
            {loadingTranscript && <span className="muted">Cargando transcript...</span>}
          </div>

          {currentVideo ? (
            <>
              <div className="summary-grid">
                <div className="summary-box">
                  <span>Idioma</span>
                  <strong>{currentVideo.transcript_language || "No detectado"}</strong>
                </div>
                <div className="summary-box">
                  <span>Fuente</span>
                  <strong>{currentVideo.transcript_source || "Sin transcript"}</strong>
                </div>
                <div className="summary-box">
                  <span>Segmentos</span>
                  <strong>{currentVideo.transcript_segments.length}</strong>
                </div>
                <div className="summary-box">
                  <span>Generado</span>
                  <strong>
                    {currentVideo.transcript_is_generated == null
                      ? "N/D"
                      : currentVideo.transcript_is_generated
                        ? "Sí"
                        : "No"}
                  </strong>
                </div>
              </div>

              {currentVideo.transcript_error && (
                <div className="warning-banner">
                  El video fue guardado, pero no se pudo obtener transcript:{" "}
                  {currentVideo.transcript_error}
                </div>
              )}

              <div className="segments-list">
                {(currentVideo.transcript_segments || []).map((segment, index) => (
                  <article className="segment-card" key={`${segment.start}-${index}`}>
                    <span className="timestamp">{segment.start.toFixed(1)}s</span>
                    <p>{segment.text}</p>
                  </article>
                ))}
                {currentVideo.transcript_segments.length === 0 && (
                  <p className="muted">No hay transcript real guardado para este video.</p>
                )}
              </div>
            </>
          ) : (
            <p className="muted">Carga un video o procesa un canal para ver resultados.</p>
          )}
        </section>
      </main>

      <aside className={`chat-shell ${chatOpen ? "open" : "closed"}`}>
        <button className="chat-toggle" onClick={() => setChatOpen((open) => !open)} type="button">
          {chatOpen ? "Cerrar chat" : "Abrir chat"}
        </button>

        {chatOpen && (
          <div className="chat-panel">
            <div className="chat-header">
              <div>
                <p className="section-label">Chat LLM</p>
                <h3>{currentVideo?.title || "Sin video activo"}</h3>
              </div>
            </div>

            <div className="chat-messages">
              {chatHistory.length === 0 && (
                <p className="muted">
                  Haz preguntas sobre el transcript cargado. El historial vive solo en memoria.
                </p>
              )}
              {chatHistory.map((item, index) => (
                <article className={`chat-bubble ${item.role}`} key={`${item.role}-${index}`}>
                  <span>{item.role === "user" ? "Tú" : "Asistente"}</span>
                  <p>{item.content}</p>
                </article>
              ))}
            </div>

            <form className="chat-form" onSubmit={handleChatSubmit}>
              <textarea
                disabled={!currentVideoId || chatLoading}
                onChange={(event) => setChatInput(event.target.value)}
                placeholder="Pregunta sobre el contenido del video..."
                rows="3"
                value={chatInput}
              />
              <button
                className="primary-button"
                disabled={!currentVideoId || chatLoading || !chatInput.trim()}
                type="submit"
              >
                {chatLoading ? "Consultando..." : "Enviar"}
              </button>
            </form>
          </div>
        )}
      </aside>
    </div>
  );
}
