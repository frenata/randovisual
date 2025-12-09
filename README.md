## RandoVisual

While existing [tools](https://rusa.bike/) are excellent for searching out permament [RUSA](https://rusa.org/) routes *for riding*, I wanted to examine the riding *history* of the club. RandoVisual thus makes no effort to render or display all possible routes and will likely never build a listing of routes or search-oriented tools. Instead it tries to answer the question: "what have we collectively done?".

Secondarily, thanks to no small part to my [dayjob](https://www.overstory.com/) I have an interest in exploring techniques to make exploring very large datasets *blazing fast*. RandoVisual thus serves as an outlet for experimentation of technique.

<img width="1713" height="1249" alt="randovisual-4" src="https://github.com/user-attachments/assets/04ccda03-2afb-484e-8c27-87123b7b5089" />

### Technical Details

TODO :)

### Roadmap

 - [x] capture further metadata about routes from rusa
 - [x] don't refetch from rwgps if we already have the route data
 - [x] move db to a serverless db
 - [x] deploy to cloud
 - [x] provide some basic on-click details about the routes
 - [x] cache the tiler so we don't crush the db network egress
 - [x] use PMTiles to not even need to dynamically tile anything
 - [ ] poke RUSA about whether this is possible to do for brevets
 - [x] provide some FE filtering
   - [x] start with changing year this way rather than via query param
   - [x] distance
   - [ ] # of riders
 - [x] improve route info panel
 - [ ] use TripsLayer to show routes populate over time
 - [ ] render 3d maps of the routes at high zooms
 - [x] colorize routes based on rides done *in that year*
 - [ ] move FE assets to a CDN
 - [ ] build a new BE extractor to grab ride by *year* or *month* rather than by rider
 - [x] bug: non-visible routes can prevent selecting visible routes
 - [x] highlight and show route info on hover
