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

let currentEra = "2021";

function getViewName(era, zoom) {
  const zoomSuffix = zoom <= 4 ? "z0_4" : zoom <= 7 ? "z5_7" : "z8_10";
  return `public.uk_master_${era}_${zoomSuffix}`;
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
  const newLayer = getViewName(currentEra, map.getZoom());
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

  console.log(`Switched to table: ${newLayer}, tiles: ${newTiles[0]}`);
}

map.on("load", () => {
  const initialLayer = getViewName(currentEra, map.getZoom());

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

    const areaTypeLabel =
      {
        england: "LSOA",
        wales: "LSOA",
        scotland: "Data Zone",
        northern_ireland: "SOA",
      }[nation] || "Area";
    const areaLabel = nation
      ? `${String(nation).replace(/_/g, " ").toUpperCase()} — ${areaTypeLabel}`
      : "Area";

    const content = `
      <div style="padding: 5px;">
        <strong style="display: block; margin-bottom: 5px; border-bottom: 1px solid #ccc;">
          ${areaLabel}
        </strong>
        <div><strong>Name:</strong> ${areaName}</div>
        <div><strong>Code:</strong> ${areaCode}</div>
        <div><strong>Decile:</strong> ${decile === 0 ? "No Data" : decile}</div>
        <div style="margin-top: 5px; font-size: 0.8em; color: #666;">
          Boundary Year: ${currentEra} | IMD Data Year: ${imdYear ?? "Unknown"}
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

document.getElementById("era-toggle").addEventListener("change", (e) => {
  currentEra = e.target.value;
  updateMapSource();
});

document.getElementById("nation-filter").addEventListener("change", (e) => {
  const selectedNation = e.target.value;
  map.setFilter(
    "deprivation-layer",
    selectedNation === "all" ? null : ["==", ["get", "nation"], selectedNation],
  );

  // Update legend
  updateLegend(selectedNation);
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

// Initialize legend
updateLegend("all");
