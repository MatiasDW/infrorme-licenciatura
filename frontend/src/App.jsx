import { useEffect, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:18000";

const initialChannelForm = {
  url: "https://www.youtube.com/channel/UCJTRTxPkNZtnhyDpyPeVggQ",
  title_query: "concejo|sesion|reunion|comision",
  max_videos: 1000,
  all_content: false,
};

function formatDate(value, options = { dateStyle: "medium" }) {
  if (!value) return "Sin fecha";
  return new Intl.DateTimeFormat("es-CL", options).format(new Date(value));
}

function formatDateTime(value) {
  if (!value) return "Sin registro";
  return new Intl.DateTimeFormat("es-CL", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function getReportType(title = "") {
  const normalized = title.toLowerCase();
  if (normalized.includes("comision")) return "Comisión";
  if (normalized.includes("extraordinaria")) return "Sesión extraordinaria";
  if (normalized.includes("reunion")) return "Reunión de concejo";
  return "Sesión ordinaria";
}

function getReportStatus(video) {
  if (!video) return { label: "Sin selección", tone: "quiet" };
  if (video.has_transcript) return { label: "Evidencia disponible", tone: "ready" };
  return { label: "Pendiente de transcript", tone: "pending" };
}

export default function App() {
  const [reportSearch, setReportSearch] = useState({ query: "", date_from: "", date_to: "" });
  const [channelForm, setChannelForm] = useState(initialChannelForm);
  const [library, setLibrary] = useState({ recent: [], items: [], total: 0 });
  const [currentVideo, setCurrentVideo] = useState(null);
  const [channelResult, setChannelResult] = useState(null);
  const [pageError, setPageError] = useState("");
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [loadingChannel, setLoadingChannel] = useState(false);
  const [loadingTranscript, setLoadingTranscript] = useState(false);
  const [chatOpen, setChatOpen] = useState(true);
  const [chatScope, setChatScope] = useState("archive");
  const [chatHistory, setChatHistory] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  const currentVideoId = currentVideo?.video_id || "";
  const chatVideoId = chatScope === "report" ? currentVideoId : "";
  const currentStatus = getReportStatus(currentVideo);

  function switchChatScope(scope) {
    setChatScope(scope);
    setChatHistory([]);
  }

  async function request(path, options = {}) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });

    if (!response.ok) {
      let detail = "No fue posible completar la solicitud";
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

  async function loadLibrary(filters = {}) {
    const params = new URLSearchParams({ limit: "1000" });
    if (filters.query?.trim()) params.set("q", filters.query.trim());
    if (filters.date_from) params.set("date_from", filters.date_from);
    if (filters.date_to) params.set("date_to", filters.date_to);
    const data = await request(`/api/reports?${params.toString()}`);
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
      try {
        const data = await loadLibrary();
        const firstUsable = data.items.find((video) => video.has_transcript) || data.items[0];
        if (firstUsable?.video_id) await loadTranscript(firstUsable.video_id);
      } catch (error) {
        setPageError(error.message);
      }
    }
    bootstrap();
  }, []);

  async function handleReportSearch(event) {
    event.preventDefault();
    setLoadingSearch(true);
    setPageError("");
    try {
      const data = await loadLibrary(reportSearch);
      const firstUsable = data.items.find((video) => video.has_transcript) || data.items[0];
      if (firstUsable?.video_id) {
        await loadTranscript(firstUsable.video_id);
      } else {
        setCurrentVideo(null);
        setPageError("No hay reportes que coincidan con esos filtros.");
      }
    } catch (error) {
      setPageError(error.message);
    } finally {
      setLoadingSearch(false);
    }
  }

  async function handleChannelSubmit(event) {
    event.preventDefault();
    setLoadingChannel(true);
    setPageError("");
    try {
      const endpoint = channelForm.all_content
        ? "/api/channels/scrape-all"
        : "/api/channels/scrape";
      const result = await request(endpoint, {
        method: "POST",
        body: JSON.stringify({
          ...channelForm,
          max_videos: Number(channelForm.max_videos),
        }),
      });
      setChannelResult(result);
      await loadLibrary();
      if (result.first_valid_video_id) await loadTranscript(result.first_valid_video_id);
    } catch (error) {
      setPageError(error.message);
    } finally {
      setLoadingChannel(false);
    }
  }

  async function handleChatSubmit(event) {
    event.preventDefault();
    if (!chatInput.trim() || chatLoading) return;

    const nextMessage = chatInput.trim();
    setChatHistory((history) => [...history, { role: "user", content: nextMessage }]);
    setChatInput("");
    setChatLoading(true);

    try {
      const data = await request("/api/v1/chat/message", {
        method: "POST",
        body: JSON.stringify({
          video_id: chatVideoId || null,
          message: nextMessage,
          history: chatHistory,
        }),
      });
      setChatHistory((history) => [...history, { role: "assistant", content: data.answer }]);
    } catch (error) {
      setChatHistory((history) => [
        ...history,
        { role: "assistant", content: `No se pudo consultar: ${error.message}` },
      ]);
    } finally {
      setChatLoading(false);
    }
  }

  const historyOptions = library.items || [];
  const visibleChannelVideos = channelResult?.videos?.slice(0, 60) || [];

  return (
    <div className="app-shell">
      <div className="page-backdrop" aria-hidden="true">
        <span className="backdrop-column column-one" />
        <span className="backdrop-column column-two" />
        <span className="backdrop-document document-one" />
        <span className="backdrop-document document-two" />
      </div>

      <header className="site-header">
        <a className="brand-lockup" href="/" aria-label="Observatorio Municipal">
          <span className="municipality-logo" role="img" aria-label="Logo de la Municipalidad de Pudahuel" />
          <span>
            <strong>Ilustre Municipalidad</strong>
            <small>de Pudahuel · Observatorio público</small>
          </span>
        </a>
        <div className="header-status">
          <span className="status-dot" />
          <span>Archivo público conectado</span>
          <b>v0.1</b>
        </div>
      </header>

      <main className="page-grid">
        <section className="hero-card">
          <div className="hero-copy">
            <div className="hero-kicker">
              <span className="section-label">Inteligencia de sesiones</span>
              <span className="hero-index">01 / INGESTA</span>
            </div>
            <h1>De la sesión municipal al reporte que se puede consultar.</h1>
            <p>
              Reúne videos públicos, conserva su evidencia temporal y encuentra decisiones,
              compromisos y temas relevantes sin perder la fuente original.
            </p>
            <div className="hero-notes">
              <span><b>01</b> Fuente verificable</span>
              <span><b>02</b> Transcript indexado</span>
              <span><b>03</b> Consulta asistida</span>
            </div>
          </div>

          <form className="single-ingest" onSubmit={handleReportSearch}>
            <div className="form-heading">
              <span className="form-icon">⌕</span>
              <div>
                <span className="section-label">Archivo completo</span>
                <h2>Buscar reportes</h2>
              </div>
            </div>
            <label>
              Tema, palabra o comisión
              <input
                value={reportSearch.query}
                onChange={(event) => setReportSearch((state) => ({ ...state, query: event.target.value }))}
                placeholder="presupuesto, seguridad, comisión..."
                type="search"
              />
            </label>
            <div className="search-date-row">
              <label>Desde<input type="date" value={reportSearch.date_from} onChange={(event) => setReportSearch((state) => ({ ...state, date_from: event.target.value }))} /></label>
              <label>Hasta<input type="date" value={reportSearch.date_to} onChange={(event) => setReportSearch((state) => ({ ...state, date_to: event.target.value }))} /></label>
            </div>
            <button className="primary-button" disabled={loadingSearch} type="submit">
              {loadingSearch ? "Buscando en el archivo..." : "Buscar en el archivo"}
              <span>↗</span>
            </button>
            <p className="form-footnote">{library.total || 0} reportes indexados · no necesitas pegar una URL para consultar.</p>
          </form>

          <div className="hero-footer">
            <span><i className="signal-icon" /> PostgreSQL conectado</span>
            <span>Última actualización: {formatDateTime(currentVideo?.scraped_at)}</span>
          </div>
        </section>

        <section className="intake-grid">
          <form className="panel channel-panel" onSubmit={handleChannelSubmit}>
            <div className="panel-heading">
              <div>
                <span className="section-label">Carga de archivo</span>
                <h2>Explorar el canal municipal</h2>
              </div>
              <span className="panel-number">02</span>
            </div>
            <p className="panel-intro">
              Descubre sesiones y comisiones, y deja cada registro listo para consulta posterior.
            </p>
            <label>
              URL del canal
              <input
                value={channelForm.url}
                onChange={(event) => setChannelForm((state) => ({ ...state, url: event.target.value }))}
                required
                type="url"
              />
            </label>
            <div className="form-row">
              <label>
                Términos de búsqueda
                <input
                  value={channelForm.title_query}
                  onChange={(event) =>
                    setChannelForm((state) => ({ ...state, title_query: event.target.value }))
                  }
                  placeholder="concejo|sesion|comision"
                  type="text"
                />
              </label>
              <label>
                Máximo de registros
                <input
                  min="1"
                  max="5000"
                  value={channelForm.max_videos}
                  onChange={(event) =>
                    setChannelForm((state) => ({ ...state, max_videos: event.target.value }))
                  }
                  required
                  type="number"
                />
              </label>
            </div>
            <label className="checkbox-label">
              <input
                checked={channelForm.all_content}
                onChange={(event) =>
                  setChannelForm((state) => ({
                    ...state,
                    all_content: event.target.checked,
                    title_query: event.target.checked ? "" : state.title_query,
                  }))
                }
                type="checkbox"
              />
              <span>Incluir todo el archivo, incluso piezas fuera del concejo</span>
            </label>
            <button className="secondary-button" disabled={loadingChannel} type="submit">
              {loadingChannel ? "Indexando archivo..." : "Indexar canal"}
              <span>→</span>
            </button>
          </form>

          <section className="panel method-panel">
            <div className="panel-heading">
              <div>
                <span className="section-label">Cómo trabaja</span>
                <h2>Una ficha por sesión</h2>
              </div>
              <span className="panel-number">03</span>
            </div>
            <div className="method-list">
              <div><span>01</span><p><b>Detectar</b> videos y transmisiones del canal.</p></div>
              <div><span>02</span><p><b>Conservar</b> fuente, fecha y evidencia textual.</p></div>
              <div><span>03</span><p><b>Consultar</b> por palabras o preguntas.</p></div>
            </div>
            <div className="method-stamp">ARCHIVO<br /><strong>ABIERTO</strong></div>
          </section>
        </section>

        {pageError && <section className="error-banner">{pageError}</section>}

        {channelResult && (
          <section className="panel channel-results">
            <div className="panel-heading result-heading">
              <div>
                <span className="section-label">Resultado de ingesta</span>
                <h2>Archivo incorporado</h2>
              </div>
              <span className="result-count">{channelResult.processed_count} registros</span>
            </div>
            <div className="stats-row">
              <div><span>Filtro</span><strong>{channelResult.title_query || "Todo el canal"}</strong></div>
              <div><span>Con evidencia</span><strong className="green-number">{channelResult.videos_with_transcript}</strong></div>
              <div><span>Pendientes</span><strong>{channelResult.videos_without_transcript}</strong></div>
              <div><span>Fuente</span><strong>YouTube</strong></div>
            </div>
            <div className="channel-list">
              {visibleChannelVideos.map((video) => (
                <button className="channel-item" key={video.video_id} onClick={() => loadTranscript(video.video_id)} type="button">
                  <span className="item-marker">{video.has_transcript ? "✓" : "—"}</span>
                  <span className="channel-item-copy">
                    <b>{video.title}</b>
                    <small>{video.source_tab} · {video.publish_date ? formatDate(video.publish_date) : "Fecha pendiente"}</small>
                  </span>
                  <span className={video.has_transcript ? "pill success" : "pill muted-pill"}>
                    {video.has_transcript ? "Listo" : "Pendiente"}
                  </span>
                </button>
              ))}
            </div>
            {channelResult.videos.length > visibleChannelVideos.length && (
              <p className="list-footnote">Mostrando 60 de {channelResult.videos.length} registros en esta vista.</p>
            )}
          </section>
        )}

        <section className="dashboard-grid">
          <section className="panel report-panel">
            <div className="report-header">
              <div>
                <div className="report-label"><span className="report-dot" /> Reporte activo · {getReportType(currentVideo?.title)}</div>
                <h2>{currentVideo?.title || "Selecciona una sesión del archivo"}</h2>
                {currentVideo && (
                  <p className="report-meta">
                    {currentVideo.channel_name || "Canal municipal"} · {formatDate(currentVideo.publish_date)} · guardado {formatDateTime(currentVideo.scraped_at)}
                  </p>
                )}
              </div>
              <span className={`report-status ${currentStatus.tone}`}>{currentStatus.label}</span>
            </div>

            {loadingTranscript ? (
              <div className="empty-report loading-block"><span className="loader" /> Cargando ficha documental...</div>
            ) : currentVideo ? (
              <>
                <div className="report-metrics">
                  <div><span>Idioma</span><b>{currentVideo.transcript_language || "No detectado"}</b></div>
                  <div><span>Segmentos</span><b>{currentVideo.transcript_segments?.length || 0}</b></div>
                  <div><span>Fuente</span><b>{currentVideo.transcript_source || "Pendiente"}</b></div>
                  <div><span>Generado</span><b>{currentVideo.transcript_is_generated == null ? "N/D" : currentVideo.transcript_is_generated ? "Sí" : "No"}</b></div>
                </div>
                {currentVideo.transcript_error && (
                  <div className="warning-banner">
                    <b>Registro conservado.</b> El transcript está pendiente: {currentVideo.transcript_error}
                  </div>
                )}
                <div className="evidence-heading">
                  <div><span className="section-label">Evidencia temporal</span><h3>Fragmentos del reporte</h3></div>
                  {currentVideo.url && <a href={currentVideo.url} target="_blank" rel="noreferrer">Abrir fuente ↗</a>}
                </div>
                <div className="segments-list">
                  {(currentVideo.transcript_segments || []).map((segment, index) => (
                    <article className="segment-card" key={`${segment.start}-${index}`}>
                      <span className="timestamp">{segment.start.toFixed(1)}s</span>
                      <p>{segment.text}</p>
                    </article>
                  ))}
                  {!currentVideo.transcript_segments?.length && <p className="muted">No hay evidencia textual disponible todavía.</p>}
                </div>
              </>
            ) : (
              <div className="empty-report"><span className="empty-seal">+</span><p>Carga una sesión para abrir su ficha de evidencia.</p></div>
            )}
          </section>

          <aside className="panel archive-panel">
            <div className="panel-heading">
              <div><span className="section-label">Archivo reciente</span><h2>Sesiones guardadas</h2></div>
              <span className="archive-total">{library.items.length}</span>
            </div>
            <div className="recent-list">
              {library.recent.map((video, index) => (
                <button className={`recent-item ${video.video_id === currentVideoId ? "active" : ""}`} key={video.video_id} onClick={() => loadTranscript(video.video_id)} type="button">
                  <span className="recent-index">0{index + 1}</span>
                  <span><b>{video.title}</b><small>{formatDate(video.publish_date)} · {video.has_transcript ? "Con evidencia" : "Pendiente"}</small></span>
                  <span className="arrow">↗</span>
                </button>
              ))}
              {!library.recent.length && <p className="muted">Aún no hay sesiones con transcript.</p>}
            </div>
            <label className="archive-select-label">
              Ver todo el archivo
              <select value={currentVideoId} onChange={(event) => loadTranscript(event.target.value)}>
                <option value="">Seleccionar registro</option>
                {historyOptions.map((video) => <option key={video.video_id} value={video.video_id}>{video.title}</option>)}
              </select>
            </label>
            <div className="archive-footer"><span className="signal-icon" /> Datos almacenados en PostgreSQL</div>
          </aside>
        </section>
      </main>

      <aside className={`chat-shell ${chatOpen ? "open" : "closed"}`}>
        <button className="chat-toggle" onClick={() => setChatOpen((open) => !open)} type="button">
          <span className="assistant-avatar" role="img" aria-label="Logo de la Municipalidad de Pudahuel" />
          {chatOpen ? "Ocultar asistente" : "Chat"}
        </button>
        {chatOpen && (
          <div className="chat-panel">
            <div className="chat-header">
              <div className="chat-identity">
                <span className="assistant-avatar assistant-avatar-large" role="img" aria-label="Logo de la Municipalidad de Pudahuel" />
                <div><span className="section-label">Asistente documental</span><h3>{chatScope === "archive" ? "Todo el archivo municipal" : currentVideo?.title || "Sin reporte activo"}</h3></div>
              </div>
              <span className="assistant-badge">AI</span>
            </div>
            <div className="chat-scope-toggle" aria-label="Alcance del asistente">
              <button className={chatScope === "archive" ? "active" : ""} onClick={() => switchChatScope("archive")} type="button">Todo el archivo</button>
              <button className={chatScope === "report" ? "active" : ""} disabled={!currentVideoId} onClick={() => switchChatScope("report")} type="button">Esta sesión</button>
            </div>
            <div className="chat-messages">
              {chatHistory.length === 0 && <p className="chat-empty">{chatScope === "archive" ? "Pregunta por decisiones, temas o fechas en todo el archivo municipal." : "Pregunta por decisiones, temas o momentos de esta sesión."} Responderé usando solo la evidencia almacenada.</p>}
              {chatHistory.map((item, index) => (
                <article className={`chat-bubble ${item.role}`} key={`${item.role}-${index}`}>
                  <span>{item.role === "user" ? "Tú" : "Asistente"}</span><p>{item.content}</p>
                </article>
              ))}
            </div>
            <form className="chat-form" onSubmit={handleChatSubmit}>
              <textarea disabled={chatLoading} maxLength="2000" onChange={(event) => setChatInput(event.target.value)} placeholder="¿Qué se discutió en las sesiones?" rows="3" value={chatInput} />
              <button className="primary-button" disabled={chatLoading || !chatInput.trim()} type="submit">{chatLoading ? "Consultando..." : "Preguntar ↗"}</button>
            </form>
          </div>
        )}
      </aside>
    </div>
  );
}
