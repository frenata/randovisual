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
    docker build -t {{REGISTRY}}/api:latest -f randovisual/Dockerfile .
    docker push {{REGISTRY}}/api:latest

# Build and push FE image
build-fe:
    cd fe && docker build -t {{REGISTRY}}/fe:latest .
    docker push {{REGISTRY}}/fe:latest

# Build and push tiler image
build-tiler:
    cd tiler && docker build -t {{REGISTRY}}/tiler:latest .
    docker push {{REGISTRY}}/tiler:latest

# Build and push all images
build-all: build-api build-fe build-tiler

# Call authenticated API endpoint
api endpoint:
    @curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
        $(cd infra && terraform output -raw api_url){{endpoint}}
