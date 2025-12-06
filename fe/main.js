const { DeckGL, MVTLayer, TileLayer, BitmapLayer } = deck;
const { PMTiles } = pmtiles;
const { scaleSequential, interpolateViridis } = d3;

import { PMTilesLayer } from "./pmTilesLayer.js";
import { hexToRgb } from "./utils.js";

const pmTilesSource = new PMTiles('TILER_URL_PLACEHOLDER');

const isVisible = (route, year, distance) => {
  let minimumDistance = parseInt(distance);
  let routeDistance = parseInt(route.properties["Distance"]);

  return (
    (year     === "all" || (route.properties["Distinct Years"] || []).includes(year)) &&
    (distance === "all" || routeDistance > minimumDistance ))
}

const getLayers = (year, distance) => {
  return [
    new TileLayer({
      id: 'osm-basemap',
      data: 'https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
      minZoom: 0,
      maxZoom: 19,
      tileSize: 256,
      maxRequests: 10,
      renderSubLayers: props => {
              const {
                bbox: {west, south, east, north}
              } = props.tile;

              return new BitmapLayer({
                id: `${props.id}-bitmap`,
                image: props.data,
                bounds: [west, south, east, north]
              });
            }
    }),

    new PMTilesLayer({
      id: 'routes',
      data: 'pmtiles://{z}/{x}/{y}', // fake address
      pmTiles: pmTilesSource,
      minZoom: 0,
      maxZoom: 14,
      binary: false,
      getLineColor: d => {
        const props = d.properties;
        const years = props["Distinct Years"] || [];

        if (!isVisible(d, year, distance)) {
          return [200, 200, 200, 0];
        }
        const count = props["Distinct Rides"] || 1;
        const colorMap = scaleSequential(interpolateViridis).domain([1,25]);
        const color = colorMap(count+3);
        return hexToRgb(color);
      },
      getLineWidth: d => 20,
      lineWidthMinPixels: 2,
      pickable: true,
      autoHighlight: true,
      onClick: info => {
        if (!info.object) { return; }
        if (isVisible(info.object, year, distance)) {
          const props = info.object.properties;
          const propsHtml = Object.entries(props)
            .filter(([key, val]) => !["id", "layerName"].includes(key))
            .map(([key, val]) => `${key}: ${val}`)
            .join('<br>');
          document.getElementById('properties').innerHTML = propsHtml;
          document.getElementById('selected').style.display = 'block';
        }
      },
      updateTriggers: {
        getLineColor: [year, distance],
      },
    })
  ]
}

const map = new DeckGL({
  container: 'map',
  initialViewState: {
    // NOTE: CONUS
    // latitude: 39.8283,
    // longitude: -98.5795,
    // zoom: 4.0,
    // NOTE: plus Alaska, Hawaii, and Puerto Rico
    latitude: 45.0,
    longitude: -114.0,
    zoom: 3.1,
    pitch: 0,
    bearing: 0
  },
  getCursor: ({isDragging}) => isDragging ? 'grabbing' : 'crosshair',
  controller: true,
  layers: getLayers("all", "all"),
});

const filters = document.getElementById("filters");
filters.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = new FormData(filters);
  let year = data.get("year") || "all";
  let distance = data.get("distance") || "all";
  map.setProps({layers: getLayers(year, distance)});
});
