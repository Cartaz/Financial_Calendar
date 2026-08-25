"use strict";

const FinancialCalendarNavigation = (() => {
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
      return [
        fallback.getFullYear(),
        String(fallback.getMonth() + 1).padStart(2, "0"),
        String(fallback.getDate()).padStart(2, "0"),
      ].join("-");
    }
  }

  function addCalendarDays(isoDate, days) {
    const value = new Date(`${isoDate}T00:00:00Z`);
    value.setUTCDate(value.getUTCDate() + days);
    return value.toISOString().slice(0, 10);
  }

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

  function filterEvents(events, searchQuery, quickRange, nowMs = Date.now()) {
    const query = String(searchQuery || "").trim().toLocaleLowerCase("it");
    const nextDay = nowMs + 24 * 60 * 60 * 1000;
    return events.filter((event) => {
      if (quickRange === "next24") {
        const eventDate = eventUtcDate(event);
        if (!eventDate || eventDate.getTime() < nowMs || eventDate.getTime() > nextDay) {
          return false;
        }
      }
      if (!query) return true;
      return [
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
        .toLocaleLowerCase("it")
        .includes(query);
    });
  }

  function nextHighEvent(events, nowMs = Date.now()) {
    return events
      .filter((event) => event.impact === "HIGH")
      .map((event) => ({ event, date: eventUtcDate(event) }))
      .filter((item) => item.date && item.date.getTime() > nowMs)
      .sort((left, right) => left.date.getTime() - right.date.getTime())[0] || null;
  }

  return {
    addCalendarDays,
    eventUtcDate,
    filterEvents,
    formatCountdown,
    isoDateInTimezone,
    nextHighEvent,
  };
})();
