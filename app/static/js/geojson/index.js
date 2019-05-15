mapboxgl.accessToken =
  "pk.eyJ1IjoicnNiYXVtYW5uIiwiYSI6IjdiOWEzZGIyMGNkOGY3NWQ4ZTBhN2Y5ZGU2Mzg2NDY2In0.jycgv7qwF8MMIWt4cT0RaQ";
var bounds = [
  [31.7645, 3.0865],
  [34.1937, 3.5282] 
  /** 
  [31.6711, 3.1222],
  [33.351059, 3.577842]
   *  [-75.04728500751165, 39.68392799015035],
  [-72.91058699000139, 41.87764500765852] 

  -80.415707,-210.585937,81.466261,276.679688

  32.7645,3.0865,33.2871,3.4926  ---  32.6711,3.1222,33.1937,3.5282

  */
];
var map = new mapboxgl.Map({
  container: "map",
  style: "mapbox://styles/mapbox/dark-v9",
  center: [32.879333, 3.299395],
  /** [3.294425, 32.875214] 3.337954,33.046875 center: 3.270775,32.840881 [-74.0059, 40.7128], [3.30146, 32.88627] */
  zoom: 10,
  minZoom: 9,
  maxZoom: 18,
  pitch: 40,
  maxBounds: bounds
});
function init() {
  map.addSource("veh-incidents-1", {
    type: "geojson",
    data:
      "/static/maps/nyc_pedcyc_collisions_1.geojson",
    buffer: 0,
    maxzoom: 12
  });
  map.addSource("veh-incidents-2", {
    type: "geojson",
    data:
      "/static/maps/nyc_pedcyc_collisions_2.geojson",
    buffer: 0,
    maxzoom: 12
  });
  if (window.location.search.indexOf("embed") !== -1) map.scrollZoom.disable();
  map.addLayer(
    {
      id: "veh-incd-1",
      type: "circle",
      source: "veh-incidents-1",
      paint: {
        "circle-color": {
          property: "CYC_INJ",
          type: "interval",
          stops: [[1, "orange"], [2, "red"]]
        },
        "circle-radius": {
          property: "CYC_INJ",
          base: 3,
          type: "interval",
          stops: [[1, 3], [2, 8], [3, 12]]
        },
        "circle-opacity": 0.8,
        "circle-blur": 0.5
      },
      filter: [">=", "CYC_INJ", 1]
    },
    "waterway-label"
  );
  map.addLayer(
    {
      id: "veh-incd-2",
      type: "circle",
      source: "veh-incidents-2",
      paint: {
        "circle-color": {
          property: "CYC_INJ",
          type: "interval",
          stops: [[1, "orange"], [2, "red"]]
        },
        "circle-radius": {
          property: "CYC_INJ",
          base: 3,
          type: "interval",
          stops: [[1, 3], [2, 8], [3, 12]]
        },
        "circle-opacity": 0.8,
        "circle-blur": 0.5
      },
      filter: [">=", "CYC_INJ", 1]
    },
    "waterway-label"
  );
  map.addLayer(
    {
      id: "veh-incd-base-1",
      type: "circle",
      source: "veh-incidents-1",
      paint: {
        "circle-color": "yellow",
        "circle-radius": 3,
        "circle-opacity": 0.3,
        "circle-blur": 1
      },
      filter: ["<", "CYC_INJ", 1]
    },
    "waterway-label"
  );
  map.addLayer(
    {
      id: "veh-incd-base-2",
      type: "circle",
      source: "veh-incidents-2",
      paint: {
        "circle-color": "yellow",
        "circle-radius": 3,
        "circle-opacity": 0.3,
        "circle-blur": 1
      },
      filter: ["<", "CYC_INJ", 1]
    },
    "waterway-label"
  );
}
map.once("style.load", function(e) {
  init();
  map.addControl(new mapboxgl.NavigationControl());
  map.on("click", function(e) {
    var features = map.queryRenderedFeatures(e.point, {
      layers: ["veh-incd-1", "veh-incd-2"]
    });
    if (!features.length) {
      return;
    }
    var feature = features[0];
    var popup = new mapboxgl.Popup()
      .setLngLat(map.unproject(e.point))
      .setHTML(
        "<h3>NSP Detail</h3>" +
          "<ul>" +
          "<li>Year: <b>" +
          feature.properties.YEAR +
          "</b></li>" +
          "<li>Patient Injuries: <b>" +
          feature.properties.PED_INJ +
          "</b></li>" +
          "<li>Related Fatalities: <b>" +
          feature.properties.PED_KIL +
          "</b></li>" +
          "<li>Family Illness: <b>" +
          feature.properties.CYC_INJ +
          "</b></li>" +
          "<li>Family Fatalities: <b>" +
          feature.properties.CYC_KIL +
          "</b></li>" +
          "</ul>"
      )
      .addTo(map);
  });
  //Hide loading bar once tiles from geojson are loaded
  map.on("data", function(e) {
    if (e.dataType === "source" && e.sourceId === "veh-incidents-1") {
      document.getElementById("loader").style.visibility = "hidden";
    }
  });
  // Use the same approach as above to indicate that the symbols are clickable
  // by changing the cursor style to 'pointer'.
  map.on("mousemove", function(e) {
    var features = map.queryRenderedFeatures(e.point, {
      layers: ["veh-incd-1", "veh-incd-2"]
    });
    map.getCanvas().style.cursor = features.length ? "pointer" : "";
  });
  var prop = document.getElementById("prop");
  prop.addEventListener("change", function() {
    map.setPaintProperty("veh-incd-1", "circle-color", {
      property: prop.value,
      type: "interval",
      stops: [[1, "orange"], [2, "red"]]
    });
    map.setPaintProperty("veh-incd-2", "circle-color", {
      property: prop.value,
      type: "interval",
      stops: [[1, "orange"], [2, "red"]]
    });
    map.setPaintProperty("veh-incd-1", "circle-radius", {
      property: prop.value,
      base: 3,
      type: "interval",
      stops: [[1, 3], [2, 6], [3, 9]]
    });
    map.setPaintProperty("veh-incd-2", "circle-radius", {
      property: prop.value,
      base: 3,
      type: "interval",
      stops: [[1, 3], [2, 6], [3, 9]]
    });
    map.setFilter("veh-incd-1", [">=", prop.value, 1]);
    map.setFilter("veh-incd-2", [">=", prop.value, 1]);
  });
});