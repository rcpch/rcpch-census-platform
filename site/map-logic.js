const map = new maplibregl.Map({
  container: "map",
  style: "https://demotiles.maplibre.org/style.json", // Basic basemap
  center: [-3.43, 55.37], // Center of UK
  zoom: 5,
});

map.on("load", () => {
  // 1. ADD THE SOURCE
  map.addSource("deprivation-data", {
    type: "vector",
    // You MUST provide the full URL with {z}/{x}/{y}
    tiles: [
      "http://localhost:7800/public.uk_master_tiles_z8_10/{z}/{x}/{y}.pbf",
    ],
    minzoom: 4,
    maxzoom: 14,
  });

  // 2. ADD THE LAYER
  map.addLayer({
    id: "deprivation-layer",
    type: "fill",
    source: "deprivation-data",
    // Keep the 'public.' prefix here
    "source-layer": "public.uk_master_tiles_z8_10",
    paint: {
      "fill-color": [
        "interpolate",
        ["linear"],
        // Double check if your column is 'imd_decile' or just 'decile' in the SQL View
        ["get", "imd_decile"],
        1,
        "#800026",
        10,
        "#ffffcc",
      ],
      "fill-opacity": 0.6,
    },
  });
});

// 3. THE TOGGLE LOGIC (Filtering in the client!)
document.getElementById("nation-filter").addEventListener("change", (e) => {
  const selectedNation = e.target.value;

  if (selectedNation === "all") {
    map.setFilter("deprivation-layer", null); // Show everything
  } else {
    // Only show polygons where the "nation" property matches
    map.setFilter("deprivation-layer", [
      "==",
      ["get", "nation"],
      selectedNation,
    ]);
  }
});
