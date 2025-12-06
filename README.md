## RandoVisual

Goal: extract RUSA perm (and brevet?) data over the years and visualize it on a map.

<img width="1577" height="1246" alt="randovisual-3" src="https://github.com/user-attachments/assets/d536ad9a-52c1-42b1-a7b0-fd8ac811d54b" />

Roadmap:
 - [x] capture further metadata about routes from rusa
 - [x] don't refetch from rwgps if we already have the route data
 - [x] move db to a serverless db
 - [x] deploy to cloud
 - [x] provide some basic on-click details about the routes
 - [x] cache the tiler so we don't crush the db network egress
 - [x] use PMTiles to not even need to dynamically tile anything
 - [ ] poke RUSA about whether this is possible to do for brevets
 - [ ] provide some FE filtering
   - [ ] start with changing year this way rather than via query param
 - [x] improve route info panel
 - [ ] use TripsLayer to show routes populate over time
 - [ ] render 3d maps of the routes at high zooms
 - [ ] colorize routes based on rides done *in that year*
