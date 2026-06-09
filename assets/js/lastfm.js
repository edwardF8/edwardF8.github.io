/* ----------------------------------------------------------------------------
 * Last.fm music stats — client-side fetch + render.
 * Reads window.LASTFM = { user } injected by the page.
 * Read-only public methods only; no auth/signing.
 *
 * Renders only the sections whose container elements exist on the page, so the
 * SAME script powers both the full /music/ page and a lone #lf-now "now playing"
 * widget on the home page.
 *
 * The API key is XOR+base64 obfuscated below (not a plaintext string). This is
 * DETERRENCE — it stops automated secret-scanners and casual "view source"
 * harvesting, NOT real security: client code can always be reverse-engineered.
 * The key is read-only (no write/account access) and can be regenerated if
 * abused. For true secrecy the data would have to be fetched server-side.
 * ------------------------------------------------------------------------- */
(function () {
  "use strict";

  const CFG = window.LASTFM || {};
  const API = "https://ws.audioscrobbler.com/2.0/";
  const PLACEHOLDER = "2a96cbd8b46e442fc41c2b86b821562f"; // Last.fm "no image" star
  const RECENT_POLL_MS = 30000;

  // Fetch the size that matches the display slot instead of always the biggest —
  // a 44px thumbnail should not download a 300px image. (Last.fm sizes:
  // small=34, medium=64, large=174, extralarge=300, mega≈300+.)
  const SIZE_THUMB = ["medium", "large", "small"]; // ~44px list thumbs
  const SIZE_HERO = ["large", "medium", "extralarge"]; // ~48–64px now-playing art
  const SIZE_COVER = ["extralarge", "large", "mega", "medium"]; // album grid covers

  // Obfuscated read-only key — reassembled at runtime, never stored in the clear.
  const _ENC = "XwoeEVYVBEtcBAEPDEBBWUIBHFFTCw9aTBJUE1EdA1M=";
  const _SALT = "mixtape-ef8";
  function apiKey() {
    const raw = atob(_ENC);
    let out = "";
    for (let i = 0; i < raw.length; i++) {
      out += String.fromCharCode(raw.charCodeAt(i) ^ _SALT.charCodeAt(i % _SALT.length));
    }
    return out;
  }

  const $ = (id) => document.getElementById(id);
  // Write into an element only if it exists on this page (no-op otherwise).
  const set = (id, html) => {
    const el = $(id);
    if (el) el.innerHTML = html;
  };
  const fmt = (n) => Number(n).toLocaleString();
  const esc = (s) =>
    String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );

  /* --- API ---------------------------------------------------------------- */
  async function api(method, params) {
    const qs = new URLSearchParams({
      method,
      user: CFG.user,
      api_key: apiKey(),
      format: "json",
      ...params,
    });
    const res = await fetch(`${API}?${qs}`);
    if (!res.ok) throw new Error(`Last.fm ${method} HTTP ${res.status}`);
    const data = await res.json();
    if (data.error) throw new Error(`Last.fm ${method}: ${data.message}`);
    return data;
  }

  // Last.fm returns a single object instead of an array when there's one item.
  const asArray = (x) => (Array.isArray(x) ? x : x ? [x] : []);

  /* --- images / art ------------------------------------------------------- */
  function pickImage(images, order) {
    const arr = asArray(images);
    for (const size of order) {
      const hit = arr.find((i) => i.size === size && i["#text"]);
      if (hit && !hit["#text"].includes(PLACEHOLDER)) return hit["#text"];
    }
    // fall back to any real (non-placeholder) image if the preferred sizes are absent
    const any = arr.find((i) => i["#text"] && !i["#text"].includes(PLACEHOLDER));
    return any ? any["#text"] : null;
  }

  function hue(str) {
    let h = 0;
    for (let i = 0; i < (str || "").length; i++) h = (h * 31 + str.charCodeAt(i)) % 360;
    return h;
  }

  // <img> when art exists, otherwise a colored initial tile. `cls` controls size;
  // `order` picks the smallest image size that still looks sharp at that slot.
  function art(name, images, cls, order) {
    const url = pickImage(images, order || SIZE_COVER);
    const safe = esc(name);
    if (url)
      return `<img class="${cls}" src="${esc(url)}" alt="${safe}" loading="lazy" decoding="async">`;
    const initial = esc((name || "?").trim().charAt(0).toUpperCase());
    return `<div class="${cls} lf-initial" style="--h:${hue(name)}">${initial}</div>`;
  }

  function relTime(uts) {
    if (!uts) return "";
    const diff = Math.floor(Date.now() / 1000) - Number(uts);
    if (diff < 60) return "now";
    if (diff < 3600) return Math.floor(diff / 60) + "m";
    if (diff < 86400) return Math.floor(diff / 3600) + "h";
    return Math.floor(diff / 86400) + "d";
  }

  /* --- skeletons / errors ------------------------------------------------- */
  const skel = (n) => Array.from({ length: n }, () => `<div class="lf-skel"></div>`).join("");
  const errMsg = (what) => `<div class="lf-err">couldn't load ${esc(what)} right now.</div>`;

  /* --- renderers ---------------------------------------------------------- */
  function renderNow(track, live) {
    const album = track.album && track.album["#text"];
    set(
      "lf-now",
      `
      ${art(album || track.name, track.image, "lf-hero-art", SIZE_HERO)}
      <div style="flex:1; min-width:0">
        <div class="lf-badge">${
          live
            ? `<span class="lf-eq"><span></span><span></span><span></span></span> Listening now`
            : "Last played"
        }</div>
        <div class="t">${esc(track.name)}</div>
        <div class="a">${esc(track.artist["#text"])}${album ? " · " + esc(album) : ""}</div>
      </div>`
    );
  }

  function renderRecent(tracks) {
    set(
      "lf-recent",
      tracks
        .map(
          (r) => `
      <div class="lf-row">
        ${art((r.album && r.album["#text"]) || r.name, r.image, "lf-thumb", SIZE_THUMB)}
        <div class="meta"><div class="t">${esc(r.name)}</div><div class="a">${esc(
            r.artist["#text"]
          )}</div></div>
        <div class="plays">${
          r["@attr"] && r["@attr"].nowplaying ? "now" : relTime(r.date && r.date.uts)
        }</div>
      </div>`
        )
        .join("")
    );
  }

  async function loadRecent() {
    try {
      const data = await api("user.getRecentTracks", { limit: "8" });
      const tracks = asArray(data.recenttracks && data.recenttracks.track);
      if (!tracks.length) {
        set("lf-now", errMsg("now playing"));
        return;
      }
      const first = tracks[0];
      const live = !!(first["@attr"] && first["@attr"].nowplaying);
      renderNow(first, live);
      // The hero shows the first track; the recent list shows the history after it.
      renderRecent(tracks.slice(1, 7));
    } catch (e) {
      console.error(e);
      set("lf-now", errMsg("now playing"));
      set("lf-recent", errMsg("recent tracks"));
    }
  }

  async function loadTotals() {
    try {
      const u = (await api("user.getInfo", {})).user;
      set(
        "lf-totals",
        [
          ["Scrobbles", u.playcount],
          ["Artists", u.artist_count],
          ["Albums", u.album_count],
          ["Tracks", u.track_count],
        ]
          .map(
            ([l, n]) =>
              `<div class="lf-stat"><div class="n">${fmt(n)}</div><div class="l">${l}</div></div>`
          )
          .join("")
      );
    } catch (e) {
      console.error(e);
      set("lf-totals", errMsg("totals"));
    }
  }

  async function loadTops(period) {
    set("lf-albums", skel(8));
    set("lf-artists", skel(10));
    set("lf-tracks", skel(10));

    try {
      const albums = asArray(
        (await api("user.getTopAlbums", { period, limit: "8" })).topalbums.album
      );
      set(
        "lf-albums",
        albums
          .map(
            (a) => `
        <div class="lf-album">
          ${art(a.name, a.image, "lf-cover", SIZE_COVER)}
          <div class="t">${esc(a.name)}</div>
          <div class="a">${esc(a.artist && a.artist.name)}</div>
        </div>`
          )
          .join("")
      );
    } catch (e) {
      console.error(e);
      set("lf-albums", errMsg("top albums"));
    }

    try {
      const artists = asArray(
        (await api("user.getTopArtists", { period, limit: "10" })).topartists.artist
      );
      set(
        "lf-artists",
        artists
          .map(
            (a, i) => `
        <div class="lf-row">
          <div class="rank">${i + 1}</div>
          ${art(a.name, a.image, "lf-thumb", SIZE_THUMB)}
          <div class="meta"><div class="t">${esc(a.name)}</div></div>
          <div class="plays">${fmt(a.playcount)} plays</div>
        </div>`
          )
          .join("")
      );
    } catch (e) {
      console.error(e);
      set("lf-artists", errMsg("top artists"));
    }

    try {
      const tracks = asArray(
        (await api("user.getTopTracks", { period, limit: "10" })).toptracks.track
      );
      set(
        "lf-tracks",
        tracks
          .map(
            (t, i) => `
        <div class="lf-row">
          <div class="rank">${i + 1}</div>
          <div class="meta"><div class="t">${esc(t.name)}</div><div class="a">${esc(
              t.artist && t.artist.name
            )}</div></div>
          <div class="plays">${fmt(t.playcount)} plays</div>
        </div>`
          )
          .join("")
      );
    } catch (e) {
      console.error(e);
      set("lf-tracks", errMsg("top tracks"));
    }
  }

  /* --- period toggle ------------------------------------------------------ */
  function initToggle() {
    const bar = $("lf-period");
    if (!bar) return;
    bar.addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-period]");
      if (!btn) return;
      bar.querySelectorAll("button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      loadTops(btn.dataset.period);
    });
  }

  /* --- boot --------------------------------------------------------------- */
  function boot() {
    if (!CFG.user) {
      document.querySelectorAll(".lf-section").forEach(
        (el) => (el.innerHTML = errMsg("music stats (missing Last.fm username)"))
      );
      return;
    }

    initToggle();

    if ($("lf-totals")) {
      set("lf-totals", skel(4));
      loadTotals();
    }
    if ($("lf-albums") || $("lf-artists") || $("lf-tracks")) {
      loadTops("1month"); // default period — matches the .active button in the page
    }
    if ($("lf-now") || $("lf-recent")) {
      set("lf-recent", skel(6));
      loadRecent();
      setInterval(loadRecent, RECENT_POLL_MS);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
