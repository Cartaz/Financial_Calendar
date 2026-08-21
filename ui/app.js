"use strict";

const state = {
  bridge: null,
  initial: null,
  activeSource: "ig",
  sources: new Map(),
  events: [],
  sortKey: null,
  sortDirection: "asc",
  refreshing: new Set(),
  logs: [],
  requestSerial: 0,
  autoRefreshMinutes: 15,
  freshnessTimer: null,
};

const els = {
  app: document.getElementById("app"),
  appName: document.getElementById("app-name"),
  appDescription: document.getElementById("app-description"),
  connectionState: document.getElementById("connection-state"),
  connectionLabel: document.getElementById("connection-label"),
  sourceTabs: [...document.querySelectorAll(".source-tab")],
  filters: document.getElementById("filters"),
  date: document.getElementById("filter-date"),
  region: document.getElementById("filter-region"),
  impact: document.getElementById("filter-impact"),
  timezone: document.getElementById("filter-timezone"),
  autoRefresh: document.getElementById("auto-refresh"),
  refreshSource: document.getElementById("refresh-source"),
  refreshAll: document.getElementById("refresh-all"),
  sourceKicker: document.getElementById("source-kicker"),
  sourceTitle: document.getElementById("source-title"),
  sourceDescription: document.getElementById("source-description"),
  sourceStatus: document.getElementById("source-status"),
  sourceStatusLabel: document.getElementById("source-status-label"),
  activityLine: document.getElementById("activity-line"),
  activityLabel: document.getElementById("activity-label"),
  errorBanner: document.getElementById("error-banner"),
  errorMessage: document.getElementById("error-message"),
  errorDetailsWrap: document.getElementById("error-details-wrap"),
  errorDetails: document.getElementById("error-details"),
  dismissError: document.getElementById("dismiss-error"),
  tableHead: document.getElementById("table-head"),
  tableBody: document.getElementById("table-body"),
  emptyState: document.getElementById("empty-state"),
  eventCount: document.getElementById("event-count"),
  lastRefresh: document.getElementById("last-refresh"),
  freshnessLabel: document.getElementById("freshness-label"),
  logCount: document.getElementById("log-count"),
  logViewer: document.getElementById("log-viewer"),
  copyLog: document.getElementById("copy-log"),
  toastRegion: document.getElementById("toast-region"),
};

function bridgeCall(method, ...args) {
  return new Promise((resolve, reject) => {
    try {
      state.bridge[method](...args, (result) => resolve(result));
    } catch (error) {
      reject(error);
    }
  });
}

function sourceState(sourceKey = state.activeSource) {
  return state.sources.get(sourceKey);
}

function normalizeList(value) {
  return Array.isArray(value) ? value : [];
}

function impactLabel(value) {
  return {
    ALL: "Tutti",
    HIGH: "Alto",
    MID: "Medio",
    LOW: "Basso",
  }[value] || value;
}

function regionLabel(value) {
  return value === "ALL" ? "Tutte le aree" : value;
}

function formatOffset(offset) {
  const sign = offset >= 0 ? "+" : "-";
  const absolute = Math.abs(offset);
  const hours = Math.floor(absolute);
  const minutes = Math.round((absolute - hours) * 60);
  return `UTC${sign}${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

function localTimezoneName() {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
}

function currentTimezoneSpec() {
  const selected = els.timezone.value || "local";
  return selected === "local" ? localTimezoneName() : selected;
}

function calendarDateToBackend(value) {
  if (!value) return "";
  const parts = value.split("-");
  if (parts.length !== 3) return "";
  return `${parts[2]}/${parts[1]}/${parts[0]}`;
}

function buildSelect(select, values, labeler) {
  select.replaceChildren();
  for (const value of values) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = labeler(value);
    select.append(option);
  }
}

function ensureSelectValue(select, value, label = value) {
  if (!value) return;
  const exists = [...select.options].some((option) => option.value === value);
  if (exists) return;
  const option = document.createElement("option");
  option.value = value;
  option.textContent = label;
  select.append(option);
}

function buildTimezoneSelect(preference = "local") {
  els.timezone.replaceChildren();
  const localZone = localTimezoneName();

  const local = document.createElement("option");
  local.value = "local";
  local.textContent = `Locale (${localZone})`;
  els.timezone.append(local);

  const namedZones = [
    "UTC",
    "Europe/Rome",
    "Europe/London",
    "America/New_York",
    "America/Chicago",
    "America/Los_Angeles",
    "Asia/Tokyo",
    "Asia/Shanghai",
    "Asia/Hong_Kong",
    "Asia/Singapore",
    "Asia/Kolkata",
    "Australia/Sydney",
    "Pacific/Auckland",
  ];

  for (const zone of namedZones) {
    const option = document.createElement("option");
    option.value = zone;
    option.textContent = zone;
    els.timezone.append(option);
  }

  for (let offset = -12; offset <= 14; offset += 0.5) {
    if (offset === 0) continue;
    const spec = formatOffset(offset);
    const option = document.createElement("option");
    option.value = spec;
    option.textContent = `${spec} (fisso)`;
    els.timezone.append(option);
  }

  ensureSelectValue(els.timezone, preference);
  els.timezone.value = preference || "local";
  if (!els.timezone.value) els.timezone.value = "local";
}

function buildAutoRefreshSelect(selectedMinutes) {
  els.autoRefresh.replaceChildren();
  const options = normalizeList(state.initial?.auto_refresh_options);
  for (const raw of options) {
    const minutes = Number(raw);
    if (!Number.isFinite(minutes)) continue;
    const option = document.createElement("option");
    option.value = String(minutes);
    option.textContent = minutes === 0 ? "Manuale" : `${minutes} min`;
    els.autoRefresh.append(option);
  }
  const selected = String(Number(selectedMinutes));
  els.autoRefresh.value = selected;
  if (!els.autoRefresh.value) els.autoRefresh.value = "15";
  state.autoRefreshMinutes = Number(els.autoRefresh.value) || 0;
}

function setConnectionReady(version) {
  els.connectionState.classList.add("is-ready");
  els.connectionLabel.textContent = `Backend connesso · v${version}`;
}

function setConnectionError(message) {
  els.connectionState.classList.remove("is-ready");
  els.connectionLabel.textContent = message;
}

function refreshDate(source) {
  const value = source?.last_refresh_iso || "";
  if (!value) return null;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function freshnessAgeMinutes(source) {
  const parsed = refreshDate(source);
  if (!parsed) return null;
  return Math.max(0, (Date.now() - parsed.getTime()) / 60000);
}

function freshnessText(source) {
  const age = freshnessAgeMinutes(source);
  if (age === null) return "nessun aggiornamento";
  if (age < 1.5) return "adesso";
  if (age < 60) return `${Math.floor(age)} min fa`;
  if (age < 24 * 60) return `${Math.floor(age / 60)} h fa`;
  return `${Math.floor(age / (24 * 60))} g fa`;
}

function freshnessThresholdMinutes() {
  return state.autoRefreshMinutes > 0
    ? Math.max(15, state.autoRefreshMinutes * 2)
    : 60;
}

function sourceIsStale(source) {
  const age = freshnessAgeMinutes(source);
  return age !== null && age > freshnessThresholdMinutes();
}

function sourceFreshnessSummary(source) {
  if (!source || !refreshDate(source)) return "In attesa dati";
  const ageText = freshnessText(source);
  if (source.data_origin === "cache") return `Salvati · ${ageText}`;
  if (sourceIsStale(source)) return `Non recenti · ${ageText}`;
  return `Aggiornati · ${ageText}`;
}

function updateSourceTabs() {
  for (const tab of els.sourceTabs) {
    const sourceKey = tab.dataset.source;
    const selected = sourceKey === state.activeSource;
    tab.setAttribute("aria-pressed", String(selected));
    const freshness = tab.querySelector(".source-freshness");
    if (freshness) freshness.textContent = sourceFreshnessSummary(sourceState(sourceKey));
  }
}

function applySourceFilters() {
  const source = sourceState();
  if (!source) return;
  els.region.value = source.selected_region || "ALL";
  els.impact.value = source.selected_impact || "ALL";
}

function applySourceSort() {
  const source = sourceState();
  state.sortKey = source?.sort_key || null;
  state.sortDirection = source?.sort_direction === "desc" ? "desc" : "asc";
}

function updateSourceHeader() {
  const source = sourceState();
  if (!source) return;
  els.sourceKicker.textContent = source.key === "ig" ? "FOREXFACTORY" : "FXSTREET";
  els.sourceTitle.textContent = source.name;
  els.sourceDescription.textContent = source.description;
  els.lastRefresh.textContent = source.last_refresh || "mai";
  els.freshnessLabel.textContent = freshnessText(source);
  updateActivityState();
}

function updateActivityState() {
  const source = sourceState();
  const running = state.refreshing.has(state.activeSource) || Boolean(source?.refreshing);
  els.activityLine.hidden = !running;
  els.refreshSource.disabled = running;
  els.refreshSource.classList.toggle("is-active", running);
  els.refreshAll.classList.toggle("is-active", state.refreshing.size > 0);
  els.refreshAll.disabled = state.refreshing.size >= state.sources.size && state.sources.size > 0;

  els.sourceStatus.classList.remove("is-ready", "is-running", "is-error", "is-stale");
  if (running) {
    els.sourceStatus.classList.add("is-running");
    els.sourceStatusLabel.textContent = "Aggiornamento…";
    els.activityLabel.textContent = `Aggiornamento ${source?.name || "sorgente"} in corso…`;
  } else if (!els.errorBanner.hidden) {
    els.sourceStatus.classList.add("is-error");
    if (source?.data_origin === "cache") {
      els.sourceStatusLabel.textContent = `Errore · dati salvati · ${freshnessText(source)}`;
    } else if (source?.data_origin === "network") {
      els.sourceStatusLabel.textContent = `Errore · dati precedenti · ${freshnessText(source)}`;
    } else {
      els.sourceStatusLabel.textContent = "Errore · nessun dato";
    }
  } else if (source?.data_origin === "cache") {
    els.sourceStatus.classList.add(sourceIsStale(source) ? "is-stale" : "is-ready");
    els.sourceStatusLabel.textContent = `Dati salvati · ${freshnessText(source)}`;
  } else if (source?.data_origin === "network") {
    els.sourceStatus.classList.add(sourceIsStale(source) ? "is-stale" : "is-ready");
    els.sourceStatusLabel.textContent = sourceIsStale(source)
      ? `Dati non recenti · ${freshnessText(source)}`
      : `Dati aggiornati · ${freshnessText(source)}`;
  } else {
    els.sourceStatusLabel.textContent = "In attesa dati";
  }
}

function updateFreshnessUi() {
  updateSourceTabs();
  const source = sourceState();
  els.freshnessLabel.textContent = freshnessText(source);
  updateActivityState();
}

function startFreshnessClock() {
  if (state.freshnessTimer !== null) {
    window.clearInterval(state.freshnessTimer);
  }
  state.freshnessTimer = window.setInterval(updateFreshnessUi, 30000);
}

function orderedColumns() {
  const source = sourceState();
  if (!source) return [];
  const columns = normalizeList(source.columns);
  const fallback = columns.map((_, index) => index);
  const order = normalizeList(source.column_order);
  const valid = order.length === columns.length && new Set(order).size === columns.length;
  return (valid ? order : fallback)
    .map((originalIndex) => ({ ...columns[originalIndex], originalIndex }))
    .filter((column) => column.key);
}

function renderHeader() {
  els.tableHead.replaceChildren();
  for (const column of orderedColumns()) {
    const th = document.createElement("th");
    th.draggable = true;
    th.dataset.originalIndex = String(column.originalIndex);
    th.scope = "col";

    const button = document.createElement("button");
    button.type = "button";
    button.dataset.key = column.key;
    button.dataset.direction = state.sortDirection;
    button.setAttribute("aria-label", `Ordina per ${column.label}`);
    if (state.sortKey === column.key) {
      button.classList.add("is-sorted");
      button.setAttribute(
        "aria-sort",
        state.sortDirection === "asc" ? "ascending" : "descending",
      );
    }

    const label = document.createElement("span");
    label.textContent = column.label;
    const indicator = document.createElement("span");
    indicator.className = "sort-indicator";
    indicator.setAttribute("aria-hidden", "true");
    button.append(label, indicator);

    button.addEventListener("click", () => toggleSort(column.key));
    th.addEventListener("dragstart", onHeaderDragStart);
    th.addEventListener("dragend", onHeaderDragEnd);
    th.addEventListener("dragover", onHeaderDragOver);
    th.addEventListener("dragleave", onHeaderDragLeave);
    th.addEventListener("drop", onHeaderDrop);
    th.append(button);
    els.tableHead.append(th);
  }
}

function onHeaderDragStart(event) {
  const th = event.currentTarget;
  th.classList.add("is-dragging");
  event.dataTransfer.effectAllowed = "move";
  event.dataTransfer.setData("text/plain", th.dataset.originalIndex);
}

function onHeaderDragEnd(event) {
  event.currentTarget.classList.remove("is-dragging");
  document.querySelectorAll("th.is-drop-target").forEach((item) => item.classList.remove("is-drop-target"));
}

function onHeaderDragOver(event) {
  event.preventDefault();
  event.dataTransfer.dropEffect = "move";
  event.currentTarget.classList.add("is-drop-target");
}

function onHeaderDragLeave(event) {
  event.currentTarget.classList.remove("is-drop-target");
}

async function onHeaderDrop(event) {
  event.preventDefault();
  event.currentTarget.classList.remove("is-drop-target");
  const source = sourceState();
  if (!source) return;

  const dragged = Number(event.dataTransfer.getData("text/plain"));
  const target = Number(event.currentTarget.dataset.originalIndex);
  if (!Number.isInteger(dragged) || !Number.isInteger(target) || dragged === target) return;

  const previous = normalizeList(source.column_order).slice();
  const next = previous.slice();
  const from = next.indexOf(dragged);
  const to = next.indexOf(target);
  if (from < 0 || to < 0) return;
  next.splice(from, 1);
  next.splice(to, 0, dragged);
  source.column_order = next;
  renderHeader();
  renderBody();

  const saved = await bridgeCall("saveColumnOrder", state.activeSource, JSON.stringify(next));
  if (!saved) {
    source.column_order = previous;
    renderHeader();
    renderBody();
    showToast("Impossibile salvare l’ordine delle colonne");
  }
}

async function toggleSort(key) {
  const source = sourceState();
  if (!source) return;

  const previousKey = state.sortKey;
  const previousDirection = state.sortDirection;
  if (state.sortKey === key) {
    state.sortDirection = state.sortDirection === "asc" ? "desc" : "asc";
  } else {
    state.sortKey = key;
    state.sortDirection = "asc";
  }

  source.sort_key = state.sortKey || "";
  source.sort_direction = state.sortDirection;
  renderHeader();
  renderBody();

  try {
    const saved = await bridgeCall(
      "saveSort",
      state.activeSource,
      source.sort_key,
      source.sort_direction,
    );
    if (saved) return;
  } catch (error) {
    // Revert below.
  }

  state.sortKey = previousKey;
  state.sortDirection = previousDirection;
  source.sort_key = previousKey || "";
  source.sort_direction = previousDirection;
  renderHeader();
  renderBody();
  showToast("Impossibile salvare l’ordinamento");
}

function comparableValue(event, key) {
  const value = event[key] ?? "";
  if (key === "impact") {
    return { HIGH: 3, MID: 2, LOW: 1 }[value] || 0;
  }
  if (key === "date") {
    const [day, month, year] = String(value).split("/").map(Number);
    return Number.isFinite(year) ? year * 10000 + month * 100 + day : 0;
  }
  if (key === "time") {
    return String(value).replace(":", "");
  }
  return String(value);
}

function sortedEvents() {
  if (!state.sortKey) return state.events.slice();
  const direction = state.sortDirection === "asc" ? 1 : -1;
  const key = state.sortKey;
  return state.events.slice().sort((left, right) => {
    const a = comparableValue(left, key);
    const b = comparableValue(right, key);
    if (typeof a === "number" && typeof b === "number") {
      return (a - b) * direction;
    }
    return String(a).localeCompare(String(b), "it", { numeric: true, sensitivity: "base" }) * direction;
  });
}

function makeCountryCell(event) {
  const wrapper = document.createElement("span");
  wrapper.className = "country-cell";
  const flagCode = state.initial?.flag_codes?.[event.country];
  if (flagCode) {
    const img = document.createElement("img");
    img.className = "country-flag";
    img.alt = "";
    img.loading = "lazy";
    img.src = `../assets/flags/${flagCode}.svg`;
    img.addEventListener("error", () => img.remove(), { once: true });
    wrapper.append(img);
  }
  const label = document.createElement("span");
  label.textContent = event.country || "—";
  wrapper.append(label);
  return wrapper;
}

function makeImpactCell(event) {
  const tag = document.createElement("span");
  tag.className = "impact-tag";
  tag.dataset.impact = event.impact || "LOW";
  tag.textContent = impactLabel(event.impact || "LOW").toUpperCase();
  return tag;
}

function makeCell(event, key) {
  const td = document.createElement("td");
  td.dataset.key = key;
  if (key === "country") {
    td.append(makeCountryCell(event));
  } else if (key === "impact") {
    td.append(makeImpactCell(event));
  } else {
    const value = event[key];
    td.textContent = value === null || value === undefined || value === "" ? "—" : String(value);
  }
  return td;
}

function renderBody() {
  els.tableBody.replaceChildren();
  const columns = orderedColumns();
  const events = sortedEvents();

  for (const event of events) {
    const row = document.createElement("tr");
    for (const column of columns) {
      row.append(makeCell(event, column.key));
    }
    els.tableBody.append(row);
  }

  els.emptyState.hidden = events.length > 0;
  els.eventCount.textContent = `${events.length} ${events.length === 1 ? "evento" : "eventi"}`;
}

function hideError() {
  els.errorBanner.hidden = true;
  els.errorMessage.textContent = "";
  els.errorDetails.textContent = "";
  els.errorDetailsWrap.hidden = true;
  els.errorDetailsWrap.open = false;
  updateActivityState();
}

function showError(message, details = "") {
  els.errorMessage.textContent = message || "Il backend non ha fornito ulteriori dettagli.";
  els.errorDetails.textContent = details || "";
  els.errorDetailsWrap.hidden = !details;
  els.errorBanner.hidden = false;
  updateActivityState();
}

async function loadEvents() {
  const requestId = ++state.requestSerial;
  const sourceKey = state.activeSource;
  const source = sourceState(sourceKey);
  if (!source) return;

  try {
    const events = await bridgeCall(
      "getEventsInTimezone",
      sourceKey,
      els.region.value || "ALL",
      els.impact.value || "ALL",
      calendarDateToBackend(els.date.value),
      currentTimezoneSpec(),
    );
    if (requestId !== state.requestSerial || sourceKey !== state.activeSource) return;
    state.events = normalizeList(events);
    renderBody();
  } catch (error) {
    if (sourceKey === state.activeSource) {
      showError("Impossibile leggere gli eventi dal backend.", String(error));
    }
  }
}

async function persistFiltersAndReload() {
  const source = sourceState();
  if (!source) return;
  source.selected_region = els.region.value || "ALL";
  source.selected_impact = els.impact.value || "ALL";
  try {
    const saved = await bridgeCall(
      "saveFilters",
      state.activeSource,
      source.selected_region,
      source.selected_impact,
    );
    if (!saved) showToast("Impossibile salvare i filtri");
  } catch (error) {
    showToast("Errore nel salvataggio dei filtri");
  }
  await loadEvents();
}

async function persistUiState() {
  state.autoRefreshMinutes = Number(els.autoRefresh.value) || 0;
  try {
    const saved = await bridgeCall(
      "saveUiState",
      state.activeSource,
      els.timezone.value || "local",
      els.date.value || "",
      state.autoRefreshMinutes,
    );
    if (!saved) showToast("Impossibile salvare lo stato dell’interfaccia");
    updateFreshnessUi();
    return Boolean(saved);
  } catch (error) {
    showToast("Errore nel salvataggio dello stato");
    return false;
  }
}

async function persistUiStateAndReload() {
  await persistUiState();
  await loadEvents();
}

async function selectSource(sourceKey) {
  if (!state.sources.has(sourceKey) || sourceKey === state.activeSource) return;
  state.activeSource = sourceKey;
  hideError();
  applySourceFilters();
  applySourceSort();
  updateSourceTabs();
  updateSourceHeader();
  renderHeader();
  await persistUiState();
  await loadEvents();
}

function updateSourceRefresh(sourceKey, payload) {
  const source = sourceState(sourceKey);
  if (!source) return;
  if (payload.last_refresh !== undefined) source.last_refresh = payload.last_refresh;
  if (payload.last_refresh_iso !== undefined) source.last_refresh_iso = payload.last_refresh_iso;
  if (payload.data_origin !== undefined) source.data_origin = payload.data_origin;
  source.refreshing = false;
}

async function handleBackendEvent(eventName, payload) {
  const sourceKey = payload?.source || "";
  if (eventName === "calendar_refresh_started") {
    state.refreshing.add(sourceKey);
    const source = sourceState(sourceKey);
    if (source) source.refreshing = true;
    if (sourceKey === state.activeSource) hideError();
    updateFreshnessUi();
    return;
  }

  if (eventName === "calendar_refreshed") {
    state.refreshing.delete(sourceKey);
    updateSourceRefresh(sourceKey, payload || {});
    if (sourceKey === state.activeSource) {
      hideError();
      els.lastRefresh.textContent = sourceState()?.last_refresh || "mai";
      await loadEvents();
      showToast(`${sourceState()?.name || "Calendario"}: ${payload.count ?? 0} eventi aggiornati`);
    }
    updateFreshnessUi();
    return;
  }

  if (eventName === "calendar_refresh_error") {
    state.refreshing.delete(sourceKey);
    updateSourceRefresh(sourceKey, payload || {});
    if (sourceKey === state.activeSource) {
      showError(payload?.error || "Aggiornamento non riuscito", payload?.details || "");
    } else {
      showToast(`Aggiornamento ${sourceState(sourceKey)?.name || sourceKey} non riuscito`);
    }
    updateFreshnessUi();
  }
}

function appendLog(payload) {
  if (!payload || !payload.message) return;
  state.logs.push(payload);
  if (state.logs.length > 250) state.logs.shift();
  renderLogs();
}

function renderLogs() {
  els.logViewer.replaceChildren();
  els.logCount.textContent = String(state.logs.length);
  for (const item of state.logs) {
    const row = document.createElement("div");
    row.className = "log-line";
    row.dataset.level = item.level || "INFO";

    const time = document.createElement("span");
    time.className = "log-time";
    time.textContent = item.time || "--:--:--";
    const level = document.createElement("span");
    level.className = "log-level";
    level.textContent = item.level || "INFO";
    const message = document.createElement("span");
    message.textContent = item.message || "";
    row.append(time, level, message);
    els.logViewer.append(row);
  }
  els.logViewer.scrollTop = els.logViewer.scrollHeight;
}

async function copyLogs() {
  const text = state.logs
    .map((item) => `${item.time || ""} [${item.level || "INFO"}] ${item.message || ""}`)
    .join("\n");
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    showToast("Log copiato negli appunti");
  } catch (error) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.append(textarea);
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
    showToast("Log copiato negli appunti");
  }
}

function showToast(message) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  els.toastRegion.replaceChildren(toast);
  window.setTimeout(() => {
    if (toast.isConnected) toast.remove();
  }, 3000);
}

function bindControls() {
  for (const tab of els.sourceTabs) {
    tab.addEventListener("click", () => selectSource(tab.dataset.source));
  }
  els.region.addEventListener("change", persistFiltersAndReload);
  els.impact.addEventListener("change", persistFiltersAndReload);
  els.date.addEventListener("change", persistUiStateAndReload);
  els.timezone.addEventListener("change", persistUiStateAndReload);
  els.autoRefresh.addEventListener("change", async () => {
    if (await persistUiState()) {
      showToast(
        state.autoRefreshMinutes === 0
          ? "Auto-refresh disattivato"
          : `Auto-refresh ogni ${state.autoRefreshMinutes} minuti`,
      );
    }
  });
  els.refreshSource.addEventListener("click", () => state.bridge.refreshSource(state.activeSource));
  els.refreshAll.addEventListener("click", () => state.bridge.refreshAll());
  els.dismissError.addEventListener("click", hideError);
  els.copyLog.addEventListener("click", copyLogs);
}

async function bootstrap() {
  try {
    state.initial = await bridgeCall("getInitialState");
    const meta = state.initial?.app || {};
    const uiState = state.initial?.ui_state || {};
    els.appName.textContent = meta.name || "Calendario Finanziario";
    els.appDescription.textContent = meta.description || "Calendari economici";
    document.title = meta.name || "Calendario Finanziario";

    for (const source of normalizeList(state.initial?.sources)) {
      state.sources.set(source.key, { ...source });
      if (source.refreshing) state.refreshing.add(source.key);
    }

    const preferredSource = uiState.active_source || "ig";
    state.activeSource = state.sources.has(preferredSource) ? preferredSource : "ig";

    buildSelect(els.region, normalizeList(state.initial?.regions), regionLabel);
    buildSelect(els.impact, normalizeList(state.initial?.impacts), impactLabel);
    buildTimezoneSelect(uiState.timezone_name || "local");
    buildAutoRefreshSelect(uiState.auto_refresh_minutes ?? 15);
    els.date.value = uiState.selected_date || "";

    applySourceFilters();
    applySourceSort();
    bindControls();
    updateSourceTabs();
    updateSourceHeader();
    renderHeader();
    await loadEvents();

    const logs = await bridgeCall("getRecentLogs");
    state.logs = normalizeList(logs).slice(-250);
    renderLogs();

    startFreshnessClock();
    setConnectionReady(meta.version || "—");
    els.app.setAttribute("aria-busy", "false");
    state.bridge.start();
  } catch (error) {
    setConnectionError("Backend non disponibile");
    els.app.setAttribute("aria-busy", "false");
    showError("Impossibile inizializzare l’interfaccia.", String(error));
  }
}

function connectWebChannel() {
  if (typeof qt === "undefined" || !qt.webChannelTransport || typeof QWebChannel === "undefined") {
    setConnectionError("WebChannel non disponibile");
    els.app.setAttribute("aria-busy", "false");
    showError("Il bridge Qt non è disponibile. Avvia l’applicazione tramite main.py.");
    return;
  }

  new QWebChannel(qt.webChannelTransport, (channel) => {
    state.bridge = channel.objects.bridge;
    state.bridge.backendEvent.connect(handleBackendEvent);
    state.bridge.logMessage.connect(appendLog);
    bootstrap();
  });
}

connectWebChannel();
