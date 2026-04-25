const map = new maplibregl.Map({
  container: "map",
  style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
  center: [-3.43, 55.37],
  zoom: 5,
  refreshExpired: true,
});

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

function getPropCaseInsensitive(props, candidateKeys) {
  if (!props) return undefined;

  for (const key of candidateKeys) {
    if (props[key] !== undefined && props[key] !== null) {
      return props[key];
    }
  }

  const lowerMap = Object.create(null);
  for (const key of Object.keys(props)) {
    lowerMap[key.toLowerCase()] = props[key];
  }

  for (const key of candidateKeys) {
    const value = lowerMap[key.toLowerCase()];
    if (value !== undefined && value !== null) {
      return value;
    }
  }

  return undefined;
}

// Per-nation, per-era dataset facts
// Scotland and NI are always on 2011-era boundaries regardless of era toggle.
// Wales has no published 2025 WIMD, so this map uses 2019 WIMD on 2011 LSOAs.
// (2021 Welsh boundaries may exist but are not used in the current UK-wide dataset.)
// The era toggle therefore only affects England.
// For the All UK view we always use uk_master_2011_* so all 4 nations appear.
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

const LA_SOURCE_ID = "la-boundaries-source";
const LA_LAYER_ID = "la-boundaries-layer";
const LA_SOURCE_LAYER = "public.la_tiles";

const HEALTH_BOUNDARIES = {
  nhser: {
    sourceId: "nhser-boundaries-source",
    layerId: "nhser-boundaries-layer",
    sourceLayerBase: "public.nhser_tiles_2021",
    toggleId: "nhser-toggle",
    groupId: "nhser-toggle-group",
    noteId: "nhser-note",
    color: "rgba(55, 65, 81, 0.85)",
    widthBase: 1.5,
    enabledIn: ["all", "england"],
    disabledNote: "England only",
  },
  icb: {
    sourceId: "icb-boundaries-source",
    layerId: "icb-boundaries-layer",
    sourceLayerBase: "public.icb_tiles_2023",
    toggleId: "icb-toggle",
    groupId: "icb-toggle-group",
    noteId: "icb-note",
    color: "rgba(127, 29, 29, 0.82)",
    widthBase: 1.25,
    enabledIn: ["all", "england"],
    disabledNote: "England only",
  },
  lhb: {
    sourceId: "lhb-boundaries-source",
    layerId: "lhb-boundaries-layer",
    sourceLayerBase: "public.lhb_tiles_2022",
    toggleId: "lhb-toggle",
    groupId: "lhb-toggle-group",
    noteId: "lhb-note",
    color: "rgba(22, 101, 52, 0.78)",
    widthBase: 1.4,
    enabledIn: ["all", "wales"],
    disabledNote: "Wales only",
  },
};

// Returns the tile era to actually request for the given nation selection.
// Only England solo respects the era toggle; everything else uses 2011.
function effectiveEra(nation) {
  return nation === "england" ? currentEra : "2011";
}

function getViewName(era, zoom) {
  const zoomSuffix =
    zoom <= 4 ? "z0_4" : zoom <= 7 ? "z5_7" : zoom <= 10 ? "z8_10" : "z11_14";
  return `public.uk_master_${era}_${zoomSuffix}`;
}

function getHealthBoundaryViewName(sourceLayerBase, zoom) {
  const zoomSuffix =
    zoom <= 4 ? "z0_4" : zoom <= 7 ? "z5_7" : zoom <= 10 ? "z8_10" : "z11_14";
  return `${sourceLayerBase}_${zoomSuffix}`;
}

function getLocalAuthorityYearForNation(nation) {
  if (nation === "england") {
    return currentNation === "england" && currentEra === "2021" ? 2024 : 2019;
  }
  if (nation === "wales") {
    return 2019;
  }
  if (nation === "scotland") {
    return 2011;
  }
  return null;
}

function getLocalAuthorityFilter() {
  if (currentNation === "northern_ireland") {
    return null;
  }

  if (currentNation === "england") {
    return [
      "all",
      ["==", ["slice", ["get", "lad_code"], 0, 1], "E"],
      ["==", ["get", "year"], getLocalAuthorityYearForNation("england")],
    ];
  }

  if (currentNation === "wales") {
    return [
      "all",
      ["==", ["slice", ["get", "lad_code"], 0, 1], "W"],
      ["==", ["get", "year"], 2019],
    ];
  }

  if (currentNation === "scotland") {
    return [
      "all",
      ["==", ["slice", ["get", "lad_code"], 0, 1], "S"],
      ["==", ["get", "year"], 2011],
    ];
  }

  return [
    "any",
    [
      "all",
      ["==", ["slice", ["get", "lad_code"], 0, 1], "E"],
      ["==", ["get", "year"], 2019],
    ],
    [
      "all",
      ["==", ["slice", ["get", "lad_code"], 0, 1], "W"],
      ["==", ["get", "year"], 2019],
    ],
    [
      "all",
      ["==", ["slice", ["get", "lad_code"], 0, 1], "S"],
      ["==", ["get", "year"], 2011],
    ],
  ];
}

function ensureLocalAuthoritySource() {
  if (map.getSource(LA_SOURCE_ID)) {
    return;
  }

  map.addSource(LA_SOURCE_ID, {
    type: "vector",
    tiles: [`${TILES_BASE_URL}/${LA_SOURCE_LAYER}/{z}/{x}/{y}.pbf`],
    minzoom: 0,
    maxzoom: 14,
  });
}

function removeLocalAuthorityLayer() {
  if (map.getLayer(LA_LAYER_ID)) {
    map.removeLayer(LA_LAYER_ID);
  }
}

function updateLocalAuthorityLayer() {
  const laToggle = document.getElementById("la-toggle");
  const requested = !!laToggle?.checked;

  if (!requested || currentNation === "northern_ireland") {
    removeLocalAuthorityLayer();
    return;
  }

  ensureLocalAuthoritySource();

  if (!map.getLayer(LA_LAYER_ID)) {
    map.addLayer({
      id: LA_LAYER_ID,
      type: "line",
      source: LA_SOURCE_ID,
      "source-layer": LA_SOURCE_LAYER,
      paint: {
        "line-color": "rgba(55, 65, 81, 0.55)",
        "line-width": [
          "interpolate",
          ["linear"],
          ["zoom"],
          4,
          0.6,
          7,
          1.1,
          10,
          1.8,
        ],
        "line-opacity": 1,
      },
    });
  }

  // Keep LA boundaries above the deprivation fill layer after source/layer swaps.
  map.moveLayer(LA_LAYER_ID);

  const laFilter = getLocalAuthorityFilter();
  if (laFilter) {
    map.setFilter(LA_LAYER_ID, laFilter);
  } else {
    removeLocalAuthorityLayer();
  }
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
        ? "All UK: England/Wales 2019 + Scotland 2011 boundaries"
        : "Showing matching Local Authority boundaries for this view"
    : "Not available for Northern Ireland in this layer";
}

function isHealthBoundaryEnabledForCurrentNation(config) {
  return config.enabledIn.includes(currentNation);
}

function ensureHealthBoundarySource(config) {
  const sourceLayer = getHealthBoundaryViewName(
    config.sourceLayerBase,
    map.getZoom(),
  );

  if (map.getLayer(config.layerId)) {
    map.removeLayer(config.layerId);
  }

  if (map.getSource(config.sourceId)) {
    map.removeSource(config.sourceId);
  }

  map.addSource(config.sourceId, {
    type: "vector",
    tiles: [`${TILES_BASE_URL}/${sourceLayer}/{z}/{x}/{y}.pbf`],
    minzoom: 0,
    maxzoom: 14,
  });

  return sourceLayer;
}

function removeHealthBoundaryLayer(config) {
  if (map.getLayer(config.layerId)) {
    map.removeLayer(config.layerId);
  }
}

function updateHealthBoundaryLayer(boundaryKey) {
  const config = HEALTH_BOUNDARIES[boundaryKey];
  const toggle = document.getElementById(config.toggleId);
  const requested = !!toggle?.checked;
  const enabled = isHealthBoundaryEnabledForCurrentNation(config);

  if (!requested || !enabled) {
    removeHealthBoundaryLayer(config);
    return;
  }

  const sourceLayer = ensureHealthBoundarySource(config);

  if (!map.getLayer(config.layerId)) {
    map.addLayer({
      id: config.layerId,
      type: "line",
      source: config.sourceId,
      "source-layer": sourceLayer,
      paint: {
        "line-color": config.color,
        "line-width": [
          "interpolate",
          ["linear"],
          ["zoom"],
          4,
          config.widthBase * 0.6,
          7,
          config.widthBase,
          10,
          config.widthBase * 1.4,
        ],
        "line-opacity": 1,
      },
    });
  }

  map.moveLayer(config.layerId);
}

function updateHealthBoundaryLayers() {
  Object.keys(HEALTH_BOUNDARIES).forEach(updateHealthBoundaryLayer);
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
  });
}

function getColorExpression() {
  return [
    "case",
    ["==", ["get", "imd_decile"], 0],
    "#cccccc", // No data

    // England - Reds (darkest = most deprived)
    ["==", ["get", "nation"], "england"],
    [
      "interpolate",
      ["linear"],
      ["get", "imd_decile"],
      1,
      "#67000d", // Dark red
      3,
      "#a50f15",
      5,
      "#ef3b2c",
      7,
      "#fb6a4a",
      10,
      "#fee5d9", // Light red
    ],

    // Scotland - Blues
    ["==", ["get", "nation"], "scotland"],
    [
      "interpolate",
      ["linear"],
      ["get", "imd_decile"],
      1,
      "#08306b", // Dark blue
      3,
      "#2171b5",
      5,
      "#6baed6",
      7,
      "#bdd7e7",
      10,
      "#eff3ff", // Light blue
    ],

    // Wales - Greens
    ["==", ["get", "nation"], "wales"],
    [
      "interpolate",
      ["linear"],
      ["get", "imd_decile"],
      1,
      "#00441b", // Dark green
      3,
      "#238b45",
      5,
      "#74c476",
      7,
      "#bae4b3",
      10,
      "#edf8e9", // Light green
    ],

    // Northern Ireland - Yellows/Oranges
    ["==", ["get", "nation"], "northern_ireland"],
    [
      "interpolate",
      ["linear"],
      ["get", "imd_decile"],
      1,
      "#7f2704", // Dark orange
      3,
      "#d94801",
      5,
      "#fd8d3c",
      7,
      "#fdbe85",
      10,
      "#feedde", // Light yellow
    ],

    // Fallback
    "#cccccc",
  ];
}

function updateMapSource() {
  const newLayer = getViewName(effectiveEra(currentNation), map.getZoom());
  const newTiles = [`${TILES_BASE_URL}/${newLayer}/{z}/{x}/{y}.pbf`];

  const currentFilter = map.getFilter("deprivation-layer");

  if (map.getLayer("deprivation-layer")) {
    map.removeLayer("deprivation-layer");
  }
  if (map.getSource("deprivation-source")) {
    map.removeSource("deprivation-source");
  }

  map.addSource("deprivation-source", {
    type: "vector",
    tiles: newTiles,
    minzoom: 0,
    maxzoom: 14,
  });

  map.addLayer({
    id: "deprivation-layer",
    type: "fill",
    source: "deprivation-source",
    "source-layer": newLayer,
    paint: {
      "fill-color": getColorExpression(),
      "fill-opacity": 0.7,
      "fill-outline-color": "rgba(255, 255, 255, 0.2)",
    },
  });

  if (currentFilter) {
    map.setFilter("deprivation-layer", currentFilter);
  }

  updateLocalAuthorityLayer();
  updateHealthBoundaryLayers();

  console.log(`Switched to table: ${newLayer}, tiles: ${newTiles[0]}`);
}

map.on("load", () => {
  const initialLayer = getViewName(effectiveEra(currentNation), map.getZoom());

  map.addSource("deprivation-source", {
    type: "vector",
    tiles: [`${TILES_BASE_URL}/${initialLayer}/{z}/{x}/{y}.pbf`],
    minzoom: 0,
    maxzoom: 14,
  });

  map.addLayer({
    id: "deprivation-layer",
    type: "fill",
    source: "deprivation-source",
    "source-layer": initialLayer,
    paint: {
      "fill-color": getColorExpression(),
      "fill-opacity": 0.7,
      "fill-outline-color": "rgba(255, 255, 255, 0.2)",
    },
  });

  map.on("zoomend", updateMapSource);

  updateLocalAuthorityControlState();
  updateLocalAuthorityLayer();
  updateHealthBoundaryControlState();
  updateHealthBoundaryLayers();

  const popup = new maplibregl.Popup({
    closeButton: false,
    closeOnClick: false,
  });

  map.on("mousemove", "deprivation-layer", (e) => {
    map.getCanvas().style.cursor = "pointer";

    const feature = e.features[0];
    const props = feature.properties;

    const decile = getPropCaseInsensitive(props, ["imd_decile"]);
    const nation = getPropCaseInsensitive(props, ["nation"]);
    const areaName =
      getPropCaseInsensitive(props, [
        "area_name",
        "areaname",
        "name",
        "lsoa_name",
        "data_zone_name",
        "soa_name",
      ]) || "Unknown area";
    const areaCode =
      getPropCaseInsensitive(props, [
        "code",
        "lsoa_code",
        "data_zone_code",
        "soa_code",
      ]) || "Unknown code";
    const imdYear = getPropCaseInsensitive(props, ["imd_year", "year"]);
    const localAuthorityCode = getPropCaseInsensitive(props, [
      "la_code",
      "lad_code",
      "local_authority_code",
      "local_authority_district_code",
    ]);
    const localAuthorityName = getPropCaseInsensitive(props, [
      "la_name",
      "lad_name",
      "local_authority_name",
      "local_authority_district_name",
    ]);
    const localAuthorityYear = getPropCaseInsensitive(props, [
      "la_year",
      "lad_year",
      "local_authority_year",
      "local_authority_district_year",
    ]);
    const nhserCode = getPropCaseInsensitive(props, [
      "nhser_code",
      "nhs_region_code",
      "nhser21cd",
    ]);
    const nhserName = getPropCaseInsensitive(props, [
      "nhser_name",
      "nhs_region_name",
      "nhser21nm",
    ]);
    const icbCode = getPropCaseInsensitive(props, ["icb_code", "icb23cd"]);
    const icbName = getPropCaseInsensitive(props, ["icb_name", "icb23nm"]);
    const lhbCode = getPropCaseInsensitive(props, ["lhb_code", "lhb22cd"]);
    const lhbName = getPropCaseInsensitive(props, ["lhb_name", "lhb22nm"]);

    const areaLabel = nation
      ? `${String(nation).replace(/_/g, " ").toUpperCase()}`
      : "Area";

    // Look up the canonical boundary and IMD descriptions from DATASET_INFO
    // so the tooltip always reflects the actual dataset for each nation,
    // not just the raw era key (which would show "2011" for NI instead of "2001 SOAs").
    const eraKey = effectiveEra(nation);
    const datasetEntry =
      nation && DATASET_INFO[nation] && DATASET_INFO[nation][eraKey]
        ? DATASET_INFO[nation][eraKey]
        : null;
    const boundariesLabel = datasetEntry ? datasetEntry.boundaries : eraKey;
    const imdLabel = datasetEntry ? datasetEntry.imd : (imdYear ?? "Unknown");
    const localAuthorityLine =
      nation === "northern_ireland"
        ? "<div><strong>Local Government District:</strong> Not currently mapped in this layer</div>"
        : `
          <div><strong>Local Authority Name:</strong> ${localAuthorityName || "Unknown"}</div>
          <div><strong>Local Authority Code:</strong> ${localAuthorityCode || "Unknown"}</div>
          <div><strong>Local Authority Year:</strong> ${localAuthorityYear || "Unknown"}</div>
        `;
    const healthBoundaryLine =
      nation === "england"
        ? `
          <div><strong>NHS England Region:</strong> ${nhserName || "Not currently mapped in this layer"}</div>
          <div><strong>NHS England Region Code:</strong> ${nhserCode || "Unknown"}</div>
          <div><strong>Integrated Care Board:</strong> ${icbName || "Not currently mapped in this layer"}</div>
          <div><strong>Integrated Care Board Code:</strong> ${icbCode || "Unknown"}</div>
        `
        : nation === "wales"
          ? `
            <div><strong>Local Health Board:</strong> ${lhbName || "Not currently mapped in this layer"}</div>
            <div><strong>Local Health Board Code:</strong> ${lhbCode || "Unknown"}</div>
          `
          : "";

    const content = `
      <div style="padding: 5px;">
        <strong style="display: block; margin-bottom: 5px; border-bottom: 1px solid #ccc;">
          ${areaLabel}
        </strong>
        <div><strong>Name:</strong> ${areaName}</div>
        <div><strong>Code:</strong> ${areaCode}</div>
        ${localAuthorityLine}
        ${healthBoundaryLine}
        <div><strong>Decile:</strong> ${decile === 0 ? "No Data" : decile}</div>
        <div style="margin-top: 5px; font-size: 0.8em; color: #666;">
          Boundaries: ${boundariesLabel} | Index: ${imdLabel}
        </div>
      </div>
    `;

    popup.setLngLat(e.lngLat).setHTML(content).addTo(map);
  });

  map.on("mouseleave", "deprivation-layer", () => {
    map.getCanvas().style.cursor = "";
    popup.remove();
  });
});

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

  // Era toggle is only meaningful when England is the sole selected nation.
  const eraActive = selectedNation === "england";
  eraGroup.style.opacity = eraActive ? "1" : "0.45";
  eraSelect.disabled = !eraActive;
  noteEl.textContent = eraActive
    ? ""
    : selectedNation === "all"
      ? "All UK always shows latest data per country"
      : "Era selector applies to England only";

  const nations =
    selectedNation === "all"
      ? ["england", "wales", "scotland", "northern_ireland"]
      : [selectedNation];

  const lines = nations.map((n) => {
    // England uses chosen era; all others are fixed on 2011.
    const eraKey = n === "england" ? era : "2011";
    const d = DATASET_INFO[n][eraKey];
    const noteStr = d.note
      ? ` <span style="color:#9a6700;font-style:italic;">(${d.note})</span>`
      : "";
    return `<div><strong>${LABELS[n]}:</strong> ${d.imd} &middot; ${d.boundaries}${noteStr}</div>`;
  });

  infoEl.innerHTML = lines.join("");
}

document.getElementById("era-toggle").addEventListener("change", (e) => {
  currentEra = e.target.value;
  updateMapSource();
  updateDatasetInfo(currentNation, currentEra);
  updateLocalAuthorityControlState();
  updateLocalAuthorityLayer();
  updateHealthBoundaryControlState();
  updateHealthBoundaryLayers();
});

document.getElementById("nation-filter").addEventListener("change", (e) => {
  currentNation = e.target.value;
  const selectedNation = currentNation;
  map.setFilter(
    "deprivation-layer",
    selectedNation === "all" ? null : ["==", ["get", "nation"], selectedNation],
  );
  // Changing nation may change the effective era (England→2021, others→2011)
  updateMapSource();
  updateLegend(selectedNation);
  updateDatasetInfo(selectedNation, currentEra);
  updateLocalAuthorityControlState();
  updateLocalAuthorityLayer();
  updateHealthBoundaryControlState();
  updateHealthBoundaryLayers();
});

document.getElementById("la-toggle").addEventListener("change", (e) => {
  updateLocalAuthorityLayer();
});

document.getElementById("nhser-toggle").addEventListener("change", () => {
  updateHealthBoundaryLayer("nhser");
});

document.getElementById("icb-toggle").addEventListener("change", () => {
  updateHealthBoundaryLayer("icb");
});

document.getElementById("lhb-toggle").addEventListener("change", () => {
  updateHealthBoundaryLayer("lhb");
});

function updateLegend(nation) {
  const legendScale = document.querySelector(".legend-scale");

  let colors, title;

  if (nation === "all") {
    title = "Deprivation Decile (All Nations)";
    legendScale.innerHTML = `
      <div class="legend-item"><div class="color-box" style="background: #67000d;"></div> England - Most Deprived</div>
      <div class="legend-item"><div class="color-box" style="background: #08306b;"></div> Scotland - Most Deprived</div>
      <div class="legend-item"><div class="color-box" style="background: #00441b;"></div> Wales - Most Deprived</div>
      <div class="legend-item"><div class="color-box" style="background: #7f2704;"></div> N. Ireland - Most Deprived</div>
      <div class="legend-item"><div class="color-box" style="background: #cccccc;"></div> No Data</div>
    `;
  } else if (nation === "england") {
    title = "England Deprivation Decile";
    legendScale.innerHTML = `
      <div class="legend-item"><div class="color-box" style="background: #67000d;"></div> 1 (Most Deprived)</div>
      <div class="legend-item"><div class="color-box" style="background: #a50f15;"></div> 3</div>
      <div class="legend-item"><div class="color-box" style="background: #ef3b2c;"></div> 5</div>
      <div class="legend-item"><div class="color-box" style="background: #fb6a4a;"></div> 7</div>
      <div class="legend-item"><div class="color-box" style="background: #fee5d9;"></div> 10 (Least Deprived)</div>
      <div class="legend-item"><div class="color-box" style="background: #cccccc;"></div> No Data</div>
    `;
  } else if (nation === "scotland") {
    title = "Scotland Deprivation Decile";
    legendScale.innerHTML = `
      <div class="legend-item"><div class="color-box" style="background: #08306b;"></div> 1 (Most Deprived)</div>
      <div class="legend-item"><div class="color-box" style="background: #2171b5;"></div> 3</div>
      <div class="legend-item"><div class="color-box" style="background: #6baed6;"></div> 5</div>
      <div class="legend-item"><div class="color-box" style="background: #bdd7e7;"></div> 7</div>
      <div class="legend-item"><div class="color-box" style="background: #eff3ff;"></div> 10 (Least Deprived)</div>
      <div class="legend-item"><div class="color-box" style="background: #cccccc;"></div> No Data</div>
    `;
  } else if (nation === "wales") {
    title = "Wales Deprivation Decile";
    legendScale.innerHTML = `
      <div class="legend-item"><div class="color-box" style="background: #00441b;"></div> 1 (Most Deprived)</div>
      <div class="legend-item"><div class="color-box" style="background: #238b45;"></div> 3</div>
      <div class="legend-item"><div class="color-box" style="background: #74c476;"></div> 5</div>
      <div class="legend-item"><div class="color-box" style="background: #bae4b3;"></div> 7</div>
      <div class="legend-item"><div class="color-box" style="background: #edf8e9;"></div> 10 (Least Deprived)</div>
      <div class="legend-item"><div class="color-box" style="background: #cccccc;"></div> No Data</div>
    `;
  } else if (nation === "northern_ireland") {
    title = "Northern Ireland Deprivation Decile";
    legendScale.innerHTML = `
      <div class="legend-item"><div class="color-box" style="background: #7f2704;"></div> 1 (Most Deprived)</div>
      <div class="legend-item"><div class="color-box" style="background: #d94801;"></div> 3</div>
      <div class="legend-item"><div class="color-box" style="background: #fd8d3c;"></div> 5</div>
      <div class="legend-item"><div class="color-box" style="background: #fdbe85;"></div> 7</div>
      <div class="legend-item"><div class="color-box" style="background: #feedde;"></div> 10 (Least Deprived)</div>
      <div class="legend-item"><div class="color-box" style="background: #cccccc;"></div> No Data</div>
    `;
  }

  document.querySelector(".legend-title").textContent = title;
}

// Initialize legend and dataset info panel
updateLegend("all");
updateDatasetInfo("all", currentEra);
