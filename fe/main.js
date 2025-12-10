const { DeckGL, MVTLayer, TileLayer, BitmapLayer, DataFilterExtension } = deck;
const { PMTiles } = pmtiles;
const { scaleSequential, interpolateViridis } = d3;

import { PMTilesLayer } from "./pmTilesLayer.js";
import { hexToRgb } from "./utils.js";

const isVisible = (year, distance, riders, route) => {
  let minimumDistance = parseInt(distance);
  let routeDistance = parseInt(route.properties["Distance"]);
  let minimumRiders = parseInt(riders);
  let routeRiders   = parseInt(route.properties["Distinct Riders"]);

  return +(
    (year     === "all" || (route.properties["Distinct Years"] || []).includes(year)) &&
    (distance === "all" || routeDistance > minimumDistance ) &&
    (riders   === "all" || routeRiders   > minimumRiders )
  )
}

const tilerUrl = 'TILER_URL_PLACEHOLDER';
const tilerClass = (tilerUrl.includes("pmtiles")) ? PMTilesLayer : MVTLayer; 
const tilerData = (tilerUrl.includes("pmtiles")) ? new PMTiles('TILER_URL_PLACEHOLDER') : `${tilerUrl}/public.ride_routes/{z}/{x}/{y}.pbf`;

const getLayers = (year, distance, riders, hoverID) => {
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

    new tilerClass({
      id: 'routes',
      data: tilerData,
      minZoom: 0,
      maxZoom: 14,
      binary: false,
      getLineColor: d => {
        if (d.properties.ID === hoverID) {
          return [255, 0, 0, 200];
        }
        const props = d.properties;
        const count = year === "all" ? props["Distinct Rides"] : JSON.parse(props["Rides By Year"])[year];
        const colorMap = scaleSequential(interpolateViridis).domain([1,25]);
        const color = colorMap(count+3);
        return hexToRgb(color);
      },
      getFilterValue: d => isVisible(year, distance, riders, d),
      filterRange: [1, 1],
      extensions: [new DataFilterExtension({filterSize: 1})],
      getLineWidth: d => { return d.properties.ID === hoverID ? 100 : 20 },
      getRadius: d => { return d.properties.ID === hoverID ? 12 : 5 },
      lineWidthMinPixels: 2,
      pickable: true,
      onClick: d => { resetMap(setRouteInfo(year, distance, riders, d)) },
      onHover: d => { resetMap(setRouteInfo(year, distance, riders, d)) },
      updateTriggers: {
        getFilterValue: [year, distance, riders],
        getLineColor: [year, distance, hoverID],
        getRadius: [hoverID],
        getLineWidth: [hoverID],
        getPosition: [hoverID], // TODO: try to 'lift' the hovered route to the top?
      },
    })
  ]
}

const renderProp = ([key, val]) => {
  if (key == "Distinct Years") {
    val = JSON.parse(val);
  } else if (key == "RWGPS URL") {
    val = `<a href="https://${val}">${val}</a>`;
  }
  return `
    <span class='label'>${key}</span>
    <span class='value'>${val}</span>
  `
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
  layers: getLayers("all", "all", "all", null),
});

const filters = document.getElementById("filters");

filters.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = new FormData(filters);
  let year = data.get("year") || "all";
  let distance = data.get("distance") || "all";
  let riders = data.get("riders") || "all";
  map.setProps({layers: getLayers(year, distance, riders, null)});
});

function resetMap(info) {
  if (info && info.object) {
    const data = new FormData(filters);
    let year = data.get("year") || "all";
    let distance = data.get("distance") || "all";
    let riders = data.get("riders") || "all";
    map.setProps({layers: getLayers(year, distance, riders, info.object.properties.ID)});
  }
  return info;
}

function setRouteInfo(year, distance, riders, info) {
  if (!info.object) { return; }
  if (isVisible(year, distance, riders, info.object)) {
    const props = info.object.properties;
    const noDisplay = ["id", "layerName", "Name", "Rides By Year"];
    const propsHtml = Object.entries(props)
      .filter(([key, val]) => !noDisplay.includes(key))
      .map(renderProp)
      .join('<br/>');
    document.getElementById("routeName").innerHTML = props["Name"] || "";
    document.getElementById('properties').innerHTML = "<div class='spacer'></div>" + propsHtml;
    document.getElementById('selected').style.display = 'block';
    document.getElementById('info').style.display = 'block';
  }
  return info;
}

addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    document.getElementById("routeName").innerHTML = "";
    document.getElementById('properties').innerHTML = "";
    document.getElementById('selected').style.display = 'none';
    document.getElementById('info').style.display = 'none';
  }
});
