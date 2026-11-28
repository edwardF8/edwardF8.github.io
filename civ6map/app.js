(() => {
  "use strict";

  const DATA = (window.CIV6_WONDERS || []).concat(window.CIV6_CIVS || []);
  const CIV = "#efe2c2";
  const ERAS = ["Ancient", "Classical", "Medieval", "Renaissance", "Industrial", "Modern", "Atomic", "Information"];
  const ERA_COLORS = {
    Ancient: "#e7b75a", Classical: "#e07a4f", Medieval: "#d4566f", Renaissance: "#a274de",
    Industrial: "#5b8fd9", Modern: "#4fc3e0", Atomic: "#9ad35a", Information: "#f0e68c",
  };
  const NATURAL = "#2dd4bf";
  const YIELDS = {
    Faith: ["#d9ccff", "Faith"], Science: ["#6cb6ff", "Science"], Culture: ["#d58cff", "Culture"], Gold: ["#ffd166", "Gold"],
    Production: ["#ff9f43", "Production"], Food: ["#7bd389", "Food"], Amenity: ["#ffc6a5", "Amenity"], Housing: ["#a0c4ff", "Housing"],
    Tourism: ["#ff8fab", "Tourism"], Citizen: ["#e9ecef", "Population"], Envoy: ["#9bf6ff", "Envoys"], TradeRoute: ["#ffc078", "Trade Route"],
    Power: ["#ffe066", "Power"], Movement: ["#cfd8dc", "Movement"], Favor: ["#b5e48c", "Diplomatic Favor"], Strength: ["#ff6b6b", "Combat Strength"],
  };

  const byId = new Map(DATA.map((w) => [w.id, w]));
  const colorOf = (w) => (w.kind === "natural" ? NATURAL : w.kind === "civ" ? CIV : ERA_COLORS[w.era] || "#d6b25e");
  const byName = new Map(DATA.filter((w) => w.kind !== "civ").map((w) => [w.name, w]));
  // wonder name -> civs tied to it (reverse of civ.wonders)
  const civsOfWonder = new Map();
  for (const c of DATA.filter((w) => w.kind === "civ")) {
    for (const n of c.wonders || []) {
      if (!civsOfWonder.has(n)) civsOfWonder.set(n, []);
      civsOfWonder.get(n).push(c);
    }
  }
  const leaderNames = (c) => [...new Set((c.leaders || []).map((l) => l.name))].join(", ");

  const state = {
    kinds: new Set(["world", "natural", "civ"]),
    eras: new Set(ERAS),
    query: "",
    selected: null,
    visible: DATA.slice(),
  };

  const $ = (s, el = document) => el.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const isMobile = () => matchMedia("(max-width: 760px)").matches;
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch { /* ignore */ } },
  };
  const fandom = (url, w) => (url ? url.replace(/\/revision\/latest(\/[^?]*)?(\?|$)/, `/revision/latest/scale-to-width-down/${w}$2`) : "");

  /* ------------------------------------------------------------ map */
  const map = L.map("map", {
    zoomControl: false,
    worldCopyJump: true,
    minZoom: 2,
    maxZoom: 18,
    // smooth, continuous wheel / trackpad zoom
    zoomSnap: 0,
    zoomDelta: 1,
    wheelPxPerZoomLevel: 150,
    wheelDebounceTime: 20,
    zoomAnimationThreshold: 8,
    inertiaDeceleration: 2600,
    easeLinearity: 0.2,
    maxBounds: [[-86, -400], [86, 400]],
    maxBoundsViscosity: 0.85,
    attributionControl: true,
  });
  const WORLD = [[-48, -125], [66, 152]];
  const showWorld = (animate) => {
    const opts = { paddingTopLeft: [isMobile() ? 0 : 352, 20], paddingBottomRight: [20, 20], animate };
    if (animate) map.flyToBounds(WORLD, { ...opts, duration: 1 });
    else map.fitBounds(WORLD, opts);
  };
  showWorld(false);

  const esriAttr = "Tiles &copy; Esri &mdash; Esri, Maxar, Earthstar Geographics, USGS and the GIS User Community";
  const osmAttr = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';
  // keep extra tiles around and don't swap tiles mid-animation, so zooming doesn't flash blank squares
  const T = { maxZoom: 18, keepBuffer: 6, updateWhenZooming: false };
  const LAYERS = {
    satellite: () => L.layerGroup([
      L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", { ...T, attribution: esriAttr }),
      L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}", { ...T, opacity: 0.6, className: "labels" }),
    ]),
    night: () => L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", { ...T, subdomains: "abcd", attribution: osmAttr }),
    terrain: () => L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}", { ...T, attribution: esriAttr }),
    light: () => L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", { ...T, subdomains: "abcd", attribution: osmAttr }),
  };
  let baseLayer = null;
  function setLayer(name) {
    if (!LAYERS[name]) name = "satellite";
    if (baseLayer) map.removeLayer(baseLayer);
    baseLayer = LAYERS[name]().addTo(map);
    document.querySelectorAll(".layers button").forEach((b) => b.classList.toggle("on", b.dataset.layer === name));
    store.set("civ6map.layer", name);
  }
  setLayer(store.get("civ6map.layer") || "satellite");
  document.querySelectorAll(".layers button").forEach((b) => b.addEventListener("click", () => setLayer(b.dataset.layer)));
  $("#zoomIn").addEventListener("click", () => map.zoomIn());
  $("#zoomOut").addEventListener("click", () => map.zoomOut());
  $("#zoomWorld").addEventListener("click", () => showWorld(true));

  function zoomClass() {
    const z = map.getZoom();
    const c = map.getContainer().classList;
    c.toggle("z-far", z < 3.5);
    c.toggle("z-near", z >= 6);
  }
  map.on("zoomend", zoomClass);
  zoomClass();

  /* -------------------------------------------------------- markers */
  const markerLayer = L.layerGroup().addTo(map);
  const markers = new Map();
  for (const w of DATA) {
    const lat = Math.max(-84.6, Math.min(84.6, w.lat));
    const inner = w.kind === "civ" && w.icon
      ? `<span><img src="${esc(fandom(w.icon, 64))}" alt="" referrerpolicy="no-referrer"></span>`
      : "<span></span>";
    const sz = w.kind === "civ" ? 30 : 24;
    const icon = L.divIcon({
      className: "wm-wrap",
      html: `<div class="wm ${w.kind}${w.approx ? " approx" : ""}" style="--c:${colorOf(w)}">${inner}</div>`,
      iconSize: [sz, sz],
      iconAnchor: [sz / 2, sz / 2],
    });
    const m = L.marker([lat, w.lng], { icon, title: w.name, riseOnHover: true, keyboard: true, alt: w.name });
    const sub = w.kind === "world" ? `${w.era} Era · ${w.place}`
      : w.kind === "civ" ? `Civilization · ${leaderNames(w)}`
      : `Natural Wonder · ${w.place}`;
    m.bindTooltip(`<b>${esc(w.name)}</b><small>${esc(sub)}</small>`, {
      direction: "top", offset: [0, -12], className: `wtip ${w.kind}`, opacity: 1,
    });
    m.on("click", () => select(w.id, { fly: true }));
    markers.set(w.id, m);
  }
  function setSelectedMarker(id) {
    document.querySelectorAll(".wm.selected").forEach((el) => el.classList.remove("selected"));
    const m = markers.get(id);
    const el = m && m.getElement();
    if (el) {
      el.querySelector(".wm").classList.add("selected");
      m.setZIndexOffset(1000);
    }
    markers.forEach((mm, k) => k !== id && mm.setZIndexOffset(0));
  }

  /* Pan so the marker sits in the middle of the map area left visible by the panels. */
  function focusOn(w, zoom) {
    const lat = Math.max(-84.6, Math.min(84.6, w.lat));
    const ll = L.latLng(lat, w.lng);
    const z = zoom ?? map.getZoom();
    let dx = 0, dy = 0;
    if (isMobile()) {
      dy = window.innerHeight * 0.72 / 2 - 10;
    } else {
      const sidebarAway = window.innerWidth <= 1180 && document.body.classList.contains("detail-open");
      const left = sidebarAway ? 0 : 340 + 12;
      const right = 440 + 12;
      dx = (right - left) / 2;
    }
    const p = map.project(ll, z).add([dx, dy]);
    return { center: map.unproject(p, z), zoom: z };
  }
  /* How close to fly for each place: buildings get street level on the satellite map,
     big landscapes and civilizations get a regional view. */
  const ZOOM_OVERRIDES = {
    // world wonders that are large, approximate or at the map edge
    "Panama Canal": 10, "Ruhr Valley": 11, "Amundsen-Scott Research Station": 4, "Hanging Gardens": 14,
    "Great Library": 14, "Golden Gate Bridge": 14, "Broadway": 15, "Pyramids": 15, "Petra": 15, "Machu Picchu": 15.5,
    "Forbidden City": 15, "Angkor Wat": 15, "Venetian Arsenal": 15, "Colossus": 15, "Great Lighthouse": 15.5,
    // natural wonders, sized to the feature
    "Bermuda Triangle": 5, "Great Barrier Reef": 7, "Pantanal": 7, "Païtiti": 7, "Galápagos Islands": 8,
    "Ubsunur Hollow": 8, "Kakadu": 8, "Dead Sea": 9, "Sahara el Beyda": 10, "Eye of the Sahara": 10,
    "Hạ Long Bay": 11, "Lysefjord": 11, "Eyjafjallajökull": 11, "Mount Kilimanjaro": 11, "Yosemite": 11.5,
    "Torres del Paine": 11.5, "Piopiotahi": 11.5, "Mount Everest": 12, "Chocolate Hills": 12, "Crater Lake": 12,
    "Zhangye Danxia": 12, "Mount Roraima": 12, "Tsingy de Bemaraha": 12, "Gobustan": 13, "Matterhorn": 13,
    "Mount Vesuvius": 13, "Uluru": 13, "Cliffs of Dover": 13, "Lake Retba": 13, "Mato Tipila": 14.5,
    "Pinnacles": 14.5, "Vinland": 15.5, "Pamukkale": 15, "Giant's Causeway": 15.5, "Delicate Arch": 16,
    "Fountain of Youth": 16, "Ik-Kil": 17,
  };
  const zoomFor = (w) => ZOOM_OVERRIDES[w.name] ?? (w.kind === "civ" ? 6 : w.kind === "natural" ? 11 : 16.5);

  function flyToWonder(w) {
    const target = Math.min(zoomFor(w), map.getMaxZoom());
    const { center, zoom } = focusOn(w, target);
    const from = map.getZoom();
    const dist = map.getCenter().distanceTo(center) / 1000; // km
    // close by and already at the right zoom: a short glide instead of a full flight
    if (Math.abs(from - zoom) < 0.3 && dist < 50) {
      map.panTo(center, { animate: true, duration: 0.6, easeLinearity: 0.25 });
      return;
    }
    const duration = Math.min(3.2, 1.1 + Math.abs(from - zoom) * 0.11 + Math.min(dist, 8000) / 8000);
    map.flyTo(center, zoom, { duration, easeLinearity: 0.15 });
  }

  /* --------------------------------------------------------- filters */
  const erasEl = $("#eras");
  erasEl.innerHTML = ERAS.filter((e) => DATA.some((w) => w.era === e))
    .map((e) => `<button class="era-chip on" data-era="${e}" style="--c:${ERA_COLORS[e]}" aria-pressed="true"><i></i>${e}</button>`)
    .join("");
  erasEl.addEventListener("click", (ev) => {
    const b = ev.target.closest(".era-chip");
    if (!b) return;
    const era = b.dataset.era;
    const all = state.eras.size === ERAS.length;
    if (ev.altKey || ev.metaKey || all) {
      // first click isolates an era; alt/cmd-click always isolates
      state.eras = new Set([era]);
    } else if (state.eras.has(era)) {
      state.eras.delete(era);
      if (!state.eras.size) state.eras = new Set(ERAS);
    } else {
      state.eras.add(era);
    }
    if (!state.kinds.has("world")) state.kinds.add("world");
    syncFilterUI();
    apply();
  });
  document.querySelectorAll(".kind").forEach((b) =>
    b.addEventListener("click", () => {
      const k = b.dataset.kind;
      if (state.kinds.has(k)) state.kinds.delete(k);
      else state.kinds.add(k);
      if (!state.kinds.size) state.kinds = new Set(["world", "natural"]);
      syncFilterUI();
      apply();
    })
  );
  function syncFilterUI() {
    document.querySelectorAll(".era-chip").forEach((b) => {
      const on = state.eras.has(b.dataset.era) && state.kinds.has("world");
      b.classList.toggle("on", on);
      b.setAttribute("aria-pressed", on);
    });
    document.querySelectorAll(".kind").forEach((b) => {
      const on = state.kinds.has(b.dataset.kind);
      b.classList.toggle("on", on);
      b.setAttribute("aria-pressed", on);
    });
  }
  const searchEl = $("#search");
  searchEl.addEventListener("input", () => { state.query = searchEl.value.trim().toLowerCase(); apply(); });
  const norm = (s) => String(s || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const hay = new Map(DATA.map((w) => [w.id, norm([
    w.name, w.real, w.place, w.era, w.expansion, w.adjective, w.capital, w.dlc,
    w.kind === "natural" ? "natural" : w.kind === "civ" ? "civilization civ leader" : "world wonder",
    ...(w.leaders || []).map((l) => `${l.name} ${l.persona || ""}`),
    ...(w.uniques || []).map((u) => u.name),
    ...(w.leaders || []).flatMap((l) => (l.uniques || []).map((u) => u.name)),
  ].join(" "))]));

  function apply() {
    const q = norm(state.query);
    state.visible = DATA.filter((w) => {
      if (!state.kinds.has(w.kind)) return false;
      if (w.kind === "world" && !state.eras.has(w.era)) return false;
      if (q && !q.split(/\s+/).every((t) => hay.get(w.id).includes(t))) return false;
      return true;
    });
    const vis = new Set(state.visible.map((w) => w.id));
    markers.forEach((m, id) => {
      const on = vis.has(id);
      if (on && !markerLayer.hasLayer(m)) markerLayer.addLayer(m);
      if (!on && markerLayer.hasLayer(m)) markerLayer.removeLayer(m);
    });
    if (state.selected) setSelectedMarker(state.selected);
    renderList();
    const total = DATA.length, n = state.visible.length;
    $("#showing").textContent = n === total ? `Showing all ${total}` : `Showing ${n} of ${total}`;
  }
  $("#countWorld").textContent = DATA.filter((w) => w.kind === "world").length;
  $("#countNatural").textContent = DATA.filter((w) => w.kind === "natural").length;
  $("#countCiv").textContent = DATA.filter((w) => w.kind === "civ").length;

  /* ------------------------------------------------------------ list */
  const listEl = $("#list");
  function itemHTML(w) {
    const src = w.kind === "civ" ? w.icon : w.civ && w.civ.icon;
    const icon = src ? `<img src="${esc(fandom(src, 80))}" alt="" loading="lazy" referrerpolicy="no-referrer">` : "";
    const sub = w.kind === "civ" ? leaderNames(w) : w.place;
    return `<button class="item${state.selected === w.id ? " active" : ""}${w.kind === "civ" ? " civ" : ""}" data-id="${w.id}" style="--c:${colorOf(w)}">
      <span class="item-icon">${icon}</span>
      <span class="item-text"><span class="item-name">${esc(w.name)}</span><span class="item-place">${esc(sub)}</span></span>
    </button>`;
  }
  function renderList() {
    const groups = [];
    for (const era of ERAS) {
      const items = state.visible.filter((w) => w.kind === "world" && w.era === era);
      if (items.length) groups.push({ title: `${era} Era`, color: ERA_COLORS[era], items });
    }
    const nat = state.visible.filter((w) => w.kind === "natural");
    if (nat.length) groups.push({ title: "Natural Wonders", color: NATURAL, items: nat.sort((a, b) => a.name.localeCompare(b.name)) });
    const civs = state.visible.filter((w) => w.kind === "civ");
    if (civs.length) groups.push({ title: "Civilizations", color: CIV, items: civs.sort((a, b) => a.name.localeCompare(b.name)) });
    listEl.innerHTML = groups.length
      ? groups.map((g) => `<h4 class="group-title" style="--c:${g.color}">${g.title} <small>${g.items.length}</small></h4>${g.items.map(itemHTML).join("")}`).join("")
      : `<div class="empty">Nothing matches “${esc(state.query)}”.</div>`;
    // order used by prev/next follows the list
    state.order = groups.flatMap((g) => g.items);
  }
  listEl.addEventListener("click", (ev) => {
    const b = ev.target.closest(".item");
    if (!b) return;
    select(b.dataset.id, { fly: "hard" });
    if (isMobile()) document.body.classList.remove("sidebar-open");
  });

  $("#randomBtn").addEventListener("click", () => {
    const pool = (state.order && state.order.length ? state.order : DATA).filter((w) => w.id !== state.selected);
    const w = pool[Math.floor(Math.random() * pool.length)];
    if (w) {
      select(w.id, { fly: "hard" });
      if (isMobile()) document.body.classList.remove("sidebar-open");
    }
  });

  /* ---------------------------------------------------------- detail */
  const detail = $("#detail");
  const body = $("#detailBody");

  function fmt(text) {
    let s = esc(text);
    s = s.replace(/\{(\w+)\}(s?)/g, (_, k, pl) => {
      const y = YIELDS[k];
      return y ? `<span class="y" style="--y:${y[0]}"><i></i>${y[1]}${pl && !/s$/.test(y[1]) ? "s" : ""}</span>` : k + pl;
    });
    s = s.replace(/\[GS\]/g, '<span class="xp gs" title="Gathering Storm rules">GS</span>');
    s = s.replace(/\[R&amp;F\]/g, '<span class="xp rf" title="Rise and Fall rules">R&amp;F</span>');
    return s;
  }
  const ICONS = {
    wiki: '<svg viewBox="0 0 24 24"><path d="M4 19.5V5a2 2 0 0 1 2-2h12v16H6a2 2 0 0 0-2 2v-1.5zM8 7h6M8 11h6"/></svg>',
    civ: '<svg viewBox="0 0 24 24"><path d="m12 2 9 5v10l-9 5-9-5V7z"/><path d="m12 22V12M3 7l9 5 9-5"/></svg>',
    pin: '<svg viewBox="0 0 24 24"><path d="M12 22s7-6.2 7-12a7 7 0 1 0-14 0c0 5.8 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/></svg>',
    play: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="m10 8.5 5.5 3.5-5.5 3.5z"/></svg>',
  };

  function coordStr(w) {
    const la = Math.abs(w.lat).toFixed(3) + "°" + (w.lat >= 0 ? "N" : "S");
    const lo = Math.abs(w.lng).toFixed(3) + "°" + (w.lng >= 0 ? "E" : "W");
    return `${la}, ${lo}`;
  }

  /* --- civilization-specific sections --- */
  function uniqueCard(u) {
    const meta = [u.kind && u.kind !== "Unique" ? `Unique ${u.kind.toLowerCase()}` : "Unique", u.replaces && `replaces ${u.replaces}`].filter(Boolean).join(" · ");
    const desc = (u.desc || "").split("\n").filter(Boolean);
    return `<div class="uniq">
      ${u.icon ? `<img src="${esc(fandom(u.icon, 96))}" alt="" loading="lazy" referrerpolicy="no-referrer">` : `<span class="uniq-ph"></span>`}
      <div>
        <div class="uniq-name">${u.url ? `<a href="${esc(u.url)}" target="_blank" rel="noopener">${esc(u.name)}</a>` : esc(u.name)}</div>
        <div class="uniq-meta">${esc(meta)}</div>
        ${desc.length ? `<div class="uniq-desc">${desc.slice(0, 4).map(fmt).join("<br>")}</div>` : ""}
      </div>
    </div>`;
  }
  function leaderCard(l) {
    return `<article class="leader">
      <header>
        ${l.portrait ? `<img class="portrait" src="${esc(fandom(l.portrait, 160))}" alt="${esc(l.name)}" loading="lazy" referrerpolicy="no-referrer">` : ""}
        <div>
          <h4>${l.url ? `<a href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.name)}</a>` : esc(l.name)}</h4>
          ${l.persona ? `<span class="persona">${esc(l.persona)} persona</span>` : ""}
          ${l.dlc ? `<span class="leader-dlc">${esc(l.dlc)}</span>` : ""}
        </div>
      </header>
      ${l.quote ? `<p class="leader-quote">“${esc(l.quote)}”</p>` : ""}
      ${l.ability ? `<div class="trait"><b>${esc(l.ability)}</b><span>Leader ability</span><p>${fmt(l.abilityDesc).replace(/\n/g, "<br>")}</p></div>` : ""}
      ${l.agenda ? `<div class="trait agenda"><b>${esc(l.agenda)}</b><span>Agenda</span><p>${fmt(l.agendaDesc)}</p></div>` : ""}
      ${(l.uniques || []).length ? `<div class="leader-uniques">${l.uniques.map(uniqueCard).join("")}</div>` : ""}
    </article>`;
  }
  function civSections(w) {
    return `
      <section class="sec">
        <h3>Civilization Ability</h3>
        ${w.ability ? `<div class="trait big"><b>${esc(w.ability)}</b><p>${fmt(w.abilityDesc).replace(/\n/g, "<br>")}</p></div>` : `<p class="no-photos">—</p>`}
      </section>
      ${(w.uniques || []).length ? `<section class="sec"><h3>Unique Units &amp; Infrastructure</h3><div class="uniqs">${w.uniques.map(uniqueCard).join("")}</div></section>` : ""}
      <section class="sec">
        <h3>Leaders <small class="count">${(w.leaders || []).length}</small></h3>
        <div class="leaders">${(w.leaders || []).map(leaderCard).join("")}</div>
      </section>`;
  }
  function chip(x) {
    const src = x.kind === "civ" ? x.icon : x.civ && x.civ.icon;
    return `<button class="chip" data-go="${x.id}" style="--c:${colorOf(x)}">${src ? `<img src="${esc(fandom(src, 64))}" alt="" referrerpolicy="no-referrer">` : ""}${esc(x.name)}</button>`;
  }
  function relatedSection(w) {
    const items = w.kind === "civ" ? (w.wonders || []).map((n) => byName.get(n)).filter(Boolean) : civsOfWonder.get(w.name) || [];
    if (!items.length) return "";
    const title = w.kind === "civ" ? `Wonders of ${w.adjective || w.name} history` : "Linked civilizations";
    return `<section class="sec"><h3>${esc(title)}</h3><div class="chips">${items.map(chip).join("")}</div></section>`;
  }

  function render(w) {
    const c = colorOf(w);
    const civ = w.civ || {};
    const arts = [];
    if (civ.splash) arts.push({ src: fandom(civ.splash, 900), label: "Completion art" });
    if (civ.render) arts.push({ src: fandom(civ.render, 900), label: "In-game model" });
    const photos = w.photos || [];
    const hero = arts[0] || (photos[0] && { src: photos[0].src, label: "Photograph" });
    const isCiv = w.kind === "civ";
    const kicker = w.kind === "world" ? `${w.era} Era · World Wonder` : isCiv ? "Civilization" : "Natural Wonder";
    const lead = isCiv ? (w.leaders || []).find((l) => l.quote) : null;
    const quote = isCiv ? lead && { text: lead.quote, by: lead.name + (lead.persona ? ` (${lead.persona})` : "") }
      : (window.CIV6_QUOTES || {})[w.name];
    const iconSrc = isCiv ? w.icon : civ.icon;
    const wikiPage = isCiv ? w.civUrl : civ.page;

    const order = state.order && state.order.length ? state.order : DATA;
    const idx = order.findIndex((x) => x.id === w.id);
    const prev = idx >= 0 ? order[(idx - 1 + order.length) % order.length] : null;
    const next = idx >= 0 ? order[(idx + 1) % order.length] : null;

    const badges = [];
    if (w.kind === "world") badges.push(`<span class="badge era" style="--c:${c}">${esc(w.era)} Era</span>`);
    if (w.scenario) badges.push(`<span class="badge scenario">${esc(w.scenario)}</span>`);
    if (w.expansion) badges.push(`<span class="badge">${esc(w.expansion)}</span>`);
    if (w.cost) badges.push(`<span class="badge"><b>${esc(w.cost)}</b> ${fmt("{Production}")}</span>`);

    const kv = [];
    if (w.req) kv.push(["Requires", fmt(w.req)]);
    if (w.placement) kv.push(["Placement", fmt(w.placement)]);
    if (w.size) kv.push(["Size", esc(w.size)]);
    if (w.notes) kv.push(["Notes", fmt(w.notes).replace(/\n/g, "<br>")]);

    const gallery = photos.length
      ? `<div class="gallery">${photos.map((p, i) => `<button data-photo="${i}" aria-label="Open photo ${i + 1}">
            <img src="${esc(i === 0 ? p.src : p.small || p.src)}" alt="${esc(p.caption || w.name)}" loading="lazy" referrerpolicy="no-referrer">
            ${i === 0 && p.caption ? `<span class="cap">${esc(p.caption)}</span>` : ""}
          </button>`).join("")}</div>
         <p class="gallery-note">Photos from Wikimedia Commons · click to enlarge</p>`
      : `<p class="no-photos">No photos found — try the Wikipedia link below.</p>`;

    const gmaps = `https://www.google.com/maps/search/?api=1&query=${w.lat},${w.lng}`;
    const yt = `https://www.youtube.com/results?search_query=${encodeURIComponent(
      isCiv ? `Civilization VI First Look ${w.name}` : `Civilization VI ${w.name} ${w.kind === "world" ? "wonder movie" : "natural wonder"}`)}`;

    body.innerHTML = `
      <div class="hero">
        ${hero ? `<img class="hero-img" id="heroImg" src="${esc(hero.src)}" alt="${esc(w.name)}" referrerpolicy="no-referrer">` : ""}
        <div class="hero-top">
          ${arts.length > 1
            ? `<div class="art-tabs" role="tablist">${arts.map((a, i) => `<button class="${i === 0 ? "on" : ""}" data-art="${i}">${a.label}</button>`).join("")}</div>`
            : hero ? `<span class="art-label">${arts.length ? "Civilization VI · " + arts[0].label : "Photograph"}</span>` : ""}
          <button class="icon-btn" id="closeDetail" aria-label="Close details">✕</button>
        </div>
        <div class="hero-title">
          ${iconSrc ? `<img class="civ-icon${isCiv ? " emblem" : ""}" style="--c:${c}" src="${esc(fandom(iconSrc, 160))}" alt="" referrerpolicy="no-referrer">` : ""}
          <div>
            <span class="kicker ${w.kind}" style="--c:${c}"><i></i>${kicker}</span>
            <h2>${esc(w.name)}</h2>
            <div class="real">${w.real && w.real !== w.name ? esc(w.real) + " · " : ""}${esc(w.place)}</div>
          </div>
        </div>
      </div>
      ${quote ? `
      <figure class="epigraph" style="--c:${c}">
        <blockquote>${esc(quote.text).replace(/\n/g, "<br>")}</blockquote>
        <figcaption>
          <span>— ${esc(quote.by || "Unknown")}</span>
          ${"speechSynthesis" in window ? `<button class="speak" id="speakQuote" aria-label="Read the quote aloud" title="Read aloud"><svg viewBox="0 0 24 24"><path d="M11 5 6 9H3v6h3l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M18.5 5.5a9 9 0 0 1 0 13"/></svg></button>` : ""}
        </figcaption>
      </figure>` : ""}
      <div class="d-body">
        <div class="badges">${badges.join("")}</div>

        ${isCiv ? civSections(w) : `
        <section class="sec">
          <h3>In Civilization VI</h3>
          <ul class="effects">${(w.effects || []).map((e) => `<li>${fmt(e)}</li>`).join("")}</ul>
          ${kv.length ? `<dl class="kv">${kv.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("")}</dl>` : ""}
        </section>`}

        <section class="sec">
          <h3>The Real Place</h3>
          ${gallery}
        </section>

        <section class="sec history">
          <h3>History</h3>
          <p>${esc(w.history)}</p>
          <div class="facts">
            <div class="fact"><span>${w.kind === "world" ? "Built" : isCiv ? "Era" : "Age"}</span><b>${esc(w.when || "—")}</b></div>
            <div class="fact"><span>Coordinates</span><b>${coordStr(w)}</b></div>
            ${isCiv && w.capital ? `<div class="fact wide"><span>Capital marked</span><b>${esc(w.capital)}</b></div>` : ""}
            <div class="fact wide"><span>Location</span><b>${esc(w.place)}</b></div>
          </div>
          ${w.approx ? `<div class="approx-note">This marker is approximate — the site is legendary, lost, or its exact location is debated.</div>` : ""}
          ${Math.abs(w.lat) > 84.6 ? `<div class="approx-note">The marker sits at the edge of the map; the real site is at ${coordStr(w)}, beyond what a flat web map can show.</div>` : ""}
        </section>

        ${relatedSection(w)}

        <div class="links">
          ${w.wikiUrl ? `<a href="${esc(w.wikiUrl)}" target="_blank" rel="noopener">${ICONS.wiki}Wikipedia</a>` : ""}
          ${wikiPage ? `<a href="${esc(wikiPage)}" target="_blank" rel="noopener">${ICONS.civ}Civ VI Wiki</a>` : ""}
          <a href="${gmaps}" target="_blank" rel="noopener">${ICONS.pin}Google Maps</a>
          <a href="${yt}" target="_blank" rel="noopener">${ICONS.play}Watch in-game</a>
        </div>

        <div class="pager">
          ${prev ? `<button data-go="${prev.id}"><small>‹ Previous</small><span>${esc(prev.name)}</span></button>` : ""}
          ${next ? `<button data-go="${next.id}"><small>Next ›</small><span>${esc(next.name)}</span></button>` : ""}
        </div>

        <p class="credits">Game data and art: <a href="${esc(civ.page || "https://civilization.fandom.com")}" target="_blank" rel="noopener">Civilization Wiki</a> (Civilization VI © Firaxis Games / 2K). Photos: Wikimedia Commons contributors, credited in the photo viewer.</p>
      </div>`;

    body.scrollTop = 0;
    body.classList.remove("swap");
    void body.offsetWidth;
    body.classList.add("swap");

    $("#closeDetail", body).addEventListener("click", closeDetail);
    const speakBtn = $("#speakQuote", body);
    if (speakBtn) speakBtn.addEventListener("click", () => speak(quote, speakBtn));
    body.querySelectorAll("[data-art]").forEach((b) =>
      b.addEventListener("click", () => {
        body.querySelectorAll("[data-art]").forEach((x) => x.classList.toggle("on", x === b));
        const img = $("#heroImg", body);
        img.style.animation = "none";
        img.src = arts[+b.dataset.art].src;
        void img.offsetWidth;
        img.style.animation = "";
      })
    );
    body.querySelectorAll("[data-photo]").forEach((b) => b.addEventListener("click", () => openLightbox(w, +b.dataset.photo)));
    body.querySelectorAll("[data-go]").forEach((b) => b.addEventListener("click", () => select(b.dataset.go, { fly: "hard" })));
    // hide broken images gracefully
    body.querySelectorAll("img").forEach((img) => img.addEventListener("error", () => {
      const btn = img.closest(".gallery button");
      if (btn) btn.remove(); else img.style.visibility = "hidden";
    }, { once: true }));
  }

  /* Read the quote aloud, in the spirit of the in-game narration. */
  function speak(q, btn) {
    const synth = window.speechSynthesis;
    if (synth.speaking) {
      synth.cancel();
      return;
    }
    const u = new SpeechSynthesisUtterance(`${q.text.replace(/\n/g, " ")} ... ${q.by}`);
    const voices = synth.getVoices();
    u.voice = voices.find((v) => /en-GB/i.test(v.lang) && /male|daniel|arthur|george/i.test(v.name))
      || voices.find((v) => /en-GB/i.test(v.lang)) || voices.find((v) => /^en/i.test(v.lang)) || null;
    u.rate = 0.88;
    u.pitch = 0.85;
    u.onstart = () => btn.classList.add("on");
    u.onend = u.onerror = () => btn.classList.remove("on");
    synth.speak(u);
  }

  function select(id, { fly = "hard", push = true } = {}) {
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();
    const w = byId.get(id);
    if (!w) return;
    // make sure the wonder is visible even if filtered out
    if (!state.visible.some((x) => x.id === id)) {
      state.kinds.add(w.kind);
      if (w.kind === "world") state.eras.add(w.era);
      state.query = "";
      searchEl.value = "";
      syncFilterUI();
      apply();
    }
    state.selected = id;
    render(w);
    detail.hidden = false;
    document.body.classList.add("detail-open");
    setSelectedMarker(id);
    listEl.querySelectorAll(".item").forEach((el) => el.classList.toggle("active", el.dataset.id === id));
    const active = listEl.querySelector(`.item[data-id="${CSS.escape(id)}"]`);
    if (active && !isMobile()) active.scrollIntoView({ block: "nearest", behavior: "smooth" });
    if (fly) flyToWonder(w, fly);
    if (push && location.hash.slice(1) !== id) history.replaceState(null, "", "#" + id);
  }
  function closeDetail() {
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();
    detail.hidden = true;
    document.body.classList.remove("detail-open");
    state.selected = null;
    setSelectedMarker(null);
    listEl.querySelectorAll(".item.active").forEach((el) => el.classList.remove("active"));
    history.replaceState(null, "", location.pathname + location.search);
  }

  /* -------------------------------------------------------- lightbox */
  const lb = $("#lightbox"), lbImg = $("#lbImg"), lbCap = $("#lbCap");
  let lbState = null;
  function openLightbox(w, i) {
    lbState = { w, i };
    lb.hidden = false;
    showPhoto();
  }
  function showPhoto() {
    const { w, i } = lbState;
    const p = w.photos[i];
    lbImg.src = p.src;
    lbImg.alt = p.caption || w.name;
    const credit = [p.credit && `Photo: ${esc(p.credit)}`, p.license && esc(p.license)].filter(Boolean).join(" · ");
    lbCap.innerHTML = `${esc(p.caption || w.name)}<small>${credit}${credit ? " · " : ""}<a href="${esc(p.page)}" target="_blank" rel="noopener">Wikimedia Commons ↗</a> · ${i + 1} / ${w.photos.length}</small>`;
  }
  function stepPhoto(d) {
    if (!lbState) return;
    const n = lbState.w.photos.length;
    lbState.i = (lbState.i + d + n) % n;
    showPhoto();
  }
  function closeLightbox() { lb.hidden = true; lbState = null; lbImg.removeAttribute("src"); }
  $("#lbClose").addEventListener("click", closeLightbox);
  $("#lbPrev").addEventListener("click", () => stepPhoto(-1));
  $("#lbNext").addEventListener("click", () => stepPhoto(1));
  lb.addEventListener("click", (e) => { if (e.target === lb) closeLightbox(); });

  /* -------------------------------------------------------- keyboard */
  document.addEventListener("keydown", (e) => {
    if (!lb.hidden) {
      if (e.key === "Escape") closeLightbox();
      else if (e.key === "ArrowLeft") stepPhoto(-1);
      else if (e.key === "ArrowRight") stepPhoto(1);
      return;
    }
    const typing = /input|textarea/i.test(document.activeElement && document.activeElement.tagName);
    if (e.key === "/" && !typing) { e.preventDefault(); searchEl.focus(); return; }
    if (e.key === "Escape") {
      if (typing) { searchEl.blur(); return; }
      if (!detail.hidden) closeDetail();
      return;
    }
    if (typing) {
      if (e.key === "Enter" && state.order && state.order.length) select(state.order[0].id, { fly: "hard" });
      return;
    }
    if (state.selected && (e.key === "ArrowRight" || e.key === "ArrowLeft" || e.key === "j" || e.key === "k")) {
      const btns = body.querySelectorAll("[data-go]");
      const forward = e.key === "ArrowRight" || e.key === "j";
      const b = forward ? btns[btns.length - 1] : btns[0];
      if (b) select(b.dataset.go, { fly: "hard" });
    }
  });

  /* ---------------------------------------------------------- mobile */
  $("#sidebarOpen").addEventListener("click", () => document.body.classList.add("sidebar-open"));
  $("#sidebarClose").addEventListener("click", () => document.body.classList.remove("sidebar-open"));

  /* ------------------------------------------------------------ boot */
  apply();
  const initial = decodeURIComponent(location.hash.slice(1));
  if (byId.has(initial)) setTimeout(() => select(initial, { fly: "hard", push: false }), 300);
  window.addEventListener("hashchange", () => {
    const id = decodeURIComponent(location.hash.slice(1));
    if (byId.has(id) && id !== state.selected) select(id, { fly: "hard", push: false });
  });
})();
