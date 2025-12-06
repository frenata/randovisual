const { DeckGL, MVTLayer, TileLayer, BitmapLayer } = deck;
const { PMTiles } = pmtiles;
const { scaleSequential, interpolateViridis } = d3;

import { PMTilesLayer } from "./pmTilesLayer.js";
import { hexToRgb } from "./utils.js";

const pmTilesSource = new PMTiles('TILER_URL_PLACEHOLDER');

const getLayers = (year) => {
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

        if (year !== "all" && !years.includes(parseInt(year))) {
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
        if (info.object && (year === "all" || (info.object.properties["Distinct Years"] || []).includes(year) )) {
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
        getLineColor: [year],
      },
    })
  ]
}

const map = new DeckGL({
  container: 'map',
  initialViewState: {
    latitude: 39.8283,
    longitude: -98.5795,
    zoom: 4,
    pitch: 0,
    bearing: 0
  },
  getCursor: ({isDragging}) => isDragging ? 'grabbing' : 'crosshair',
  controller: true,
  layers: getLayers("all"),
});

const filters = document.getElementById("filters");
filters.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = new FormData(filters);
  let year = data.get("year") || "all";
  map.setProps({layers: getLayers(year)});
});
