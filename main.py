from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from poly_query import Poly_Query
from poly_query_old import Poly_Query_Old
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title='Polygon Querying of NLDI for catchments and flowlines',
    root_path='/nldipolygonservices'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Item(BaseModel):
    data: dict
    return_flowlines: bool
    return_gages: bool
    downstream_dist: float

# Redirect root and /settings.SERVICE_NAME to the docs
@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Hello World"}


@app.post("/nldi_poly_query_new/")
async def query_poly(request: Item):

    # Use post operation to process geojson object with polygons to query.
    # Includes two additional params to use in the query.
    content = request.data
    return_flowlines = request.return_flowlines
    return_gages = request.return_gages
    downstream_dist = request.downstream_dist

    try:
        results = Poly_Query(content, return_flowlines, return_gages, downstream_dist)
        results = results.serialize()

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class Item_Old(BaseModel):
    data: dict
    get_flowlines: bool
    downstream_dist: float


@app.post("/nldi_poly_query/")
async def query_poly_old(request: Item_Old):

    # Use post operation to process geojson object with polygons to query.
    # Includes two additional params to use in the query.
    content = request.data
    get_flowlines = request.get_flowlines
    downstream_dist = request.downstream_dist

    try:
        results = Poly_Query_Old(content, get_flowlines, downstream_dist)
        results = results.serialize()

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
