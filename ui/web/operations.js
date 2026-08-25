"use strict";

const FinancialCalendarOperations = (() => {
  function sourceLabel(source) {
    return source === "ig" ? "ForexFactory" : "FXStreet";
  }

  function duplicateGroup(event) {
    return String(event?.duplicate_group || "");
  }

  function duplicateGroupCount(events) {
    return new Set(events.map(duplicateGroup).filter(Boolean)).size;
  }

  return {
    duplicateGroup,
    duplicateGroupCount,
    sourceLabel,
  };
})();
