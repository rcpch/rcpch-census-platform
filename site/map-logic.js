const map = new maplibregl.Map({
  container: "map",
  style: "https://tiles.stadiamaps.com/styles/alidade_smooth.json",
  center: [-3.43, 55.37],
  zoom: 5,
  refreshExpired: true, // Helps with local dev updates
});

function getTilesBaseUrl() {
  const params = new URLSearchParams(window.location.search);
  const fromQuery = params.get("tilesBase");
  if (fromQuery) return fromQuery.replace(/\/+$|/, "");

  const meta = document.querySelector('meta[name="rcpch-tiles-base-url"]');
  const fromMeta = meta?.getAttribute("content")?.trim();
  if (fromMeta) return fromMeta.replace(/\/+$|/, "");

  // Use injected config if present (from config.js)
  if (typeof window.PUBLIC_TILES_URL === "string" && window.PUBLIC_TILES_URL) {
    return window.PUBLIC_TILES_URL.replace(/\/+$|/, "");
  }

  if (
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1"
  ) {
    return "http://localhost:7800";
  }

  return "";
}

const TILES_BASE_URL = getTilesBaseUrl();
if (!TILES_BASE_URL) {
  console.warn(
    "No tiles base URL configured. Set ?tilesBase=https://<host>/tiles, the rcpch-tiles-base-url meta tag, or inject window.PUBLIC_TILES_URL."
  );
}

// State management
let currentEra = "2021";

function getViewName(era, zoom) {
  // Matches your SQL view suffixes
  const zoomSuffix = zoom <= 4 ? "z0_4" : zoom <= 7 ? "z5_7" : "z8_10";
  return `public.uk_master_${era}_${zoomSuffix}`;
}

function updateMapSource() {
  const newLayer = getViewName(currentEra, map.getZoom());
  const newTiles = [`${TILES_BASE_URL}/${newLayer}/{z}/{x}/{y}.pbf`];

  const source = map.getSource("deprivation-source");
  if (source) {
    // 1. Update the tiles on the source
    source.setTiles(newTiles);

    // 2. We must recreate the layer to change the 'source-layer'
    if (map.getLayer("deprivation-layer")) {
      // Record the current nation filter so we can re-apply it
      const currentFilter = map.getFilter("deprivation-layer");

      map.removeLayer("deprivation-layer");

      map.addLayer({
        id: "deprivation-layer",
        type: "fill",
        source: "deprivation-source",
        "source-layer": newLayer, // This is the vital part
        paint: {
          "fill-color": [
            "case",
            ["==", ["get", "imd_decile"], 0],
            "#cccccc",
            [
              "interpolate",
              ["linear"],
              ["get", "imd_decile"],
              1,
              "#08306b",
              10,
              "#f7fbff",
            ],
          ],
          "fill-opacity": 0.7,
          "fill-outline-color": "rgba(255, 255, 255, 0.2)",
        },
      });

      // 3. Re-apply the filter (England/Scotland/etc) if one was active
      if (currentFilter) {
        map.setFilter("deprivation-layer", currentFilter);
      }

      console.log(`Switched to table: ${newLayer}`);
    }
  }
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
      "fill-color": [
        "case",
        ["==", ["get", "imd_decile"], 0],
        "#cccccc", // Gray fallback
        [
          "interpolate",
          ["linear"],
          ["get", "imd_decile"],
          1,
          "#08306b",
          10,
          "#f7fbff",
        ],
      ],
      "fill-opacity": 0.7,
      "fill-outline-color": "rgba(255, 255, 255, 0.2)", // Subtle outlines
    },
  });

  // --- AUTOMATIC ZOOM SWITCHING ---
  // This ensures that when a user zooms from 4 to 5,
  // the source switches from the z0_4 table to the z5_7 table.
  map.on("zoomend", updateMapSource);

  // Create a single popup instance (reused on hover)
  const popup = new maplibregl.Popup({
    closeButton: false,
    closeOnClick: false,
  });

  map.on("mousemove", "deprivation-layer", (e) => {
    // Change the cursor style as a UI cue
    map.getCanvas().style.cursor = "pointer";

    const feature = e.features[0];
    const props = feature.properties;
    const decile = props.imd_decile;

    // Create the HTML content for the popup
    const content = `
      <div style="padding: 5px;">
        <strong style="display: block; margin-bottom: 5px; border-bottom: 1px solid #ccc;">
          ${props.nation.toUpperCase()} LSOA
        </strong>
        <div><strong>Code:</strong> ${props.code}</div>
        <div><strong>Decile:</strong> ${decile === 0 ? "No Data" : decile}</div>
        <div style="margin-top: 5px; font-size: 0.8em; color: #666;">
          Era: ${currentEra} | Data Year: ${props.imd_year}
        </div>
      </div>
    `;

    // Position and display the popup
    popup.setLngLat(e.lngLat).setHTML(content).addTo(map);
  });

  map.on("mouseleave", "deprivation-layer", () => {
    map.getCanvas().style.cursor = "";
    popup.remove();
  });
});

// --- THE ERA TOGGLE ---
document.getElementById("era-toggle").addEventListener("change", (e) => {
  currentEra = e.target.value; // Update state
  updateMapSource(); // Trigger update
});

document.getElementById("nation-filter").addEventListener("change", (e) => {
  const selectedNation = e.target.value;
  map.setFilter(
    "deprivation-layer",
    selectedNation === "all" ? null : ["==", ["get", "nation"], selectedNation]
  );
});
