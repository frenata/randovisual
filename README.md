## RUSA historical perm visualizer

Goal: extract perm (and brevet?) data over the years and visualize it on a map.

<img width="2215" height="1239" alt="randovisual-2" src="https://github.com/user-attachments/assets/e72e5765-728f-4545-b0bd-50a7da5e48da" />

Roadmap:
 - [x] capture further metadata about routes from rusa
 - [x] don't refetch from rwgps if we already have the route data
 - [x] move db to a serverless db
 - [x] deploy to cloud
 - [x] provide some basic on-click details about the routes
 - [x] cache the tiler so we don't crush the db network egress
 - [ ] poke RUSA about whether this is possible to do for brevets
 - [ ] provide some FE filtering
 - [ ] improve route info panel
 - [ ] use TripsLayer to show routes populate over time
 - [ ] render 3d maps of the routes at high zooms
