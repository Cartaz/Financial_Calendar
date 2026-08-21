"use strict";

state.navigation = {
  searchQuery: "",
  quickRange: "all",
  timer: null,
};

Object.assign(els, {
  eventSearch: document.getElementById("event-search"),
  quickRangeButtons: [...document.querySelectorAll("[data-quick-range]")],
  nextEventSummary: document.getElementById("next-event-summary"),
});

function eventUtcDate(event) {
  if (!event?.utc_dt) return null;
  const parsed = new Date(event.utc_dt);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function fixedOffsetMinutes(spec) {
  const match = /^UTC([+-])(\d{2}):(\d{2})$/.exec(spec || "");
  if (!match) return null;
  const minutes = Number(match[2]) * 60 + Number(match[3]);
  return match[1] === "-" ? -minutes : minutes;
}

function isoDateInTimezone(date, timezoneSpec) {
  const offset = fixedOffsetMinutes(timezoneSpec);
  if (offset !== null) {
    const shifted = new Date(date.getTime() + offset * 60000);
    return [
      shifted.getUTCFullYear(),
      String(shifted.getUTCMonth() + 1).padStart(2, "0"),
      String(shifted.getUTCDate()).padStart(2, "0"),
    ].join("-");
  }

  try {
    const parts = new Intl.DateTimeFormat("en-CA", {
      timeZone: timezoneSpec,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).formatToParts(date);
    const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
    return `${values.year}-${values.month}-${values.day}`;
  } catch (error) {
    const fallback = new Date(date);
    const year = fallback.getFullYear();
    const month = String(fallback.getMonth() + 1).padStart(2, "0");
    const day = String(fallback.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }
}

function addCalendarDays(isoDate, days) {
  const value = new Date(`${isoDate}T00:00:00Z`);
  value.setUTCDate(value.getUTCDate() + days);
  return value.toISOString().slice(0, 10);
}

function navigationFilteredEvents() {
  const query = state.navigation.searchQuery.trim().toLocaleLowerCase("it");
  const now = Date.now();
  const nextDay = now + 24 * 60 * 60 * 1000;

  return state.events.filter((event) => {
    if (state.navigation.quickRange === "next24") {
      const eventDate = eventUtcDate(event);
      if (!eventDate || eventDate.getTime() < now || eventDate.getTime() > nextDay) {
        return false;
      }
    }

    if (!query) return true;
    const searchable = [
      event.event_name,
      event.country,
      event.impact,
      event.actual,
      event.forecast,
      event.previous,
      event.deviation,
    ]
      .filter((value) => value !== null && value !== undefined)
      .join(" ")
      .toLocaleLowerCase("it");
    return searchable.includes(query);
  });
}

sortedEvents = function sortedNavigationEvents() {
  const events = navigationFilteredEvents();
  if (!state.sortKey) return events.slice();
  const direction = state.sortDirection === "asc" ? 1 : -1;
  const key = state.sortKey;
  return events.slice().sort((left, right) => {
    const a = comparableValue(left, key);
    const b = comparableValue(right, key);
    if (typeof a === "number" && typeof b === "number") {
      return (a - b) * direction;
    }
    return String(a).localeCompare(String(b), "it", {
      numeric: true,
      sensitivity: "base",
    }) * direction;
  });
};

function formatCountdown(milliseconds) {
  if (!Number.isFinite(milliseconds) || milliseconds <= 0) return "";
  const totalMinutes = Math.max(1, Math.ceil(milliseconds / 60000));
  if (totalMinutes < 60) return `tra ${totalMinutes} min`;

  const totalHours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  if (totalHours < 24) {
    return `tra ${totalHours} h${minutes ? ` ${String(minutes).padStart(2, "0")} min` : ""}`;
  }

  const days = Math.floor(totalHours / 24);
  const hours = totalHours % 24;
  return `tra ${days} g${hours ? ` ${hours} h` : ""}`;
}

const baseMakeCell = makeCell;
makeCell = function makeNavigationCell(event, key) {
  if (key !== "event_name") return baseMakeCell(event, key);

  const td = document.createElement("td");
  td.dataset.key = key;
  const wrapper = document.createElement("span");
  wrapper.className = "event-name-wrap";

  const title = document.createElement("span");
  title.className = "event-name-label";
  title.textContent = event.event_name || "—";
  wrapper.append(title);

  const eventDate = eventUtcDate(event);
  const remaining = eventDate ? eventDate.getTime() - Date.now() : 0;
  const countdown = formatCountdown(remaining);
  if (countdown) {
    const timing = document.createElement("small");
    timing.className = "event-countdown";
    timing.textContent = countdown;
    wrapper.append(timing);
  }

  td.append(wrapper);
  return td;
};

function nextHighEvent(events) {
  const now = Date.now();
  return events
    .filter((event) => event.impact === "HIGH")
    .map((event) => ({ event, date: eventUtcDate(event) }))
    .filter((item) => item.date && item.date.getTime() > now)
    .sort((left, right) => left.date.getTime() - right.date.getTime())[0] || null;
}

function updateNextEventSummary(events) {
  if (!els.nextEventSummary) return;
  const next = nextHighEvent(events);
  if (!next) {
    els.nextEventSummary.textContent = "Nessun evento HIGH imminente";
    return;
  }
  const countdown = formatCountdown(next.date.getTime() - Date.now());
  els.nextEventSummary.textContent = `Prossimo HIGH: ${next.event.event_name} · ${countdown}`;
}

renderBody = function renderNavigationBody() {
  els.tableBody.replaceChildren();
  const columns = orderedColumns();
  const events = sortedEvents();
  const next = nextHighEvent(events);
  const now = Date.now();

  for (const event of events) {
    const row = document.createElement("tr");
    const eventDate = eventUtcDate(event);
    if (eventDate && eventDate.getTime() < now) row.classList.add("is-past");
    if (next?.event === event) row.classList.add("is-next-high");

    for (const column of columns) {
      row.append(makeCell(event, column.key));
    }
    els.tableBody.append(row);
  }

  els.emptyState.hidden = events.length > 0;
  els.eventCount.textContent = `${events.length} ${events.length === 1 ? "evento" : "eventi"}`;
  updateNextEventSummary(events);
};

function updateQuickRangeButtons() {
  for (const button of els.quickRangeButtons) {
    const selected = button.dataset.quickRange === state.navigation.quickRange;
    button.setAttribute("aria-pressed", String(selected));
  }
}

async function selectQuickRange(range) {
  const timezone = currentTimezoneSpec();
  const today = isoDateInTimezone(new Date(), timezone);

  state.navigation.quickRange = range;
  if (range === "today") {
    els.date.value = today;
  } else if (range === "tomorrow") {
    els.date.value = addCalendarDays(today, 1);
  } else {
    els.date.value = "";
  }

  updateQuickRangeButtons();
  await persistUiStateAndReload();
}

function startNavigationClock() {
  if (state.navigation.timer !== null) {
    window.clearInterval(state.navigation.timer);
  }
  state.navigation.timer = window.setInterval(() => {
    renderBody();
  }, 30000);
}

const baseBindControls = bindControls;
bindControls = function bindNavigationControls() {
  baseBindControls();

  els.eventSearch.addEventListener("input", () => {
    state.navigation.searchQuery = els.eventSearch.value || "";
    renderBody();
  });

  for (const button of els.quickRangeButtons) {
    button.addEventListener("click", () => selectQuickRange(button.dataset.quickRange));
  }

  els.date.addEventListener("change", () => {
    state.navigation.quickRange = els.date.value ? "manual" : "all";
    updateQuickRangeButtons();
  });

  els.timezone.addEventListener("change", () => {
    if (["today", "tomorrow"].includes(state.navigation.quickRange)) {
      state.navigation.quickRange = "manual";
      updateQuickRangeButtons();
    }
  });

  startNavigationClock();
};

const baseBootstrap = bootstrap;
bootstrap = async function bootstrapNavigation() {
  await baseBootstrap();
  state.navigation.quickRange = els.date.value ? "manual" : "all";
  updateQuickRangeButtons();
  renderBody();
};
