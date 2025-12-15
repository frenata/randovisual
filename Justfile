PROJECT_ID := "randovisual"
REGION := "us-west1"
REGISTRY := REGION + "-docker.pkg.dev/" + PROJECT_ID + "/randovisual"

# Authenticate with GCP
auth:
    gcloud auth login
    gcloud config set project {{PROJECT_ID}}
    gcloud auth print-access-token | docker login -u oauth2accesstoken --password-stdin https://{{REGION}}-docker.pkg.dev

# Build and push API image
build-api:
    cd be && docker build -t {{REGISTRY}}/api:latest .
    docker push {{REGISTRY}}/api:latest
    gcloud run services update randovisual-api --region={{REGION}} --image={{REGISTRY}}/api:latest

# Build and push FE image
build-fe:
    cd fe && docker build -t {{REGISTRY}}/fe:latest .
    docker push {{REGISTRY}}/fe:latest
    gcloud run services update randovisual-fe --region={{REGION}} --image={{REGISTRY}}/fe:latest

# Build and push tiler image
# build-tiler:
#     cd tiler && docker build -t {{REGISTRY}}/tiler:latest .
#     docker push {{REGISTRY}}/tiler:latest
#     gcloud run services update randovisual-tiler --region={{REGION}} --image={{REGISTRY}}/tiler:latest

# Build and push all images
build-all: build-api build-fe

# Call authenticated API endpoint
api endpoint:
    @curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
        $(cd infra && terraform output -raw api_url){{endpoint}}

dump-geojson:
    psql $DATABASE_URL -t -A -c "select * from rides_geojson where route->>'geometry' is not null;" > data/routes.geojson

generate-pmtiles:
    docker run --rm \
        --network host \
        -v $PWD:/data \
        metacollin/tippecanoe:latest \
        tippecanoe -o /data/data/routes.mbtiles \
          --force \
          -Z0 -z14 \
          --drop-densest-as-needed \
          --coalesce-densest-as-needed \
          --extend-zooms-if-still-dropping \
          /data/data/routes.geojson
    docker run --rm \
            -v $PWD:/data \
            ghcr.io/protomaps/go-pmtiles:latest \
            convert /data/data/routes.mbtiles /data/data/routes.pmtiles

push-pmtiles:
  gcloud storage cp data/routes.pmtiles gs://randovisual-tiles/

test: test-be

lint: lint-be

[working-directory: 'be']
lint-be:
  uv run ruff check
  uv run ty check
  uv run ruff format --check

[working-directory: 'be']
test-be file='':
  uv run pytest {{file}}

[working-directory: 'be']
coverage format='term':
  uv run pytest --cov=randovisual --cov-branch --cov-report={{format}} --junitxml=junit.xml -o junit_family=legacy
