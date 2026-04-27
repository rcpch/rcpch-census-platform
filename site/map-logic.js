function getTilesBaseUrl() {
  const params = new URLSearchParams(window.location.search);
  const fromQuery = params.get("tilesBase");
  if (fromQuery) return fromQuery.replace(/\/+$/, "");

  const meta = document.querySelector('meta[name="rcpch-tiles-base-url"]');
  const fromMeta = meta?.getAttribute("content")?.trim();
  if (fromMeta) return fromMeta.replace(/\/+$/, "");

  if (typeof window.PUBLIC_TILES_URL === "string" && window.PUBLIC_TILES_URL) {
    return window.PUBLIC_TILES_URL.replace(/\/+$/, "");
  }

  if (
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1"
  ) {
    return "http://localhost:7800";
  }

  return "https://api.rcpch.ac.uk/deprivation/v2/tiles";
}

const TILES_BASE_URL = getTilesBaseUrl();
if (!TILES_BASE_URL) {
  console.warn(
    "No tiles base URL configured. Set ?tilesBase=https://<host>/tiles, the rcpch-tiles-base-url meta tag, or inject window.PUBLIC_TILES_URL.",
  );
}

const DATASET_INFO = {
  england: {
    2021: { imd: "2025 IMD", boundaries: "2021 LSOAs" },
    2011: { imd: "2019 IMD", boundaries: "2011 LSOAs" },
  },
  wales: {
    2011: {
      imd: "2019 WIMD",
      boundaries: "2011 LSOAs",
      note: "No 2025 WIMD published",
    },
  },
  scotland: {
    2011: { imd: "2020 SIMD", boundaries: "2011 DataZones" },
  },
  northern_ireland: {
    2011: { imd: "2017 NIMDM", boundaries: "2001 SOAs" },
  },
};

let currentEra = "2021";
let currentNation = "all";
let mapInstance = null;

const HEALTH_BOUNDARIES = {
  nhser: {
    toggleId: "nhser-toggle",
    groupId: "nhser-toggle-group",
    noteId: "nhser-note",
    enabledIn: ["all", "england"],
    disabledNote: "England only",
  },
  icb: {
    toggleId: "icb-toggle",
    groupId: "icb-toggle-group",
    noteId: "icb-note",
    enabledIn: ["all", "england"],
    disabledNote: "England only",
  },
  lhb: {
    toggleId: "lhb-toggle",
    groupId: "lhb-toggle-group",
    noteId: "lhb-note",
    enabledIn: ["all", "wales"],
    disabledNote: "Wales only",
  },
};

function isHealthBoundaryEnabledForCurrentNation(config) {
  return config.enabledIn.includes(currentNation);
}

function updateDatasetInfo(selectedNation, era) {
  const infoEl = document.getElementById("dataset-info");
  const noteEl = document.getElementById("era-note");
  const eraGroup = document.getElementById("era-toggle-group");
  const eraSelect = document.getElementById("era-toggle");

  const LABELS = {
    england: "England",
    wales: "Wales",
    scotland: "Scotland",
    northern_ireland: "N. Ireland",
  };

  const eraActive = selectedNation === "england" || selectedNation === "all";
  eraGroup.style.opacity = eraActive ? "1" : "0.45";
  eraSelect.disabled = !eraActive;
  noteEl.textContent = eraActive
    ? selectedNation === "all"
      ? "All UK: era switch changes England between 2025/2021 and 2019/2011 datasets"
      : ""
    : "Era selector applies to England and All UK";

  const nations =
    selectedNation === "all"
      ? ["england", "wales", "scotland", "northern_ireland"]
      : [selectedNation];

  const lines = nations.map((n) => {
    const eraKey = n === "england" ? era : "2011";
    const d = DATASET_INFO[n][eraKey];
    const noteStr = d.note
      ? ` <span style="color:#9a6700;font-style:italic;">(${d.note})</span>`
      : "";
    return `<div><strong>${LABELS[n]}:</strong> ${d.imd} &middot; ${d.boundaries}${noteStr}</div>`;
  });

  infoEl.innerHTML = lines.join("");
}

function updateLocalAuthorityControlState() {
  const laToggle = document.getElementById("la-toggle");
  const laNote = document.getElementById("la-note");
  const laGroup = document.getElementById("la-toggle-group");

  const enabled = currentNation !== "northern_ireland";
  laToggle.disabled = !enabled;
  laGroup.style.opacity = enabled ? "1" : "0.45";

  if (!enabled && laToggle.checked) {
    laToggle.checked = false;
  }

  laNote.textContent = enabled
    ? currentNation === "england" && currentEra === "2021"
      ? "Using 2024 Local Authority boundaries"
      : currentNation === "all"
        ? currentEra === "2021"
          ? "All UK: England 2024 + Wales 2019 + Scotland 2011 boundaries"
          : "All UK: England/Wales 2019 + Scotland 2011 boundaries"
        : "Showing matching Local Authority boundaries for this view"
    : "Not available for Northern Ireland in this layer";
}

function updateHealthBoundaryControlState() {
  Object.values(HEALTH_BOUNDARIES).forEach((config) => {
    const toggle = document.getElementById(config.toggleId);
    const group = document.getElementById(config.groupId);
    const note = document.getElementById(config.noteId);
    if (!toggle || !group || !note) return;

    const enabled = isHealthBoundaryEnabledForCurrentNation(config);
    toggle.disabled = !enabled;
    group.style.opacity = enabled ? "1" : "0.45";
    note.textContent = enabled ? "" : config.disabledNote;

    if (!enabled && toggle.checked) {
      toggle.checked = false;
    }
  });
}

function applyOverlayVisibility() {
  if (!mapInstance) return;

  const localAuthorityEnabled =
    currentNation !== "northern_ireland" &&
    !!document.getElementById("la-toggle")?.checked;

  const nhserEnabled =
    isHealthBoundaryEnabledForCurrentNation(HEALTH_BOUNDARIES.nhser) &&
    !!document.getElementById("nhser-toggle")?.checked;

  const icbEnabled =
    isHealthBoundaryEnabledForCurrentNation(HEALTH_BOUNDARIES.icb) &&
    !!document.getElementById("icb-toggle")?.checked;

  const lhbEnabled =
    isHealthBoundaryEnabledForCurrentNation(HEALTH_BOUNDARIES.lhb) &&
    !!document.getElementById("lhb-toggle")?.checked;

  mapInstance.setOverlayVisibility({
    localAuthority: localAuthorityEnabled,
    nhser: nhserEnabled,
    icb: icbEnabled,
    lhb: lhbEnabled,
  });
}

function normalizeNation(nationText) {
  return String(nationText || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "_");
}

function shouldShowTooltipRowForNation(rowKey, nation) {
  if (rowKey === "nhser" || rowKey === "icb") return nation === "england";
  if (rowKey === "lhb") return nation === "wales";
  if (rowKey === "lad") {
    return nation === "england" || nation === "wales" || nation === "scotland";
  }
  return true;
}

function getBoundaryTypeLabelForNation(nation) {
  if (nation === "scotland") return "Data Zones";
  if (nation === "northern_ireland") return "SOAs";
  return "LSOAs";
}

function isMeaningfulTooltipValue(value) {
  const compact = String(value || "")
    .replace(/\s+/g, "")
    .trim();
  if (!compact) return false;
  return !/^[-–()]+$/.test(compact);
}

function postProcessTooltipRows(rootEl) {
  const popups = rootEl.querySelectorAll(".maplibregl-popup-content");
  popups.forEach((popupEl) => {
    const nationEl = popupEl.querySelector("[data-tooltip-nation]");
    const nation = normalizeNation(nationEl?.textContent || "");
    const boundaryLabelEl = popupEl.querySelector(
      "[data-tooltip-boundary-label]",
    );

    if (boundaryLabelEl) {
      boundaryLabelEl.textContent = `${getBoundaryTypeLabelForNation(nation)}:`;
    }

    const conditionalRows = popupEl.querySelectorAll("[data-tooltip-row]");

    conditionalRows.forEach((rowEl) => {
      const rowKey = rowEl.getAttribute("data-tooltip-row") || "";
      const valueEl = rowEl.querySelector("[data-tooltip-value]");
      const valueText = valueEl?.textContent || "";
      const showForNation = shouldShowTooltipRowForNation(rowKey, nation);
      const hasValue = isMeaningfulTooltipValue(valueText);
      rowEl.style.display = showForNation && hasValue ? "block" : "none";
    });
  });
}

let tooltipPostProcessScheduled = false;

function scheduleTooltipPostProcessor() {
  if (tooltipPostProcessScheduled) return;

  tooltipPostProcessScheduled = true;
  window.requestAnimationFrame(() => {
    tooltipPostProcessScheduled = false;
    const mapEl = document.getElementById("map");
    if (!mapEl) return;
    postProcessTooltipRows(mapEl);
  });
}

function installTooltipPostProcessor() {
  const mapEl = document.getElementById("map");
  if (!mapEl) return;

  mapEl.addEventListener("mousemove", scheduleTooltipPostProcessor, {
    passive: true,
  });

  mapEl.addEventListener("mouseenter", scheduleTooltipPostProcessor, {
    passive: true,
  });

  scheduleTooltipPostProcessor();
}

function getTooltipTemplate() {
  return [
    '<strong style="display:block;margin-bottom:3px;">{{areaName}}</strong>',
    '<span data-tooltip-nation style="display:none;">{{nation}}</span>',
    "<div><strong>Code:</strong> {{areaCode}}</div>",
    "<div><strong>Decile:</strong> {{imdDecile}}</div>",
    "<div><strong>Nation:</strong> {{nation}}</div>",
    "<div><strong data-tooltip-boundary-label>LSOAs:</strong> {{boundaryYear}}</div>",
    "<div><strong>Index Year:</strong> {{imdYear}}</div>",
    '<div data-tooltip-row="lad"><strong>Local Authority:</strong> <span data-tooltip-value>{{laName}} ({{laCode}})</span></div>',
    '<div data-tooltip-row="lad"><strong>LA Year:</strong> <span data-tooltip-value>{{laYear}}</span></div>',
    '<div data-tooltip-row="nhser"><strong>NHSER:</strong> <span data-tooltip-value>{{nhserName}} ({{nhserCode}})</span></div>',
    '<div data-tooltip-row="icb"><strong>ICB:</strong> <span data-tooltip-value>{{icbName}} ({{icbCode}})</span></div>',
    '<div data-tooltip-row="lhb"><strong>LHB:</strong> <span data-tooltip-value>{{lhbName}} ({{lhbCode}})</span></div>',
  ].join("");
}

function initMap() {
  if (
    !window.RcpchImdMap ||
    typeof window.RcpchImdMap.createImdMap !== "function"
  ) {
    console.error("RcpchImdMap bundle not loaded.");
    return;
  }

  mapInstance = window.RcpchImdMap.createImdMap({
    container: "map",
    tilesBaseUrl: TILES_BASE_URL,
    initialNation: currentNation,
    initialEra: currentEra,
    areaTooltipMode: "template",
    legendPosition: "bottom-right",
    legendTitle: "Map layers",
    showLegend: true,
    style: {
      choropleth: {
        baseColorByNation: {
          england: "#b91c1c",
          scotland: "#08306b",
          wales: "#00441b",
          northern_ireland: "#7f2704",
        },
        fillOpacity: 0.62,
      },
      boundaries: {
        localAuthorityColor: "#374151",
        localAuthorityWidth: 1.5,
        nhserColor: "#0f766e",
        nhserWidth: 2.4,
        icbColor: "#b45309",
        icbWidth: 2.2,
        lhbColor: "#166534",
        lhbWidth: 2.2,
      },
      tooltip: {
        backgroundColor: "#0d0d58",
        textColor: "#ffffff",
        borderColor: "#0d0d58",
        areaLabel: "Area",
        decileLabel: "IMD decile",
        nationLabel: "Nation",
        areaTooltipText: getTooltipTemplate(),
      },
      legend: {
        width: 250,
      },
    },
    onViewChange(view) {
      currentNation = view.nation;
      currentEra = view.era;
      updateDatasetInfo(currentNation, currentEra);
      updateLocalAuthorityControlState();
      updateHealthBoundaryControlState();
      applyOverlayVisibility();
    },
    onWarning(warning) {
      console.warn("[rcpch-imd-map]", warning.code, warning.message);
    },
  });

  updateDatasetInfo(currentNation, currentEra);
  updateLocalAuthorityControlState();
  updateHealthBoundaryControlState();
  applyOverlayVisibility();
  installTooltipPostProcessor();
}

document.getElementById("era-toggle").addEventListener("change", (e) => {
  currentEra = e.target.value;
  if (!mapInstance) return;
  mapInstance.setEra(currentEra);
  updateDatasetInfo(currentNation, currentEra);
  updateLocalAuthorityControlState();
  updateHealthBoundaryControlState();
  applyOverlayVisibility();
});

document.getElementById("nation-filter").addEventListener("change", (e) => {
  currentNation = e.target.value;
  if (!mapInstance) return;
  mapInstance.setNation(currentNation);
  updateDatasetInfo(currentNation, currentEra);
  updateLocalAuthorityControlState();
  updateHealthBoundaryControlState();
  applyOverlayVisibility();
});

document.getElementById("la-toggle").addEventListener("change", () => {
  applyOverlayVisibility();
});

document.getElementById("nhser-toggle").addEventListener("change", () => {
  applyOverlayVisibility();
});

document.getElementById("icb-toggle").addEventListener("change", () => {
  applyOverlayVisibility();
});

document.getElementById("lhb-toggle").addEventListener("change", () => {
  applyOverlayVisibility();
});

initMap();
