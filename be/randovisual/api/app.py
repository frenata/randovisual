import fastapi
from . import extract

app = fastapi.FastAPI()
app.include_router(extract.router)
