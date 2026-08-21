"use strict";

state.operations = {
  duplicateGroups: new Map(),
};

Object.assign(els, {
  notificationLead: document.getElementById("notification-lead"),
  exportCsv: document.getElementById("export-csv"),
  exportIcs: document.getElementById("export-ics"),
});

function eventIdentity(event) {
  return [
    event?.source || "",
    event?.utc_dt || "",
    event?.country || "",
    event?.event_name || "",
  ].join("|");
}

function normalizedEventName(value) {
  return String(value || "")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("en")
    .replace(/[^a-z0-9]+/g, " ")
    .trim()
    .replace(/\s+/g, " ");
}

function bigramDice(left, right) {
  const a = normalizedEventName(left);
  const b = normalizedEventName(right);
  if (!a || !b) return 0;
  if (a === b) return 1;
  if (a.length < 2 || b.length < 2) return 0;

  const counts = new Map();
  for (let index = 0; index < a.length - 1; index += 1) {
    const pair = a.slice(index, index + 2);
    counts.set(pair, (counts.get(pair) || 0) + 1);
  }

  let matches = 0;
  for (let index = 0; index < b.length - 1; index += 1) {
    const pair = b.slice(index, index + 2);
    const available = counts.get(pair) || 0;
    if (available > 0) {
      matches += 1;
      counts.set(pair, available - 1);
    }
  }
  return (2 * matches) / (a.length + b.length - 2);
}

function eventsProbablyDuplicate(left, right) {
  if (!left || !right || left.source === right.source) return false;
  if ((left.country || "") !== (right.country || "")) return false;

  const leftDate = eventUtcDate(left);
  const rightDate = eventUtcDate(right);
  if (!leftDate || !rightDate) return false;
  if (Math.abs(leftDate.getTime() - rightDate.getTime()) > 15 * 60 * 1000) return false;

  const leftName = normalizedEventName(left.event_name);
  const rightName = normalizedEventName(right.event_name);
  if (!leftName || !rightName) return false;
  if (leftName === rightName) return true;

  const shorter = leftName.length <= rightName.length ? leftName : rightName;
  const longer = leftName.length > rightName.length ? leftName : rightName;
  if (shorter.length >= 8 && longer.includes(shorter)) return true;
  return bigramDice(leftName, rightName) >= 0.72;
}

function buildDuplicateGroups(events) {
  if (state.activeSource !== "combined" || events.length < 2) return new Map();

  const parents = events.map((_, index) => index);
  const find = (index) => {
    let current = index;
    while (parents[current] !== current) {
      parents[current] = parents[parents[current]];
      current = parents[current];
    }
    return current;
  };
  const unite = (left, right) => {
    const a = find(left);
    const b = find(right);
    if (a !== b) parents[b] = a;
  };

  for (let left = 0; left < events.length; left += 1) {
    for (let right = left + 1; right < events.length; right += 1) {
      if (eventsProbablyDuplicate(events[left], events[right])) unite(left, right);
    }
  }

  const members = new Map();
  events.forEach((event, index) => {
    const root = find(index);
    const list = members.get(root) || [];
    list.push(event);
    members.set(root, list);
  });

  const groups = new Map();
  let serial = 1;
  for (const list of members.values()) {
    if (list.length < 2) continue;
    const group = `D${serial}`;
    serial += 1;
    for (const event of list) groups.set(eventIdentity(event), group);
  }
  return groups;
}

const operationsBaseMakeCell = makeCell;
makeCell = function makeOperationsCell(event, key) {
  if (key === "source") {
    const td = document.createElement("td");
    td.dataset.key = key;
    const label = document.createElement("span");
    label.className = "source-label";
    label.textContent = event.source === "ig" ? "ForexFactory" : "FXStreet";
    td.append(label);
    return td;
  }

  const td = operationsBaseMakeCell(event, key);
  if (key === "event_name") {
    const group = state.operations.duplicateGroups.get(eventIdentity(event));
    if (group) {
      const badge = document.createElement("small");
      badge.className = "duplicate-badge";
      badge.textContent = `Possibile duplicato · ${group}`;
      const wrapper = td.querySelector(".event-name-wrap") || td;
      wrapper.append(badge);
    }
  }
  return td;
};

renderBody = function renderOperationsBody() {
  els.tableBody.replaceChildren();
  const columns = orderedColumns();
  const events = sortedEvents();
  state.operations.duplicateGroups = buildDuplicateGroups(events);
  const duplicateGroupCount = new Set(state.operations.duplicateGroups.values()).size;
  const next = nextHighEvent(events);
  const now = Date.now();

  for (const event of events) {
    const row = document.createElement("tr");
    const eventDate = eventUtcDate(event);
    if (eventDate && eventDate.getTime() < now) row.classList.add("is-past");
    if (next?.event === event) row.classList.add("is-next-high");
    if (state.operations.duplicateGroups.has(eventIdentity(event))) {
      row.classList.add("is-probable-duplicate");
    }

    for (const column of columns) row.append(makeCell(event, column.key));
    els.tableBody.append(row);
  }

  els.emptyState.hidden = events.length > 0;
  const countText = `${events.length} ${events.length === 1 ? "evento" : "eventi"}`;
  els.eventCount.textContent = duplicateGroupCount
    ? `${countText} · ${duplicateGroupCount} ${duplicateGroupCount === 1 ? "gruppo duplicato" : "gruppi duplicati"}`
    : countText;
  updateNextEventSummary(events);
};

const operationsBaseUpdateSourceHeader = updateSourceHeader;
updateSourceHeader = function updateOperationsSourceHeader() {
  operationsBaseUpdateSourceHeader();
  if (state.activeSource === "combined") {
    els.sourceKicker.textContent = "COMBINATO";
  }
};

const operationsBaseHandleBackendEvent = handleBackendEvent;
handleBackendEvent = async function handleOperationsBackendEvent(eventName, payload) {
  const combined = payload?.combined_state;
  if (combined) {
    const previous = sourceState("combined") || {};
    state.sources.set("combined", { ...previous, ...combined });
  }
  if (eventName === "calendar_refresh_started") {
    const combinedState = sourceState("combined");
    if (combinedState) combinedState.refreshing = true;
  }

  await operationsBaseHandleBackendEvent(eventName, payload);

  if (state.activeSource !== "combined") return;
  if (["calendar_refresh_started", "calendar_refreshed", "calendar_refresh_error"].includes(eventName)) {
    updateSourceHeader();
    updateFreshnessUi();
  }
  if (["calendar_refreshed", "calendar_refresh_error"].includes(eventName)) {
    await loadEvents();
  }
};

function exportableEvents() {
  const events = sortedEvents();
  const groups = buildDuplicateGroups(events);
  return events.map((event) => ({
    ...event,
    duplicate_group: groups.get(eventIdentity(event)) || "",
  }));
}

async function requestExport(format) {
  const events = exportableEvents();
  if (!events.length) {
    showToast("Nessun evento visibile da esportare");
    return;
  }

  try {
    const result = await bridgeCall("exportEvents", format, JSON.stringify(events));
    if (result?.cancelled) return;
    if (!result?.ok) {
      showToast(result?.error || "Export non riuscito");
      return;
    }
    showToast(`${format.toUpperCase()} esportato · ${result.count ?? events.length} eventi`);
  } catch (error) {
    showToast("Export non riuscito");
  }
}

const operationsBaseBindControls = bindControls;
bindControls = function bindOperationsControls() {
  operationsBaseBindControls();

  els.notificationLead.addEventListener("change", async () => {
    const minutes = Number(els.notificationLead.value) || 0;
    try {
      const saved = await bridgeCall("saveNotificationLead", minutes);
      if (!saved) {
        showToast("Impossibile salvare le notifiche");
        return;
      }
      showToast(
        minutes === 0
          ? "Notifiche HIGH disattivate"
          : `Notifiche HIGH ${minutes} minuti prima`,
      );
    } catch (error) {
      showToast("Errore nel salvataggio delle notifiche");
    }
  });

  els.exportCsv.addEventListener("click", () => requestExport("csv"));
  els.exportIcs.addEventListener("click", () => requestExport("ics"));
};

const operationsBaseBootstrap = bootstrap;
bootstrap = async function bootstrapOperations() {
  await operationsBaseBootstrap();
  const lead = Number(state.initial?.ui_state?.high_notification_minutes) || 0;
  els.notificationLead.value = String(lead);
  if (!els.notificationLead.value) els.notificationLead.value = "0";
  updateSourceHeader();
  renderBody();
};
